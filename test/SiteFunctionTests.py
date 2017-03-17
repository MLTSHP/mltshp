from tornado.testing import AsyncHTTPTestCase
from torndb import Connection
from tornado.options import options
from tornado.httpclient import HTTPRequest
import handlers
import base64
import time
import os

from base import BaseAsyncTestCase

from models import Sourcefile, User


class AccountInfoTests(BaseAsyncTestCase):
    def setUp(self):
        super(AccountInfoTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf()
        
        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path) 
        self.test_file1_content_type = "image/png"
        
        self.test_file2_path = os.path.abspath("test/files/love.gif")
        self.test_file2_sha1 = Sourcefile.get_sha1_file_key(self.test_file2_path) 
        self.test_file2_content_type = "image/gif"

    def test_account_images_page_works(self):
        response = self.upload_test_file()
        response = self.fetch_url('/user/admin')
        self.assertTrue(response.body.find("/p/1") > 0)
    
    def test_no_friends(self):
        response = self.fetch_url('/friends')
        self.assertEqual(response.code, 200)


class FileViewTests(BaseAsyncTestCase):
    def setUp(self):
        super(FileViewTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf()
        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path) 
        self.test_file1_content_type = "image/png"
        
        self.test_file2_path = os.path.abspath("test/files/love.gif")
        self.test_file2_sha1 = Sourcefile.get_sha1_file_key(self.test_file2_path) 
        self.test_file2_content_type = "image/gif"

    def test_cdn_image_view(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1,
            self.test_file1_content_type, 1, self.sid, self.xsrf)

        options.use_cdn = True
        request = HTTPRequest(self.get_url('/r/1'), 'GET',
            {"Cookie": "sid=%s" % (self.sid), "Host": "s.mltshp.com"},
            follow_redirects=False)
        self.http_client.fetch(request, self.stop)

        response = self.wait()
        options.use_cdn = False
        self.assertEquals(response.headers['location'], 'http://s.mltshp-cdn.com/r/1')

    def test_raw_image_view_counts(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1,
            self.test_file1_content_type, 1, self.sid, self.xsrf)
        self.http_client.fetch(self.get_url("/user/admin"), self.stop)
        response = self.wait()
        self.assertTrue(response.body.find("1.png") > 0)
        
        for i in range(0,10):
            if i % 2 == 0:
                request = HTTPRequest(self.get_url('/r/1'), 'GET',
                    {"Cookie":"sid=%s" % (self.sid)})
            else:
                request = HTTPRequest(self.get_url('/r/1'), 'GET')
            self.http_client.fetch(request, self.stop)
            response = self.wait()

        imageviews = self.db.query("SELECT id, user_id, sharedfile_id, created_at from fileview")
        self.assertEqual(len(imageviews), 10)
        
        imageviews = self.db.query("SELECT id, user_id, sharedfile_id, created_at from fileview WHERE user_id = 0")
        self.assertEqual(len(imageviews), 5)


class AuthenticationTests(BaseAsyncTestCase):
    def setUp(self):
        super(AuthenticationTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.user.set_password('asdfasdf')
        self.user.save()
                
    def test_sign_in(self):
        sid = self.sign_in('admin', 'asdfasdf')
        self.assertTrue(sid != '')
        
    # TURNED OFF, NOT ENFORCED
    #def test_sign_in_with_unverifed_account(self):
    #    user = User.get("id=%s", 1)
    #    user.email_confirmed = 0
    #    user.save()
    #    sid = self.sign_in('admin', 'asdfasdf')
    #    self.assertEqual(sid, None)
