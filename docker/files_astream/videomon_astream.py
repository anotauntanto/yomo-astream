#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Cise Midoglu
# Last Update: March 2018
# License: GNU General Public License v3
# Developed for use by the EU H2020 MONROE project

import io
import json
import zmq
import sys
import netifaces
import time
from subprocess import check_output, CalledProcessError
from multiprocessing import Process, Manager
import shutil
from tempfile import NamedTemporaryFile
import glob
import dash_client
import config_dash
import numpy
import pandas


def run_astream(mpd,server_host,server_port,video,algorithm,segment_limit,download,logdirectory,videodirectory,q1,q2,q3,q4,segmentduration):

    #TODO: update config_dash args from this script
    #config_dash.LOG_FOLDER = logdirectory

    if mpd is not None:
        dash_client.main(mpd,algorithm,segment_limit,download,videodirectory)
    else:
        mpd_url = 'http://' + server_host + ':' + str(server_port) + '/' + video + '.mpd'
        dash_client.main(mpd_url,algorithm,segment_limit,download,videodirectory)

    astream_segment_log = glob.glob(logdirectory+'ASTREAM*.json')[0]
    astream_buffer_log = glob.glob(logdirectory+'DASH_BUFFER*.csv')[0]
    astream_runtime_log = glob.glob(logdirectory+'DASH_RUNTIME*.log')[0]

    # if cfg['verbosity'] > 2:
    print('\n-----------------------------')
    print('DBG: Output files from AStream core:')
    print('-----------------------------')
    print(astream_segment_log)
    print(astream_buffer_log)
    print(astream_runtime_log)
    print('-----------------------------')

    # #CM: generating output
    out_astream = getOutput(astream_segment_log,astream_buffer_log,q1,q2,q3,q4,segmentduration)
    return out_astream


def getOutput(segmentlog,bufferlog,q1,q2,q3,q4,segmentduration):
    out = calculateBitrate(segmentlog,q1,q2,q3,q4) + ',' + calculateBuffer(bufferlog,q1,q2,q3,q4,segmentduration) + ',' + calculateStallings(segmentlog,q1,q2,q3,q4)
    return out

def calculateBitrate(segmentlog,q1,q2,q3,q4):

    try:
        bitrates=[]
        json_in = open(segmentlog)
        clientlog=json.load(json_in)
        #playback_info = clientlog["playback_info"]
        #down_shifts = playback_info["down_shifts"]
        #up_shifts = playback_info["up_shifts"]
        segment_info = clientlog["segment_info"]
        for segment in segment_info:
            #print segment
            if 'init' not in segment[0]:
                bitrates.append(segment[1]/1000)
                #print segment[0], segment[1]

        bitrates_avg=numpy.mean(bitrates)
        bitrates_max=max(bitrates)
        bitrates_min=min(bitrates)
        bitrates_q1=numpy.percentile(bitrates, q1)
        bitrates_q2=numpy.percentile(bitrates, q2)
        bitrates_q3=numpy.percentile(bitrates, q3)
        bitrates_q4=numpy.percentile(bitrates, q4)

        video_metadata = clientlog["video_metadata"]
        available_bitrates = video_metadata["available_bitrates"]

        bitrates_list=''
        for available_bitrate in available_bitrates:
            try:
                bitrate_current = str(available_bitrate["bandwidth"])
            except Exception:
                #CM: bitrates list is not a dictionary
                bitrate_current = str(available_bitrate)

            bitrates_list = bitrates_list + 'b' + bitrate_current + ' '

        #print (bitrates_list + ',' + str(bitrates_avg) + ',' + str(bitrates_max) + ',' + str(bitrates_min) + ',' + str(bitrates_q1) + ',' + str(bitrates_q2) + ',' + str(bitrates_q3) + ',' + str(bitrates_q4))
        return bitrates_list + ',' + str(bitrates_avg) + ',' + str(bitrates_max) + ',' + str(bitrates_min) + ',' + str(bitrates_q1) + ',' + str(bitrates_q2) + ',' + str(bitrates_q3) + ',' + str(bitrates_q4)

    except Exception as e:
        print ('[ERROR] AStream calculateBitrate exception: {}').format(e)
        return 'NA,NA,NA,NA,NA,NA,NA,NA'

def calculateBuffer(bufferlog,q1,q2,q3,q4,segmentduration):

    try:
        csvfile = pandas.read_csv(bufferlog)
        epoch_time = csvfile.EpochTime
        current_playback_time = csvfile.CurrentPlaybackTime
        current_buffer_size_raw = csvfile.CurrentBufferSize
        current_buffer_size = [0 if i < 0 else i for i in current_buffer_size_raw] #convert negative values to 0

        current_playback_state = csvfile.CurrentPlaybackState
        action = csvfile.Action

        # csvfile= csv.reader(open(bufferlog, 'r'), delimiter=',')
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

            current_buffer_s = isnotbuffering * buffers[i-1] + iswriting * segmentduration - isplaying * (epoch_time[i] - epoch_time[i-1])
            buffers.append(current_buffer_s)

        #CM: interpolating to 1s granularity
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

        #print str(buffers_avg) + ',' + str(buffers_max) + ',' + str(buffers_min) + ',' + str(buffers_q1) + ',' + str(buffers_q2) + ',' + str(buffers_q3) + ',' + str(buffers_q4)
        return str(buffers_avg) + ',' + str(buffers_max) + ',' + str(buffers_min) + ',' + str(buffers_q1) + ',' + str(buffers_q2) + ',' + str(buffers_q3) + ',' + str(buffers_q4)

    except Exception as e:
        print ('[ERROR] AStream calculateBuffer exception: {}').format(e)
        return 'NA,NA,NA,NA,NA,NA,NA'

def calculateStallings(segmentlog,q1,q2,q3,q4):

    try:
        json_in = open(segmentlog)
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

        return str(num_stalls) + ',' + str(durstalls_avg) + ',' + str(durstalls_max) + ',' + str(durstalls_min) + ',' + str(durstalls_q1) + ',' + str(durstalls_q2) + ',' + str(durstalls_q3) + ',' + str(durstalls_q4) + ',' + str(stalls_total_duration) + ',' + str(up_shifts) + ',' + str(down_shifts)

    except Exception as e:
        print ('[ERROR] AStream calculateStallings exception: {}').format(e)
        return "NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA"
