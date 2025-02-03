import time
import hashlib

import test.base
from models import User

class VerifyEmailTests(test.base.BaseAsyncTestCase):

    def test_verify_key_success(self):
        h = hashlib.sha1()
        h.update(("%s" % time.time()).encode('ascii'))
        verify_token = h.hexdigest()

        existant_user = User(
            name='admin',
            email='admin@mltshp.com',
            email_confirmed=0,
            verify_email_token=verify_token
        )
        existant_user.set_password('asdfasdf')
        existant_user.save()
        response = self.fetch_url('/verify-email/%s' % verify_token)
        reloaded_user = User.get('id = %s', existant_user.id)
        self.assertEqual(reloaded_user.email_confirmed, 1)
        self.assertEqual(reloaded_user.verify_email_token, '')
        self.assertEqual(response.effective_url, self.get_url('/'))

    def test_verify_key_failures(self):
        existant_user = User(
            name='admin',
            email='admin@mltshp.com',
            email_confirmed=0,
            verify_email_token='some-token'
        )
        existant_user.set_password('asdfasdf')
        existant_user.save()

        bad_keys = [
            'asdf',
            '',
            '%20',
            '?lksdfjlskdfj=sldkfjasdf',
            '282938898932893289328932'
        ]
        for key in bad_keys:
            response = self.fetch_url('/verify-email/%s' % key)
            reloaded_user = User.get('id = %s', existant_user.id)
            self.assertEqual(reloaded_user.email_confirmed, 0)
            self.assertEqual(reloaded_user.verify_email_token, 'some-token')
            self.assertTrue(response.code == 404)

