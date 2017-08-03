#!/bin/bash

#last update: 02.08.2017

VIDEO='transformers'
SEGMENT_DURATION='10'
SEGMENT_SIZE='184.0'
SEGMENT_SCALE='Kbits'
NUM_SEGMENTS=10
MIME_TYPE='video/webm'
CODECS='vp9'
TIMESCALE='1000'
DURATION='10000'
REPRESENTATIONS='144p 240p 1080p'

function func_addsegment {
  VIDEO=$1
  SEGMENT_DURATION=$2
  SEGMENT_SIZE=$3
  SEGMENT_SCALE=$4
  SEGMENT_NO=$5

  SEGMENT_ID=$VIDEO'_'$SEGMENT_DURATION's'$SEGMENT_NO'.m4s'
  echo '<SegmentSize id="'$SEGMENT_ID'" size="'$SEGMENT_SIZE'" scale="'$SEGMENT_SCALE'"/>'
}

function func_addrepresentation {
  VIDEO=$1
  SEGMENT_DURATION=$2
  SEGMENT_SIZE=$3
  SEGMENT_SCALE=$4
  NUM_SEGMENTS=$5
  REPRESENTATION_ID=$6
  MIME_TYPE=$7
  CODECS=$8
  WIDTH=$9
  HEIGHT=${10}
  TIMESCALE=${11}
  DURATION=${12}

  MEDIA='media/'$VIDEO'/'$SEGMENT_DURATION'/'$REPRESENTATION_ID'/'$VIDEO'_'$SEGMENT_DURATION's$Number$.m4s'
  #MEDIA='media/BigBuckBunny/4sec/bunny_$Bandwidth$bps/BigBuckBunny_4s$Number$%d.m4s'
  INITIALIZATION='media/'$VIDEO'/'$SEGMENT_DURATION'/'$REPRESENTATION_ID'/'$VIDEO'_'$SEGMENT_DURATION's_init.mp4'
  #INITIALIZATION='media/BigBuckBunny/4sec/bunny_$Bandwidth$bps/BigBuckBunny_4s_init.mp4'


echo '<Representation id="'$REPRESENTATION_ID'" mimeType="'$MIME_TYPE'" codecs="'$CODECS'" width="'$WIDTH'"  height="'$HEIGHT'" frameRate="'$FRAME_RATE'" sar="1:1" startWithSAP="1"  bandwidth="45226" >
  <SegmentTemplate timescale="'$TIMESCALE'" media="'$MEDIA'" startNumber="1" duration="'$DURATION'" initialization="'$INITIALIZATION'" />'

for i in `seq 1 $NUM_SEGMENTS`; do
  func_addsegment $VIDEO $SEGMENT_DURATION $SEGMENT_SIZE $SEGMENT_SCALE $i
done

echo '</Representation>'

}

function func_addadaptationset {
  VIDEO=$1
  SEGMENT_DURATION=$2
  SEGMENT_SIZE=$3 #might need to adjust according to representation
  SEGMENT_SCALE=$4
  NUM_SEGMENTS=$5

  MIME_TYPE=$6
  CODECS=$7

  TIMESCALE=$8
  DURATION=$9
  #REPRESENTATIONS=${10}
  #echo $REPRESENTATIONS

args=("$@")

#reps=($REPRESENTATIONS)
#echo $reps
#NUM_REPRESENTATIONS=${#reps[@]} #count number of representations

NUM_REPRESENTATIONS=$(( $#-9 ))
#echo $NUM_REPRESENTATIONS

echo '<AdaptationSet mimeType="'$MIME_TYPE'" segmentAlignment="true" group="1" maxWidth="480" maxHeight="360" maxFrameRate="24" par="4:3">'

#for i in `seq 1 $NUM_REPRESENTATIONS`; do
for i in `seq 9 $#`; do

  REPRESENTATION_ID=${args[$i]} #parse ID from $REPRESENTATIONS
  #echo $REPRESENTATION_ID

  WIDTH='1920'
  #$(cat filename | grep $REPRESENTATION_ID | awk {print $2})
  #TODO: parse from resolution
  HEIGHT='1080'
  #$(cat filename | grep $REPRESENTATION_ID | awk {print $2})
  #TODO: parse from resolution

  func_addrepresentation $VIDEO $SEGMENT_DURATION $SEGMENT_SIZE $SEGMENT_SCALE $NUM_SEGMENTS $REPRESENTATION_ID $MIME_TYPE $CODECS $WIDTH $HEIGHT $TIMESCALE $DURATION
done

echo '</AdaptationSet>'

}

### ACTIONS ###

echo '
<?xml version="1.0" encoding="UTF-8"?>
<!-- MPD file Generated with bash script  on 2017-08-02T-->
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" minBufferTime="PT1.500000S" type="static" mediaPresentationDuration="PT0H9M56.46S" profiles="urn:mpeg:dash:profile:isoff-live:2011">
  <Period duration="PT0H9M56.46S">'


func_addadaptationset $VIDEO $SEGMENT_DURATION $SEGMENT_SIZE $SEGMENT_SCALE $NUM_SEGMENTS $MIME_TYPE $CODECS $TIMESCALE $DURATION $REPRESENTATIONS

echo '</Period>
</MPD>'
