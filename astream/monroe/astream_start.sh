#!/bin/bash

INTERFACE='eth0'

tshark -n -i $INTERFACE -E separator=, -T fields -e frame.time_epoch -e tcp.len -e frame.len -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.analysis.ack_rtt -e tcp.analysis.lost_segment -e tcp.analysis.out_of_order -e tcp.analysis.fast_retransmission -e tcp.analysis.duplicate_ack -e dns -Y 'tcp or dns'  >> /monroe/results/astream_tshark_$(date +%Y-%m-%d_%H-%M-%S).txt 2> /monroe/results/astream_tshark_error_$(date +%Y-%m-%d_%H-%M-%S).txt &

/usr/bin/python /opt/monroe/AStream_MONROE.py
