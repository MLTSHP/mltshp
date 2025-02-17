import random
import os
import mock
from tornado.options import options

import test.base
import test.factories

from models import Sourcefile


class ReadonlyTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(ReadonlyTests, self).setUp()
        options.readonly = False
        self.admin = test.factories.user()
        self.sid = self.sign_in("admin", "password")
        self.xsrf = self.get_xsrf().decode("ascii")

        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path)
        self.test_file1_content_type = "image/png"

    def tearDown(self):
        pass

    def test_login_works(self):
        self.sign_out()

        options.readonly = True
        response = self.fetch_url("/sign-in?next=/")
        self.assertEqual(200, response.code)
        response = self.post_url('/sign-in', {"name": self.admin.name, "password": "password"})
        self.assertEqual(200, response.code)

    def test_user_model_wont_save(self):
        options.readonly = True
        user = test.factories.user()
        self.assertEqual(None, user.id)

    def test_uploads_return_403(self):
        options.readonly = True
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.get_xsrf().decode("ascii"))
        self.assertEqual(response.code, 403)

    def test_no_post_button(self):
        # when site is writable, "New Post" button is present:
        response = self.fetch_url('/')
        self.assertEqual(200, response.code)
        self.assertIn('New Post', response.body)

        # when site is readonly, "New Post" button is suppressed:
        options.readonly = True
        response = self.fetch_url('/')
        self.assertEqual(200, response.code)
        self.assertNotIn('New Post', response.body)
