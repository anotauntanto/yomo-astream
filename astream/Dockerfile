FROM monroe/base

MAINTAINER cise@simula.no

COPY monroe /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/bin/bash", "-e", "/opt/monroe/astream_start.sh"]
