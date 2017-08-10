firefox --version
#google-chrome-stable -version 
#python -c 'import selenium; print selenium.__version__'
#find -name google-chrome
#find -name chromedriver
#tshark -v


#dpkg-query -L firefox		
#pip show selenium									#Version 2.53.6
#dpkg -s firefox | grep 'Version'		#Version 49.0-2
#cat /etc/issue 										#Debian GNU/Linux 8
#lsb_release -a

#echo "move chomedriver"
#chmod +x /opt/monroe/chromedriver
#mv -f /opt/monroe/chromedriver /usr/local/share/chromedriver
#ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
#ln -s /usr/local/share/chromedriver /usr/bin/chromedriver

#top -b >> /monroe/results/top.txt &
#ifconfig >> /monroe/results/ifconfig.txt 

#echo "[1] set firefox config"
#mv /opt/monroe/autoconfig.js /opt/firefox/defaults/pref
#mv /opt/monroe/mozilla.cfg  /opt/firefox


#echo "[2] add yomo and adblock_plus to firefox"
#mv /opt/monroe/yomo-42.florian.wamser@informatik.uni-wuerzburg.de.xpi /opt/firefox/browser/extensions 
#mv /opt/monroe/{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}.xpi /opt/firefox/browser/extensions


echo "[5] start collecting network traffic infos"
#sleep 10s

currDate=$(date +%Y-%m-%d_%H-%M-%S)
tshark -n -i eth0 -E separator=, -T fields -e frame.time_epoch -e tcp.len -e frame.len -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.analysis.ack_rtt -e tcp.analysis.lost_segment -e tcp.analysis.out_of_order -e tcp.analysis.fast_retransmission -e tcp.analysis.duplicate_ack -e dns -Y "tcp or dns"  >> /monroe/results/YT_tshark_"$currDate".txt 2> /monroe/results/YT_tshark_error_"$currDate".txt &
# -e dns.resp.primaryname

echo "[5] start dstat" 
dstat -t -c -C 0,1,2,3,4,5,6,7,8,total --nocolor --output /monroe/results/YT_dstat-"$currDate".csv 2>/dev/null &



#echo "[6] copy cpuinfos" 
#cat /proc/cpuinfo >  /monroe/results/cpuinfos.txt &

#lspci -v > /monroe/results/lspci.txt 

#echo "[6.1] run stress-ng"
#stress-ng --cpu 4 &

echo "[7] do measurements"
python /opt/monroe/measurements.py
#python /opt/monroe/measurementsPlugIn.py

cd /monroe/results/
YTid=$(find -name YT_b* | cut -d'_' -f3)
echo "YTID = $YTid"
mv YT_dstat-"$currDate".csv YT_dstat_"$YTid"_"$currDate".csv
mv YT_tshark_"$currDate".txt YT_tshark_"$YTid"_"$currDate".txt
mv YT_tshark_error_"$currDate".txt YT_tshark_error_"$YTid"_"$currDate".txt

echo "[8] finished"

exit
