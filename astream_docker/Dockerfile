FROM monroe/base

MAINTAINER cise@simula.no

RUN echo "install additional packages" \
        && apt-get update \
        && export DEBIAN_FRONTEND=noninteractive \
        && apt-get update -q \
        && apt-get install -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" tshark

COPY monroe /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/bin/bash", "-e", "/opt/monroe/astream_start.sh"]
