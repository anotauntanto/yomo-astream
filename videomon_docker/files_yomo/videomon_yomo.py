#!/usr/bin/env python

import time
import shutil
import os
import csv
import time
import datetime
import sys
import random
import psutil
import numpy as np

import monroe_exporter
import json

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from subprocess import call


def run_yomo(ytid, duration, prefix, bitrates,interf,resultDir,quant1,quant2,quant3,quant4):

	try:
		# write output without buffering
		sys.stdout.flush()
		sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

		# start tshark
		callTshark = "tshark -n -i " + interf + " -E separator=, -T fields -e frame.time_epoch -e tcp.len -e frame.len -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.analysis.ack_rtt -e tcp.analysis.lost_segment -e tcp.analysis.out_of_order -e tcp.analysis.fast_retransmission -e tcp.analysis.duplicate_ack -e dns -Y 'tcp or dns'  >>" + resultDir + prefix + "_tshark_.txt  2>" + resultDir + prefix + "_tshark_error.txt &"
		call(callTshark, shell=True)

		# start display	
		display = Display(visible=0, size=(4000,2400)) #old: 1920, 1080
		print time.time(), ' start display'
		display.start()
		time.sleep(10)

		# get url
		url = 'https://www.youtube.com/watch?v=' + ytid

		# define firefox settings
		caps = DesiredCapabilities().FIREFOX
		#caps["pageLoadStrategy"] = "normal"  #  complete
		caps["pageLoadStrategy"] = "none"

		# start firefox
		print time.time(), ' start firefox'
		browser = webdriver.Firefox(capabilities=caps)

		# set window size	
		browser.set_window_position(0,0)
		browser.set_window_size(3840, 2260)
		time.sleep(10)

		# read in js
		print "-- using WIDE mode"
		jsFile = open('/opt/monroe/getVideoInfos.js', 'r')
		js = jsFile.read()
		jsFile.close

		# open webpage
		print time.time(), ' start video ', ytid
		browser.get(url) 

		# inject js
		browser.execute_script(js)
		time.sleep(duration)
		browser.get_screenshot_as_file(resultDir + 'screenshot.png')
		print "video playback ended"

		# get infos from js and write to file
		out = browser.execute_script('return document.getElementById("outC").innerHTML;')
		outE = browser.execute_script('return document.getElementById("outE").innerHTML;')
		with open(resultDir + prefix + '_buffer.txt', 'w') as f:
			f.write(out.encode("UTF-8"))
		with open(resultDir + prefix + '_events.txt', 'w') as f:
			f.write(outE.encode("UTF-8"))

		# close browser and stop display
		browser.close()
		print time.time(), ' finished firefox'
		display.stop()
		print time.time(), 'display stopped'

	except Exception as e:
		# handle exception
		print time.time(), ' exception thrown'
		print e
		ts = time.time()
		st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')
		print st
		display.stop()

	try:
		# Calculate output
		out = getOutput(resultDir,prefix,bitrates,quant1,quant2,quant3,quant4)
		#print out
		return out

	except Exception as e:
		print time.time(), ' exception thrown'
		print e
		ts = time.time()
		st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')
		print st
		## Kill Tshark
		#sys.exit(0)
		return "NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA,NA"

	return ""

  
# Calculate average, max, min, 25-50-75-90 quantiles of the following: bitrate [KB], buffer [s], number of stalls, duration of stalls, total stall duration, quality switches (up/down)
def getOutput(resultDir,prefix, bitrates,quant1,quant2,quant3,quant4):
	out = calculateBitrate(resultDir,prefix, bitrates.split(","),quant1,quant2,quant3,quant4) + "," + calculateBuffer(resultDir,prefix,quant1,quant2,quant3,quant4) + "," + calculateStallings(resultDir,prefix,quant1,quant2,quant3,quant4)
	return out

def getEvents(resultDir,prefix):
	timestamps = []
	qualities = []
	with open(resultDir + prefix + "_events.txt", "r") as filestream:
		for line in filestream:
			currentline = line.split("#")
			if ("quality" in currentline[1]): 
				timestamps.append(float(currentline[0]))
				quality = str(currentline[1])
				quality = quality.split(":")[1]
				quality = quality.split(" ")[0]
				qualities.append(quality)
			if ("ended" in currentline[1]):
				endtime = float(currentline[0])
	if 'endtime' not in locals():
		[times, playtime, buffertime, avPlaytime] = getBuffer(resultDir,prefix)
		endtime = times[-1]
	#print "timestamps: ", timestamps, ", qualities: ", qualities, "endtime: ", endtime
	return [timestamps, qualities, endtime]

def getBuffer(resultDir,prefix):
	timestamps = []
	playtime = []
	buffertime = []
	avPlaytime = []
	isFirstLine = True
	with open(resultDir + prefix + "_buffer.txt", "r") as filestream:
		for line in filestream:
			currentline = line.split("#")
			# end of video
			if (isFirstLine is False and float(currentline[1]) == playtime[-1]): #TODO
				break;
			timestamps.append(float(currentline[0]))
			playtime.append(float(currentline[1]))
			buffertime.append(float(currentline[2]))
			avPlaytime.append(float(currentline[3][:-1]))
			isFirstLine = False
	return [timestamps , playtime, buffertime, avPlaytime]


def calculateBitrate(resultDir,prefix, bitrates,quant1,quant2,quant3,quant4):
	[timestamps, qualities, endtime] = getEvents(resultDir,prefix)
	timestamps.append(endtime)
	periods = [x / 1000 for x in timestamps]
	periods = np.diff(periods)
	periods = np.round(periods)
	periods = [int(i) for i in periods]

	usedBitrates = []
	qualUpSwitch = 0;
	qualDownSwitch = 0;

	for x in range(0,len(qualities)):
		index = [i for i, j in enumerate(bitrates) if qualities[x] in j]
		#print "index: ", index
		currRate = float(bitrates[index[0]].split(":")[1])
		#print "currRate: ", currRate
		usedBitrates.extend([currRate] * periods[x])
		if(int(qualities[x].split('p')[0]) > int(qualities[x-1].split('p')[0])): 
			qualUpSwitch += 1
		elif(int(qualities[x].split('p')[0]) < int(qualities[x-1].split('p')[0])): 
			qualDownSwitch += 1
			
	#print "len(usedBitrates): ", len(usedBitrates)
	print "qualities", qualities
	print "qualUpSwitch: ", qualUpSwitch
	print "qualDownSwitch: ", qualDownSwitch
	avgBitrate = sum(usedBitrates)/len(usedBitrates)
	maxBitrate = max(usedBitrates)
	minBitrate = min(usedBitrates)
	q1 = np.percentile(usedBitrates, quant1)
	q2 = np.percentile(usedBitrates, quant2)
	q3 = np.percentile(usedBitrates, quant3)
	q4 = np.percentile(usedBitrates, quant4)
	return str(avgBitrate) + "," + str(maxBitrate) + "," + str(minBitrate) + "," + str(q1) + "," + str(q2) + "," + str(q3) + "," + str(q4) + "," + str(qualUpSwitch) + "," + str(qualDownSwitch)

def calculateBuffer(resultDir,prefix,quant1,quant2,quant3,quant4):
	[timestamps , playtime, buffertime, avPlaytime] = getBuffer(resultDir,prefix)
	#print "len(buffertime): ", len(buffertime)
	avgBuffer = sum(buffertime)/len(buffertime)
	maxBuffer = max(buffertime)
	minBuffer = min(buffertime)
	q1 = np.percentile(buffertime, quant1)
	q2 = np.percentile(buffertime, quant2)
	q3 = np.percentile(buffertime, quant3)
	q4 = np.percentile(buffertime, quant4)
	return str(avgBuffer) + "," + str(maxBuffer) + "," + str(minBuffer) + "," + str(q1) + "," + str(q2) + "," + str(q3) + "," + str(q4)

def calculateStallings(resultDir,prefix,quant1,quant2,quant3,quant4):
	[timestamps , playtime, buffertime, avPlaytime] = getBuffer(resultDir,prefix)
	diffTimestamps = np.diff(timestamps)/1000
	diffPlaytime = np.diff(playtime)

	diffTimePlaytime = diffTimestamps - diffPlaytime
	stallings = []
	for i in diffTimePlaytime:
		if (i > 0.5):
			stallings.append(i)

	numOfStallings = len(stallings)
	print "len(stallings)", len(stallings)
	if (numOfStallings < 1):
		avgStalling = 0
		maxStalling = 0
		minStalling = 0
		q1 = 0
		q2 = 0
		q3 = 0
		q4 = 0
		totalStalling = 0
	else:
		avgStalling = sum(stallings)/len(stallings)
		maxStalling = max(stallings)
		minStalling = min(stallings)
		q1 = np.percentile(stallings, quant1)
		q2 = np.percentile(stallings, quant2)
		q3 = np.percentile(stallings, quant3)
		q4 = np.percentile(stallings, quant4)
		totalStalling = sum(stallings)
	print "totalStalling: ", totalStalling
	return str(numOfStallings) + "," + str(avgStalling) + "," + str(maxStalling) + "," + str(minStalling) + "," + str(q1) + "," + str(q2) + "," + str(q3) + "," + str(q4) + "," + str(totalStalling)
