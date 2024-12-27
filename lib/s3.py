import io
import base64
from hashlib import md5

import boto3
from tornado.options import options


def S3Client():
    kwargs = {}
    # We shouldn't override any arguments if we're using the real AWS S3
    if options.aws_host and options.aws_host != "s3.amazonaws.com":
        kwargs['use_ssl'] = options.aws_port == 443
        if kwargs['use_ssl']:
            scheme = "https"
            port = ""
        else:
            kwargs['use_ssl'] = False
            scheme = "http"
            port = ":%s" % options.aws_port
        kwargs['endpoint_url'] = "%s://%s%s" % (scheme, options.aws_host, port)

    return boto3.client('s3',
        aws_access_key_id=options.aws_key,
        aws_secret_access_key=options.aws_secret,
        **kwargs)


class S3BucketWrapper(object):
    def __init__(self, bucket_name, create=False):
        self.bucket_name = bucket_name
        self.client = S3Client()
        if create:
            self.client.create_bucket(Bucket=options.aws_bucket)

    def generate_url(self, key, **kwargs):
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                'Bucket': self.bucket_name,
                'Key': key,
            },
            **kwargs)

    def upload_file(self, file_name, key, **kwargs):
        return self.client.upload_file(
            Filename=file_name,
            Key=key,
            Bucket=self.bucket_name,
            **kwargs
        )

    def put_object(self, data, key, **kwargs):
        if 'ContentMD5' not in kwargs:
            md5_hash = md5()
            md5_hash.update(data)
            kwargs['ContentMD5'] = base64.encodebytes(md5_hash.digest()).decode('ascii')
        if 'ContentLength' not in kwargs:
            if hasattr(data, 'read'):
                kwargs['ContentLength'] = data.seek(0, 2)
                data.seek(0)
            else:
                kwargs['ContentLength'] = len(data)
        return self.client.put_object(
            Body=data,
            Key=key,
            Bucket=self.bucket_name,
            **kwargs,
        )

    def get_object(self, key, **kwargs):
        data = io.BytesIO()
        self.client.download_fileobj(
            Key=key, Fileobj=data, Bucket=self.bucket_name, **kwargs
        )
        return data.getvalue()

    def download_file(self, file_name, key, **kwargs):
        with open(file_name, "wb") as f:
            self.client.download_fileobj(
                Key=key, Fileobj=f, Bucket=self.bucket_name, **kwargs
            )


def S3Bucket():
    return S3BucketWrapper(
        options.aws_bucket,
        # if we're testing, then just auto-create a bucket if it doesn't exist already
        create=options.aws_bucket.endswith("-dev") or options.aws_bucket.endswith("-testing"))
