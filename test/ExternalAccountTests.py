from functools import wraps

from tornado.testing import AsyncHTTPTestCase
from torndb import Connection
from tornado.httpclient import HTTPRequest
from tornado.options import options
import tornado.ioloop
import Cookie
import base64
import time
import os
import hashlib

from base import BaseAsyncTestCase
from models import User, Sharedfile, Sourcefile, Externalservice


def twittertest(fn):
    # This would be a "skip" if unittest v1 supported skipping.
    @wraps(fn)
    def test(self):
        if options.twitter_consumer_key:
            return fn(self)
    return test


class TwitterTests(BaseAsyncTestCase):
    def setUp(self):
        super(TwitterTests, self).setUp()
        self.user = User(name="admin", email="admin@mltshp.com", email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.sid = self.sign_in("admin", "asdfasdf")        
        
        self.externalservice = Externalservice(user_id=self.user.id, service_id=555, screen_name='mltshp', type=Externalservice.TWITTER, service_key="blah", service_secret="mah")
        self.externalservice.save()
        
    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    @twittertest
    def test_twitter_connect(self):
        request = HTTPRequest(self.get_url("/tools/twitter/connect"), 'GET', {'Cookie':"sid=%s" % (self.sid)}, follow_redirects=False)
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertTrue(response.headers['location'].startswith("https://api.twitter.com/oauth/authorize?oauth"))

    def test_post_from_twitter(self):
        #provider = "https://api.twitter.com/1.1/account/verify_credentials.json"
        provider = self.get_url('/heartbeat')
        
        """
        Copies a file to the file-system, then POSTs the location and details to the upload method
        for processing
        """
        file_path = os.path.abspath("test/files/1.png")
        sha1 = Sourcefile.get_sha1_file_key(file_path) 
        content_type = "image/png"
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        body = "media_name=%s&media_content_type=%s&media_sha1=%s&media_size=%s&media_path=%s&skip_s3=1" % (file_name, content_type, sha1, file_size, file_path)

        request = HTTPRequest(
            url=self.get_url('/upload'), 
            method='POST',
            headers={'X-Auth-Service-Provider':provider, 'X-Verify-Credentials-Authorization': 'OAuth oauth_timestamp="1290404453", oauth_version="1.0", oauth_consumer_key="IQKbtAYlXLripLGPWd0HUA", oauth_token="37458155-JCG7c8oejM6N4TK4HJbXVC5VGq1gtaSUPt90wxFI", oauth_signature="9QxkJqBAJfZ83sbz6SCJKSaPn9U%3D", oauth_nonce="C7AB0CBC-9193-44EE-AFC1-6FE3BA51F048", oauth_signature_method="HMAC-SHA1"'},
            body=body,
            )
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, "<mediaurl>https://s.mltshp.com/r/1.png</mediaurl>")
        sf = Sharedfile.get("id = %s", 1)
        self.assertEqual(sf.id, 1)
        self.assertEqual(sf.name, '1.png')
        self.assertEqual(sf.user_id, self.user.id)
        
    def test_posting_fails_when_provider_is_not_localhost(self):
        provider = "https://example.com"
        """
        Copies a file to the file-system, then POSTs the location and details to the upload method
        for processing
        """
        file_path = os.path.abspath("test/files/1.png")
        sha1 = Sourcefile.get_sha1_file_key(file_path) 
        content_type = "image/png"
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        body = "media_name=%s&media_content_type=%s&media_sha1=%s&media_size=%s&media_path=%s&skip_s3=1" % (file_name, content_type, sha1, file_size, file_path)

        request = HTTPRequest(
            url=self.get_url('/upload'), 
            method='POST',
            headers={'X-Auth-Service-Provider':provider, 'X-Verify-Credentials-Authorization': 'OAuth oauth_timestamp="1290404453", oauth_version="1.0", oauth_consumer_key="IQKbtAYlXLripLGPWd0HUA", oauth_token="37458155-JCG7c8oejM6N4TK4HJbXVC5VGq1gtaSUPt90wxFI", oauth_signature="9QxkJqBAJfZ83sbz6SCJKSaPn9U%3D", oauth_nonce="C7AB0CBC-9193-44EE-AFC1-6FE3BA51F048", oauth_signature_method="HMAC-SHA1"'},
            body=body,
            )
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 403)

    def test_post_from_twitter_with_message(self):
        provider = self.get_url('/heartbeat')

        """
        Copies a file to the file-system, then POSTs the location and details to the upload method
        for processing
        """
        file_path = os.path.abspath("test/files/1.png")
        sha1 = Sourcefile.get_sha1_file_key(file_path) 
        content_type = "image/png"

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        message = "hey look\r\n at me!\r\n"
        body = "message=%s&media_name=%s&media_content_type=%s&media_sha1=%s&media_size=%s&media_path=%s&skip_s3=1" % (message, file_name, content_type, sha1, file_size, file_path)

        request = HTTPRequest(
            url=self.get_url('/upload'),
            method='POST',
            headers={'X-Auth-Service-Provider':provider, 'X-Verify-Credentials-Authorization': 'OAuth oauth_timestamp="1290404453", oauth_version="1.0", oauth_consumer_key="IQKbtAYlXLripLGPWd0HUA", oauth_token="37458155-JCG7c8oejM6N4TK4HJbXVC5VGq1gtaSUPt90wxFI", oauth_signature="9QxkJqBAJfZ83sbz6SCJKSaPn9U%3D", oauth_nonce="C7AB0CBC-9193-44EE-AFC1-6FE3BA51F048", oauth_signature_method="HMAC-SHA1"'},
            body=body,
            )
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, "<mediaurl>https://s.mltshp.com/r/1.png</mediaurl>")
        sf = Sharedfile.get("id = %s", 1)
        self.assertEqual(sf.id, 1)
        self.assertEqual(sf.get_title(), message.replace('\n', '').replace('\r', ''))
        self.assertEqual(sf.user_id, self.user.id)
