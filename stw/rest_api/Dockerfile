FROM ubuntu:bionic

RUN apt-get update \
    && apt-get install -y \
    gnupg \
    systemd

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 8AA7AF1F1091A5FD && \
    echo 'deb [arch=amd64] http://repo.sawtooth.me/ubuntu/chime/stable bionic universe' >> /etc/apt/sources.list && \
    apt-get update --fix-missing

RUN apt-get install --fix-missing -y --allow-unauthenticated -q \
    locales \
    python3-pip \
    python3-sawtooth-sdk \
    python3-setuptools \
    python3-sawtooth-rest-api \
    python3-grpcio-tools \
    python3-sawtooth-cli \
    python3-secp256k1 \
    iputils-ping \
    curl \
    telnet

RUN locale-gen en_US.UTF-8

RUN pip3 install \
    requests \
    sanic==19.03.1 \
    sanic_cors

WORKDIR /project/da

ENV PATH $PATH:/project/da/bin
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8
