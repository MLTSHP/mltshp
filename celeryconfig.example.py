## mltshp settings initialization

import mltshpoptions
import settings as app_settings
mltshpoptions.parse_dictionary(app_settings.settings)

## Celery configuration

# List of modules to import when celery starts.
imports = ("tasks.timeline", "tasks.counts", "tasks.migration", "tasks.transcode", "tasks.admin")

task_routes = {
    "tasks.transcode.*": { "queue": "transcode" },
}

## Result store settings.
result_backend = "rpc://"
result_persistent = False

## Broker settings.
broker_url = "amqp://user:password@broker_host:5672/vhost"
