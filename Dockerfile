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
    htop \
    libpcre3 \
    libpcre3-dev \
    libssl-dev \
    libffi-dev \
    ruby-sass \
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
    --with-http_stub_status_module \
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
RUN mkdir -p /mnt/tmpuploads/0 /mnt/tmpuploads/1 /mnt/tmpuploads/2  \
    /mnt/tmpuploads/3 /mnt/tmpuploads/4 /mnt/tmpuploads/5 \
    /mnt/tmpuploads/6 /mnt/tmpuploads/7 /mnt/tmpuploads/8 \
    /mnt/tmpuploads/9 && \
    chmod 777 /mnt/tmpuploads/* && \
    mkdir -p /srv/mltshp.com/uploaded && \
    mkdir -p /srv/mltshp.com/logs && \
    chown -R ubuntu:ubuntu /srv/mltshp.com

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY setup/production/supervisord-web.conf /etc/supervisor/conf.d/mltshp.conf
COPY setup/production/nginx.conf /etc/nginx/nginx.conf

# NOTE: /srv/mltshp.com/logs should be a mounted volume for this image
ADD . /srv/mltshp.com/mltshp
WORKDIR /srv/mltshp.com/mltshp

# Compile sass files
RUN sass --update --stop-on-error --style compressed static/sass:static/css

EXPOSE 80
CMD ["/usr/bin/supervisord"]
