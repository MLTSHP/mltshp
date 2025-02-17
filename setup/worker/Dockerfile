FROM python:3.12-alpine
LABEL maintainer="brad@bradchoate.com"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/usr/lib/python3.12/site-packages

# Installs the base system dependencies for running the site.
# None of this will change with the codebase itself, so this
# whole layer and steps to build it should be cached.

RUN apk add --no-cache \
    apk-cron \
    py3-mysqlclient \
    py3-beautifulsoup4 \
    py3-boto3 \
    py3-curl \
    py3-dateutil \
    py3-kombu \
    py3-mysqlclient \
    py3-pip \
    py3-pillow \
    py3-requests \
    py3-tornado \
    py3-yoyo-migrations \
    ffmpeg \
    supervisor

RUN mkdir -p /srv/mltshp.com/logs /srv/mltshp.com/bin && \
    adduser -D mltshp && \
    chown -R mltshp /srv/mltshp.com

# Install python dependencies which will be cached on the
# contents of requirements.txt:
RUN --mount=type=bind,source=worker/requirements.txt,target=/tmp/requirements.txt \
    pip install --break-system-packages -r /tmp/requirements.txt

# Copy configuration settings into place
COPY setup/worker/supervisor/prod.conf /etc/mltshp/supervisor.conf
COPY web/lib web/models web/tasks web/mltshpoptions.py web/torndb.py worker /srv/mltshp.com/mltshp/

WORKDIR /srv/mltshp.com/mltshp

RUN crontab -u mltshp setup/worker/crontab/prod.cron

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/mltshp/supervisor.conf", "--logfile", "/srv/mltshp.com/logs/supervisord.log", "--pidfile", "/srv/mltshp.com/logs/supervisord.pid"]
