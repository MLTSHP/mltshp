import random

import test.base
import test.factories
from models import User, Sourcefile, Sharedfile, Shakesharedfile, Bookmark

class ErrorTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(ErrorTests, self).setUp()
        self.admin = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()
        self.sign_in('admin', 'asdfasdf')
    
    def test_custom_404(self):
        """
        Request an invalid route.
        - Should error! 
        """
        response = self.fetch_url('/lakjsdlfka')
        self.assertEqual(404, response.code)
        self.assertIn("404 - Uh oh!", response.body)
