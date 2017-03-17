from functools import wraps

from tornado.options import options

import test.base
import models


def twittertest(fn):
    # This would be a "skip" if unittest v1 supported skipping.
    @wraps(fn)
    def test(self):
        if options.twitter_consumer_key:
            return fn(self)
    return test


class ToolsFindPeopleTests(test.base.BaseAsyncTestCase):

    def setUp(self):
        super(ToolsFindPeopleTests, self).setUp()
        self.user = models.User(name='admin', email='admin@mltshp.com', email_confirmed=1)
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
        response = self.fetch('/tools/find-shakes/twitter')
        self.assertEqual(200, response.code)
        
    @twittertest
    def test_tools_find_people_from_twitter_errors(self):
        """
        /tools/find-people-from-twitter should return an
        error message if no external service connected.
        """
        self.sign_in('admin', 'pass')        
        response = self.fetch_url('/tools/find-shakes/quick-fetch-twitter')
        self.assertTrue(response.body.find('to find your Twitter friends') > 0)

    @twittertest
    def test_tools_find_people_from_twitter_returns_friends_when_populated(self):
        """
        /tools/find-shakes/quick-fetch-twitter should return an
        a list of users if we already have a friend graph for a user populated.
        """
        self.sign_in('admin', 'pass')
        self.user_service = models.Externalservice(user_id=self.user.id, service_id=1000, screen_name='torrez', 
            type=models.Externalservice.TWITTER, service_key='asdf', service_secret='qwer')
        self.user_service.save()
        
        user2 = models.User(name='user2', email='user2@mltshp.com', email_confirmed=1)
        user2.save()
        user2_service = models.Externalservice(user_id=user2.id, service_id=2000, screen_name='user2', 
            type=models.Externalservice.TWITTER, service_key='asdf', service_secret='qwer')
        user2_service.save()
        models.ExternalRelationship.add_relationship(self.user, 2000, models.Externalservice.TWITTER)
        
        response = self.fetch_url('/tools/find-shakes/quick-fetch-twitter')
        self.assertTrue(response.body.find('user2') > 1)
        self.assertEqual(200, response.code)
        
