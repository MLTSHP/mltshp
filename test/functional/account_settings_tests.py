import os

import test.base
from models import User, Sharedfile, Sourcefile, Conversation, Comment, App, Accesstoken

class AccountSettingsTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(AccountSettingsTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.sign_in("admin", "asdfasdf")

    def test_account_settings_200(self):
        """
        Account settings pages should return a success response.
        """
        response = self.fetch('/account/settings')
        self.assertEqual(200, response.code)
        response = self.fetch('/account/settings/profile')
        self.assertEqual(200, response.code)
        response = self.fetch('/account/settings/connections')
        self.assertEqual(200, response.code)

    def test_updating_account_settings(self):
        """
        Should be able to update email address and notifications status.
        """
        self.assertEqual('admin@mltshp.com', self.user.email)
        self.assertEqual(0, self.user.disable_notifications)
        arguments = {
            'email' : 'user2@mltshp.com',
            'disable_notifications' : '1'
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual('user2@mltshp.com', user_reloaded.email)
        self.assertEqual(1, user_reloaded.disable_notifications)

    def test_notification_settings_turned_off(self):
        """
        Notification Status set to 0 when value does not exist
        """
        self.user.disable_notifications = 1
        self.user.save()

        arguments = {
            'email' : 'user2@mltshp.com'
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual('user2@mltshp.com', user_reloaded.email)
        self.assertEqual(0, user_reloaded.disable_notifications)


    def test_show_naked_people_turns_on_and_off(self):
        """
        Turning the NSFW filter on and off
        """
        self.assertFalse(self.user.show_naked_people)

        #ON
        arguments = {
            'show_naked_people':1,
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual(1, user_reloaded.show_naked_people)

        #OFF
        arguments = {
            'nothing':'nothing',
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual(0, user_reloaded.show_naked_people)

        #ON
        arguments = {
            'show_naked_people':1,
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual(1, user_reloaded.show_naked_people)

    def test_show_stats_turns_on_and_off(self):
        """
        Turning show stats on and off.
        """
        self.assertFalse(self.user.show_stats)

        #ON
        arguments = {
            'show_stats':1,
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual(1, user_reloaded.show_stats)

        #OFF
        arguments = {
            'nothing':'nothing',
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual(0, user_reloaded.show_stats)

        #ON
        arguments = {
            'show_stats':1,
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual(1, user_reloaded.show_stats)


    def test_changing_email_sets_email_confirmed_false(self):
        """
        If you change your email it should set email_confirmed to 0
        """
        arguments = {
            'email' : 'different@mltshp.com',
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual('different@mltshp.com', user_reloaded.email)
        self.assertEqual(0, user_reloaded.email_confirmed)


    def test_changing_email_to_same_does_not_change_email_confirmed(self):
        """
        If you change your email it should set email_confirmed to 0
        """
        arguments = {
            'email' : 'admin@mltshp.com',
        }
        self.post_url('/account/settings', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual('admin@mltshp.com', user_reloaded.email)
        self.assertEqual(1, user_reloaded.email_confirmed)


    def test_updating_account_profile_settings(self):
        """
        Account profile settings can update full name, about, and website.
        """
        self.assertEqual('', self.user.full_name)
        self.assertEqual('', self.user.about)
        self.assertEqual('', self.user.website)
        arguments = {
            'full_name' : 'Some User',
            'about' : 'About text.',
            'website' : 'https://my-mltshp.com/'
        }
        self.post_url('/account/settings/profile', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertEqual('Some User', user_reloaded.full_name)
        self.assertEqual('About text.', user_reloaded.about)
        self.assertEqual('https://my-mltshp.com/', user_reloaded.website)

    def test_updating_user_profile_photo(self):
        """
        Emulate the variables that nginx passes in via the upload module
        and see if the file gets uploaded.
        """
        photo_path = os.path.abspath("static/images/test-avatar.png")
        arguments = {
            'photo_path': photo_path,
            'photo_content_type': "image/png",
            'photo_name': os.path.basename(photo_path),
            'photo_size': os.path.getsize(photo_path),
            'skip_s3': '1',
        }
        response = self.post_url('/account/settings/profile', arguments=arguments)
        user_reloaded = User.get('id = %s', self.user.id)
        self.assertTrue(user_reloaded.profile_image)
        self.assertTrue(user_reloaded.profile_image_url().find('/account') > -1)

    def test_disconnecting_connection(self):
        """
        Sending a post request to /settings/connections/{{app_id}}/disconnect should mark
        an access token as deleted.
        """
        # app created by Torrez.
        app = App(user_id=self.user.id,title='Title')
        app.save()

        # another user.
        new_user = User(name='newuser', email='newuser@example.com', email_confirmed=1, is_paid=1)
        new_user.set_password('asdfasdf')
        new_user.save()

        #connect another user and app
        token = Accesstoken(user_id=new_user.id, app_id=app.id, deleted=0)
        token.save()

        # If torrez hits URL, which he should never be able to find, nothing happens
        # to token.
        self.post_url("/account/settings/connections/%s/disconnect" % app.id)
        token_reloaded = Accesstoken.get('id = %s', token.id)
        self.assertEqual(0, token_reloaded.deleted)

        # but if the user it's about hits it, the token deletes.
        self.sign_in('newuser', 'asdfasdf')
        self.post_url("/account/settings/connections/%s/disconnect" % app.id)
        token_reloaded = Accesstoken.get('id = %s', token.id)
        self.assertEqual(1, token_reloaded.deleted)

        # Even if there are several undeleted access tokens, they all end up deleted.
        token_two = Accesstoken(user_id=new_user.id, app_id=app.id, deleted=0)
        token_two.save()
        token_three = Accesstoken(user_id=new_user.id, app_id=app.id, deleted=0)
        token_three.save()

        self.post_url("/account/settings/connections/%s/disconnect" % app.id)
        token_reloaded = Accesstoken.get('id = %s', token.id)
        token_two_reloaded = Accesstoken.get('id = %s', token_two.id)
        token_three_reloaded = Accesstoken.get('id = %s', token_three.id)
        self.assertEqual(1, token_reloaded.deleted)  # still
        self.assertEqual(1, token_two_reloaded.deleted)
        self.assertEqual(1, token_three_reloaded.deleted)

    def test_unverified_email_notification_on_settings_page(self):
        self.user.email_confirmed = 0
        self.user.save()
        response = self.fetch_url("/account/settings")

        self.assertIn('Please check your inbox for verification', response.body)

    def test_resend_verification_email_changes_key(self):
        self.user.verify_email_token = "asdf"
        self.user.email_confirmed = 0
        self.user.save()
        response = self.post_url('/account/settings/resend-verification-email')

        reloaded_user = User.get('id=%s', self.user.id)
        self.assertTrue(reloaded_user.verify_email_token)
        self.assertTrue("asdf" != reloaded_user.verify_email_token)


