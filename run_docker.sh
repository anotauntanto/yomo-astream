#!/bin/bash

#last update: 31.07.2017

LOC_CONFIG='/home/cise/yomo-astream/config'
LOC_RESULT='/home/cise/yomo-astream/results'

###FUNCTION DECLARATIONS###

function func_stopMONROEprocesses {
  echo 'DBG: stopping unnecessary MONROE processes'
  sleep 1
  systemctl stop marvind cron wd_keepalive watchdog
}

function func_pullYoMo {
  echo 'DBG: updating YoMo container'
  sleep 1
  docker pull mobiqoe/yomo_docker
}

function func_runYoMo {
  echo 'DBG: running YoMo container'
  sleep 1
  docker run --net=host -it --rm -v /pwd/results:/monroe/results mobiqoe/yomo_docker
}

function func_pullAStream {
  echo 'DBG: updating AStream container'
  sleep 1
  docker pull cmidoglu/astream
}

function func_runAStream {
  echo 'DBG: running AStream container'
  sleep 1
  docker run --net=host -it --rm -v $LOC_CONFIG/astream.config:/monroe/config -v $LOC_RESULT:/monroe/results cmidoglu/astream
}

function func_runAStream_basic {
  echo 'DBG: running AStream container'
  sleep 1
  docker run --net=host -it --rm -v $LOC_CONFIG/astream-basic.config:/monroe/config -v $LOC_RESULT:/monroe/results cmidoglu/astream
}

function func_runAStream_sara {
  echo 'DBG: running AStream container'
  sleep 1
  docker run --net=host -it --rm -v $LOC_COFIG/astream-sara.config:/monroe/config -v $LOC_RESULT:/monroe/results cmidoglu/astream
}

function func_runAStream_netflix {
  echo 'DBG: running AStream container'
  sleep 1
  docker run --net=host -it --rm -v $LOC_CONFIG/astream-netflix.config:/monroe/config -v $LOC_RESULT:/monroe/results cmidoglu/astream
}

function func_runRandomOrder {
  entries=$(shuf -i 1-4 -n 4)
  echo 'DBG: test order:' $entries
  for entry in ${entries[@]}; do
    if [ $entry -eq 1 ]; then
      func_runAStream_basic
      sleep 1; fi

      if [ $entry -eq 2 ]; then
        func_runAStream_sara
        sleep 1; fi

        if [ $entry -eq 3 ]; then
          func_runAStream_netflix
          sleep 1; fi

          if [ $entry -eq 4 ]; then
            func_runYoMo
            sleep 1; fi
          done
        }

function func_runNonRandomOrder {
  func_runAStream_basic
  sleep 1
  func_runAStream_sara
  sleep 1
  func_runAStream_netflix
  sleep 1
  func_runYoMo
  sleep 1
}

function func_test {
  func_runAStream
  sleep 1
  func_runYoMo
  sleep 1
}

###ACTIONS###

#echo '----------DBG: starting script----------'
#echo "Enter number of batches:"
#read input1

#for i in `seq 1 $input1`;
#do
#echo ''
#echo '----------DBG: running measurement batch $i----------'
#func_stopMONROEprocesses
#func_stopMONROEprocesses
#func_pullAStream
#func_pullYoMo
#	func_runRandomOrder
#	#func_runNonRandomOrder
#	sleep 1800
#done

func_stopMONROEprocesses
func_stopMONROEprocesses
func_pullAStream
func_pullYoMo
func_runRandomOrder

###END Of SCRIPT##
