FROM monroe/base:web

MAINTAINER VideoMon

RUN  echo "export HOME=/" \
		&& export HOME=/ 

RUN echo "install dstat" \
        && apt-get update -q \
        && apt-get install -q -y dstat

RUN echo "install pciutils" \
        && export DEBIAN_FRONTEND=noninteractive \
		&& apt-get install -q -y pciutils


RUN echo "install numpy, psutil, pandas"
RUN apt-get update -q
RUN apt-get install -y libblas-dev liblapack-dev liblapacke-dev gfortran
RUN apt-get install -y python-pip 
RUN pip install numpy
RUN pip install psutil
RUN pip install pandas


# Gecko Driver
ENV GD_VER 0.19.1
#APT OPTS
RUN curl -L -o geckodriver.tgz "https://github.com/mozilla/geckodriver/releases/download/v${GD_VER}/geckodriver-v${GD_VER}-linux64.tar.gz" \
    && tar -C /usr/bin -zxf geckodriver.tgz


COPY videomon_start.py /opt/monroe/
COPY files_yomo /opt/monroe/
COPY files_astream /opt/monroe/

COPY files_yomo/autoconfig.js /opt/firefox/defaults/pref
COPY files_yomo/mozilla.cfg  /opt/firefox
COPY files_yomo/{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}.xpi /opt/firefox/browser/extensions

ENTRYPOINT ["dumb-init", "--", "/usr/bin/python", "/opt/monroe/videomon_start.py"]
