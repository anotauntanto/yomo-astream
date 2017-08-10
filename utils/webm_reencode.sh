#!/bin/bash

#code for re-encoding webm videos
#last update: 01.08.2017

brew reinstall ffmpeg --with-libvpx --with-libvorbis —-with-libopus

echo 'DBG: 144p'
ffmpeg -i transformers_144p.webm -c:v libvpx-vp9 -s 256x144 -b:v 118k -keyint_min 150 -g 150 -tile-columns 4 -frame-parallel 1 -an -f webm -dash 1 transformers_144p_new.webm
sleep 1

echo 'DBG: 240p'
ffmpeg -i transformers_240p.webm -c:v libvpx-vp9 -s 426x240 -b:v 118k -keyint_min 150 -g 150 -tile-columns 4 -frame-parallel 1 -an -f webm -dash 1 transformers_240p_new.webm
sleep 1

echo 'DBG: 360p'
ffmpeg -i transformers_360p.webm -c:v libvpx-vp9 -s 640x360 -b:v 118k -keyint_min 150 -g 150 -tile-columns 4 -frame-parallel 1 -an -f webm -dash 1 transformers_360p_new.webm
sleep 1

echo 'DBG: 480p'
ffmpeg -i transformers_480p.webm -c:v libvpx-vp9 -s 854x480 -b:v 118k -keyint_min 150 -g 150 -tile-columns 4 -frame-parallel 1 -an -f webm -dash 1 transformers_480p_new.webm
sleep 1

echo 'DBG: 720p'
ffmpeg -i transformers_720p.webm -c:v libvpx-vp9 -s 1280x720 -b:v 118k -keyint_min 150 -g 150 -tile-columns 4 -frame-parallel 1 -an -f webm -dash 1 transformers_720p_new.webm
sleep 1

echo 'DBG: 1080p'
ffmpeg -i transformers_1080p.webm -c:v libvpx-vp9 -s 1920x1080 -b:v 118k -keyint_min 150 -g 150 -tile-columns 4 -frame-parallel 1 -an -f webm -dash 1 transformers_1080p_new.webm
sleep 1

echo 'DBG: 1440p'
ffmpeg -i transformers_1440p.webm -c:v libvpx-vp9 -s 2560x1440 -b:v 118k -keyint_min 150 -g 150 -tile-columns 4 -frame-parallel 1 -an -f webm -dash 1 transformers_1440p_new.webm
sleep 1

echo 'DBG: 2160p'
ffmpeg -i transformers_2160p.webm -c:v libvpx-vp9 -s 3840x2160 -b:v 118k -keyint_min 150 -g 150 -tile-columns 4 -frame-parallel 1 -an -f webm -dash 1 transformers_2160p_new.webm
sleep 1

ffmpeg -i transformers_audio_opus_50k.webm -c:a libopus -b:a 58k -vn -f webm -dash 1 transformers_audio_opus_50k_new.webm

ffmpeg -i transformers_audio_opus_70k.webm -c:a libopus -b:a 77k -vn -f webm -dash 1 transformers_audio_opus_70k_new.webm

ffmpeg -i transformers_audio_opus_160k.webm -c:a libopus -b:a 143k -vn -f webm -dash 1 transformers_audio_opus_160k_new.webm
