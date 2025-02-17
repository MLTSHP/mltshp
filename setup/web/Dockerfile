FROM python:3.12-alpine
LABEL maintainer="brad@bradchoate.com"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/srv/mltshp.com/mltshp:/srv/mltshp.com/mltshp/test:/usr/lib/python3.12/site-packages

# Installs the base system dependencies for running the site.
# None of this will change with the codebase itself, so this
# whole layer and steps to build it should be cached.

RUN apk add --no-cache \
    py3-mysqlclient \
    py3-beautifulsoup4 \
    py3-boto3 \
    py3-curl \
    py3-dateutil \
    py3-kombu \
    py3-mock \
    py3-mysqlclient \
    py3-pip \
    py3-pillow \
    py3-requests \
    py3-tornado \
    py3-yoyo-migrations \
    supervisor

# Install python dependencies which will be cached on the
# contents of requirements.txt:
RUN --mount=type=bind,source=web/requirements.txt,target=/tmp/requirements.txt \
    pip install --break-system-packages -r /tmp/requirements.txt

RUN mkdir -p /srv/mltshp.com/uploaded /srv/mltshp.com/logs /srv/mltshp.com/bin && \
    adduser -D mltshp && \
    chown -R mltshp /srv/mltshp.com

COPY web /srv/mltshp.com/mltshp/

WORKDIR /srv/mltshp.com/mltshp

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/mltshp/supervisor.conf", "--logfile", "/srv/mltshp.com/logs/supervisord.log", "--pidfile", "/srv/mltshp.com/logs/supervisord.pid"]
