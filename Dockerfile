FROM ubuntu:16.04
LABEL maintainer "brad@bradchoate.com"
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update && apt-get install -y \
    supervisor \
    libmysqlclient-dev \
    mysql-client \
    python-dev \
    libjpeg-dev \
    libcurl4-openssl-dev \
    curl \
    wget \
    vim \
    libpcre3 \
    libpcre3-dev \
    libssl-dev \
    libffi-dev \
    python-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U pip setuptools distribute
# Fix for a really weird issue when installing postmark library
# distribute fails to run since it sees a setuptools with "0.7"
# in the name, even though ubuntu:16.04 has pre-installed "20.7.0"
# https://github.com/pypa/setuptools/issues/543
RUN rm -rf /usr/lib/python2.7/dist-packages/setuptools-20.7.0.egg-info

# nginx + nginx-upload module
RUN mkdir -p /tmp/install && mkdir -p /var/log/nginx
WORKDIR /tmp/install
RUN wget http://nginx.org/download/nginx-0.8.55.tar.gz && tar zxf nginx-0.8.55.tar.gz
#RUN wget http://nginx.org/download/nginx-1.2.9.tar.gz && tar zxf nginx-1.2.9.tar.gz
#RUN wget http://nginx.org/download/nginx-1.10.3.tar.gz && tar zxf nginx-1.10.3.tar.gz
RUN wget https://github.com/vkholodkov/nginx-upload-module/archive/2.2.tar.gz && tar zxf 2.2.tar.gz
#WORKDIR /tmp/install/nginx-1.10.3
#WORKDIR /tmp/install/nginx-1.2.9
WORKDIR nginx-0.8.55

RUN ./configure \
    --with-http_ssl_module \
    --with-pcre \
    --sbin-path=/usr/sbin/nginx \
    --pid-path=/run/nginx.pid \
    --conf-path=/etc/nginx/nginx.conf \
    --error-log-path=/var/log/nginx/error.log \
    --http-log-path=/var/log/nginx/access.log \
    --add-module=/tmp/install/nginx-upload-module-2.2 \
    && make && make install && mkdir -p /etc/nginx
RUN rm -rf /tmp/install

RUN groupadd ubuntu --gid=1010 && \
    useradd ubuntu --create-home --home-dir=/home/ubuntu \
        --uid=1010 --gid=1010
RUN mkdir -p /mnt/tmpuploads/0 && \
    mkdir -p /mnt/tmpuploads/1 && \
    mkdir -p /mnt/tmpuploads/2 && \
    mkdir -p /mnt/tmpuploads/3 && \
    mkdir -p /mnt/tmpuploads/4 && \
    mkdir -p /mnt/tmpuploads/5 && \
    mkdir -p /mnt/tmpuploads/6 && \
    mkdir -p /mnt/tmpuploads/7 && \
    mkdir -p /mnt/tmpuploads/8 && \
    mkdir -p /mnt/tmpuploads/9 && \
    chmod 777 /mnt/tmpuploads/* && \
    mkdir -p /srv/mltshp.com/uploaded && \
    mkdir -p /srv/mltshp.com/logs && \
    chown -R ubuntu:ubuntu /srv/mltshp.com

# NOTE: /srv/mltshp.com/logs and /srv/mltshp.com/uploaded need to be mounted volumes for this image
ADD requirements.txt /srv/mltshp.com/mltshp
WORKDIR /srv/mltshp.com/mltshp
RUN pip install -r requirements.txt
COPY setup/production/supervisord.conf /etc/supervisor/conf.d/mltshp.conf
COPY setup/production/nginx.conf /etc/nginx/nginx.conf

# code for app
ADD . /srv/mltshp.com/mltshp

EXPOSE 80
CMD ["/usr/bin/supervisord"]