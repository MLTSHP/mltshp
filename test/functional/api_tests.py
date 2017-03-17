from contextlib import contextmanager
import time
from datetime import datetime, timedelta
import random
import string
from urlparse import urlparse
from hashlib import md5, sha1
import urllib
import hmac
import base64
import os

from tornado.testing import AsyncHTTPTestCase
from torndb import Connection
from tornado.httpclient import HTTPRequest
from tornado.escape import url_escape, json_decode
from tornado.httputil import HTTPHeaders
from tornado.options import options
import handlers

import test.base
from models import Accesstoken, Apihit, App, Authorizationcode, Favorite, \
    ShakeManager, Sharedfile, Sourcefile, User, Comment
from lib.utilities import normalize_string, base36encode
from tasks.counts import calculate_likes


@contextmanager
def test_option(name, value):
    old_value = getattr(options, name)
    setattr(options, name, value)
    yield
    setattr(options, name, old_value)


class APIAuthorizationTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        """
        . Need to create a user and a test app
        . Create second account that is going to auth
        """
        super(APIAuthorizationTests, self).setUp()
        self.user_a = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.user_a.set_password('asdfasdf')
        self.user_a.save()
        self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf()


        self.user_b = User(name='user2', email='user2@mltshp.com', email_confirmed=1)
        self.user_b.set_password('asdfasdf')
        self.user_b.save()

        self.app = App(user_id=self.user_a.id, title='An App', description='Nothing yet.', redirect_url='http://client.example.com/return')
        self.app.save()

        self.app_query = App(user_id=self.user_a.id, title='An App', description='Nothing yet.', redirect_url='http://client.example.com/return?query=param')
        self.app_query.save()

        self.app_no_redirect = App(user_id=self.user_a.id, title='An App', description='Nothing yet.', redirect_url='')
        self.app_no_redirect.save()

    def test_authorize_code_request_redirects_to_sign_in(self):

        authorization_url = '/api/authorize?response_type=code&client_id=%s' % (self.app.key())

        response = api_request(self, self.get_url(authorization_url), unsigned=True)
        self.assertEqual(response.effective_url, self.get_url('/sign-in?next=%s' % url_escape(authorization_url)))
        self.assertEqual(response.code, 200)

    def test_authorization_code_request_accepts_authenticated_user(self):
        authorization_url = '/api/authorize?response_type=code&client_id=%s' % (self.app.key())

        response = api_request(self, self.get_url(authorization_url), headers={'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, unsigned=True)
        self.assertEqual(response.effective_url, self.get_url(authorization_url))

    def test_authorization_code_request_accepts_authtime_redirect(self):
        authorization_url = '/api/authorize?response_type=code&client_id=%s&redirect_uri=http://client.example.com/return' % (self.app_no_redirect.key())

        response = api_request(self, self.get_url(authorization_url), headers={'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, unsigned=True)
        self.assertEqual(response.effective_url, self.get_url(authorization_url))
        self.assertEqual(response.code, 200)
        self.assertTrue('http://client.example.com/return' in response.body)

    def test_authorization_code_request_accepts_matching_redirect(self):
        authorization_url = '/api/authorize?response_type=code&client_id=%s&redirect_uri=http://client.example.com/return' % (self.app.key())

        response = api_request(self, self.get_url(authorization_url), headers={'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, unsigned=True)
        self.assertEqual(response.effective_url, self.get_url(authorization_url))
        self.assertEqual(response.code, 200)
        self.assertTrue('http://client.example.com/return' in response.body)

    def test_authorization_code_request_error_on_mismatched_redirect(self):
        authorization_url = '/api/authorize?response_type=code&client_id=%s&redirect_uri=http://othersite.example.com/path' % (self.app.key())
        response = self.fetch_url(authorization_url, follow_redirects=False)
        self.assertEqual(response.code, 400)

    def test_authorize_code_submitting_agree_redirects_to_apps_redirect_url(self):
        authorization_url = '/api/authorize?response_type=code&client_id=%s' % (self.app.key())
        arguments = { 'agree' : 1 }
        response = self.post_url(authorization_url, arguments, follow_redirects=False)
        auth_code = Authorizationcode.get('id = 1')
        self.assert_redirect(
            response,
            'http://client.example.com/return?code=%s' % auth_code.code
        )

    def test_authorize_code_submitting_agree_redirects_to_apps_redirect_url_with_query(self):
        authorization_url = '/api/authorize?response_type=code&client_id=%s' % (self.app_query.key())
        arguments = { 'agree' : 1 }
        response = self.post_url(authorization_url, arguments, follow_redirects=False)
        auth_code = Authorizationcode.get('id = 1')
        self.assert_redirect(
            response,
            'http://client.example.com/return?query=param&code=%s' % auth_code.code
        )

    def test_authorize_code_submitting_agree_redirects_to_authtime_redirect_url(self):
        authorization_url = '/api/authorize?response_type=code&client_id=%s&redirect_uri=http://client.example.com/return' % (self.app_no_redirect.key())
        arguments = { 'agree' : 1 }
        response = self.post_url(authorization_url, arguments, follow_redirects=False)
        auth_code = Authorizationcode.get('id = 1')
        self.assert_redirect(
            response,
            'http://client.example.com/return?code=%s' % auth_code.code
        )

    def test_authorize_code_submitting_disagree_redirects_to_apps_redirect_url(self):
        """
        access_denied
            The resource owner or authorization server denied the
            request.
        """
        authorization_url = '/api/authorize?response_type=code&client_id=%s' % (self.app.key())
        response = self.post_url(authorization_url, follow_redirects=False)
        auth_codes = Authorizationcode.all()
        self.assertEqual(len(auth_codes), 0)
        self.assert_redirect(
            response,
            'http://client.example.com/return?error=access_denied'
        )

    def test_authorize_code_submitting_disagree_redirects_to_apps_redirect_url_with_query(self):
        """
        access_denied
            The resource owner or authorization server denied the
            request.
        """
        authorization_url = '/api/authorize?response_type=code&client_id=%s' % (self.app_query.key())
        response = self.post_url(authorization_url, follow_redirects=False)
        auth_codes = Authorizationcode.all()
        self.assertEqual(len(auth_codes), 0)
        self.assert_redirect(
            response,
            'http://client.example.com/return?query=param&error=access_denied'
        )

    def test_authorize_code_submitting_disagree_redirects_to_authtime_redirect_url(self):
        authorization_url = '/api/authorize?response_type=code&client_id=%s&redirect_uri=http://client.example.com/return' % (self.app_no_redirect.key())
        response = self.post_url(authorization_url, follow_redirects=False)
        auth_codes = Authorizationcode.all()
        self.assert_redirect(
          response,
          'http://client.example.com/return?error=access_denied'
        )
        self.assertEqual(len(auth_codes), 0)

    def test_authorize_code_returns_errors(self):
        """
        invalid_request - The request is missing a required parameter, includes an
               unsupported parameter or parameter value, or is otherwise
               malformed.
        """
        authorization_url = '/api/authorize?response_type=&client_id=%s' % (self.app.key())
        response = self.fetch_url(authorization_url, follow_redirects=False)
        self.assert_redirect(
            response,
            'http://client.example.com/return?error=invalid_request'
        )

        """
        invalid_client - The client identifier provided is invalid.
        """
        authorization_url = '/api/authorize?response_type=code&client_id=0&redirect_uri=%s' % url_escape('http://client.example.com/return')
        response = self.fetch_url(authorization_url, follow_redirects=False)
        self.assert_redirect(
            response,
            'http://client.example.com/return?error=invalid_client'
        )

        ##THIS TEST is if the client is invalid and no redirect_uri is given
        authorization_url = '/api/authorize?response_type=code&client_id=0'
        response = self.fetch_url(authorization_url, follow_redirects=False)
        self.assertEqual(response.code, 404)

        """
        unsupported_response_type
               The authorization server does not support obtaining an
               authorization code using this method.
        """
        authorization_url = '/api/authorize?response_type=asdf&client_id=%s' % (self.app.key())
        response = self.fetch_url(authorization_url, follow_redirects=False)
        self.assert_redirect(
            response,
            'http://client.example.com/return?error=unsupported_response_type'
        )

        """
        unauthorized_client
               The client is not authorized to request an authorization
               code using this method.
        invalid_scope
               The requested scope is invalid, unknown, or malformed.
        """

class APITokenTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(APITokenTests, self).setUp()
        self.user_a = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.user_a.set_password('asdfasdf')
        self.user_a.save()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf()


        self.user_b = User(name='user2', email='user2@mltshp.com', email_confirmed=1)
        self.user_b.set_password('asdfasdf')
        self.user_b.save()

        self.app = App(user_id=self.user_a.id, title='An App', description='Nothing yet.', redirect_url='http://client.example.com/return')
        self.app.save()

        self.authorization = Authorizationcode.generate(self.app.id, self.app.redirect_url, self.user_b.id)

    def test_access_token_returned_for_valid_authorization_code_and_credentials(self):
        message="grant_type=authorization_code&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (self.authorization.code, self.app.redirect_url, self.app.key(), self.app.secret)

        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)

        #one access token should have been created:
        access_token = Accesstoken.get('id=1')

        j_response = json_decode(response.body)
        self.assertEqual(j_response['token_type'], 'mac')
        self.assertEqual(j_response['access_token'], access_token.consumer_key)
        self.assertEqual(j_response['secret'], access_token.consumer_secret)
        self.assertEqual(j_response['algorithm'], 'hmac-sha-1')

    def test_access_token_is_not_deleted_when_new_one_is_requested(self):
        # First request one.
        message = "grant_type=authorization_code&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (self.authorization.code, self.app.redirect_url, self.app.key(), self.app.secret)

        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)

        #one access token should have been created:
        access_token = Accesstoken.get('id=1')
        self.assertTrue(access_token)
        self.assertFalse(access_token.deleted)
        access_tokens = Accesstoken.all()
        self.assertEqual(len(access_tokens), 1)

        j_response = json_decode(response.body)
        self.assertEqual(j_response['token_type'], 'mac')
        self.assertEqual(j_response['access_token'], access_token.consumer_key)
        self.assertEqual(j_response['secret'], access_token.consumer_secret)
        self.assertEqual(j_response['algorithm'], 'hmac-sha-1')

        # Now request another.
        other_authorization = Authorizationcode.generate(self.app.id, self.app.redirect_url, self.user_b.id)
        message = "grant_type=authorization_code&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (other_authorization.code, self.app.redirect_url, self.app.key(), self.app.secret)

        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)

        # A second access token should have been created, but the
        # first one should be gone.
        access_token = Accesstoken.get('id=1')
        self.assertFalse(access_token.deleted)
        access_token = Accesstoken.get('id=2')
        self.assertFalse(access_token.deleted)
        access_tokens = Accesstoken.all()
        self.assertEqual(len(access_tokens), 2)

        j_response = json_decode(response.body)
        self.assertEqual(j_response['token_type'], 'mac')
        self.assertEqual(j_response['access_token'], access_token.consumer_key)
        self.assertEqual(j_response['secret'], access_token.consumer_secret)
        self.assertEqual(j_response['algorithm'], 'hmac-sha-1')

    def test_access_token_is_denied_with_missing_grant_type(self):
        message="grant_type=&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (self.authorization.code, self.app.redirect_url, self.app.key(), self.app.secret)

        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)
        j_response = json_decode(response.body)
        self.assertEqual(response.code, 400)
        self.assertEqual(j_response['error'], 'invalid_request')

    def test_access_token_is_denied_with_bad_grant_type(self):
        message="grant_type=asdfasdf&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (self.authorization.code, self.app.redirect_url, self.app.key(), self.app.secret)

        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)
        j_response = json_decode(response.body)
        self.assertEqual(response.code, 401)
        self.assertEqual(j_response['error'], 'invalid_grant')

    def test_access_token_is_denied_with_bad_client_id(self):
        message="grant_type=authorization_code&code=%s&redirect_uri=%s&client_id=fart&client_secret=%s" % (self.authorization.code, self.app.redirect_url, self.app.secret)

        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)
        j_response = json_decode(response.body)
        self.assertEqual(response.code, 401)
        self.assertEqual(j_response['error'], 'invalid_client')

    def test_access_token_denied_for_bad_secret(self):
        message="grant_type=authorization_code&code=%s&redirect_uri=%s&client_id=%s&client_secret=porkchops" % (self.authorization.code, self.app.redirect_url, self.app.key())

        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)
        j_response = json_decode(response.body)
        self.assertEqual(response.code, 401)
        self.assertEqual(j_response['error'], 'access_denied')

    def test_access_token_denied_too_old(self):
        self.authorization.expires_at = datetime.utcnow() - timedelta(seconds=50)
        self.authorization.save()
        message="grant_type=authorization_code&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (self.authorization.code, self.app.redirect_url, self.app.key(), self.app.secret)

        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)
        j_response = json_decode(response.body)
        self.assertEqual(response.code, 401)
        self.assertEqual(j_response['error'], 'invalid_grant')


class APIResourceOwnerPasswordCredentials(test.base.BaseAsyncTestCase):
    """
    Passing in a username and password along with API credentials returns a valid access
        token.
    """
    def setUp(self):
        super(APIResourceOwnerPasswordCredentials, self).setUp()
        self.user_a = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.user_a.set_password('asdfasdf')
        self.user_a.save()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf()


        self.user_b = User(name='user2', email='user2@mltshp.com', email_confirmed=1)
        self.user_b.set_password('asdfasdf')
        self.user_b.save()

        self.app = App(user_id=self.user_a.id, title='An App', description='Nothing yet.', redirect_url='http://client.example.com/return')
        self.app.save()

    def test_sending_valid_request_returns_access_token(self):
        message = "grant_type=password&client_id=%s&client_secret=%s&username=%s&password=%s" % (self.app.key(), self.app.secret, 'admin', 'asdfasdf')
        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)
        access_token = Accesstoken.all()
        self.assertEqual(len(access_token), 1)
        self.assertTrue(access_token[0])

        # Now clean up so the invalid test will work out of order.
        for token in access_token:
            token.delete()

    def test_sending_invalid_password_returns_error(self):
        message = "grant_type=password&client_id=%s&client_secret=%s&username=%s&password=%s" % (self.app.key(), self.app.secret, 'admin', 'qwerqwer')
        response = api_request(self, self.get_url('/api/token'), method='POST', body=message, unsigned=True)
        access_token = Accesstoken.all()
        self.assertEqual(len(access_token), 0)

    #def test_sending_invalid_client_returns_error(self):
    #    """invalid_client"""
    #    pass


class APIResourceRequests(test.base.BaseAsyncTestCase):

    def _post_to_shake(self, user, to_shake=None):
        """
        Utility method for creating a post to a shake.  If shake is
        not specified, the newly created sharedfile will be added to
        the user's shake.
        """
        source_file = Sourcefile(width=10, height=10, file_key='mumbles', thumb_key='bumbles')
        source_file.save()
        sf = Sharedfile(source_id=source_file.id, user_id=user.id, name="sharedfile.png",
                        title='shared file', content_type='image/png', deleted=0)
        sf.save()
        sf.share_key = base36encode(sf.id)
        sf.save()
        if to_shake:
            sf.add_to_shake(to_shake)
        else:
            sf.add_to_shake(user.shake())
        return sf

    def setUp(self):
        """
        user_a -> admin
        user_b -> user2

        user_a uploads shared file.

        We authenticate to the API with user_b.

        user_b subscribes to user_a's shake.]
        """
        super(APIResourceRequests, self).setUp()
        self.user_a = User(
                name='admin',
                email='admin@mltshp.com',
                email_confirmed=1,
                about="admin",
                website='http://mltshp.com')
        self.user_a.set_password('asdfasdf')
        self.user_a.save()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf()

        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path)
        self.test_file1_content_type = "image/png"
        response = self.upload_file(file_path=self.test_file1_path, sha1=self.test_file1_sha1,
            content_type=self.test_file1_content_type, user_id=self.user_a.id, sid=self.sid, xsrf=self.xsrf)

        self.user_b = User(name='user2', email='user2@mltshp.com', email_confirmed=1)
        self.user_b.set_password('asdfasdf')
        self.user_b.save()

        self.group_shake = self.user_b.create_group_shake(title='Group Shake', name='groupshake', description='This is a group shake.')
        self.group_shake_2 = self.user_a.create_group_shake(title='Another Group', name='anothergroup')
        # Add user_b to user_a's group shake, so we get it in user_b's /shakes endpoint.
        shake_manager = ShakeManager(user_id=self.user_b.id, shake_id=self.group_shake_2.id)
        shake_manager.save()

        self.app = App(user_id=self.user_a.id, title='An App', description='Nothing yet.', redirect_url='http://client.example.com/return')
        self.app.save()

        self.authorization = Authorizationcode.generate(self.app.id, self.app.redirect_url, self.user_b.id)
        self.access_token = Accesstoken.generate(self.authorization.id)

        extra_authorization = Authorizationcode.generate(self.app.id, self.app.redirect_url, self.user_b.id)
        self.ratelimited_access_token = Accesstoken.generate(extra_authorization.id)
        now_hour = datetime.utcnow().strftime('%Y-%m-%d %H:00:00')
        ratelimit = Apihit(accesstoken_id=self.ratelimited_access_token.id, hits=options.api_hits_per_hour - 2, hour_start=now_hour)
        ratelimit.save()

        #subscription
        self.user_b.subscribe(self.user_a.shake())

    def test_bad_signature_denied(self):
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/1'))
        request.headers['Authorization'] =  request.headers['Authorization'].replace('signature="', 'signature="asdf')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertTrue(response.code, 401)

    def test_unsigned_resource_query_denied(self):
        response = api_request(self, self.get_url('/api/sharedfile/1'), unsigned=True)
        self.assertEqual(response.code, 401)

    def test_duplicate_nonce(self):
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/1'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        self.assertEqual(response.code, 200)
        self.assertTrue('Www-Authenticate' not in response.headers)

        self.http_client.fetch(request, self.stop)
        response = self.wait()

        self.assertEqual(response.code, 401)
        self.assertTrue(response.headers['Www-Authenticate'].find("Duplicate nonce.") > 0)

    def test_rate_limit(self):
        request = signed_request(self.ratelimited_access_token, self.get_url('/api/sharedfile/1'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        self.assertEqual(response.code, 200)
        self.assertEqual(response.headers['X-RateLimit-Remaining'], '1')

        request = signed_request(self.ratelimited_access_token, self.get_url('/api/sharedfile/1'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        self.assertEqual(response.code, 400)
        self.assertEqual(response.headers['X-RateLimit-Remaining'], '0')

    def test_query_favorites(self):
        # Set up a favorite.
        f = Favorite()
        f.user_id = self.user_b.id
        f.sharedfile_id = 1
        f.save()

        request = signed_request(self.access_token, self.get_url('/api/favorites'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)

        self.assertTrue('favorites' in j_response)
        favs = j_response['favorites']
        fav_ids = (fav['permalink_page'].rsplit('/', 1)[-1] for fav in favs)
        self.assertEqual(list(fav_ids), ['1'])

    def test_query_favorites_before_after(self):
        for x in range(10):
            sf = self._post_to_shake(self.user_a)
            self.user_b.add_favorite(sf)

        request = signed_request(self.access_token, self.get_url('/api/favorites'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        original_favorites = json_decode(response.body)
        pivot_id = original_favorites['favorites'][5]['pivot_id']
        after_pivot_ids = [fav['sharekey'] for fav in original_favorites['favorites'][0:5]]
        before_pivot_ids = [fav['sharekey'] for fav in original_favorites['favorites'][6:]]

        request = signed_request(self.access_token, self.get_url('/api/favorites/before/%s' % pivot_id))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertTrue('favorites' in j_response)
        favs = j_response['favorites']
        self.assertEqual(len(favs), 4)
        pivot_ids = [fav['sharekey'] for fav in favs]
        self.assertEqual(before_pivot_ids, pivot_ids)

        request = signed_request(self.access_token, self.get_url('/api/favorites/after/%s' % pivot_id))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertTrue('favorites' in j_response)
        favs = j_response['favorites']
        self.assertEqual(len(favs), 5)
        pivot_ids = [fav['sharekey'] for fav in favs]
        self.assertEqual(after_pivot_ids, pivot_ids)

    def test_query_file_resource(self):
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/1'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(j_response['name'], '1.png')
        self.assertEqual(j_response['user']['name'], 'admin')

    def test_query_sharedfile_resource(self):
        sf = Sharedfile.get('id=%s', 1)
        posted = sf.created_at.replace(microsecond=0, tzinfo=None).isoformat() + 'Z'

        request = signed_request(self.access_token, self.get_url('/api/sharedfile/1'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(j_response['user']['name'], 'admin')
        self.assertEqual(j_response['posted_at'], posted)

    def test_can_update_own_sharedfile(self):
        user_b_file = self._post_to_shake(self.user_b)
        message_body = "description=newdescription&title=newtitle"
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/%s' % user_b_file.share_key), 'POST', {}, message_body)
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)
        user_b_file = Sharedfile.get("id = %s", user_b_file.id)
        self.assertEqual('newdescription', user_b_file.description)
        self.assertEqual('newtitle', user_b_file.title)

    def test_can_not_update_anothers_sharedfile(self):
        user_a_file = self._post_to_shake(self.user_a)
        message_body = "description=newdescription&title=newtitle"
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/%s' % user_a_file.share_key), 'POST', {}, message_body)
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 403)
        user_a_file = Sharedfile.get("id = %s", user_a_file.id)
        self.assertNotEqual('newdescription', user_a_file.description)
        self.assertNotEqual('newtitle', user_a_file.title)

    def test_query_user_name_resource(self):
        request = signed_request(self.access_token, self.get_url('/api/user_name/admin'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(j_response['name'], 'admin')
        self.assertEqual(j_response['profile_image_url'], 'http://mltshp.com/static/images/default-icon-venti.png')
        self.assertEqual(j_response['id'], 1)
        self.assertEqual(j_response['about'], self.user_a.about)
        self.assertEqual(j_response['website'], self.user_a.website)
        self.assertEqual(2, len(j_response['shakes']))

    def test_query_user_id_resource(self):
        request = signed_request(self.access_token, self.get_url('/api/user_id/1'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(j_response['name'], 'admin')
        self.assertEqual(j_response['id'], 1)

    def test_query_user_resource(self):
        request = signed_request(self.access_token, self.get_url('/api/user'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(j_response['name'], 'user2')
        self.assertEqual(j_response['id'], 2)

    def test_query_usershakes_resource(self):
        request = signed_request(self.access_token, self.get_url('/api/shakes'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(len(j_response['shakes']), 3)
        user_shake, group_shake, group_shake_2 = j_response['shakes']

        self.assertEqual(user_shake['id'], 2)
        self.assertEqual(user_shake['type'], 'user')
        self.assertEqual(user_shake['name'], 'user2')
        self.assertEqual(user_shake['owner'], {'name': 'user2', 'id': 2, 'profile_image_url': "http://mltshp.com/static/images/default-icon-venti.png"})
        self.assertEqual(user_shake['thumbnail_url'], 'http://mltshp.com/static/images/default-icon-venti.png')
        self.assertEqual(user_shake['url'], 'http://mltshp.com/user/user2')
        self.assertTrue('description' in user_shake)
        self.assertTrue('created_at' in user_shake)
        self.assertTrue('updated_at' in user_shake)

        self.assertEqual(group_shake['id'], 3)
        self.assertEqual(group_shake['type'], 'group')
        self.assertEqual(group_shake['name'], 'Group Shake')
        self.assertEqual(group_shake['owner'], {'name': 'user2', 'id': 2,  'profile_image_url': "http://mltshp.com/static/images/default-icon-venti.png"})
        self.assertEqual(group_shake['thumbnail_url'], 'http://mltshp.com/static/images/default-icon-venti.png')
        self.assertEqual(group_shake['url'], 'http://mltshp.com/groupshake')
        self.assertEqual(group_shake['description'], 'This is a group shake.')
        self.assertTrue('created_at' in group_shake)
        self.assertTrue('updated_at' in group_shake)

        self.assertEqual(group_shake_2['id'], 4)
        self.assertEqual(group_shake_2['owner'], {'name': 'admin', 'id': 1, 'profile_image_url': "http://mltshp.com/static/images/default-icon-venti.png"})

    def test_query_friend_shake(self):
        request = signed_request(self.access_token, self.get_url('/api/friends'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(j_response['friend_shake'][0]['name'], '1.png')
        self.assertEqual(j_response['friend_shake'][0]['width'], 1)
        self.assertEqual(j_response['friend_shake'][0]['height'], 1)
        self.assertEqual(j_response['friend_shake'][0]['nsfw'], False)

    def test_query_friend_shake_shows_nsfw(self):
        sf = Sharedfile.get('id=%s', 1)
        sf.set_nsfw(self.user_a)

        request = signed_request(self.access_token, self.get_url('/api/friends'))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(j_response['friend_shake'][0]['nsfw'], True)

    def test_query_friend_shake_before_after(self):
        """
        Admin (user_a), who user2 (user_b) follows, uploads 10 files, which appear in
        Admin's stream.

        /friends/before/{share_key} should return all files that came before passed in share_key
        while /friends/after/{share_key} should return those that came after.

        We assume there is already one file uploaded by Admin (share_key -> 1)
        """
        files = []
        for x in range(10):
            source_file = Sourcefile(width=10, height=10, file_key='mumbles', thumb_key='bumbles')
            source_file.save()
            sf = Sharedfile(source_id = source_file.id, user_id = self.user_a.id, name="shgaredfile.png",
                            title='shared file', content_type='image/png', deleted=0)
            sf.save()
            sf.share_key = base36encode(sf.id)
            sf.save()
            sf.add_to_shake(self.user_a.shake())
            files.append(sf)

        request = signed_request(self.access_token, self.get_url('/api/friends/before/%s' % files[3].share_key))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(4, len(j_response['friend_shake']))

        request = signed_request(self.access_token, self.get_url('/api/friends/after/%s' % files[3].share_key))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(6, len(j_response['friend_shake']))

    def test_shake_stream(self):
        user_shake = self.user_a.shake()
        url = self.get_url("/api/shakes/%s" % user_shake.id)
        request = signed_request(self.access_token, url, 'GET', {})
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(1, len(j_response['sharedfiles']))

    def test_shake_stream_before(self):
        user_shake = self.user_a.shake()
        self._post_to_shake(self.user_a, user_shake)
        self._post_to_shake(self.user_a, user_shake)
        sharedfiles = user_shake.sharedfiles()
        self.assertEqual(3, len(sharedfiles))
        url = self.get_url("/api/shakes/%s/before/%s" % (user_shake.id, sharedfiles[1].share_key))
        request = signed_request(self.access_token, url, 'GET', {})
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(1, len(j_response['sharedfiles']))
        self.assertEqual(sharedfiles[2].share_key, j_response['sharedfiles'][0]['sharekey'])

    def test_shake_stream_after(self):
        user_shake = self.user_a.shake()
        self._post_to_shake(self.user_a, user_shake)
        self._post_to_shake(self.user_a, user_shake)
        sharedfiles = user_shake.sharedfiles()
        self.assertEqual(3, len(sharedfiles))
        url = self.get_url("/api/shakes/%s/after/%s" % (user_shake.id, sharedfiles[1].share_key))
        request = signed_request(self.access_token, url, 'GET', {})
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(1, len(j_response['sharedfiles']))
        self.assertEqual(sharedfiles[0].share_key, j_response['sharedfiles'][0]['sharekey'])

    def test_upload_file(self):
        message = "file_name=%s&file_content_type=%s&file_sha1=%s&file_size=%s&file_path=%s" % \
                ("2.png", self.test_file1_content_type, self.test_file1_sha1, 69, self.test_file1_path)
        request = signed_request(self.access_token, self.get_url('/api/upload'), 'POST', {}, message)
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual(j_response['name'], '2.png')
        self.assertEqual(j_response['share_key'], '2')

    def test_upload_file_with_title_description(self):
        message = "file_name=%s&title=%s&description=%s&file_content_type=%s&file_sha1=%s&file_size=%s&file_path=%s" % \
                ("2.png", "two", "a thing i wrote", self.test_file1_content_type, self.test_file1_sha1, 69, self.test_file1_path)
        request = signed_request(self.access_token, self.get_url('/api/upload'), 'POST', {}, message)
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        sf = Sharedfile.get('share_key = %s', j_response['share_key'])
        self.assertEqual(sf.title, 'two')
        self.assertEqual(sf.description, 'a thing i wrote')

    def test_magicfiles_resource(self):
        # Set up some more files.
        testfile = Sharedfile.get("id = %s", 1)

        response = self.upload_file(file_path=self.test_file1_path, sha1=self.test_file1_sha1,
            content_type=self.test_file1_content_type, user_id=1, sid=self.sid, xsrf=self.xsrf)
        testfile_2 = Sharedfile.get("id = %s", 2)
        testfile_2.name = "test file 2"
        testfile_2.save()

        testfile_in_user2_shake = testfile_2.save_to_shake(self.user_b)
        testfile_in_another_group = testfile_2.save_to_shake(self.user_a, self.group_shake_2)

        sid_b = self.sign_in('user2', 'asdfasdf')
        xsrf_b = self.get_xsrf()
        response = self.upload_file(file_path=self.test_file1_path, sha1=self.test_file1_sha1,
            content_type=self.test_file1_content_type, user_id=2, sid=sid_b, xsrf=xsrf_b,
            shake_id=self.group_shake.id)
        testfile_3 = Sharedfile.get("id = %s", 5)
        testfile_3.name = "test file 5"
        testfile_3.save()

        with test_option('likes_to_magic', 5):
            # Set up their favorites.
            for sf, likes in zip((testfile, testfile_2, testfile_in_user2_shake, testfile_3), (0, 7, 3, 5)):
                for i in range(likes):
                    f = Favorite()
                    f.user_id = i
                    f.sharedfile_id = sf.id
                    f.save()
                    calculate_likes(sf.id)

        # What's best?
        request = signed_request(self.access_token, self.get_url('/api/magicfiles'), 'GET')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)

        magicfiles = j_response['magicfiles']
        pivot_ids = [sf['pivot_id'] for sf in magicfiles]
        share_keys = [sf['sharekey'] for sf in magicfiles]
        self.assertEqual(share_keys, ['5', '2'])
        self.assertEqual(pivot_ids, ['2', '1'])

        # Pagination check.
        request = signed_request(self.access_token, self.get_url('/api/magicfiles/before/2'), 'GET')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual('1', j_response['magicfiles'][0]['pivot_id'])

        request = signed_request(self.access_token, self.get_url('/api/magicfiles/after/1'), 'GET')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        j_response = json_decode(response.body)
        self.assertEqual('2', j_response['magicfiles'][0]['pivot_id'])

    def test_like_resource(self):
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/1/like'), 'POST', {}, '')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)

        j_response = json_decode(response.body)
        self.assertEqual(j_response['permalink_page'], 'http://mltshp.com/p/1')

        testfile = Sharedfile.get("id = %s", 1)
        self.assertEqual(testfile.like_count, 1)

    def test_like_resource_already_liked(self):
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/1/like'), 'POST', {}, '')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)

        request = signed_request(self.access_token, self.get_url('/api/sharedfile/1/like'), 'POST', {}, '')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 400)

        j_response = json_decode(response.body)
        self.assertTrue('error' in j_response)

        # Still only one like.
        testfile = Sharedfile.get("id = %s", 1)
        self.assertEqual(testfile.like_count, 1)

    def test_like_resource_not_found(self):
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/444Z/like'), 'POST')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 404)
        j_response = json_decode(response.body)
        self.assertTrue('error' in j_response)

    def test_save_sharedfile(self):
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/1/save'), 'POST')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)
        testfile = Sharedfile.get("id = %s", 1)
        self.assertEqual(1, testfile.save_count)
        j_response = json_decode(response.body)
        self.assertTrue(1, j_response['saves'])

    def test_save_nonexistant_sharedfile(self):
        request = signed_request(self.access_token, self.get_url('/api/sharedfile/50000/save'), 'POST')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 404)

    def test_save_own_sharedfile(self):
        self._post_to_shake(self.user_b)
        sharedfile = self.user_b.shake().sharedfiles()[0]
        url = self.get_url('/api/sharedfile/%s/save' % sharedfile.share_key)
        request = signed_request(self.access_token, url, 'POST', {}, '')
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 400)

    def test_save_to_shake_with_valid_permissions(self):
        url = self.get_url('/api/sharedfile/1/save')
        body = "shake_id=%s" % self.group_shake.id
        self.assertEqual(0, len(self.group_shake.sharedfiles()))
        request = signed_request(self.access_token, url, 'POST', body=body)
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)
        self.assertEqual(1, len(self.group_shake.sharedfiles()))
        j_response = json_decode(response.body)
        self.assertTrue(1, j_response['saves'])

    def test_save_to_shake_with_no_permissions(self):
        url = self.get_url('/api/sharedfile/1/save')
        shake = self.user_a.shake()
        body = "shake_id=%s" % shake.id
        original_num_sharedfiles = len(shake.sharedfiles())
        request = signed_request(self.access_token, url, 'POST', body=body)
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(original_num_sharedfiles, len(shake.sharedfiles()))
        self.assertEqual(response.code, 403)

    def test_double_save_sharedfile_only_saves_once(self):
        sharedfile = Sharedfile.get("id = 1")
        url = self.get_url('/api/sharedfile/1/save')
        arguments = {
            'shake_id' : self.group_shake.id
        }
        self.assertEqual(0, len(self.group_shake.sharedfiles()))

        response = api_request(self, url, arguments=arguments, method='POST')
        self.assertEqual(response.code, 200)
        self.assertEqual(1, len(self.group_shake.sharedfiles()))

        response = api_request(self, url, arguments=arguments, method='POST')
        self.assertEqual(response.code, 200)
        self.assertEqual(1, len(self.group_shake.sharedfiles()))

    def test_sharedfile_comments_returns_comments(self):
        sharedfile = self._post_to_shake(self.user_a)
        Comment.add(user=self.user_a, sharedfile=sharedfile, body="A comment")
        self.assertEqual(1, sharedfile.comment_count())
        url = self.get_url('/api/sharedfile/%s/comments' % sharedfile.id)
        response = api_request(self, url, method='GET')
        self.assertEqual(response.code, 200)
        j_response = json_decode(response.body)
        self.assertEqual(1, len(j_response['comments']))
        self.assertEqual("A comment", j_response['comments'][0]['body'])

    def test_sharedfile_comments_returns_404_if_bad_sharedfile(self):
        url = self.get_url('/api/sharedfile/%s/comments' % "NOFILEHERE")
        response = api_request(self, url, method='GET')
        self.assertEqual(response.code, 404)

    def test_sharedfile_post_comment_adds_comment(self):
        sharedfile = self._post_to_shake(self.user_a)
        self.assertEqual(0, sharedfile.comment_count())

        url = self.get_url('/api/sharedfile/%s/comments' % sharedfile.id)
        arguments = {
            'body' : 'A fine comment.'
        }
        response = api_request(self, url, arguments=arguments, method='POST')
        self.assertEqual(response.code, 200)
        self.assertEqual(1, sharedfile.comment_count())
        self.assertEqual('A fine comment.', sharedfile.comments()[0].body)

    def test_sharedfile_post_comment_returns_400_if_there_is_no_body(self):
        sharedfile = self._post_to_shake(self.user_a)
        self.assertEqual(0, sharedfile.comment_count())

        url = self.get_url('/api/sharedfile/%s/comments' % sharedfile.id)
        response = api_request(self, url, method='POST')
        self.assertEqual(response.code, 400)


    def test_sharedfile_post_comment_bad_sharedfile_404(self):
        url = self.get_url('/api/sharedfile/%s/comments' % "NOTHERE")
        arguments = {
            'body' : 'A fine comment.'
        }
        response = api_request(self, url, arguments=arguments, method='POST')
        self.assertEqual(response.code, 404)

    def test_incoming_gets_latest_files(self):
        sharedfile = self._post_to_shake(self.user_a)
        url = self.get_url('/api/incoming')
        response = api_request(self, url, method='GET')
        j_response = json_decode(response.body)
        self.assertEqual(response.code, 200)
        self.assertEqual(sharedfile.share_key, j_response['incoming'][0]['sharekey'])

    def test_incoming_before_pagination(self):
        sharedfile = self._post_to_shake(self.user_a)
        sharedfile2 = self._post_to_shake(self.user_a)
        url = self.get_url('/api/incoming/before/' + sharedfile2.share_key)
        response = api_request(self, url, method='GET')
        self.assertEqual(response.code, 200)
        j_response = json_decode(response.body)
        self.assertEqual(sharedfile.share_key, j_response['incoming'][0]['sharekey'])

    def test_incoming_after_pagination(self):
        sharedfile = self._post_to_shake(self.user_a)
        sharedfile2 = self._post_to_shake(self.user_a)
        url = self.get_url('/api/incoming/after/' + sharedfile.share_key)
        response = api_request(self, url, method='GET')
        self.assertEqual(response.code, 200)
        j_response = json_decode(response.body)
        self.assertEqual(1, len(j_response['incoming']))
        self.assertEqual(sharedfile2.share_key, j_response['incoming'][0]['sharekey'])

    def test_incoming_with_nsfw_filter(self):
        sharedfile = self._post_to_shake(self.user_a)
        self.user_a.flag_nsfw()
        url = self.get_url('/api/incoming')
        response = api_request(self, url, arguments={ 'filter_nsfw' : True }, method='GET')
        j_response = json_decode(response.body)
        self.assertEqual(response.code, 200)
        self.assertEqual(0, len(j_response['incoming']))


def api_request(obj, url, unsigned=False, arguments={}, headers={}, method='GET', body=''):
    if method == 'GET':
        body = None
    elif arguments:
        body = urllib.urlencode(arguments)
    if unsigned:
        request = HTTPRequest(url, method, headers, body)
    else:
        request = signed_request(obj.access_token, url, headers=headers, method=method, body=body)
    obj.http_client.fetch(request, obj.stop)
    response = obj.wait()
    return response


def signed_request(access_token, url, method='GET', headers={}, body=''):
    timestamp = int(time.mktime(datetime.utcnow().timetuple()))
    nonce = md5("%s%s" % (str(timestamp), random.random())).hexdigest()
    parsed_url = urlparse(url)
    query_array = []
    if parsed_url.query:
        query_array += parsed_url.query.split('&')
    for i in range(len(query_array)):
        if query_array[i].find('=') == -1:
            query_array[i] += '='
    query_array.sort()

    if method == 'GET':
        body = None

    normalized_string = normalize_string(access_token.consumer_key,
        int(timestamp),
        nonce,
        method.upper(),
        parsed_url.hostname,
        parsed_url.port,
        parsed_url.path,
        query_array)
    digest = hmac.new(access_token.consumer_secret, normalized_string, sha1).digest()
    signature = base64.encodestring(digest).strip()
    authorization_string = 'MAC token="%s", timestamp="%s", nonce="%s", signature="%s"' % (access_token.consumer_key, str(int(timestamp)), nonce, signature)
    if headers:
        headers.add("Authorization", authorization_string)
    else:
        headers = HTTPHeaders({"Authorization": authorization_string})

    return HTTPRequest(url, method, headers, body)
