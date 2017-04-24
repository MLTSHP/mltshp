from tornado.testing import AsyncHTTPTestCase
from torndb import Connection
from tornado.httpclient import HTTPRequest
from tornado.escape import json_decode


import Cookie
import base64
import time
import copy
import hashlib
import random
import os


from base import BaseAsyncTestCase

from models import User, Sourcefile, Sharedfile, Shake, Subscription, Notification, Post

class AccountIndexTests(BaseAsyncTestCase):
    def setUp(self):
        super(AccountIndexTests, self).setUp()
        self.admin = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()
        self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf()
        self.flake=str(time.time())
        
    def test_pagination_returns_correct_counts(self):
        """
        This tests creating 111 shared files for a user and then tests that pagination
        on their user page returns the correct pages
        """
        user = User.get('name="admin"')
        user_shake = user.shake()
        source_file = Sourcefile(width=10, height=10, file_key='mumbles', thumb_key='bumbles')
        source_file.save()
        
        missing_ids = []
        
        for i in range(111):
            sf = Sharedfile(source_id = source_file.id, user_id = user.id, name="shgaredfile.png", title='shared file', share_key='asdf', content_type='image/png', deleted=0)  
            sf.save()
            sf.add_to_shake(user_shake)
            
        for i in range(12):
            response = self.fetch('/user/admin/%s' % (i + 1))
            self.assertEqual(response.code, 200)

    def test_new_user_sees_welcome_page(self):
        """
        This tests that a new user who just signed up will see the welcome page.
        """
        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)
        self.assertTrue(response.body.find('Getting Started'))


class SubscriptionTests(BaseAsyncTestCase):    
    def setUp(self):
        super(SubscriptionTests, self).setUp()
        self.admin = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()
        
        self.user2 = User(name='user2', email='user2@mltshp.com', email_confirmed=1, is_paid=1)
        self.user2.set_password('asdfasdf')
        self.user2.save()
        
        self.user3 = User(name='user3', email='user3@mltshp.com', email_confirmed=1, is_paid=1)
        self.user3.set_password('asdfasdf')
        self.user3.save()
        
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf()
        self.flake=str(time.time())
        
    def test_follow_signed_in(self):
        request = HTTPRequest(self.get_url('/user/user3/subscribe?json=1'), 'POST', {'Cookie':'sid=%s;_xsrf=%s' % (self.sid, self.xsrf)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
                
        j = json_decode(response.body)
        self.assertEqual(j['subscription_status'], True)
        
        subscription = Subscription.get('user_id=1 and shake_id=3')
        self.assertTrue(subscription)
        self.assertFalse(subscription.deleted)
    
    def test_follow_creates_posts(self):
        self.sign_in('user3', 'asdfasdf')
        response = self.upload_test_file()
        self.sign_in('admin', 'asdfasdf')
        self.post_url('/user/user3/subscribe?json=1')
    
        post = Post.where('user_id=%s', self.admin.id)
        self.assertEqual(3, post[0].shake_id)
        
    def test_cannot_follow_self(self):
        request = HTTPRequest(self.get_url('/user/admin/subscribe?json=1'), 'POST', {'Cookie':'sid=%s;_xsrf=%s' % (self.sid, self.xsrf)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
                
        j = json_decode(response.body)
        self.assertTrue('error' in j)
        
        subscription = Subscription.all()
        self.assertTrue(len(subscription) == 0)

    def test_cannot_subscribe_if_not_signed_in(self):
        request = HTTPRequest(self.get_url('/user/user3/subscribe?json=1'), 'POST', {'Cookie':'_xsrf=%s' % (self.xsrf)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 403)
    
    def test_unsubscribe_shake(self):
        request = HTTPRequest(self.get_url('/user/user3/subscribe?json=1'), 'POST', {'Cookie':'sid=%s;_xsrf=%s' % (self.sid, self.xsrf)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
                
        request = HTTPRequest(self.get_url('/user/user3/unsubscribe?json=1'), 'POST', {'Cookie':'sid=%s;_xsrf=%s' % (self.sid, self.xsrf)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
                
        j = json_decode(response.body)
        self.assertEqual(j['subscription_status'], False)
        
        subscription = Subscription.get('user_id=1 and shake_id=3')
        self.assertTrue(subscription)
        self.assertTrue(subscription.deleted)
        
        
    def test_subscribe_unsubscribe_is_same_object(self):
        request = HTTPRequest(self.get_url('/user/user3/subscribe?json=1'), 'POST', {'Cookie':'sid=%s;_xsrf=%s' % (self.sid, self.xsrf)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        
        first_subscription = Subscription.get('user_id=1 and shake_id=3')
                
        request = HTTPRequest(self.get_url('/user/user3/unsubscribe?json=1'), 'POST', {'Cookie':'sid=%s;_xsrf=%s' % (self.sid, self.xsrf)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
                
        j = json_decode(response.body)
        self.assertEqual(j['subscription_status'], False)
        
        second_subscription = Subscription.get('user_id=1 and shake_id=3')
        self.assertEqual(first_subscription.id, second_subscription.id)
        
    def test_notification_created_when_subscription_created(self):
        """
        User is followed. Notification created.
        """
        request = HTTPRequest(self.get_url('/user/user3/subscribe?json=1'), 'POST', {'Cookie':'sid=%s;_xsrf=%s' % (self.sid, self.xsrf)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        
        subscriptions = Subscription.all()
        self.assertEqual(len(subscriptions), 1)
        notifications = Notification.all()
        self.assertEqual(len(notifications), 1)
        notification = notifications[0]
        self.assertEqual(notification.sender_id, self.admin.id)
        self.assertEqual(notification.receiver_id, self.user3.id)
        self.assertEqual(notification.action_id, subscriptions[0].id)
        self.assertEqual(notification.type, 'subscriber')


class EmailVerificationTests(BaseAsyncTestCase):
    def setUp(self):
        super(EmailVerificationTests, self).setUp()
        self.user = User(name="admin", email="admin@mltshp.com", email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.xsrf = self.get_xsrf()
        
    def test_email_verification(self):
        self.assertEqual(self.user.email_confirmed, 1)
        self.assertTrue(self.user.verify_email_token == None)
        
        
        self.user.invalidate_email()
        
        reload_user = User.get("id=%s", self.user.id)
        
        self.assertEqual(reload_user.email_confirmed, 0)
        self.assertTrue(len(reload_user.verify_email_token) == 40)
        
    def test_lost_password(self):
        self.assertTrue(self.user.reset_password_token == None)
        request=HTTPRequest(
                    url = self.get_url("/account/forgot-password"),
                    method='POST',
                    headers = {'Cookie':'_xsrf=%s' % (self.xsrf)},
                    body = "_xsrf=%s&email=%s" % (self.xsrf, self.user.email))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertEqual(response.code, 200)
        self.assertTrue(response.body.find("We Sent You Instructions!") > 0)
        user = User.get("id=%s", 1)
        self.assertTrue(len(user.reset_password_token) == 40)
        
    def test_lost_password_lookup_failure(self):
        self.assertTrue(self.user.reset_password_token == None)
    
        request=HTTPRequest(
                    url = self.get_url("/account/forgot-password"),
                    method='POST',
                    headers = {'Cookie':'_xsrf=%s' % self.xsrf},
                    body = "_xsrf=%s&email=25235235" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertTrue(response.body.find("That email address doesn't have an account.") > 0)
        
    def test_reset_password_lookup(self):
        """
        Hitting the reset-password url with a valid key will correctly look it up.
        """
        h = hashlib.sha1()
        h.update("%s-%s" % (time.time(), random.random()))
        self.user.reset_password_token = h.hexdigest()
        self.user.save()
        
        self.http_client.fetch(self.get_url("/account/reset-password/%s" % (self.user.reset_password_token)), self.stop)
        response = self.wait()
        self.assertTrue(response.body.find("Enter a new password for your account.") > -1)
        
    def test_reset_password_finish(self):
        """
        Posting the actual reset-password will reset it
        """
        self.user.create_reset_password_token()
        
        self.http_client.fetch(self.get_url("/account/reset-password/%s" % (self.user.reset_password_token)), self.stop)
        response = self.wait()
        
        request = HTTPRequest(
                    url = self.get_url("/account/reset-password/%s" % (self.user.reset_password_token)),
                    method='POST',
                    headers={"Cookie":"_xsrf=%s" % (self.xsrf)},
                    body="password=%s&password_again=%s&_xsrf=%s" % ("qwertyqwerty", "qwertyqwerty", self.xsrf)
                    )
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        
        self.user = User.get("id=%s", 1)
        self.assertEqual(self.user.reset_password_token, "")
        self.assertEqual(self.user.hashed_password, User.generate_password_digest('qwertyqwerty'))
        
    def test_reset_password_throws_error_if_passwords_dont_match(self):
        """
        Send two different passwords.
        """
        self.user.create_reset_password_token()
        reset_token = self.user.reset_password_token
        
        request = HTTPRequest(
                    url = self.get_url("/account/reset-password/%s" % (reset_token)),
                    method='POST',
                    headers={"Cookie":"_xsrf=%s" % (self.xsrf)},
                    body="password=%s&password_again=%s&_xsrf=%s" % ("qwertyqwerty", "poiupoiu", self.xsrf)
        )
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        self.assertTrue(response.body.find("Those passwords didn't match, or are invalid. Please try again.") > -1)
        self.user = User.get("id = %s", 1)
        self.assertEqual(self.user.hashed_password, User.generate_password_digest('asdfasdf'))
        self.assertEqual(reset_token, self.user.reset_password_token)
        
    def test_reset_password_throws_404s_on_invalid_tokens(self):
        """
        Grabbing reset-password will throw a 404 if not found.
        """
        invalid_tokens = ["1234567890123456789012345678901234567890", 
                            "123456789012345678901234567890123456789", 
                            "123",
                            "",
                            "029%203208%2032093093%2020923"]
        for token in invalid_tokens:
            self.http_client.fetch(self.get_url("/account/reset-password/%s" % (token)), self.stop)
            response = self.wait()
            self.assertEqual(response.code, 404)

    def test_password_reset_while_signed_in(self):
        """
        This should sign you out.
        """
        sid = self.sign_in("admin", "asdfasdf")
        self.user.create_reset_password_token()
        
        request = HTTPRequest(
                    url = self.get_url("/account/reset-password/%s" % (self.user.reset_password_token)),
                    method='GET',
                    headers={'Cookie':"sid=%s" % (sid)},
                    follow_redirects=False
        )
        self.http_client.fetch(request, self.stop)
        response = self.wait()

class NotificationTests(BaseAsyncTestCase):
    def setUp(self):
        super(NotificationTests, self).setUp()
        self.sender = User(name="admin", email="admin@mltshp.com", email_confirmed=1, is_paid=1)
        self.sender.set_password('asdfasdf')
        self.sender.save()
        self.receiver = User(name="user2", email="user2@torrez.org", email_confirmed=1, is_paid=1)
        self.receiver.set_password('asdfasdf')
        self.receiver.save()

        self.xsrf = self.get_xsrf()
        self.sender_sid = self.sign_in('admin', 'asdfasdf')        
        self.receiver_sid = self.sign_in('user2', 'asdfasdf')

        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path) 
        self.test_file1_content_type = "image/png"

        self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.receiver_sid, self.xsrf)
        
    def test_clear_single_notification(self):
        sharedfile = Sharedfile.get('id=1')
        n = Notification.new_favorite(self.sender, sharedfile)
        
        request = HTTPRequest(self.get_url('/account/clear-notification'), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.receiver_sid)}, '_xsrf=%s&type=single&id=%s' % (self.xsrf, n.id))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        j = json_decode(response.body)
        self.assertTrue('response' in j)
        n = Notification.get('id=1')
        self.assertTrue(n.deleted)
        
    def test_only_allowed_to_clear_own_notifications(self):
        sharedfile = Sharedfile.get('id=1')
        n = Notification.new_favorite(self.sender, sharedfile)
        
        request = HTTPRequest(self.get_url('/account/clear-notification'), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sender_sid)}, '_xsrf=%s&type=single&id=%s' % (self.xsrf, n.id))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        j = json_decode(response.body)
        self.assertTrue('error' in j)
        n = Notification.get('id=1')
        self.assertFalse(n.deleted)

    
    def test_clears_all_saves(self):
        self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.receiver_sid, self.xsrf)
        
        sharedfile = Sharedfile.get('id=1')
        n = Notification.new_save(self.sender, sharedfile)
        n = Notification.new_save(self.sender, sharedfile)
        
        
        request = HTTPRequest(self.get_url('/account/clear-notification'), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.receiver_sid)}, '_xsrf=%s&type=save' % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        j = json_decode(response.body)
        self.assertEqual(j['response'], "0 new saves")
        ns = Notification.where('receiver_id=%s' % (self.receiver.id))
        for n in ns:
            self.assertTrue(n.deleted)
    
    def test_clears_all_favorites(self):
        self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.receiver_sid, self.xsrf)
        
        sharedfile = Sharedfile.get('id=1')
        n = Notification.new_favorite(self.sender, sharedfile)
        n = Notification.new_favorite(self.sender, sharedfile)
        
        request = HTTPRequest(self.get_url('/account/clear-notification'), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.receiver_sid)}, '_xsrf=%s&type=favorite' % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        j = json_decode(response.body)
        self.assertEqual(j['response'], "0 new likes")
        ns = Notification.where('receiver_id=%s' % (self.receiver.id))
        for n in ns:
            self.assertTrue(n.deleted)

        
    def test_clears_all_subscriptions(self):
        user3 = User(name="user3", email="user3@example.com", email_confirmed=1)
        user3.set_password('asdfasdf')
        user3.save()
        
        Subscription(user_id=self.sender.id, shake_id=2).save()
        Subscription(user_id=user3.id, shake_id=2).save()
        
        
        Notification.new_subscriber(self.sender, self.receiver, 1)
        Notification.new_subscriber(user3, self.receiver, 2)
        
        request = HTTPRequest(self.get_url('/account/clear-notification'), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.receiver_sid)}, '_xsrf=%s&type=subscriber' % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        j = json_decode(response.body)
        self.assertEqual(j['response'], "You have 0 new followers")
        ns = Notification.where('receiver_id=%s' % (self.receiver.id))
        for n in ns:
            self.assertTrue(n.deleted)
    
class AccountFormattingTests(BaseAsyncTestCase):
    def setUp(self):
        super(AccountFormattingTests, self).setUp()
        self.admin = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf()
        self.flake=str(time.time())

    def test_usernames_with_special_characters_can_be_seen(self):
        test_names = ['john-mike']
        for name in test_names:
            new_user = User(name=name, email='%s@mltshp.com' % (name), email_confirmed=1)
            new_user.set_password('asdfasdf')
            new_user.save()
            self.http_client.fetch(self.get_url('/user/%s' % name), self.stop)
            response = self.wait()            
            self.assertEqual(response.code, 200)
            

