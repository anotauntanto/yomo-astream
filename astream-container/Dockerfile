FROM monroe/base

MAINTAINER cise@simula.no

COPY monroe /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/usr/bin/python", "/opt/monroe/AStream_MONROE.py"]
