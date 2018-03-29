#!/usr/bin/python
# -*- coding: utf-8 -*-

# Authors: Cise Midoglu, Anika Schwind (based on a MONROE template)
# Last Update: March 2018
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple wrapper to run the yomo-astream client.
The script will execute one experiment for each of the enabled interfaces.
All default values are configurable from the scheduler.
The output will be formatted into a JSON object suitable for storage in the MONROE database.
"""

import io
import json
import zmq
import sys
import netifaces
import time
from subprocess import Popen, PIPE, STDOUT, call, check_output, CalledProcessError
from multiprocessing import Process, Manager
import shutil
from tempfile import NamedTemporaryFile
import glob

#sys.path.append('files_yomo')
#sys.path.append('files_astream')
from videomon_yomo import *
from videomon_astream import *

# Configuration
CONFIGFILE = '/monroe/config'
DEBUG = False
CONTAINER_VERSION = 'v2.1'
#CM: version information
#v2.0   (CM) working container with new structure 03.2018
#v2.1   (CM) metadata reading within container 03.2018

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
  # The following values are specific to the MONROE platform
  "guid": "fake.guid",               # Should be overridden by scheduler
  "zmqport": "tcp://172.17.0.1:5556",
  "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
  "dataversion": 2,
  "dataid": "MONROE.EXP.VIDEO",
  "nodeid": "fake.nodeid",
  "meta_grace": 10,                              # Grace period to wait for interface metadata
  "exp_grace": 10000,                               # Grace period before killing experiment
  "ifup_interval_check": 3,                       # Interval to check if interface is up
  "time_between_experiments": 0,
  "verbosity": 3,                                 # 0 = "Mute", 1=error, 2=information, 3=verbose
  "resultdir": "/monroe/results/",
  "modeminterfacename": "InternalInterface",
  "save_metadata_topic": "MONROE.META",
  "save_metadata_resultdir": None,                # set to a dir to enable saving of metadata
  "add_modem_metadata_to_result": True,          # set to True to add one captured modem metadata to videomon result
  "enabled_interfaces":["op0","op1","eth0"],
  "disabled_interfaces": ["lo",
                          "metadata",
                          "eth2",
                          "wlan0",
                          "wwan0",
                          "wwan1",
                          "wwan2",
                          "docker0"
                          ],                      # Interfaces to NOT run the experiment on
  "interfaces_without_metadata": ["eth0",
                                  "wlan0"],       # Manual metadata on these IF
  "timestamp": time.gmtime(),

  # These values are specific for this experiment
  "cnf_tag": "None",
  "cnf_video_id": "D8YQn7o_AyA", #"7kAy3b9hvWM", # (YouTube) ID of the video to be streamed #"pJ8HFgPKiZE",#"7kAy3b9hvWM",#"QS7lN7giXXc",
  "cnf_astream_algorithm": "Basic",               # Playback type in astream
  "cnf_astream_mpd": "http://www-itec.uni-klu.ac.at/ftp/datasets/mmsys12/BigBuckBunny/bunny_2s/BigBuckBunny_2s_isoffmain_DIS_23009_1_v_2_1c2_2011_08_30.mpd",
  "cnf_astream_download": False,                   # Download option for AStream
  "cnf_astream_segment_limit": 5,                  # Segment limit option for AStream
  "cnf_astream_segment_duration": 2,                  # Segment duration info for AStream
  "cnf_astream_server_host": "128.39.36.18",      # REQUIRED PARAMETER; Host/IP to connect to for astream
  "cnf_astream_server_port": "12345",              # REQUIRED PARAMETER; Port to connect to for astream
  #"cnf_yomo_resolution": "1920,1080",
  "cnf_yomo_playback_duration_s": 0,              # Nominal duration for the YouTube video playback
  "cnf_yomo_bitrates_kbps": "144p:114.792,240p:250.618,360p:606.343,480p:1166.528,720p:2213.150,1080p:4018.795,1440p:9489.022,2160p:21322.799", #for D8YQn7o_AyA,
  #"180p:236.059,270p:461.195,360p:922.220,540p:1780.741,810p:3369.892,1080p:7823.352,1620p:15500.364",
  #"144p:110.139,240p:246.425,360p:262.750,480p:529.500,720p:1036.744,1080p:2793.167",             	   # REQUIRED PARAMETER; list (as String) with all available qualities and their bitrates in KBs
  "cnf_wait_btw_algorithms_s": 20,                 # Time to wait between different algorithms
  "cnf_wait_btw_videos_s": 20,                     # Time to wait between different videos
  "cnf_compress_additional_results": True,         # Whether or not to tar additional log files
  "cnf_q1": 25,
  "cnf_q2": 50,
  "cnf_q3": 75,
  "cnf_q4": 90,
  "cnf_astream_skip": False,
  "cnf_yomo_skip": True,

  "cnf_astream_out_fields": "res_astream_available_bitrates,\
res_astream_bitrate_mean,res_astream_bitrate_max,res_astream_bitrate_min,\
res_astream_bitrate_q1,res_astream_bitrate_q2,res_astream_bitrate_q3,res_astream_bitrate_q4,\
res_astream_buffer_mean,res_astream_buffer_max,res_astream_buffer_min,\
res_astream_buffer_q1,res_astream_buffer_q2,res_astream_buffer_q3,res_astream_buffer_q4,\
res_astream_numstalls,\
res_astream_durstalls_mean,res_astream_durstalls_max,res_astream_durstalls_min,\
res_astream_durstalls_q1,res_astream_durstalls_q2,res_astream_durstalls_q3,res_astream_durstalls_q4,\
res_astream_durstalls_total,\
res_astream_numswitches_up,res_astream_numswitches_down",

  "cnf_yomo_out_fields": "res_yomo_bitrate_mean,res_yomo_bitrate_max,res_yomo_bitrate_min,\
res_yomo_bitrate_q1,res_yomo_bitrate_q2,res_yomo_bitrate_q3,res_yomo_bitrate_q4,\
res_yomo_numswitches_up,res_yomo_numswitches_down,\
res_yomo_buffer_mean,res_yomo_buffer_max,res_yomo_buffer_min,\
res_yomo_buffer_q1,res_yomo_buffer_q2,res_yomo_buffer_q3,res_yomo_buffer_q4,\
res_yomo_numstalls,\
res_yomo_durstalls_mean,res_yomo_durstalls_max,res_yomo_durstalls_min,\
res_yomo_durstalls_q1,res_yomo_durstalls_q2,res_yomo_durstalls_q3,res_yomo_durstalls_q4,\
res_yomo_durstalls_total"

}

def get_filename(data, postfix, ending, tstamp, interface):
    return "{}_{}_{}_{}_{}_{}{}.{}".format(data['dataid'], data['cnf_video_id'], str.lower(data['cnf_astream_algorithm']), data['nodeid'], interface, tstamp,
        ("_" + postfix) if postfix else "", ending)

def get_prefix(data, postfix, tstamp, interface):
    return "{}_{}_{}_{}_{}_{}{}".format(data['dataid'], data['cnf_video_id'], str.lower(data['cnf_astream_algorithm']), data['nodeid'], interface, tstamp,
        ("_" + postfix) if postfix else "")

def save_output(data, msg, postfix=None, ending='json', tstamp=time.time(), outdir='/monroe/results/', interface='interface'):
    f = NamedTemporaryFile(mode='w+', delete=False, dir=outdir)
    f.write(msg)
    f.close()
    outfile = os.path.join(outdir, get_filename(data, postfix, ending, tstamp, interface))
    move_file(f.name, outfile)

def move_file(f, t):
    try:
        shutil.move(f, t)
        os.chmod(t, 0o644)
    except:
        traceback.print_exc()

def copy_file(f, t):
    try:
        shutil.copyfile(f, t)
        os.chmod(t, 0o644)
    except:
        traceback.print_exc()

def metadata(meta_ifinfo, ifname, expconfig):
    """Seperate process that attach to the ZeroMQ socket as a subscriber.

        Will listen forever to messages with topic defined in topic and update
        the meta_ifinfo dictionary (a Manager dict).
    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(expconfig['zmqport'])
    topic = expconfig['modem_metadata_topic']
    do_save = False
    if 'save_metadata_topic' in expconfig and 'save_metadata_resultdir' in expconfig and expconfig['save_metadata_resultdir']:
        topic = expconfig['save_metadata_topic']
        do_save = True
    socket.setsockopt(zmq.SUBSCRIBE, topic.encode('ASCII'))
    # End Attach
    while True:
        data = socket.recv_string()
        try:
            (topic, msgdata) = data.split(' ', 1)
            msg = json.loads(msgdata)
            if do_save and not topic.startswith("MONROE.META.DEVICE.CONNECTIVITY."):
                # Skip all messages that belong to connectivity as they are redundant
                # as we save the modem messages.
                msg['nodeid'] = expconfig['nodeid']
                msg['dataid'] = msg['DataId']
                msg['dataversion'] = msg['DataVersion']
                tstamp = time.time()
                if 'Timestamp' in msg:
                    tstamp = msg['Timestamp']
                if expconfig['verbosity'] > 2:
                    print(msg)
                save_output(data=msg, msg=json.dumps(msg), tstamp=tstamp, outdir=expconfig['save_metadata_resultdir'])

            if topic.startswith(expconfig['modem_metadata_topic']):
                if (expconfig["modeminterfacename"] in msg and
                        msg[expconfig["modeminterfacename"]] == ifname):
                    # In place manipulation of the reference variable
                    for key, value in msg.items():
                        meta_ifinfo[key] = value
        except Exception as e:
            if expconfig['verbosity'] > 0:
                print ("Cannot get metadata in container: {}"
                       ", {}").format(e, expconfig['guid'])
            pass

def check_if(ifname):
    """Check if interface is up and have got an IP address."""
    return (ifname in netifaces.interfaces() and
            netifaces.AF_INET in netifaces.ifaddresses(ifname))

def get_ip(ifname):
    """Get IP address of interface."""
    # TODO: what about AFINET6 / IPv6?
    return netifaces.ifaddresses(ifname)[netifaces.AF_INET][0]['addr']

def check_meta(info, graceperiod, expconfig):
    """Check if we have recieved required information within graceperiod."""
    if not (expconfig["modeminterfacename"] in info and
            "Operator" in info and
            "Timestamp" in info and
            time.time() - info["Timestamp"] < graceperiod):
        return False
    if not "require_modem_metadata" in expconfig:
        return True
    for k,v in expconfig["require_modem_metadata"].items():
        if k not in info:
            if expconfig['verbosity'] > 0:
                print("Got metadata but key '{}' is missing".format(k))
            return False
        if not info[k] == v:
            if expconfig['verbosity'] > 0:
                print("Got metadata but '{}'='{}'; expected: '{}''".format(k, info[k], v))
            return False
    return True

def add_manual_metadata_information(info, ifname, expconfig):
    """Only used for local interfaces that do not have any metadata information.

       Normally eth0 and wlan0.
    """
    info[expconfig["modeminterfacename"]] = ifname
    info["Operator"] = "local.operator"
    info["ICCID"] = "local.iccid"
    info["Timestamp"] = time.time()

def create_meta_process(ifname, expconfig):
    meta_info = Manager().dict()
    process = Process(target=metadata,
                      args=(meta_info, ifname, expconfig, ))
    process.daemon = True
    return (meta_info, process)

def create_exp_process(meta_info, expconfig):
    process = Process(target=run_exp, args=(meta_info, expconfig, ))
    process.daemon = True
    return process

def run_exp(meta_info, expconfig):
    """Seperate process that runs the experiment and collect the ouput.
        Will abort if the interface goes down.
    """

    cfg = expconfig.copy()
    output = None

    try:
        if 'cnf_add_to_result' not in cfg:
            cfg['cnf_add_to_result'] = {}

        cfg['cnf_add_to_result'].update({
            "Guid": cfg['guid'],
            "DataId": cfg['dataid'],
            "DataVersion": cfg['dataversion'],
            "NodeId": cfg['nodeid'],
            "Time": time.strftime('%Y%m%d-%H%M%S',cfg['timestamp']),
            "Interface": cfg['modeminterfacename'],
            "cnf_astream_mpd": cfg['cnf_astream_mpd'],
            "cnf_astream_server_host": cfg['cnf_astream_server_host'],
            "cnf_astream_server_port": cfg['cnf_astream_server_port'],
            "cnf_astream_algorithm": cfg['cnf_astream_algorithm'],
            "cnf_astream_segment_limit": cfg['cnf_astream_segment_limit'],
            "cnf_astream_segment_duration": cfg['cnf_astream_segment_duration'],
            "cnf_astream_download": cfg['cnf_astream_download'],
            "cnf_video_id": cfg['cnf_video_id'],
            "cnf_yomo_playback_duration_s": cfg["cnf_yomo_playback_duration_s"],
            "cnf_q1": cfg['cnf_q1'],
            "cnf_q2": cfg['cnf_q2'],
            "cnf_q3": cfg['cnf_q3'],
            "cnf_q4": cfg['cnf_q4'],
            "cnf_tag": cfg['cnf_tag'],
            "ContainerVersion": CONTAINER_VERSION,
            "DEBUG": DEBUG
            })

        if 'ICCID' in meta_info:
            cfg['cnf_add_to_result']['ICCID'] = meta_info['ICCID']
        if 'Operator' in meta_info:
            cfg['cnf_add_to_result']['OPERATOR'] = meta_info['Operator']
        if 'IMSIMCCMNC' in meta_info:
            cfg['cnf_add_to_result']['IMSIMCCMNC'] = meta_info['IMSIMCCMNC']
        if 'NWMCCMNC' in meta_info:
            cfg['cnf_add_to_result']['NWMCCMNC'] = meta_info['NWMCCMNC']
        if 'CID' in meta_info:
            cfg['cnf_add_to_result']['CID'] = meta_info['CID']
        if 'LAC' in meta_info:
            cfg['cnf_add_to_result']['LAC'] = meta_info['LAC']
        if 'DEVICEMODE' in meta_info:
            cfg['cnf_add_to_result']['DEVICEMODE'] = meta_info['DEVICEMODE']
        if 'DEVICESUBMODE' in meta_info:
            cfg['cnf_add_to_result']['DEVICESUBMODE'] = meta_info['DEVICESUBMODE']
        if 'LATITUDE' in meta_info:
            cfg['cnf_add_to_result']['LATITUDE'] = meta_info['LATITUDE']
        if 'LONGITUDE' in meta_info:
            cfg['cnf_add_to_result']['LONGITUDE'] = meta_info['LONGITUDE']

        # Add metadata if requested
        if cfg['add_modem_metadata_to_result']:

            for k,v in meta_info.items():
                cfg['cnf_add_to_result']['info_meta_modem_' + k] = v

        towrite_data = cfg['cnf_add_to_result']
        ifname = meta_info[cfg['modeminterfacename']]
        towrite_data['Interface']=ifname

        #CM: constructing filename prefixes for YoMo and AStream, and output directory
        prefix_timestamp=time.strftime('%Y%m%d-%H%M%S',cfg['timestamp'])
        prefix_yomo=get_prefix(data=cfg, postfix="yomo", tstamp=prefix_timestamp, interface=ifname)
        prefix_astream=get_prefix(data=cfg, postfix="astream", tstamp=prefix_timestamp, interface=ifname)

        #resultdir=cfg['resultdir']
        resultdir_videomon=cfg['resultdir']+"videomon/"

        resultdir_astream=resultdir_videomon+'astream/'
        resultdir_astream_video = resultdir_astream + 'videos/'
        if not os.path.exists(resultdir_astream_video):
            os.makedirs(resultdir_astream_video)

        resultdir_yomo=resultdir_videomon+'yomo'
        if not os.path.exists(resultdir_yomo):
            os.makedirs(resultdir_yomo)

        if cfg['verbosity'] > 2:
            print('')
            print('-----------------------------')
            print('DBG: Prefix for YoMo: '+prefix_yomo)
            print('DBG: Prefix for AStream: '+prefix_astream)
            print('DBG: Temporary result directory: '+resultdir_videomon)
            print('-----------------------------')

        #TODO for VideoMon starts here:

        #PART 0 - Traceroutes
        # Run traceroute + YoMo, then traceroute + AStream once
        #print ("Running traceroute against YouTube server on interface: {}".format(cfg['modeminterfacename']))
        #run_traceroute(<target1>)
        #print ("Running YoMo with video: {}".format(cfg['cnf_video_id']))

        #print ("Running traceroute against AStream server on interface: {}".format(cfg['modeminterfacename']))
        #run_traceroute(<target2>)
        #print ("Running AStream ({}) with video: {}".format(cfg['cnf_astream_algorithm'],cfg['cnf_video_id']))

        try:

            if not cfg['cnf_astream_skip']:

                #PART I - AStream
                if cfg['verbosity'] > 1:
                    print('\n-----------------------------')
                    print('DBG: Running AStream')
                    print('-----------------------------')

                out_astream=run_astream(cfg['cnf_astream_mpd'],cfg['cnf_astream_server_host'],cfg['cnf_astream_server_port'],cfg['cnf_video_id'],cfg['cnf_astream_algorithm'],cfg['cnf_astream_segment_limit'],cfg['cnf_astream_download'],resultdir_astream,resultdir_astream_video,cfg['cnf_q1'],cfg['cnf_q2'],cfg['cnf_q3'],cfg['cnf_q4'],cfg['cnf_astream_segment_duration'])

                if cfg['verbosity'] > 2:
                    print('')
                    print('-----------------------------')
                    print('DBG: AStream output:')
                    print('-----------------------------')
                    print(out_astream)

                out_astream_fields = out_astream.split(",")
                summary_astream_fields = cfg['cnf_astream_out_fields'].split(",")

                if len(out_astream_fields) == len(summary_astream_fields):
                   for i in xrange(0,len(summary_astream_fields)-1):
                       towrite_data[summary_astream_fields[i]]=out_astream_fields[i]
                else:
                   for i in xrange(0,len(summary_astream_fields)-1):
                       towrite_data[summary_astream_fields[i]]="NA" #all summary fields will be assigned NA

            if not cfg['cnf_yomo_skip']:

                #PART II - YoMo

                if cfg['verbosity'] > 1:
                    print('')
                    print('-----------------------------')
                    print('DBG: Running YoMo')
                    print('-----------------------------')

                #out_yomo=run_yomo(cfg['cnf_video_id'],cfg['cnf_yomo_playback_duration_s'],prefix_yomo,cfg['cnf_yomo_resolution'],cfg['cnf_yomo_bitrates_kbps'],ifname,resultdir_videomon,cfg['cnf_q1'],cfg['cnf_q2'],cfg['cnf_q3'],cfg['cnf_q4'])
                out_yomo=run_yomo(cfg['cnf_video_id'],cfg['cnf_yomo_playback_duration_s'],prefix_yomo,cfg['cnf_yomo_bitrates_kbps'],ifname,resultdir_videomon,cfg['cnf_q1'],cfg['cnf_q2'],cfg['cnf_q3'],cfg['cnf_q4'],'chrome')

                if cfg['verbosity'] > 2:
                    print('')
                    print('-----------------------------')
                    print('DBG: YoMo output')
                    print('-----------------------------')
                    print(out_yomo)

                out_yomo_fields = out_yomo.split(",")
                summary_yomo_fields = cfg['cnf_yomo_out_fields'].split(",")

                if len(out_yomo_fields) == len(summary_yomo_fields):
                    for i in xrange(0,len(out_yomo_fields)-1):
                        towrite_data[summary_yomo_fields[i]]=out_yomo_fields[i]
                else:
                    for i in xrange(0,len(out_yomo_fields)-1):
                        towrite_data[summary_yomo_fields[i]]="NA"

        except Exception as e:
            if cfg['verbosity'] > 0:
                print ('[Exception #2] Execution or parsing failed for error: {}').format(e)

        if not DEBUG:
            if cfg['verbosity'] > 1:
                print('')
                print('-----------------------------')
                print('DBG: Compressing and saving results')
                print('-----------------------------')

            #CM: compressing all outputs other than summary JSON

            save_output(data=cfg, msg=json.dumps(towrite_data), postfix="summary", tstamp=prefix_timestamp, outdir=cfg['resultdir'], interface=ifname)

            if 'cnf_compress_additional_results' in cfg and cfg['cnf_compress_additional_results']:
                files_to_compress=resultdir_videomon+"*"
                #with tarfile.open(os.path.join(cfg['resultdir'], get_filename(data=cfg, postfix=None, ending="tar.gz", tstamp=prefix_timestamp, interface=ifname)), mode='w:gz') as tar:
                #tar.add(cfg['resultdir'], recursive=False)
                #tar.add(files_to_compress)

                #print ('DBG1')
                shutil.make_archive(base_name=os.path.join(cfg['resultdir'], get_filename(data=cfg, postfix=None, ending="extra", tstamp=prefix_timestamp, interface=ifname)), format='gztar', root_dir=resultdir_videomon,base_dir="./")
                #print ('DBG2')
                #print(os.listdir(resultdir_astream))
                #print('DBG3')
                #print(os.listdir(resultdir_videomon))
                shutil.rmtree(resultdir_videomon)

                #os.remove(cfg['resultdir'])
                # foldername_zip=get_filename(data=cfg, postfix=None, ending="extra", tstamp=prefix_timestamp, interface=ifname)
                # basename_zip=os.path.join(resultdir,foldername_zip)
                # #print(foldername_zip)
                # shutil.move(resultdir_astream,basename_zip)
                # shutil.make_archive(base_name=basename_zip, format='gztar', root_dir=resultdir, base_dir=foldername_zip)#"./")
                # shutil.rmtree(basename_zip)


    except Exception as e:
        if cfg['verbosity'] > 0:
            print ('[Exception #1] Execution or parsing failed for error: {}').format(e)

if __name__ == '__main__':
    """The main thread control the processes (experiment/metadata))."""
    # Try to get the experiment config as provided by the scheduler
    try:
        with open(CONFIGFILE) as configfd:
            EXPCONFIG.update(json.load(configfd))
    except Exception as e:
        print("Cannot retrive expconfig {}".format(e))
        raise e

    if DEBUG:
        # We are in debug state always put out all information
        EXPCONFIG['verbosity'] = 3
        try:
            EXPCONFIG['disabled_interfaces'].remove("eth0")
        except Exception as e:
            pass

    # Short hand variables and check so we have all variables we need
    try:
        disabled_interfaces = EXPCONFIG['disabled_interfaces']
        if_without_metadata = EXPCONFIG['interfaces_without_metadata']
        meta_grace = EXPCONFIG['meta_grace']
        exp_grace = EXPCONFIG['exp_grace']
        ifup_interval_check = EXPCONFIG['ifup_interval_check']
        time_between_experiments = EXPCONFIG['time_between_experiments']
        EXPCONFIG['guid']
        EXPCONFIG['modem_metadata_topic']
        EXPCONFIG['zmqport']
        EXPCONFIG['verbosity']
        EXPCONFIG['resultdir']
        EXPCONFIG['modeminterfacename']
    except Exception as e:
        print("Missing expconfig variable {}".format(e))
        raise e

    sequence_number = 0
    tot_start_time = time.time()
    for ifname in netifaces.interfaces():
        # Skip disbaled interfaces
        if ifname in disabled_interfaces:
            if EXPCONFIG['verbosity'] > 1:
                print("Interface is disabled, skipping {}".format(ifname))
            continue

        if 'enabled_interfaces' in EXPCONFIG and not ifname in EXPCONFIG['enabled_interfaces']:
            if EXPCONFIG['verbosity'] > 1:
                print("Interface is not enabled, skipping {}".format(ifname))
            continue

        # Interface is not up we just skip that one
        if not check_if(ifname):
            if EXPCONFIG['verbosity'] > 1:
                print("Interface is not up {}".format(ifname))
            continue

        EXPCONFIG['cnf_bind_ip'] = get_ip(ifname)

        # Create a process for getting the metadata
        # (could have used a thread as well but this is true multiprocessing)
        meta_info, meta_process = create_meta_process(ifname, EXPCONFIG)
        meta_process.start()

        if EXPCONFIG['verbosity'] > 1:
            print("Starting Experiment Run on if : {}".format(ifname))

        # On these Interfaces we do net get modem information so we hack
        # in the required values by hand whcih will immeditaly terminate
        # metadata loop below
        if (check_if(ifname) and ifname in if_without_metadata):
            add_manual_metadata_information(meta_info, ifname, EXPCONFIG)

        # Try to get metadata
        # if the metadata process dies we retry until the IF_META_GRACE is up
        start_time = time.time()
        while (time.time() - start_time < meta_grace and
               not check_meta(meta_info, meta_grace, EXPCONFIG)):
            if not meta_process.is_alive():
                # This is serious as we will not receive updates
                # The meta_info dict may have been corrupt so recreate that one
                meta_info, meta_process = create_meta_process(ifname,
                                                              EXPCONFIG)
                meta_process.start()
            if EXPCONFIG['verbosity'] > 1:
                print("Trying to get metadata")
            time.sleep(ifup_interval_check)

        # Ok we did not get any information within the grace period
        # we give up on that interface
        if not check_meta(meta_info, meta_grace, EXPCONFIG):
            if EXPCONFIG['verbosity'] > 1:
                print("No Metadata continuing")
            continue

        cmd1=["route","del","default"]
        #os.system(bashcommand)
        try:
                check_output(cmd1)
        except CalledProcessError as e:
                if e.returncode == 28:
                         print("Time limit exceeded for command1")
        #gw_ip="192.168."+str(meta_info["IPAddress"].split(".")[2])+".1"
        gw_ip="undefined"
        for g in netifaces.gateways()[netifaces.AF_INET]:
            if g[1] == ifname:
                gw_ip = g[0]
                break

        cmd2=["route", "add", "default", "gw", gw_ip,str(ifname)]
        try:
                check_output(cmd2)
        except CalledProcessError as e:
                 if e.returncode == 28:
                        print("Time limit exceeded for command2")

        cmd3=["ip", "route", "get", "8.8.8.8"]
        try:
                output=check_output(cmd3)
        except CalledProcessError as e:
                 if e.returncode == 28:
                        print("Time limit exceeded for command3")
        output = output.strip(' \t\r\n\0')
        output_interface=output.split(" ")[4]
        if output_interface==str(ifname):
                print("Source interface is set to " + str(ifname))

        if EXPCONFIG['verbosity'] > 1:
            print("Starting experiment")

        # Create an experiment process and start it
        start_time_exp=time.time()
        exp_process = create_exp_process(meta_info, EXPCONFIG)
        exp_process.start()

        while (time.time() - start_time_exp < exp_grace and
               exp_process.is_alive()):
            # Here we could add code to handle interfaces going up or down
            # Similar to what exist in the ping experiment
            # However, for now we just abort if we loose the interface

            if not check_if(ifname):
                if EXPCONFIG['verbosity'] > 0:
                    print("Interface went down during an experiment")
                break
            elapsed_exp = time.time() - start_time_exp
            if EXPCONFIG['verbosity'] > 1:
                print("Running Experiment for {} s".format(elapsed_exp))
            time.sleep(ifup_interval_check)

        if exp_process.is_alive():
            exp_process.terminate()
        if meta_process.is_alive():
            meta_process.terminate()

        elapsed = time.time() - start_time
        if EXPCONFIG['verbosity'] > 1:
            print("Finished {} after {}".format(ifname, elapsed))
        time.sleep(time_between_experiments)

    if EXPCONFIG['verbosity'] > 1:
        print("Complete experiment took {}, now exiting".format(time.time() - tot_start_time))
