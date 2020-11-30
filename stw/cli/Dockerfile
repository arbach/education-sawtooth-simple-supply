FROM ubuntu:bionic

RUN apt-get update \
    && apt-get install -y \
    gnupg \
    systemd

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 8AA7AF1F1091A5FD && \
    echo 'deb [arch=amd64] http://repo.sawtooth.me/ubuntu/chime/stable bionic universe' >> /etc/apt/sources.list && \
    apt-get --fix-missing update

RUN apt-get -y -f -q install \
    python3-grpcio-tools \
    python3-requests \
    python3-setuptools \
    python3-sawtooth-sdk \
#    python3-sawtooth-signing \
    python3-sawtooth-cli \
    iputils-ping \
    curl \
    telnet

WORKDIR /project/da

ENV PATH $PATH:/project/da/bin

CMD echo "\033[0;32m--- Building cli ---\n\033[0m" \
    && init-da-cli.sh