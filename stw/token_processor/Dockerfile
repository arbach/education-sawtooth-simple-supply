FROM ubuntu:bionic

RUN apt-get update \
    && apt-get install -y \
    gnupg \
    systemd

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 8AA7AF1F1091A5FD && \
    echo 'deb [arch=amd64] http://repo.sawtooth.me/ubuntu/chime/stable bionic universe' >> /etc/apt/sources.list && \
    apt-get update

RUN apt-get install -y -f -q \
    python3-grpcio-tools \
    python3-requests \
    python3-setuptools \
    python3-sawtooth-sdk \
    iputils-ping \
    curl \
    telnet

WORKDIR /project/da

ENV PATH $PATH:/project/da/bin

CMD echo "\033[0;32m--- Building token-tp ---\n\033[0m" \
    && init-token-tp.sh \
    && token-tp -v -C tcp://validator:4004
