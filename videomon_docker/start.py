#!/usr/bin/python
# -*- coding: utf-8 -*-

# Authors: Cise Midoglu, Anika Schwind (based on a MONROE template)
# Date: August 2017
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

"""
Simple wrapper to run the yomo-astream client.
The script will execute one experiment (one video, two playbacks) for each of the enabled interfaces.
All default values are configurable from the scheduler.
The output will be formatted into a JSON object suitable for storage in the MONROE db.
"""

from collections import OrderedDict
import io
from itertools import product
import json
from multiprocessing import Process, Manager
import netifaces
import os
from random import shuffle
import shutil
from subprocess import Popen, PIPE, STDOUT, call, check_output, CalledProcessError
import sys
#import tarfile
from tempfile import NamedTemporaryFile
import time
import traceback
import zmq

#sys.path.append('files_yomo')
#sys.path.append('files_astream')

from videomon_yomo import *
from videomon_astream import *

# Configuration
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
  # The following values are specific to the MONROE platform
  "guid": "no.guid.in.config.file",               # Should be overridden by scheduler
  "zmqport": "tcp://172.17.0.1:5556",
  "modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
  "dataversion": 2,
  "dataid": "MONROE.EXP.VIDEO",
  "nodeid": "fake.nodeid",
  "meta_grace": 10,                              # Grace period to wait for interface metadata
  "exp_grace": 600,                               # Grace period before killing experiment
  "ifup_interval_check": 3,                       # Interval to check if interface is up
  "time_between_experiments": 0,
  "verbosity": 2,                                 # 0 = "Mute", 1=error, 2=Information, 3=verbose
  "resultdir": "/monroe/results/",
  "modeminterfacename": "InternalInterface",
  "save_metadata_topic": "MONROE.META",
  "save_metadata_resultdir": None,                # set to a dir to enable saving of metadata
  "add_modem_metadata_to_result": False,          # set to True to add one captured modem metadata to nettest result
  "enabled_interfaces":["eth0"],
  "disabled_interfaces": ["lo",
                          "metadata",
                          "eth2",
                          "wlan0",
                          "wwan0",
                          "wwan1",
                          "wwan2",
                          "op0",
                          "op1",
                          "docker0"
                          ],                      # Interfaces to NOT run the experiment on
  "interfaces_without_metadata": ["eth0",
                                  "wlan0"],       # Manual metadata on these IF
  "timestamp": time.gmtime(),

  # These values are specific for this experiment
  "cnf_debug": True,
  "cnf_video_id": "D8VXDSMyuMk", #"pJ8HFgPKiZE",#"7kAy3b9hvWM",#"QS7lN7giXXc",                 # (YouTube) ID of the video to be streamed
  "cnf_astream_algorithm": "Basic",                # Playback type in astream
  "cnf_astream_download": False,                   # Download option for AStream
  "cnf_astream_segment_limit": 2,                  # Segment limit option for AStream
  "cnf_astream_server_host": "",                   # REQUIRED PARAMETER; Host/IP to connect to for astream
  "cnf_astream_server_port": "",                   # REQUIRED PARAMETER; Port to connect to for astream
  "cnf_yomo_playback_duration_s": 10,              # Nominal duration for the youyube video playback
  "cnf_wait_btw_algorithms_s": 20,                 # Time to wait between different algorithms
  "cnf_wait_btw_videos_s": 20,                     # Time to wait between different videos
  "cnf_compress_additional_results": True,         # Whether or not to tar additional log files
  "cnf_q1": 25,
  "cnf_q2": 50,
  "cnf_q3": 75,
  "cnf_q4": 90
  #"cnf_yomo_bitrates_KBs": "",              	   # REQUIRED PARAMETER; list (as String) with all available qualities and their bitrates in KBs
  #"cnf_file_database_output": "{time}_{ytid}_summary.json", # Output file to be exported to MONROE database
  #"cnf_file_yomo": "{time}_{ytid}_yomo",           # Prefix for YoMo logs
  #"cnf_file_astream": "{time}_{ytid}_astream"      # Prefix for AStream logs
  #"cnf_require_modem_metadata": {"DeviceMode": 4},# only run if in LTE (5) or UMTS (4)
  #"cnf_ping_": ,                                  # TODO
  #"cnf_log_granularity": 10000,                   # TODO
  #"multi_config_randomize": False,                # Randomize the muliple runs by "multi_config", has no effect without "multi_config" (see below)
  #"multi_config": [
  #  [
  #    { "cnf_dl_num_flows": 1, "cnf_ul_num_flows": 1 },
  #    { "cnf_dl_num_flows": 3, "cnf_ul_num_flows": 3 },
  #    { "cnf_dl_num_flows": 4, "cnf_ul_num_flows": 4 },
  #    { "cnf_dl_num_flows": 5, "cnf_ul_num_flows": 5 },
  #    { "cnf_dl_num_flows": 7, "cnf_ul_num_flows": 7 },
  #    { "cnf_dl_num_flows": 9, "cnf_ul_num_flows": 9 },
  #  ],
  #  [ {"cnf_server_host": "A"}, {"cnf_server_host": "B"}]
  #],
  }

# Helper functions
def get_filename(data, postfix, ending, tstamp, interface):
    return "{}_{}_{}_{}_{}_{}{}.{}".format(data['dataid'], data['cnf_video_id'], str.lower(data['cnf_astream_algorithm']), data['nodeid'], interface, tstamp,
        ("_" + postfix) if postfix else "", ending)

def get_prefix(data, postfix, tstamp, interface):
    return "{}_{}_{}_{}_{}_{}{}".format(data['dataid'], data['cnf_video_id'], str.lower(data['cnf_astream_algorithm']), data['nodeid'], interface, tstamp,
        ("_" + postfix) if postfix else "")

def save_output(data, msg, postfix=None, ending="json", tstamp=time.time(), outdir="/monroe/results/", interface="interface"):
    f = NamedTemporaryFile(mode='w+', delete=False, dir=outdir)
    f.write(msg)
    f.close()
    #mfilename=get_filename(data, postfix, ending, tstamp)
    outfile = os.path.join(outdir, get_filename(data, postfix, ending, tstamp, interface))
    #print(outfile)
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
                save_output(data=msg, msg=json.dumps(msg), postfix='summary', tstamp=tstamp, outdir=expconfig['save_metadata_resultdir'], interface=ifname)

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
    """Check if we have received required information within graceperiod."""
    if not (expconfig["modeminterfacename"] in info and
            "Operator" in info and
            "Timestamp" in info and
            time.time() - info["Timestamp"] < graceperiod):
        print('DBG: testpoint0')
        print info
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
    info["Operator"] = "fake.Operator"
    info["ICCID"] = "fake.ICCID"
    info["Timestamp"] = time.time()

def create_meta_process(ifname, expconfig):
    meta_info = Manager().dict()
    process = Process(target=metadata,
                      args=(meta_info, ifname, expconfig))
    process.daemon = True
    return (meta_info, process)

#TODO

def run_exp(meta_info, expconfig):
    """Seperate process that runs the experiment and collect the ouput.
        Will abort if the interface goes down.
    """

    cfg = expconfig.copy()
    try:
        if 'cnf_add_to_result' not in cfg:
            cfg['cnf_add_to_result'] = {}
            print('DBG: testpoint1')
            #print cfg
        cfg['cnf_add_to_result'].update({
            "Guid": cfg['guid'],
            "DataId": cfg['dataid'],
            "DataVersion": cfg['dataversion'],
            "NodeId": cfg['nodeid'],
            "Iccid": meta_info["ICCID"],
            "Operator": meta_info["Operator"],
            "Time": time.strftime('%Y%m%d-%H%M%S',cfg['timestamp']),
            "Interface": cfg['modeminterfacename'],
            "cnf_astream_server_host": cfg['cnf_astream_server_host'],
            "cnf_astream_algorithm": cfg['cnf_astream_algorithm'],
            "cnf_astream_segment_limit": cfg['cnf_astream_segment_limit'],
            "cnf_video_id": cfg['cnf_video_id'],
            "TEMPOUTPUT_AStream": "NA",
            "TEMPOUTPUT_YoMo": "NA",
            "NodeId": cfg['nodeid'],
            "cnf_yomo_playback_duration_s": cfg["cnf_yomo_playback_duration_s"]})
        print('DBG: testpoint2')

        # Add metadata if requested
        if cfg['add_modem_metadata_to_result']:
            print('DBG: testpoint3')
            for k,v in meta_info.items():
                cfg['cnf_add_to_result']['info_meta_modem_' + k] = v
                print('DBG: testpoint4')

        # Run traceroute + YoMo, then traceroute + AStream once
        #print ("Running traceroute against YouTube server on interface: {}".format(cfg['modeminterfacename']))
        #run_traceroute(<target1>)
        #print ("Running YoMo with video: {}".format(cfg['cnf_video_id']))
        #outputs_yomo=run_yomo(<fileprefix,video,playback duration>)
        #print ("Running traceroute against AStream server on interface: {}".format(cfg['modeminterfacename']))
        #run_traceroute(<target2>)
        #print ("Running AStream ({}) with video: {}".format(cfg['cnf_astream_algorithm'],cfg['cnf_video_id']))
        #outputs_astream=tream(<video id,server,port,playbacktype,segmentlimit,fileprefix>)

        #TODO: construct filename prefixes for YoMo and AStream

        #towrite_data=dict()
        #towrite_data['TEMPOUTPUT'] = 'temporary output'
        towrite_data = cfg['cnf_add_to_result']
        #print(towrite_data)

        ifname=meta_info[expconfig["modeminterfacename"]]

        prefix_timestamp=time.strftime('%Y%m%d-%H%M%S',cfg['timestamp'])
        prefix_yomo=get_prefix(data=cfg, postfix="yomo", tstamp=prefix_timestamp, interface=ifname)
        prefix_astream=get_prefix(data=cfg, postfix="astream", tstamp=prefix_timestamp, interface=ifname)

        resultdir_videomon=cfg['resultdir']+"videomon/"
        if not os.path.exists(resultdir_videomon):
            os.makedirs(resultdir_videomon)
        #prefix_yomo=cfg['dataid']+'_'+cfg['cnf_video_id']+'_'+prefix_timestamp+'_yomo_'
        #prefix_astream=cfg['dataid']+'_'+cfg['cnf_video_id']+'_'+prefix_timestamp+'_astream_'

        print('Prefix for YoMo: '+prefix_yomo)
        print('Prefix for AStream: '+prefix_astream)
        print('Temporary result directory: '+resultdir_videomon)

        #TODO: run tools and write results into summary JSON

        print('Pseudo-running YoMo/AStream')
        #bitrates="1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10"
        bitrates="144p:110.139,240p:246.425,360p:262.750,480p:529.500,720p:1036.744,1080p:2793.167"

        try:

            #PART I - YoMo
            #out_yomo=run_yomo(cfg['cnf_video_id'],cfg['cnf_yomo_playback_duration_s'],prefix_yomo,bitrates,ifname,resultdir_videomon,cfg['cnf_q1'],cfg['cnf_q2'],cfg['cnf_q3'],cfg['cnf_q4'])
            #print(out_yomo)

            #TODO: parse output before writing to summary JSON
            #towrite_data['TEMPOUTPUT_YoMo'] = out_yomo

            #PART II - AStream
            server_host="128.39.37.161"
            server_port="12345"
            video_id="BigBuckBunny_4s"

            #run_astream(video_id,server_host,server_port,cfg['cnf_astream_algorithm'],cfg['cnf_astream_segment_limit'],"False",ifname,prefix_astream,cfg['resultdir'])
            #run_astream(cfg['cnf_video_id'],server_host,server_port,cfg['cnf_astream_algorithm'],cfg['cnf_astream_segment_limit'],cfg['cnf_astream_download'],ifname,prefix_astream,cfg['resultdir'])
            out_astream=run_astream(video_id,server_host,server_port,"basic",cfg['cnf_astream_segment_limit'],cfg['cnf_astream_download'],prefix_astream,ifname,resultdir_videomon,cfg['cnf_q1'],cfg['cnf_q2'],cfg['cnf_q3'],cfg['cnf_q4'])
            #print(out_astream)
            towrite_data['TEMPOUTPUT_AStream']=out_astream

        except Exception as e:
            if cfg['verbosity'] > 0:
                print ("Execution or parsing failed for error: {}").format(e)

        towrite_data['Interface']=ifname
        #print(towrite_data)
        #towrite_file='/monroe/results/temp_log.json'
        #write_json(towrite_data,towrite_file)

        #TODO: compress outputs other than summary JSON
        if 'cnf_compress_additional_results' in cfg and cfg['cnf_compress_additional_results']:
            #with tarfile.open(os.path.join(cfg['resultdir'], get_filename(data=cfg, postfix=None, ending="tar.gz", tstamp=prefix_timestamp, interface=ifname)), mode='w:gz') as tar:
            files_to_compress=resultdir_videomon+cfg['dataid']+"*"
            #    #tar.add(cfg['resultdir'], recursive=False)
            #    tar.add(files_to_compress)

            shutil.make_archive(base_name=os.path.join(cfg['resultdir'], get_filename(data=cfg, postfix=None, ending="extra", tstamp=prefix_timestamp, interface=ifname)), format='gztar', root_dir=resultdir_videomon,base_dir="./")
            shutil.rmtree(resultdir_videomon)
            #os.remove(cfg['resultdir'])

        save_output(data=cfg, msg=json.dumps(towrite_data), postfix="summary", tstamp=prefix_timestamp, outdir=cfg['resultdir'], interface=ifname)

    except Exception as e:
        if cfg['verbosity'] > 0:
            print ("Execution or parsing failed for "
                   #"config : {}, "
                   "error: {}").format(e)#cfg, e)





def create_exp_process(meta_info, expconfig):
    process = Process(target=run_exp, args=(meta_info, expconfig, ))
    process.daemon = True
    return process


#Main functions

if __name__ == '__main__':
    """The main thread controling the processes (experiment/metadata)."""

    #try:
    #    with open(CONFIGFILE) as configfd:
    #        EXPCONFIG.update(json.load(configfd))
    #except Exception as e:
    #    print("Cannot retrive expconfig {}".format(e))
    #    raise e

    # Short hand variables and check so we have all variables we need
    try:
        enabled_interfaces = EXPCONFIG['enabled_interfaces']
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

    #TODO

    tot_start_time = time.time()
    for ifname in enabled_interfaces: #netifaces.interfaces():
        print(ifname)
        # Skip disabled interfaces
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
