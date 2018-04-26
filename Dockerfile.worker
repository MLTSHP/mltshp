FROM ubuntu:16.04
LABEL maintainer "brad@bradchoate.com"
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update && \
    apt-get install -y software-properties-common python-software-properties && \
    add-apt-repository -y ppa:jonathonf/ffmpeg-3 && \
    apt-get install -y \
    supervisor \
    cron \
    libmysqlclient-dev \
    mysql-client \
    python-dev \
    libjpeg-dev \
    libcurl4-openssl-dev \
    curl \
    run-one \
    ffmpeg \
    wget \
    vim \
    libpcre3 \
    libpcre3-dev \
    libssl-dev \
    libffi-dev \
    python-pip && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -U pip setuptools distribute && \
    # Fix for a really weird issue when installing postmark library
    # distribute fails to run since it sees a setuptools with "0.7"
    # in the name, even though ubuntu:16.04 has pre-installed "20.7.0"
    # https://github.com/pypa/setuptools/issues/543
    rm -rf /usr/lib/python2.7/dist-packages/setuptools-20.7.0.egg-info && \
    groupadd ubuntu --gid=1010 && \
    useradd ubuntu --create-home --home-dir=/home/ubuntu \
        --uid=1010 --gid=1010 && \
    mkdir -p /srv/mltshp.com/logs && \
    chown -R ubuntu:ubuntu /srv/mltshp.com

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY setup/production/supervisord-worker.conf /etc/supervisor/conf.d/mltshp.conf

# NOTE: /srv/mltshp.com/logs should be a mounted volume for this image
ADD . /srv/mltshp.com/mltshp
WORKDIR /srv/mltshp.com/mltshp
RUN crontab -u ubuntu setup/production/mltshp-worker--crontab

CMD ["/usr/bin/supervisord"]
