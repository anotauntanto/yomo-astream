#!/bin/bash

cd /opt/monroe/

echo "  "
echo "-----------------------------"
echo "DBG: Running Nettest"
echo "-----------------------------"
python nettest.py

echo "  "
echo "-----------------------------"
echo "DBG: Waiting between Nettest and VideoMon"
echo "-----------------------------"
sleep 1

echo "  "
echo "-----------------------------"
echo "DBG: Running VideoMon"
echo "-----------------------------"
python videomon_start.py
