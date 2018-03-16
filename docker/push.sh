#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#CONTAINER=${DIR##*/}
CONTAINER=yomo-astream
#CONTAINERTAG=videomon/yomo-astream
CONTAINERTAG=videomon/yomo-astream-test

#docker login &&
docker tag ${CONTAINER} ${CONTAINERTAG} && docker push ${CONTAINERTAG} && echo "Finished uploading ${CONTAINERTAG}"
