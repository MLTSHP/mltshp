from tornado.testing import AsyncHTTPTestCase, ExpectLog
from tornado.options import options
import http.cookies
from lib.flyingcow import db as _db
from main import MltshpApplication
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

from models import User, Sourcefile


class BaseAsyncTestCase(AsyncHTTPTestCase, ExpectLog):
    sid = ''

    def get_app(self):
        app_settings = MltshpApplication.app_settings()
        application = MltshpApplication(routes, autoescape=None, autoreload=False, **app_settings)
        self.db = self.create_database()
        return application

    def setUp(self):
        super(BaseAsyncTestCase, self).setUp()
        self.start_time = time.time()

    def get_httpserver_options(self):
        return {'no_keep_alive':False}

    def tearDown(self):
        super(BaseAsyncTestCase, self).tearDown()
        self.db.close()

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

    def create_database(self):
        # start_time = int(time.time())
        db = _db.connection()

        db.execute("DROP database IF EXISTS %s" % (options.database_name))
        db.execute("CREATE database %s" % (options.database_name))
        db.execute("USE %s" % (options.database_name))
        f = open("setup/db-install.sql")
        load_query = f.read()
        f.close()
        f = None
        statements = load_query.split(";")
        for statement in statements:
            if statement.strip() != "":
                db.execute(statement.strip())
        # end_time = int(time.time())
        # print "Database reset took: %s" % (end_time - start_time)
        return db

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
        return self.fetch('/upload?skip_s3=1', method='POST', headers={'Cookie':"_xsrf=%s;sid=%s" % (xsrf, sid)},
                body="_xsrf=%s&file_name=%s&file_content_type=%s&file_sha1=%s&file_size=%s&file_path=%s&%s" % (xsrf, file_name, content_type, sha1, file_size, file_path, shake_string))

    def upload_test_file(self, shake_id=None):
        arguments = {}
        if shake_id:
            arguments['shake_id'] = int(shake_id)
        arguments['file_name'] = 'love.gif'
        arguments['file_content_type'] = 'image/gif'
        arguments['file_path'] = os.path.abspath("test/files/love.gif")
        arguments['file_sha1'] = Sourcefile.get_sha1_file_key(arguments['file_path'])
        arguments['file_size'] = os.path.getsize(arguments['file_path'])
        return self.post_url('/upload?skip_s3=1', arguments)

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
