from tornado.testing import AsyncHTTPTestCase
import handlers
import time
from models import Sharedfile, Sourcefile, User
from .base import BaseAsyncTestCase
from handlers import base


#This test uses the argument passing between self.stop and self.wait 
# for a simpler, more synchronous style 
class TwoHundredTests(BaseAsyncTestCase):

    def test_sign_in(self):
        response = self.fetch('/sign-in/')
        self.assertEqual(response.code, 200)

    def test_nonexistant(self):
        response = self.fetch('/asdf/asdf')
        self.assertEqual(response.code, 404)

    def test_no_access_to_create_users(self):
        response = self.fetch('/admin/create-users')
        self.assertEqual(response.code, 403)
        
    def test_non_signed_in_permalink_view(self):
        user = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        user.save()
        src = Sourcefile(width=100, height=100, file_key="asdf", thumb_key="asdfqwer")
        src.save()
        sf = Sharedfile(source_id=src.id, user_id=1, name="some.jpg", title="some", share_key="1", content_type="image/jpg")
        sf.save()
        
        response = self.fetch('/p/1')
        self.assertEqual(response.code, 200)
        
    def test_twitter_page(self):
        response = self.fetch('/tools/twitter')
        self.assertEqual(response.code, 200)
