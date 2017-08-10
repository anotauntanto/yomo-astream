#!/bin/bash

YT_ID=$1
DIR=$2

OLD_DIR=$(pwd)


echo -e "itag,fileExtension,size(byte),bitrate(bit/s),codec,resolution,framerate"

#get best video
BEST=$(youtube-dl -F https://www.youtube.com/watch?v=$YT_ID | grep best | cut -d ' ' -f1)

# get video formats
youtube-dl -F https://www.youtube.com/watch?v=$YT_ID | while read LINE; do 

	# for i in formats download
	if [[ $LINE =~ ^[0-9].* ]]; then
		#get itag
		ITAG=$(echo "$LINE" | sed -re 's/^([0-9]+)(.*)/\1,\2/g' | sed  -e's/,//g' -e 's/ \+/,/g' | cut -d, -f1)

		#download video
		FORMAT=$(echo -n $LINE | sed -re 's/^([0-9]+).*/\1/g')
		youtube-dl -f $FORMAT https://www.youtube.com/watch?v=$YT_ID -o $DIR/_yt_dl-$ITAG.file 1>&2 > /dev/null
		sleep 5
		
		#get file extension	
		FILEEX=$(echo "$LINE" | sed -re 's/^([0-9]+)(.*)/\1,\2/g' | sed  -e's/,//g' -e 's/ \+/,/g' | cut -d, -f2)

		#get size
		SIZE="$(stat --printf="%s" $DIR/_yt_dl-$ITAG.file)"

		#get bitrate (kilobits per second)
		BITRATE=$(ffprobe -show_format $DIR/_yt_dl-$ITAG.file 2>/dev/null | grep bit_rate 2>/dev/null | cut -d= -f2) 
		#BITRATE=$(echo "scale=5; $BITRATEBIT / 1000" | bc)
		if [[ $BITRATE == 0 ]]; then
			DURATION=$(ffprobe -show_format $DIR/_yt_dl-$ITAG.file 2>/dev/null | grep duration 2>/dev/null | cut -d= -f2)
			FILESIZEBYTES=$(ffprobe -show_format $DIR/_yt_dl-$ITAG.file 2>/dev/null | grep size 2>/dev/null | cut -d= -f2)
			FILESIZEBIT=$(echo "scale=5; $FILESIZEBYTES * 0.008" | bc)
			BITRATE=$(echo "scale=5; $FILESIZEBIT / $DURATION" | bc)
		fi

		#get code name
		CODEC=$(ffprobe -show_streams $DIR/_yt_dl-$ITAG.file 2>/dev/null | grep codec_name 2>/dev/null | cut -d= -f2 | sed ':a;N;$!ba;s/\n/,/g') 

		#get resolution
		RESOLUTION=$(ffmpeg -i $DIR/_yt_dl-$ITAG.file 2>&1 | grep Stream | grep -oP ', \K[0-9]+x[0-9]+')

		#get framerate
		FRAMERATE=$(ffmpeg -i $DIR/_yt_dl-$ITAG.file 2>&1 | sed -n "s/.*, \(.*\) fp.*/\1/p")

		#write itag and resolution in file if best
		if [[ $BEST == $ITAG ]]; then
			echo "$ITAG,$RESOLUTION" > $DIR/best-$YT_ID.txt
		fi

		echo "$ITAG,$FILEEX,$SIZE,$BITRATE,$CODEC,$RESOLUTION,$FRAMERATE"
	fi

done
