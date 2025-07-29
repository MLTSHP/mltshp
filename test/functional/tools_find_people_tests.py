from functools import wraps

from tornado.options import options

import test.base
import models


class ToolsFindPeopleTests(test.base.BaseAsyncTestCase):

    def setUp(self):
        super(ToolsFindPeopleTests, self).setUp()
        self.user = models.User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('pass')
        self.user.save()
        
    def test_tools_find_shakes(self):
        """
        /tools/find-people should be accessible.
        """
        response = self.fetch('/tools/find-shakes')
        self.assertEqual(200, response.code)
        response = self.fetch('/tools/find-shakes/people')
        self.assertEqual(200, response.code)
