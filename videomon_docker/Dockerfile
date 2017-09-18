FROM monroe/base

MAINTAINER VideoMon

RUN  echo "export HOME=/" \
		&& export HOME=/ 

RUN echo "install additional packages" \
        && apt-get update \
        && export DEBIAN_FRONTEND=noninteractive

RUN echo "install dstat" \
        && apt-get install -q -y dstat

RUN echo "install lspci" \
        && export DEBIAN_FRONTEND=noninteractive \
		&& apt-get install -q -y pciutils

RUN echo "install numpy"
RUN apt-get update
RUN apt-get install -y libblas-dev liblapack-dev liblapacke-dev gfortran
RUN easy_install pip
RUN pip install --upgrade pip
RUN pip install numpy

COPY start.py /opt/monroe/
COPY files_yomo /opt/monroe/
COPY files_astream /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/usr/bin/python", "/opt/monroe/start.py"]
