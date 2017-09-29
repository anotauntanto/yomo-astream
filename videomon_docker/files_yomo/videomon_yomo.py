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
		# Write output without buffering
		sys.stdout.flush()
		sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

		## Start tShark
		callTshark = "tshark -n -i " + interf + "-E separator=, -T fields -e frame.time_epoch -e tcp.len -e frame.len -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.analysis.ack_rtt -e tcp.analysis.lost_segment -e tcp.analysis.out_of_order -e tcp.analysis.fast_retransmission -e tcp.analysis.duplicate_ack -e dns -Y 'tcp or dns'  >>" + resultDir + prefix + "_tshark_.txt  2>" + resultDir + prefix + "_tshark_error.txt &"
		call(callTshark, shell=True)

		# Start display
		display = Display(visible=0, size=(1920, 1080)) #display size has to be cutomized 1920, 1080
		print time.time(), ' start display'
		display.start()
		time.sleep(10)

		bufferFactor = 2
		url = 'https://www.youtube.com/watch?v=' + ytid

		caps = DesiredCapabilities().FIREFOX
		caps["marionette"] = True
		#caps["pageLoadStrategy"] = "normal"  #  complete
		#caps["pageLoadStrategy"] = "eager"  #  interactive
		caps["pageLoadStrategy"] = "none"
		#caps['loggingPrefs'] = { 'browser':'ALL' }

		# Start video
		print time.time(), ' start firefox'
		browser = webdriver.Firefox(capabilities=caps)
		time.sleep(10)

		jsFile = open('/opt/monroe/pluginAsJS.js', 'r')
		js = jsFile.read()
		jsFile.close

		print time.time(), ' start video ', ytid
		browser.get(url) 

		# debug
		browser.get_screenshot_as_file(resultDir + 'screenshot0.png')
		#browser.execute_script(js)
		#browser.get_screenshot_as_file(resultDir + 'screenshot1.png')
		#browser.get_screenshot_as_file(resultDir + 'screenshot2.png')
		#time.sleep(duration/2)
		#browser.get_screenshot_as_file(resultDir + 'screenshot3.png')
		#time.sleep(duration/2)
		
		browser.execute_script(js)
		time.sleep(duration)
		browser.get_screenshot_as_file(resultDir + 'screenshot1.png')
		print "video playback ended"

		out = browser.execute_script('return document.getElementById("outC").innerHTML;')
		outE = browser.execute_script('return document.getElementById("outE").innerHTML;')

		with open(resultDir + prefix + '_buffer.txt', 'w') as f:
			f.write(out)

		with open(resultDir + prefix + '_events.txt', 'w') as f:
			f.write(outE.encode("UTF-8"))


		browser.close()
		print time.time(), ' finished firefox'

		display.stop()
		print time.time(), 'display stopped'

		## Kill Tshark
		sys.exit(0)

		# Calculate output
		out = getOutput(bitrates)
		return out

	except Exception as e:
		print time.time(), ' exception thrown'
		print e
		ts = time.time()
		st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')
		print st
		display.stop()
		## Kill Tshark
		sys.exit(0)

	return ""


# Calculate average, max, min, 25-50-75-90 quantiles of the following: bitrate [KB], buffer [s], number of stalls, duration of stalls
def getOutput(prefix, bitrates):
	out = calculateBitrate(prefix, bitrates) + calculateBuffer(prefix) + calculateStallings(prefix)
	return out

def getEvents(prefix):
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
		[times, playtime, buffertime, avPlaytime] = getBuffer(prefix)
		endtime = times[-1]
	return [timestamps, qualities, endtime]

def getBuffer(prefix):
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


def calculateBitrate(prefix, bitrates):
	[timestamps, qualities, endtime] = getEvents(prefix)
	timestamps.append(endtime)
	periods = [x / 1000 for x in timestamps]
	periods = np.diff(periods)
	periods = np.round(periods)
	periods = [int(i) for i in periods]

	usedBitrates = []
	print qualities

	for x in range(0,len(qualities)):
		index = [i for i, j in enumerate(bitrates) if qualities[x] in j]
		currRate = float(bitrates[index[0]].split(":")[1])
		usedBitrates.extend([currRate] * periods[x])

	avgBitrate = sum(usedBitrates)/len(usedBitrates)
	maxBitrate = max(usedBitrates)
	minBitrate = min(usedBitrates)
	q1 = np.percentile(usedBitrates, quant1)
	q2 = np.percentile(usedBitrates, quant2)
	q3 = np.percentile(usedBitrates, quant3)
	q4 = np.percentile(usedBitrates, quant4)
	return str(avgBitrate) + "," + str(maxBitrate) + "," + str(minBitrate) + "," + str(q1) + "," + str(q2) + "," + str(q3) + "," + str(q4)

def calculateBuffer(prefix):
	[timestamps , playtime, buffertime, avPlaytime] = getBuffer(prefix)
	avgBuffer = sum(buffertime)/len(buffertime)
	maxBuffer = max(buffertime)
	minBuffer = min(buffertime)
	q1 = np.percentile(buffertime, quant1)
	q2 = np.percentile(buffertime, quant2)
	q3 = np.percentile(buffertime, quant3)
	q4 = np.percentile(buffertime, quant4)
	return str(avgBuffer) + "," + str(maxBuffer) + "," + str(minBuffer) + "," + str(q1) + "," + str(q2) + "," + str(q3) + "," + str(q4)

def calculateStallings(prefix):
	[timestamps , playtime, buffertime, avPlaytime] = getBuffer(prefix)
	diffTimestamps = np.diff(timestamps)/1000
	diffPlaytime = np.diff(playtime)

	diffTimePlaytime = diffTimestamps - diffPlaytime
	stallings = [0]
	for i in diffTimePlaytime:
		if (i > 0.5):
			stallings.append(i)

	numOfStallings = len(stallings)
	avgStalling = sum(stallings)/len(stallings)
	maxStalling = max(stallings)
	minStalling = min(stallings)
	q1 = np.percentile(stallings, quant1)
	q2 = np.percentile(stallings, quant2)
	q3 = np.percentile(stallings, quant3)
	q4 = np.percentile(stallings, quant4)
	return str(numOfStallings) + "," + str(avgStalling) + "," + str(maxStalling) + "," + str(minStalling) + "," + str(q1) + "," + str(q2) + "," + str(q3) + "," + str(q4)
