import io
import boto3

from tornado.options import options

from hashlib import md5


def S3Client():
    kwargs = {}
    if options.aws_port and options.aws_host:
        kwargs['endpoint_url'] = "http://%s:%s" % (options.aws_host, options.aws_port)
        kwargs['use_ssl'] = False

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
            kwargs['ContentMD5'] = md5_hash.hexdigest()
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
