#!/usr/bin/env python

import time
import shutil
import os
import csv
import time
import datetime
import sys
import random

import monroe_exporter
import json

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

CONFIGFILE = '/monroe/config'
EXPCONFIG = {
	"ytId": "QS7lN7giXXc",
	"duration": "fullVideo"
	}


def runTest():

	#start display	
	display = Display(visible=0, size=(1920, 1080)) #display size has to be cutomized 1920, 1080
	print time.time(), ' start display'
	display.start()
	time.sleep(10)

	source = '/tmp'
	url = 'https://time.is/de/'	

	#start browser
	try:

		print time.time(), ' start firefox'
		browser = webdriver.Firefox()
		time.sleep(10)

		print time.time(), ' start url'
		browser.get(url)

		f = open('/monroe/results/test.txt', 'w')
		out = ''
		browser.execute_script('var x = 0;var out = ""; var f = function (){if (x <= 60){out = out + new Date().getTime() + ",";x++;setTimeout(f, 1000);}else document.getElementById("top").innerHTML=out;};setTimeout(f, 1000);')
		time.sleep(70)
		out = browser.execute_script('return document.getElementById("top").innerHTML;')
		f = open('/monroe/results/test.txt', 'w')
		f.write(out)
		f.close

		browser.close()
		print time.time(), ' finished firefox'

	except Exception as e:
		print time.time(), ' exception thrown'
		print e
		ts = time.time()
		st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
		print st

	display.stop()
	print time.time(), 'display stopped'

	return;


def runBaselineVideo():

	#start display	
	display = Display(visible=0, size=(1920, 1080)) #display size has to be cutomized 1920, 1080
	print time.time(), ' start display'
	display.start()
	time.sleep(10)

	bufferFactor = 2
	url = 'https://www.youtube.com/watch?v=' + EXPCONFIG['ytId']
	#url = 'https://www.youtube.com/watch?v=QS7lN7giXXc'	

	caps = DesiredCapabilities().FIREFOX
	caps["marionette"] = True
	caps["pageLoadStrategy"] = "normal"  #  complete
	#caps["pageLoadStrategy"] = "eager"  #  interactive
	#caps["pageLoadStrategy"] = "none"
	#caps['loggingPrefs'] = { 'browser':'ALL' }

	#start video
	try:

		print time.time(), ' start firefox'
		browser = webdriver.Firefox(capabilities=caps)
		time.sleep(10)

		jsFile = open('/opt/monroe/pluginAsJS.js', 'r')
		js = jsFile.read()
		jsFile.close

		print time.time(), ' start video ', EXPCONFIG['ytId']
		browser.get(url)
		browser.execute_script(js)
		if (isinstance(EXPCONFIG['duration'], int)):
			duration = EXPCONFIG['duration']
		else:
			duration = browser.execute_script('return document.getElementsByTagName("video")[0].duration;')*bufferFactor
		time.sleep(duration)
		print "video playback ended"

		out = browser.execute_script('return document.getElementById("outC").innerHTML;')
		outE = browser.execute_script('return document.getElementById("outE").innerHTML;')

		ts = time.time()
		st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')

		f = open('/monroe/results/YT_buffer_' + EXPCONFIG['ytId'] + '_' + st + '.txt', 'w')
		f.write(out)
		f.close

		f2 = open('/monroe/results/YT_events_' + EXPCONFIG['ytId'] + '_' + st + '.txt', 'w')
		f2.write(outE.encode("UTF-8"))
		f2.close

		browser.close()
		print time.time(), ' finished firefox'

		
	except Exception as e:
		print time.time(), ' exception thrown'
		print e
		ts = time.time()
		st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')
		print st
		
	display.stop()
	print time.time(), 'display stopped'
	return;


def runRandomVideo():

	#start display	
	display = Display(visible=0, size=(1920, 1080)) #display size has to be cutomized
	display.start()
	print'started display'

	bufferFactor = 2
	source = '/tmp'
	ts = time.time()
	st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')


	#get ytid
	r = random.randint(0,100)
	lines = []
	if (r > 60):
		#random video (40%)
		print 'random int', r ,' --> select video from random list'
		with open('/opt/monroe/randYTIDs.txt','r') as f:
		  for line in f:
		      lines.append(line.rstrip('\n'))
	else:
		#video from core set (60%)
		print 'random int', r ,' --> select video from core set'
		with open('/opt/monroe/coreSet.txt','r') as f:
		  for line in f:
		      lines.append(line.rstrip('\n'))
	#get random id from list
	randInt = random.randint(0,len(lines)-1)
	print 'select video number ', randInt
	randVideoId = lines[randInt]
	url = 'https://www.youtube.com/watch?v=' + randVideoId
	print 'selected VideoId: ', randVideoId
	

	#start video
	try:
		browser = webdriver.Firefox()
		browser.get(url)
		duration = browser.execute_script('return document.getElementsByTagName("video")[0].duration;')
		print 'started video ', randVideoId, ' with duration ', duration
		time.sleep(duration*bufferFactor)
		#time.sleep(20)
		browser.close()
		print 'finished video ', randVideoId, ' with duration ', duration

		#move yomo output
		destination = '/monroe/results/' + 'random'
		if not os.path.exists(destination):
			os.makedirs(destination)
			print 'created dir' + destination
		print 'set destination of output to ' + destination

		files = os.listdir(source)
		for f in files:
			if (f.startswith("yomo_output_")):
				shutil.move(source + '/' + f, destination)
		print 'moved plugin output to ' + destination 
	except Exception as e:
		print e
		st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
		print st

	display.stop()
	print 'display stopped'
	return;


# ----- MAIN

# Write output without buffering
sys.stdout.flush()
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)


# Try to get the experiment config as provided by the scheduler
try:
    with open(CONFIGFILE) as configfd:
        EXPCONFIG.update(json.load(configfd))
except Exception as e:
    print "Cannot retrive expconfig {}".format(e), "-- use defaulte settings"



# Start Measurements
#runTest()
runBaselineVideo()
#runRandomVideo()
