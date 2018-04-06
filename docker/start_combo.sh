#!/bin/bash

cd /opt/monroe/

echo "  "
echo "-----------------------------"
echo "DBG: Running Nettest"
echo "-----------------------------"

python nettest.py
wait 1
python videomon_start.py
