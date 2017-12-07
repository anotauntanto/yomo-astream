#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Cise Midoglu (based on code by Parikshit Juluri, Andra Lutu, Jonas Karlsson)
# Date: October 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple experiment template to collect metdata and run an experiment.

The script will execute a experiment (DASH player -- AStream) on a interface with a specified
operator and log the gps position during the experiment.
The output will be formated into a json object.

The experiment received the target MPD file and the number of segments to download.
"""
import io
import json
#import zmq
import os
import sys
import netifaces
import time
from subprocess import check_output, CalledProcessError
from multiprocessing import Process, Manager
from dash_client import *
#from configure_log_file import configure_log_file, write_json
import logging
import config_dash
from dash_buffer import *
from adaptation import basic_dash, basic_dash2, weighted_dash, netflix_dash
from adaptation.adaptation import WeightedMean
import subprocess
from subprocess import call
import numpy
#import csv
import pandas

# Globals for arg parser with the default values
MPD = "http://128.39.37.161:12345/BigBuckBunny_4s.mpd"
DOWNLOAD_CHUNK = 1024
DOWNLOAD = False
SEGMENT_LIMIT = 100
WAIT_SECONDS = 5
#exp_grace = 120
#ifup_interval_check = 5

class DashPlayback:
    """
    Audio[bandwidth] : {duration, url_list}
    Video[bandwidth] : {duration, url_list}
    """
    def __init__(self):

        self.min_buffer_time = None
        self.playback_duration = None
        self.audio = dict()
        self.video = dict()

def start_playback_smart(dash_player, dp_object, domain, playback_type=None, download=False, video_segment_duration=None, ifname=None, segment_limit=SEGMENT_LIMIT):
    """ Module that downloads the MPD-FIle and download
        all the representations of the Module to download
        the MPEG-DASH media.
        Example: start_playback_smart(dp_object, domain, "SMART", DOWNLOAD, video_segment_duration)

        :param dp_object:       The DASH-playback object
        :param domain:          The domain name of the server (The segment URLS are domain + relative_address)
        :param playback_type:   The type of playback
                                1. 'BASIC' - The basic adapataion scheme
                                2. 'SARA' - Segment Aware Rate Adaptation
                                3. 'NETFLIX' - Buffer based adaptation used by Netflix
        :param download: Set to True if the segments are to be stored locally (Boolean). Default False
        :param video_segment_duration: Playback duration of each segment
        :return:
    """

    # A folder to save the segments in
    file_identifier = id_generator(ifname)
    config_dash.LOG.info("The segments are stored in %s" % file_identifier)
    dp_list = defaultdict(defaultdict)
    # Creating a Dictionary of all that has the URLs for each segment and different bitrates
    for bitrate in dp_object.video:
        # Getting the URL list for each bitrate
        dp_object.video[bitrate] = read_mpd.get_url_list(dp_object.video[bitrate], video_segment_duration,
                                                         dp_object.playback_duration, bitrate)
        if "$Bandwidth$" in dp_object.video[bitrate].initialization:
            dp_object.video[bitrate].initialization = dp_object.video[bitrate].initialization.replace(
                "$Bandwidth$", str(bitrate))
        media_urls = [dp_object.video[bitrate].initialization] + dp_object.video[bitrate].url_list
        for segment_count, segment_url in enumerate(media_urls, dp_object.video[bitrate].start):
            # segment_duration = dp_object.video[bitrate].segment_duration
            dp_list[segment_count][bitrate] = segment_url
    bitrates = dp_object.video.keys()
    bitrates.sort()
    average_dwn_time = 0
    segment_files = []
    # For basic adaptation
    previous_segment_times = []
    recent_download_sizes = []
    weighted_mean_object = None
    current_bitrate = bitrates[0]
    previous_bitrate = None
    total_downloaded = 0
    # Delay in terms of the number of segments
    delay = 0
    segment_duration = 0
    segment_size = segment_download_time = None
    # Netflix Variables
    average_segment_sizes = netflix_rate_map = None
    netflix_state = "INITIAL"
    # Start playback of all the segments
    for segment_number, segment in enumerate(dp_list, dp_object.video[current_bitrate].start):
        config_dash.LOG.info(" {}: Processing the segment {}".format(playback_type.upper(), segment_number))
        #write_json()
        if not previous_bitrate:
            previous_bitrate = current_bitrate
        if segment_limit:
            if not dash_player.segment_limit:
                dash_player.segment_limit = int(segment_limit)
            if segment_number > int(segment_limit):
                config_dash.LOG.info("Segment limit reached")
                break
        if segment_number == dp_object.video[bitrate].start:
            current_bitrate = bitrates[0]
        else:
            if playback_type.upper() == "BASIC":
                current_bitrate, average_dwn_time = basic_dash2.basic_dash2(segment_number, bitrates, average_dwn_time,
                                                                            recent_download_sizes,
                                                                            previous_segment_times, current_bitrate)

                if dash_player.buffer.qsize() > config_dash.BASIC_THRESHOLD:
                    delay = dash_player.buffer.qsize() - config_dash.BASIC_THRESHOLD
                config_dash.LOG.info("Basic-DASH: Selected {} for the segment {}".format(current_bitrate,
                                                                                         segment_number + 1))
            elif playback_type.upper() == "SMART":
                if not weighted_mean_object:
                    weighted_mean_object = WeightedMean(config_dash.SARA_SAMPLE_COUNT)
                    config_dash.LOG.debug("Initializing the weighted Mean object")
                # Checking the segment number is in acceptable range
                if segment_number < len(dp_list) - 1 + dp_object.video[bitrate].start:
                    try:
                        current_bitrate, delay = weighted_dash.weighted_dash(bitrates, dash_player,
                                                                             weighted_mean_object.weighted_mean_rate,
                                                                             current_bitrate,
                                                                             get_segment_sizes(dp_object,
                                                                                               segment_number+1))
                    except IndexError, e:
                        config_dash.LOG.error(e)

            elif playback_type.upper() == "NETFLIX":
                config_dash.LOG.info("Playback is NETFLIX")
                # Calculate the average segment sizes for each bitrate
                if not average_segment_sizes:
                    average_segment_sizes = get_average_segment_sizes(dp_object)
                if segment_number < len(dp_list) - 1 + dp_object.video[bitrate].start:
                    try:
                        if segment_size and segment_download_time:
                            segment_download_rate = segment_size / segment_download_time
                        else:
                            segment_download_rate = 0
                        current_bitrate, netflix_rate_map, netflix_state = netflix_dash.netflix_dash(
                            bitrates, dash_player, segment_download_rate, current_bitrate, average_segment_sizes,
                            netflix_rate_map, netflix_state)
                        config_dash.LOG.info("NETFLIX: Next bitrate = {}".format(current_bitrate))
                    except IndexError, e:
                        config_dash.LOG.error(e)
                else:
                    config_dash.LOG.critical("Completed segment playback for Netflix")
                    break

                # If the buffer is full wait till it gets empty
                if dash_player.buffer.qsize() >= config_dash.NETFLIX_BUFFER_SIZE:
                    delay = (dash_player.buffer.qsize() - config_dash.NETFLIX_BUFFER_SIZE + 1) * segment_duration
                    config_dash.LOG.info("NETFLIX: delay = {} seconds".format(delay))
            else:
                config_dash.LOG.error("Unknown playback type:{}. Continuing with basic playback".format(playback_type))
                current_bitrate, average_dwn_time = basic_dash.basic_dash(segment_number, bitrates, average_dwn_time,
                                                                          segment_download_time, current_bitrate)
        segment_path = dp_list[segment][current_bitrate]
        segment_url = urlparse.urljoin(domain, segment_path)
        config_dash.LOG.info("{}: Segment URL = {}".format(playback_type.upper(), segment_url))
        if delay:
            delay_start = time.time()
            config_dash.LOG.info("SLEEPING for {}seconds ".format(delay*segment_duration))
            while time.time() - delay_start < (delay * segment_duration):
                time.sleep(1)
            delay = 0
            config_dash.LOG.debug("SLEPT for {}seconds ".format(time.time() - delay_start))
        start_time = timeit.default_timer()
        try:
            segment_size, segment_filename = download_segment(segment_url, file_identifier)
            config_dash.LOG.info("{}: Downloaded segment {}".format(playback_type.upper(), segment_url))
        except IOError, e:
            config_dash.LOG.error("Unable to save segment %s" % e)
            return None
        segment_download_time = timeit.default_timer() - start_time
        previous_segment_times.append(segment_download_time)
        recent_download_sizes.append(segment_size)
        # Updating the JSON information
        segment_name = os.path.split(segment_url)[1]
        if "segment_info" not in config_dash.JSON_HANDLE:
            config_dash.JSON_HANDLE["segment_info"] = list()
        config_dash.JSON_HANDLE["segment_info"].append((segment_name, current_bitrate, segment_size,
                                                        segment_download_time))
        total_downloaded += segment_size
        config_dash.LOG.info("{} : The total downloaded = {}, segment_size = {}, segment_number = {}".format(
            playback_type.upper(),
            total_downloaded, segment_size, segment_number))
        if playback_type.upper() == "SMART" and weighted_mean_object:
            weighted_mean_object.update_weighted_mean(segment_size, segment_download_time)

        segment_info = {'playback_length': video_segment_duration,
                        'size': segment_size,
                        'bitrate': current_bitrate,
                        'data': segment_filename,
                        'URI': segment_url,
                        'segment_number': segment_number}
        segment_duration = segment_info['playback_length']
        dash_player.write(segment_info)
        segment_files.append(segment_filename)
        config_dash.LOG.info("Downloaded %s. Size = %s in %s seconds" % (
            segment_url, segment_size, str(segment_download_time)))
        if previous_bitrate:
            if previous_bitrate < current_bitrate:
                config_dash.JSON_HANDLE['playback_info']['up_shifts'] += 1
            elif previous_bitrate > current_bitrate:
                config_dash.JSON_HANDLE['playback_info']['down_shifts'] += 1
            previous_bitrate = current_bitrate
    # AEL -- moved this to the run_exp function to integrate with MONROE
    # waiting for the player to finish playing
    while dash_player.playback_state not in dash_buffer.EXIT_STATES:
        time.sleep(1)
    write_json()
    if not download:
        clean_files(file_identifier)

def print_representations(dp_object):
    """ Module to print the representations"""
    print "The DASH media has the following video representations/bitrates"
    for bandwidth in dp_object.video:
        print bandwidth

def run_astream(video_id,server_host,server_port,algorithm,segment_limit,download,prefix,ifname,resultdir,q1,q2,q3,q4):

    #TODO: start tshark
    #callTshark = "tshark -n -i " + ifname + "-E separator=, -T fields -e frame.time_epoch -e tcp.len -e frame.len -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.analysis.ack_rtt -e tcp.analysis.lost_segment -e tcp.analysis.out_of_order -e tcp.analysis.fast_retransmission -e tcp.analysis.duplicate_ack -e dns -Y 'tcp or dns'  >>" + prefix + "_tshark_.txt  2>" + prefix + "_tshark_error.txt &"

    callTshark = "tshark -n -i " + ifname + " -E separator=, -T fields -e frame.time_epoch -e tcp.len -e frame.len -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.analysis.ack_rtt -e tcp.analysis.lost_segment -e tcp.analysis.out_of_order -e tcp.analysis.fast_retransmission -e tcp.analysis.duplicate_ack -e dns -Y 'tcp or dns'  >>" + resultdir + prefix + "_tshark_.txt  2>" + resultdir + prefix + "_tshark_error.txt &"
    call(callTshark, shell=True)

    #subprocess.call("./run_tshark.sh")

    mpd='http://'+server_host+':'+server_port+'/'+video_id+'.mpd'
    #mpd='http://'+server_host+':'+server_port+'/media/'+video_id+'/stream.mpd'
    #mpd='http://'+server_host+':'+server_port+'/'+video_id+'.mpd'
    #mpd=MPD
    print mpd

    # create the log files
    playback_type=algorithm.lower()
    configure_log_file(resultdir, playback_type, config_dash.LOG_FILENAME)
    config_dash.JSON_HANDLE['playback_type'] = playback_type
    config_dash.LOG.info("Starting AStream container")
    config_dash.LOG.info("Starting Experiment Run on if : {}".format(ifname))

    # if not mpd:
    #     config_dash.LOG.info("ERROR: Please provide the URL to the MPD file. Try Again..")
    #     #return None
    #     sys.exit(1)
    config_dash.LOG.info('Downloading MPD file %s' % mpd)
    # Retrieve the MPD files for the video
    mpd_file = get_mpd(mpd)
    domain = get_domain_name(mpd)
    dp_object = DashPlayback()
    # Reading the MPD file created

    start_time_exp = time.time()

    try:
        dp_object, video_segment_duration = read_mpd.read_mpd(mpd_file, dp_object)
        print("DBG: testpoint astream2")
        config_dash.LOG.info("The DASH media has %d video representations" % len(dp_object.video))
        config_dash.LOG.info("Listing available representations... ")
        config_dash.LOG.info("The DASH media has the following video representations/bitrates")
        for bandwidth in dp_object.video:
            config_dash.LOG.info(bandwidth)

        print("DBG: testpoint astream4-run_exp")
            # ifname = meta_info[expconfig["modeminterfacename"]]

        # Initialize the DASH buffer
        config_dash.LOG.info("Initializing the DASH buffer...")
        dash_player = dash_buffer.DashPlayer(dp_object.playback_duration, video_segment_duration)
        dash_player.start()

        # start the DASH player, according to the selected playback_type
        if "all" in playback_type.lower():
            if mpd_file:
                config_dash.LOG.critical("Start ALL Parallel PLayback")
                start_playback_all(dp_object, domain)
        elif "basic" in playback_type.lower():
            config_dash.LOG.critical("Started Basic-DASH Playback")
            start_playback_smart(dash_player, dp_object, domain, "BASIC", download, video_segment_duration, ifname, segment_limit)
        elif "sara" in playback_type.lower():
            config_dash.LOG.critical("Started SARA-DASH Playback")
            start_playback_smart(dash_player, dp_object, domain, "SMART", download, video_segment_duration, ifname, segment_limit)
        elif "netflix" in playback_type.lower():
            config_dash.LOG.critical("Started Netflix-DASH Playback")
            start_playback_smart(dash_player, dp_object, domain, "NETFLIX", download, video_segment_duration, ifname, segment_limit)
        else:
            config_dash.LOG.error("Unknown Playback parameter {}".format(playback_type))
            return None
        while dash_player.playback_state not in dash_buffer.EXIT_STATES:
            time.sleep(1)

        # process = Process(target=run_exp, args=(mpd_file, dp_object, domain, playback_type, download, video_segment_duration, ))
        # process.daemon = True
        # process.start()
        # print ("DBG: testpoint astream3")
        #
        # while (time.time() - start_time_exp < exp_grace and
        #        process.is_alive()):
        #        elapsed_exp = time.time() - start_time_exp
        #        config_dash.LOG.info("Running Experiment for {} s".format(elapsed_exp))
        #        time.sleep(ifup_interval_check)

    except Exception as e:
        print ("DBG: AStream MPD read problem")
        print (e)

    elapsed = time.time() - start_time_exp
    config_dash.LOG.info("Finished {} after {}".format(ifname, elapsed))
    time.sleep(WAIT_SECONDS)
    config_dash.LOG.info("Exiting")

    #Renaming output files with prefix
    print("DBG: AStream - renaming output files")
    os.rename(resultdir + '_buffer.csv', resultdir + prefix + '_buffer.csv')
    os.rename(resultdir + '_segments.json', resultdir + prefix + '_segments.json')
    os.rename(resultdir + '_runtime.log', resultdir + prefix + '_runtime.log')

    #TODO: prepare output 7xbitrate, 7xbuffer, 1xnumstall, 7xduration
    print("DBG: AStream - preparing output fields for summary")
    out = getOutput(resultdir,prefix,q1,q2,q3,q4,video_segment_duration)

    #TODO: kill Tshark
    #sys.exit(0)

    return out

# Calculate average, max, min, quantiles of the following: bitrate [KB], buffer [s], number of stalls, duration of stalls
def getOutput(resultdir,prefix,q1,q2,q3,q4,segment_duration):
	out = calculateBitrate(resultdir,prefix,q1,q2,q3,q4) + "," + calculateBuffer(resultdir,prefix,q1,q2,q3,q4,segment_duration) + "," + calculateStallings(resultdir,prefix,q1,q2,q3,q4)
	return out

def calculateBitrate(resultdir,prefix,q1,q2,q3,q4):

    try:

        bitrates=[]
        json_in = open(resultdir + prefix + "_segments.json")
        clientlog=json.load(json_in)
        #playback_info = clientlog["playback_info"]
        #down_shifts = playback_info["down_shifts"]
        #up_shifts = playback_info["up_shifts"]
        segment_info = clientlog["segment_info"]
        for segment in segment_info:
            if "init" not in segment[0]:
                bitrates.append(segment[1]/1000)
                #print segment[0], segment[1]
                #file_out_bitrates.write(str(segment[1]) + '\n')

        bitrates_avg=numpy.mean(bitrates)
        bitrates_max=max(bitrates)
        bitrates_min=min(bitrates)
        bitrates_q1=numpy.percentile(bitrates, q1)
        bitrates_q2=numpy.percentile(bitrates, q2)
        bitrates_q3=numpy.percentile(bitrates, q3)
        bitrates_q4=numpy.percentile(bitrates, q4)

        video_metadata = clientlog["video_metadata"]
        available_bitrates = video_metadata["available_bitrates"]

        bitrates_list=""
        for available_bitrate in available_bitrates:
            bitrate_current = str(available_bitrate["bandwidth"])
            bitrates_list = bitrates_list + ";" + bitrate_current
            print(bitrates_list)

        return bitrates_list + "," + str(bitrates_avg) + "," + str(bitrates_max) + "," + str(bitrates_min) + "," + str(bitrates_q1) + "," + str(bitrates_q2) + "," + str(bitrates_q3) + "," + str(bitrates_q4)

    except Exception as e:
        print ("DBG: AStream calculateBitrate exception")
        print (e)
        return "NA,NA,NA,NA,NA,NA,NA,NA"

def calculateBuffer(resultdir,prefix,q1,q2,q3,q4,segment_duration):
    try:

        csvfile = pandas.read_csv(resultdir + prefix + "_buffer.csv")
        epoch_time = csvfile.EpochTime
        current_playback_time = csvfile.CurrentPlaybackTime
        current_buffer_size_raw = csvfile.CurrentBufferSize
        current_buffer_size = [0 if i < 0 else i for i in current_buffer_size_raw] #convert negative values to 0

        current_playback_state = csvfile.CurrentPlaybackState
        action = csvfile.Action

        # csvfile= csv.reader(open(resultdir + prefix + "_buffer.csv", 'r'), delimiter=',')
        # epoch_time = list(zip(*csvfile))[0]
        # current_playback_time = list(zip(*csvfile))[1]
        # current_buffer_size = list(zip(*csvfile))[2]
        # current_playback_state = list(zip(*csvfile))[3]
        # action = list(zip(*csvfile))[4]

        indices_buffering = [i for i, x in enumerate(current_playback_state) if x == "BUFFERING"]
        indices_playing = [i for i, x in enumerate(current_playback_state) if x == "PLAY"]
        indices_stopping = [i for i, x in enumerate(current_playback_state) if x == "STOP"]
        indices_writing = [i for i, x in enumerate(action) if x == "Writing"]
        indices_transition = [i for i, x in enumerate(action) if x == "-"]

        isnotbuffering = 1
        iswriting = 0
        isplaying = 0

        buffers = [current_buffer_size[0]]

        for i in range(1, len(epoch_time)):

            if i in indices_buffering and i not in indices_transition:
                isnotbuffering = 0
            if i in indices_writing:
                iswriting = 1
            if ((i in indices_playing or i in indices_stopping) and i not in indices_transition) or i in indices_buffering or i in indices_transition:
                isplaying = 1

            current_buffer_s = isnotbuffering * buffers[i-1] + iswriting * segment_duration - isplaying * (epoch_time[i] - epoch_time[i-1])
            buffers.append(current_buffer_s)

        #interpolating to 1s granularity
        x_interp = range(0,int(epoch_time[len(epoch_time)-1])+1)
        buffers_interp=numpy.interp(x_interp,epoch_time,buffers)

        # buffers_avg=numpy.mean(buffers)
        # buffers_max=max(buffers)
        # buffers_min=min(buffers)
        # buffers_q1=numpy.percentile(buffers, q1)
        # buffers_q2=numpy.percentile(buffers, q2)
        # buffers_q3=numpy.percentile(buffers, q3)
        # buffers_q4=numpy.percentile(buffers, q4)

        buffers_avg=numpy.mean(buffers_interp)
        buffers_max=max(buffers_interp)
        buffers_min=min(buffers_interp)
        buffers_q1=numpy.percentile(buffers_interp, q1)
        buffers_q2=numpy.percentile(buffers_interp, q2)
        buffers_q3=numpy.percentile(buffers_interp, q3)
        buffers_q4=numpy.percentile(buffers_interp, q4)

        #print str(buffers_avg) + "," + str(buffers_max) + "," + str(buffers_min) + "," + str(buffers_q1) + "," + str(buffers_q2) + "," + str(buffers_q3) + "," + str(buffers_q4)
        return str(buffers_avg) + "," + str(buffers_max) + "," + str(buffers_min) + "," + str(buffers_q1) + "," + str(buffers_q2) + "," + str(buffers_q3) + "," + str(buffers_q4)

    except Exception as e:
        print ("DBG: AStream calculateBuffer exception")
        print (e)
        return "NA,NA,NA,NA,NA,NA,NA"

def calculateStallings(resultdir,prefix,q1,q2,q3,q4):

    try:

        json_in = open(resultdir + prefix + "_segments.json")
        clientlog=json.load(json_in)
        playback_info = clientlog["playback_info"]
        interruptions = playback_info["interruptions"]
        num_stalls = interruptions["count"]
        stalls_total_duration = interruptions["total_duration"]

        down_shifts = playback_info["down_shifts"]
        up_shifts = playback_info["up_shifts"]

        durstalls = []

        if num_stalls > 0:
            events = interruptions["events"]
            for event in events:
                if (event[0] is not None) and (event[1] is not None):
                    durstall_current = event[1] - event[0]
                    durstalls.append(durstall_current)
        else:
            durstalls.append(0)

        durstalls_avg=numpy.mean(durstalls)
        durstalls_max=max(durstalls)
        durstalls_min=min(durstalls)
        durstalls_q1=numpy.percentile(durstalls, q1)
        durstalls_q2=numpy.percentile(durstalls, q2)
        durstalls_q3=numpy.percentile(durstalls, q3)
        durstalls_q4=numpy.percentile(durstalls, q4)

        return str(num_stalls) + "," + str(durstalls_avg) + "," + str(durstalls_max) + "," + str(durstalls_min) + "," + str(durstalls_q1) + "," + str(durstalls_q2) + "," + str(durstalls_q3) + "," + str(durstalls_q4) + "," + str(stalls_total_duration) + "," + str(up_shifts) + "," + str(down_shifts)

    except Exception as e:
        print ("DBG: AStream calculateStallings exception")
        print (e)
        return "NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA"

def configure_log_file(resultdir, playback_type="", log_file=config_dash.LOG_FILENAME):
    """ Module to configure the log file and the log parameters.
    Logs are streamed to the log file as well as the screen.
    Log Levels: CRITICAL:50, ERROR:40, WARNING:30, INFO:20, DEBUG:10, NOTSET	0
    """
    config_dash.LOG_FOLDER=resultdir
    config_dash.LOG = logging.getLogger(config_dash.LOG_NAME)
    config_dash.LOG_LEVEL = logging.INFO
    config_dash.LOG.setLevel(config_dash.LOG_LEVEL)
    log_formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
    # Add the handler to print to the screen
    handler1 = logging.StreamHandler(sys.stdout)
    handler1.setFormatter(log_formatter)
    config_dash.LOG.addHandler(handler1)
    # Add the handler to for the file if present
    if log_file:
        #log_filename = "_".join((log_file,playback_type, strftime('%Y-%m-%d.%H_%M_%S.log')))
        log_filename = log_file
        print("Configuring log file: {}".format(log_filename))
        handler2 = logging.FileHandler(filename=log_filename)
        handler2.setFormatter(log_formatter)
        config_dash.LOG.addHandler(handler2)
        print("Started logging in the log file:{}".format(log_filename))

def write_json(json_data=config_dash.JSON_HANDLE, json_file=config_dash.JSON_LOG):
    """
    :param json_data: dict
    :param json_file: json file
    :return: None
        Using utf-8 to reduce size of the file
    """
    # with io.open(json_file, 'w', encoding='utf-8') as json_file_handle:
    #     json_file_handle.write(unicode(json.dumps(json_data, ensure_ascii=False)))
    #AEL -- changed the json write function to append to the json_file
    with io.open(json_file, 'a+', encoding='utf-8') as json_file_handle:
        json_file_handle.write(unicode(json.dumps(json_data, ensure_ascii=False)))
