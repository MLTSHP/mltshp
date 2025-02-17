from tornado.testing import AsyncHTTPTestCase, ExpectLog
from tornado.options import options
import http.cookies
from main import MltshpApplication
from lib.flyingcow import register_connection
from tornado.escape import json_encode
from routes import routes
import urllib.request, urllib.parse, urllib.error
import os
import time
import base64
import hmac
import hashlib
import binascii
import uuid
import re
import logging

from models import User, Sourcefile


logger = logging.getLogger('mltshp.test')
logger.setLevel(logging.INFO)

class BaseAsyncTestCase(AsyncHTTPTestCase, ExpectLog):
    sid = ''

    def __init__(self, *args, **kwargs):
        self.db = register_connection(
            host=options.database_host,
            name="mysql",
            user=options.database_user,
            password=options.database_password,
            charset="utf8mb4")
        super(BaseAsyncTestCase, self).__init__(*args, **kwargs)

    def get_app(self):
        app_settings = MltshpApplication.app_settings()
        return MltshpApplication(routes, autoescape=None, autoreload=False,
                                 db=self.db, **app_settings)

    def setUp(self):
        super(BaseAsyncTestCase, self).setUp()
        self.start_time = time.time()
        if options.database_name != "mltshp_testing":
            raise Exception("Invalid database name for unit tests")
        self.reset_database()

    def get_httpserver_options(self):
        return {'no_keep_alive':False}

    def sign_in(self, name, password):
        """
        Authenticates the user and sets an instance variable to the user's
        cookie sid.  Can be used later to make post requests via post_url.
        """
        user = User.authenticate(name, password)
        if user:
            sid = {'id':user.id, 'name':user.name}
            self.sid = self.create_signed_value("sid", json_encode(sid))
            return self.sid
        else:
            return ''

    def sign_out(self):
        self.sid = None

    def get_sid(self, response):
        cookie = http.cookies.BaseCookie(response.headers['Set-Cookie'])
        return cookie['sid'].value

    def get_xsrf(self):
        return binascii.b2a_hex(uuid.uuid4().bytes)

    def reset_database(self):
        self.db.execute("USE %s" % (options.database_name))
        with open("setup/database/db-truncate.sql") as f:
            query = f.read()
        self.db.execute(query)

    def upload_file(self, file_path, sha1, content_type, user_id, sid, xsrf, shake_id=None):
        """
        Copies a file to the file-system, then POSTs the location and details to the upload method
        for processing
        """
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        shake_string = ''
        if shake_id:
            shake_string="shake_id=%s" % (shake_id)
        return self.fetch('/upload', method='POST', headers={'Cookie':"_xsrf=%s;sid=%s" % (xsrf, sid)},
                body="_xsrf=%s&file_name=%s&file_content_type=%s&file_sha1=%s&file_size=%s&file_path=%s&skip_s3=1&%s" % (xsrf, file_name, content_type, sha1, file_size, file_path, shake_string))

    def upload_test_file(self, shake_id=None):
        arguments = {}
        if shake_id:
            arguments['shake_id'] = int(shake_id)
        arguments['file_name'] = 'love.gif'
        arguments['file_content_type'] = 'image/gif'
        arguments['file_path'] = os.path.abspath("test/files/love.gif")
        arguments['file_sha1'] = Sourcefile.get_sha1_file_key(arguments['file_path'])
        arguments['file_size'] = os.path.getsize(arguments['file_path'])
        arguments['skip_s3'] = "1"
        return self.post_url('/upload', arguments)

    def create_signed_value(self, name, value):
        ### HERE!@!
        timestamp = str(int(time.time()))
        value = base64.b64encode(value.encode(encoding="utf-8")).decode("ascii")
        signature = self.cookie_signature(name, value, timestamp)
        value = "|".join([value, timestamp, signature])
        return value

    def cookie_signature(self, *parts):
        hash = hmac.new(options.cookie_secret.encode(encoding="utf-8"), digestmod=hashlib.sha1)
        for part in parts:
            hash.update(type(part) == str and part.encode(encoding="utf-8") or part)
        return hash.hexdigest()

    def post_url(self, path, arguments={}, **kwargs):
        """
        Posts the URL, if self.sign_in() is called and user is logged in,
        the user's authenticated cookie will be passed along.
        """
        xsrf = self.get_xsrf().decode("ascii")
        headers = {'Cookie':'sid=%s;_xsrf=%s' % (self.sid, xsrf)}
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            kwargs['headers'] = headers
        else:
            kwargs['headers'] = headers
        arguments['_xsrf'] = xsrf
        body = urllib.parse.urlencode(arguments)
        return self.fetch(path, method="POST", body=body, **kwargs)

    def fetch_url(self, path, **kwargs):
        """
        Gets the URL, if self.sign_in() is called and user is logged in,
        the user's authenticated cookie will be passed along.
        """
        headers = {'Cookie': 'sid=%s' % self.sid}
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            kwargs['headers'] = headers
        else:
            kwargs['headers'] = headers
        return self.fetch(path, method='GET', **kwargs)

    def assertNotIn(self, needle, haystack):
        if isinstance(needle, str):
            return super(BaseAsyncTestCase, self).assertNotIn(needle.encode("utf-8"), haystack)
        else:
            return super(BaseAsyncTestCase, self).assertNotIn(needle, haystack)

    def assertIn(self, needle, haystack):
        if isinstance(needle, str):
            return super(BaseAsyncTestCase, self).assertIn(needle.encode("utf-8"), haystack)
        else:
            return super(BaseAsyncTestCase, self).assertIn(needle, haystack)

    def assert_redirect(self, response, url):
        self.assertEqual(302, response.code)
        self.assertEqual(url, response.headers['Location'])

    def fake_upload_file(self):
        """
        TODO
        """
        pass
