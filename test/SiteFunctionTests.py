from tornado.options import options
import os

from .base import BaseAsyncTestCase

from models import Sourcefile, User


class AccountInfoTests(BaseAsyncTestCase):
    def setUp(self):
        super(AccountInfoTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf().decode("ascii")

        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path) 
        self.test_file1_content_type = "image/png"

        self.test_file2_path = os.path.abspath("test/files/love.gif")
        self.test_file2_sha1 = Sourcefile.get_sha1_file_key(self.test_file2_path) 
        self.test_file2_content_type = "image/gif"

    def test_account_images_page_works(self):
        response = self.upload_test_file()
        response = self.fetch_url('/user/admin')
        self.assertIn("/p/1", response.body)
    
    def test_no_friends(self):
        response = self.fetch_url('/friends')
        self.assertEqual(response.code, 200)


class FileViewTests(BaseAsyncTestCase):
    def setUp(self):
        super(FileViewTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()

        self.user2 = User(name="user2", email="user2@mltshp.com", email_confirmed=1, is_paid=1)
        self.user2.set_password("asdfasdf")
        self.user2.save()
        self.sid2 = self.sign_in("user2", "asdfasdf")

        self.sid = self.sign_in("admin", "asdfasdf")
        self.xsrf = self.get_xsrf().decode("ascii")

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
        response = self.fetch('/r/1', method='GET',
            headers={"Cookie": "sid=%s" % self.sid, "Host": "s.my-mltshp.com"},
            follow_redirects=False)

        options.use_cdn = False
        self.assertEqual(response.headers['location'], 'https://some-cdn.com/r/1')

    def test_cdn_image_view_with_width(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1,
            self.test_file1_content_type, 1, self.sid, self.xsrf)

        # These parameters are Fastly-specific
        options.use_fastly = True
        options.use_cdn = True
        response = self.fetch('/r/1?width=550', method='GET',
            headers={"Cookie": "sid=%s" % self.sid, "Host": "s.my-mltshp.com"},
            follow_redirects=False)

        options.use_fastly = False
        options.use_cdn = False
        self.assertEqual(response.headers['location'], 'https://some-cdn.com/r/1?width=550&dpr=1')

    def test_cdn_image_view_with_width_and_dpr(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1,
            self.test_file1_content_type, 1, self.sid, self.xsrf)

        # These parameters are Fastly-specific
        options.use_fastly = True
        options.use_cdn = True
        response = self.fetch('/r/1?width=550&dpr=2', method='GET',
            headers={"Cookie": "sid=%s" % self.sid, "Host": "s.my-mltshp.com"},
            follow_redirects=False)

        options.use_fastly = False
        options.use_cdn = False
        self.assertEqual(response.headers['location'], 'https://some-cdn.com/r/1?width=550&dpr=2')

    def test_raw_image_view_counts(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1,
            self.test_file1_content_type, 1, self.sid, self.xsrf)
        response = self.fetch('/user/admin', method='GET',
            headers={"Cookie":"sid=%s" % self.sid})
        self.assertIn("/r/1", response.body)

        for i in range(0,10):
            if i % 2 == 0:
                # views by owner aren't counted
                response = self.fetch('/r/1', method='GET',
                    headers={"Host": "s." + options.app_host, "Cookie":"sid=%s" % self.sid2})
            else:
                # views by non-owner are counted
                response = self.fetch('/r/1', method='GET', headers={"Host": "s." + options.app_host})

        imageviews = self.db.query("SELECT id, user_id, sharedfile_id, created_at from fileview")
        self.assertEqual(len(imageviews), 10)

        imageviews = self.db.query("SELECT id, user_id, sharedfile_id, created_at from fileview WHERE user_id = 0")
        self.assertEqual(len(imageviews), 5)


class AuthenticationTests(BaseAsyncTestCase):
    def setUp(self):
        super(AuthenticationTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
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
