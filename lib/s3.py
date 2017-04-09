from boto.s3.connection import S3Connection as Connection

from tornado.options import options


def S3Connection():
    kwargs = {}
    if options.aws_port and options.aws_host:
        kwargs['host'] = options.aws_host
        kwargs['port'] = options.aws_port
        # if we're using a custom AWS host/port, disable
        # SSL, since fakes3 doesn't support it
        kwargs['is_secure'] = False

    return Connection(
        options.aws_key,
        options.aws_secret,
        **kwargs)


def S3Bucket():
    # if we're testing, then just auto-create a bucket if it doesn't exist already
    if options.aws_bucket.endswith("-dev") or options.aws_bucket.endswith("-testing"):
        return S3Connection().create_bucket(options.aws_bucket)
    else:
        return S3Connection().get_bucket(options.aws_bucket)