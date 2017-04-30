import os

from tornado.escape import json_decode

import test.base
import test.factories
from models import User, Sharedfile, Sourcefile, Subscription, Notification, Comment, Shake
import lib.utilities


class AccountTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(AccountTests, self).setUp()
        self.user = User(name='admin', email='admin@example.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.sign_in("admin", "asdfasdf")

    def test_user_paid_account_rss_works(self):
        sourcefile = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        sourcefile.save()
        sharedfile = Sharedfile(source_id=sourcefile.id, name="the name",user_id=self.user.id, \
            content_type="image/png", description="description", source_url="http://www.mltshp.com/?hi")
        sharedfile.save()
        sharedfile.share_key = lib.utilities.base36encode(sharedfile.id)
        sharedfile.save()

        sharedfile.add_to_shake(self.user.shake())

        response = self.fetch_url('/user/admin/rss')
        self.assertEqual(response.headers['Content-Type'], 'application/xml')
        parsed_xml = lib.utilities.parse_xml(response.body)
        self.assertEqual(parsed_xml['rss']['channel']['item']['link'], 'http://mltshp.com/p/1')

    def test_user_unpaid_account_rss_404s(self):
        self.user.update_attribute("is_paid", 0)
        self.user.save()

        response = self.fetch_url('/user/admin/rss')
        self.assertEqual(response.code, 404)

        def test_like_save_view_count_is_returned(self):
        sharedfile = test.factories.sharedfile(self.user, view_count=25, save_count=50, like_count=100)
        response = self.fetch_url('/user/%s/counts' % self.user.name)
        j_response = json_decode(response.body)
        self.assertEqual(j_response['likes'], 100)
        self.assertEqual(j_response['saves'], 50)
        self.assertEqual(j_response['views'], 25)

    def test_email_not_confirmed_puts_notice_at_top(self):
        self.user.email_confirmed = 0
        self.user.save()

        response = self.fetch_url('/')
        self.assertTrue(response.body.find('Please visit settings to confirm your email!') > -1)

        response = self.fetch_url('/incoming')
        self.assertTrue(response.body.find('Please visit settings to confirm your email!') > -1)

        response = self.fetch_url('/friends')
        self.assertTrue(response.body.find('Please visit settings to confirm your email!') > -1)

    def test_quick_notifications(self):
        """
        /account/quick-notifications should return without error when populated with
        all possible  notification types.

        Page should also not be accessible if you're not signed in.
        """
        self.user2 = User(name='example2',email='user2@example.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1,
            is_paid=1)
        self.user2.save()
        self.sourcefile = Sourcefile(width=20,height=20,file_key="asdf", \
            thumb_key="asdf_t")
        self.sourcefile.save()
        self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file", \
            user_id=self.user.id, content_type="image/png", share_key="ok")
        self.sharedfile.save()
        self.shake = Shake(user_id=self.user2.id, name='asdf', type='group',
            title='My Test Shake', description='Testing this shake test.')
        self.shake.save()


        # new subscription
        new_sub = Subscription(user_id=self.user2.id, shake_id=1)
        new_sub.save()
        new_subscriber = Notification.new_subscriber(sender=self.user2, receiver=self.user, action_id=new_sub.id)
        # new favorite
        new_favorite = Notification.new_favorite(sender=self.user2, sharedfile=self.sharedfile)
        # new save
        new_save = Notification.new_save(sender=self.user2, sharedfile=self.sharedfile)
        # new comment
        new_comment = Comment(user_id=self.user2.id, sharedfile_id = self.sharedfile.id, body="Testing comment")
        new_comment.save()
        # new mention
        new_mention = Notification.new_mention(receiver=self.user, comment=new_comment)
        # new invitation
        new_mention = Notification.new_invitation(sender=self.user2, receiver=self.user, action_id=self.shake.id)

        response = self.fetch_url('/account/quick-notifications')
        self.assertEqual(200, response.code)
        self.sign_out()
        response = self.fetch_url('/account/quick-notifications', follow_redirects=False)
        self.assertEqual(302, response.code)



