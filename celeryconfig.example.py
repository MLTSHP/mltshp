# List of modules to import when celery starts.
imports = ("tasks.timeline", "tasks.counts", "tasks.migration", "tasks.transcode")

task_routes = {
    "tasks.transcode.*": "transcode",
}

## Result store settings.
result_backend = "rpc://"
result_persistent = False

## Broker settings.
broker_url = "amqp://user:password@broker_host:5672/vhost"
