#!/bin/bash

CONTAINER=yomo-astream
CONFIG="$(pwd)/videomon_config"
RESULT_DIR=$1
RESULT_DIR=${RESULT_DIR:=/tmp} 

docker run --shm-size=1g -v $RESULT_DIR:/monroe/results  -v $CONFIG:/monroe/config  -t $CONTAINER .
