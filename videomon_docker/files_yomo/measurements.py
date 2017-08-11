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


def run_yomo(ytid, duration, prefix):

	# Write output without buffering
	sys.stdout.flush()
	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

	#start display
	display = Display(visible=0, size=(1920, 1080)) #display size has to be cutomized 1920, 1080
	print time.time(), ' start display'
	display.start()
	time.sleep(10)

	bufferFactor = 2
	url = 'https://www.youtube.com/watch?v=' + ytid

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

		print time.time(), ' start video ', ytid
		browser.get(url)
		browser.execute_script(js)
		if (duration < 0):
			duration = browser.execute_script('return document.getElementsByTagName("video")[0].duration;')*bufferFactor
		time.sleep(duration)
		print "video playback ended"

		out = browser.execute_script('return document.getElementById("outC").innerHTML;')
		outE = browser.execute_script('return document.getElementById("outE").innerHTML;')

		f = open('/monroe/results/' + prefix + '_' + 'buffer.txt', 'w')
		f.write(out)
		f.close

		f2 = open('/monroe/results/' + prefix + '_' + 'events.txt', 'w')
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
