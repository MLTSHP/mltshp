FROM ubuntu:16.04
LABEL maintainer "brad@bradchoate.com"
ENV PYTHONUNBUFFERED 1

# Installs the base system dependencies for running the site.
# None of this will change with the codebase itself, so this
# whole layer and steps to build it should be cached.
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
        python-pip && \
    rm -rf /var/lib/apt/lists/* && \
    \
    pip install -U pip setuptools distribute && \
    # fixes a weird issue where distribute complains about setuptools "0.7"
    # (incorrectly matching version "20.7.0" which ubuntu 16.04 has preinstalled)
    rm -rf /usr/lib/python2.7/dist-packages/setuptools-20.7.0.egg-info && \
    \
    # install nginx + upload module
    mkdir -p /tmp/install && \
    cd /tmp/install && \
    wget http://nginx.org/download/nginx-0.8.55.tar.gz && tar zxf nginx-0.8.55.tar.gz && \
    wget https://github.com/fdintino/nginx-upload-module/archive/2.2.0.tar.gz && tar zxf 2.2.0.tar.gz && \
    cd /tmp/install/nginx-0.8.55 && \
    ./configure \
        --with-http_ssl_module \
        --with-http_stub_status_module \
        --with-pcre \
        --sbin-path=/usr/sbin/nginx \
        --pid-path=/run/nginx.pid \
        --conf-path=/etc/nginx/nginx.conf \
        --error-log-path=/srv/mltshp.com/nginx-error.log \
        --http-log-path=/srv/mltshp.com/nginx-access.log \
        --add-module=/tmp/install/nginx-upload-module-2.2.0 && \
    make && make install && \
    mkdir -p /etc/nginx && \
    rm -rf /tmp/install && \
    groupadd ubuntu --gid=1010 && \
    useradd ubuntu --create-home --home-dir=/home/ubuntu \
        --uid=1010 --gid=1010 && \
    mkdir -p /mnt/tmpuploads/0 /mnt/tmpuploads/1 /mnt/tmpuploads/2  \
        /mnt/tmpuploads/3 /mnt/tmpuploads/4 /mnt/tmpuploads/5 \
        /mnt/tmpuploads/6 /mnt/tmpuploads/7 /mnt/tmpuploads/8 \
        /mnt/tmpuploads/9 && \
    chmod 777 /mnt/tmpuploads/* && \
    mkdir -p /srv/mltshp.com/uploaded /srv/mltshp.com/logs && \
    chown -R ubuntu:ubuntu /srv/mltshp.com

# Install python dependencies which will be cached on the
# contents of requirements.txt:
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Copy configuration settings into place
COPY setup/production/supervisord-web.conf /etc/supervisor/conf.d/mltshp.conf
COPY setup/production/nginx.conf /etc/nginx/nginx.conf

# Add "." for the app code itself (also allows for local dev)
ADD . /srv/mltshp.com/mltshp
WORKDIR /srv/mltshp.com/mltshp

# Compile sass files
RUN sass --update --stop-on-error --style compressed static/sass:static/css

EXPOSE 80
CMD ["/usr/bin/supervisord"]
