import random

import test.base
from models import User
from lib.badpasswords import bad_list

class CreateAccountTests(test.base.BaseAsyncTestCase):

    def test_username_too_long(self):
        arguments = self._valid_arguments()
        arguments['name'] = 'asdfasdfasdfasdfasdfasdfasdfasd'
        response = self.post_url('/create-account', arguments)
        self.assertIn(
            'Username should be less than 30 characters.',
            response.body
        )

    def test_username_contains_invalid_chars(self):
        names = [
            'asdfasdfasdfas$fasdfasdf',
            '3(3)',
            '. si .',
            '/jsidifj',
            'isodfiof+djf',
            'dd#33'
        ]
        for name in names:
            arguments = self._valid_arguments()
            arguments['name'] = name
            response = self.post_url('/create-account', arguments)
            self.assertIn(
                'Username can only contain letters, numbers',
                response.body
            )

    def test_username_exists(self):
        existant_user = User(
            name='admin',
            email='admin@mltshp.com',
            email_confirmed=1,
            is_paid=1
        )
        existant_user.set_password('asdfasdf')
        existant_user.save()
        arguments = self._valid_arguments()
        arguments['name'] = existant_user.name
        response = self.post_url('/create-account', arguments)
        self.assertIn(
            'Username has already been taken.',
            response.body
        )

    def test_username_is_blank(self):
        arguments = self._valid_arguments()
        arguments['name'] = ""
        response = self.post_url('/create-account', arguments)
        self.assertIn(
            'You definitely need a username',
            response.body
        )

    def test_email_is_blank(self):
        arguments = self._valid_arguments()
        arguments['email'] = ""
        response = self.post_url('/create-account', arguments)
        self.assertIn(
            'You\'ll need an email to verify your account.',
            response.body
        )

    def test_email_already_exists(self):
        existant_user = User(
            name='admin',
            email='admin@mltshp.com',
            email_confirmed=1,
            is_paid=1
        )
        existant_user.set_password('asdfasdf')
        existant_user.save()
        arguments = self._valid_arguments()
        arguments['email'] = existant_user.email
        response = self.post_url('/create-account', arguments)
        self.assertIn(
            'This email already has an account.',
            response.body
        )

    def test_email_aint_right(self):
        arguments = self._valid_arguments()
        arguments['email'] = "admin-torresdz.org"
        response = self.post_url('/create-account', arguments)
        self.assertIn(
            'Email doesn\'t look right.',
            response.body
        )

    def test_bad_passwords(self):
        for bad_password in random.sample(bad_list, 2):
            arguments = self._valid_arguments()
            arguments['password'] = bad_password
            arguments['password_again'] = bad_password
            response = self.post_url('/create-account', arguments)
            self.assertIn(
                'That is not a good password.',
                response.body
            )

    def test_successful_signup(self):
        """
        On a succesful creation, the user should at least have:
          * the tou_agreed flag set to true
          * a user shake created
        """
        arguments = self._valid_arguments()
        response = self.post_url('/create-account', arguments)
        user = User.get('name=%s', arguments['name'])
        self.assertTrue(user.tou_agreed)
        shake = user.shake()
        self.assertEqual(shake.type, 'user')

    def _valid_arguments(self):
        return {
            'name' : 'valid_user',
            'password' : 'asdfasdf',
            'password_again' : 'asdfasdf',
            'email' : 'valid_user@mltshp.com',
            '_skip_recaptcha_test_only' : True,
        }

