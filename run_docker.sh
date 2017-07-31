#!/bin/bash

#last update: 31.07.2017

function func_stopMONROEprocesses{
echo "DBG: stopping unnecessary MONROE processes"
sleep 1
systemctl stop marvind cron wd_keepalive watchdog
}

function func_pullYoMo {
  echo "DBG: updating YoMo container"
  sleep 1
  docker pull mobiqoe/yomo_docker
}


function func_runYoMo {
echo "DBG: running YoMo container"
sleep 1
docker run --net=host -it --rm -v /pwd/results:/monroe/results mobiqoe/yomo_docker
}

function func_pullAStream {
  echo "DBG: updating AStream container"
  sleep 1
  docker pull andralutu/astream
}

function func_runAStream {
echo "DBG: running AStream container"
sleep 1
docker run --net=host -it --rm -v /home/monroeSA/astream.config:/monroe/config -v /pwd/results:/monroe/results cmidoglu/astream
}
