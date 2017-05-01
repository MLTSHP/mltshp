# List of modules to import when celery starts.
CELERY_IMPORTS = ("tasks.timeline", "tasks.counts", "tasks.migration")

## Result store settings.
CELERY_RESULT_BACKEND = "rpc://"

## Broker settings.
BROKER_HOST = "rabbitmq"
BROKER_PORT = 5672
BROKER_USER = "mltshp_user"
BROKER_PASSWORD = "password"
BROKER_VHOST = "kablam.local"

## Worker settings
## If you're doing mostly I/O you can have more processes,
## but if mostly spending CPU, try to keep it close to the
## number of CPUs on your machine. If not set, the number of CPUs/cores
## available will be used.
CELERYD_CONCURRENCY = 1
# CELERYD_LOG_LEVEL = "INFO"
