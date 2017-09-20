#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Andra Lutu (based on a template from Jonas Karlsson)
# Date: October 2016

# Updates: Cise Midoglu, August 2017

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
import sys
import netifaces
import time
from subprocess import check_output, CalledProcessError
from multiprocessing import Process, Manager
from dash_client import *
from configure_log_file import configure_log_file, write_json
import config_dash
from dash_buffer import *
from adaptation import basic_dash, basic_dash2, weighted_dash, netflix_dash
from adaptation.adaptation import WeightedMean
import subprocess
#from subprocess import call

# Globals for arg parser with the default values
MPD = "http://128.39.37.161:8080/BigBuckBunny_4s.mpd"
DOWNLOAD_CHUNK = 1024
DOWNLOAD = False
#SEGMENT_LIMIT = 100
#exp_grace = 120
ifup_interval_check = 5
wait_after_exp_s = 5


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

def start_playback_smart(dash_player, dp_object, domain, playback_type=None, download=False, video_segment_duration=None, ifname=None, SEGMENT_LIMIT=100):
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
    # Initialize the DASH buffer
    # AEL -- moved this to run_exp function to integrate interaction with MONROE
    # config_dash.LOG.info("Initializing the DASH buffer...")
    # dash_player = dash_buffer.DashPlayer(dp_object.playback_duration, video_segment_duration)
    # dash_player.start()
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
        if SEGMENT_LIMIT:
            if not dash_player.segment_limit:
                dash_player.segment_limit = int(SEGMENT_LIMIT)
            if segment_number > int(SEGMENT_LIMIT):
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

def run_astream(video_id,server_host,server_port,algorithm,segment_limit,download,ifname,prefix,resultdir):

    print("DBG: testpoint run_astream")
    #subprocess.call("./run_tshark.sh")

    #mpd='http://'+server_host+':'+server_port+'/media/'+video_id+'.mpd'
    mpd='http://'+server_host+':'+server_port+'/'+video_id+'.mpd'
    print mpd

    # create the log files
    playback_type=algorithm.lower()
    configure_log_file(playback_type=algorithm.lower(), log_file = config_dash.LOG_FILENAME)
    config_dash.JSON_HANDLE['playback_type'] = algorithm.lower()
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

        config_dash.LOG.info("Initializing the DASH buffer...")
        dash_player = dash_buffer.DashPlayer(dp_object.playback_duration, video_segment_duration)
        dash_player.start()
                # # AEL: adding meta-info to dash json output -- tracking "played" segments
                # scriptname = expconfig['script'].replace('/', '.')
                # dataid = expconfig.get('dataid', scriptname)
                # dataversion = expconfig.get('dataversion', 1)
                #
                # config_dash.JSON_HANDLE['MONROE'].append({
                #     "Guid": expconfig['guid'],
                #     "DataId": dataid,
                #     "DataVersion": dataversion,
                #     "NodeId": expconfig['nodeid'],
                #     "Timestamp": time.time(),
                #     "Iccid": "fakeICCID",#meta_info["ICCID"],
                #     "NWMCCMNC": meta_info["NWMCCMNC"], # modify to MCCMNC from SIM
                #     "InterfaceName": ifname,
                #     "Operator": meta_info["Operator"],
                #     "SequenceNumber": 1
                # })

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
        print ("DBG: mpd read problem")
        print (e)

    elapsed = time.time() - start_time_exp
    config_dash.LOG.info("Finished {} after {}".format(ifname, elapsed))
    time.sleep(wait_after_exp_s)
    config_dash.LOG.info("Exiting")

    return "Fake output from AStream"
