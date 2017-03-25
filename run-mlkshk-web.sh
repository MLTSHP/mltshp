#!/bin/sh

LOCAL_PORT=8000

docker run -t -i \
    -p $LOCAL_PORT:80
    -v logs:/srv/mltshp.com/logs \
    -v uploaded:/srv/mltshp.com/uploaded \
    -v settings.py:/srv/mltshp.com/mltshp/settings.py
    -v /etc/mltshp/celeryconfig.py:/srv/mltshp.com/mltshp/celeryconfig.py
    --name mltshp-web
    mltshp/mltshp-web
