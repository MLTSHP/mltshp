import os

import test.base
from models import User, Shake, Sharedfile, Sourcefile, Subscription
import lib.utilities
from tornado.escape import json_encode

class ShakeCrudTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(ShakeCrudTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.is_paid = 1
        self.user.save()
        self.sign_in("admin", "asdfasdf")

    def test_shake_create_success(self):
        """
        Create a shake for user admin. Should succeed and redirect to /short_name
        """
        self.user.stripe_plan_id = "mltshp-double"
        self.user.save()
        arguments = {
            'name' : 'yo',
            'description' : 'My little corner of the world',
            'title' : 'title'
        }
        response = self.post_url('/shake/create', arguments=arguments)
        s = Shake.get('name=%s', 'yo')
        self.assertEqual(response.effective_url, self.get_url('/yo'))
        self.assertTrue(s)

    def test_shake_create_error_on_name(self):
        """
        Can't create a shake without a name.
        """
        self.user.stripe_plan_id = "mltshp-double"
        self.user.save()
        arguments = {
            'name' : '',
            'title': 'title',
            'description' : 'My little corner of the world'
        }
        response = self.post_url('/shake/create', arguments=arguments)
        self.assertEqual(response.effective_url, self.get_url('/shake/create'))
        self.assertTrue(response.body.find('That URL is not valid.') > -1)

    def test_shake_create_error_on_title(self):
        """
        Can't create a shake without a title.
        """
        self.user.stripe_plan_id = "mltshp-double"
        self.user.save()
        arguments = {
            'name' : 'got one',
            'title': '',
            'description' : 'My little corner of the world'
        }
        response = self.post_url('/shake/create', arguments=arguments)
        self.assertEqual(response.effective_url, self.get_url('/shake/create'))
        self.assertTrue(response.body.find("Title can't be blank.") > -1)


    def test_shake_update_description(self):
        self.user.stripe_plan_id = "mltshp-double"
        self.user.save()
        arguments = {
            'name' : 'test1',
            'description' : 'OLD OLD OLD',
            'title' : 'indeed'
        }
        response = self.post_url('/shake/create', arguments=arguments)

        arguments = {
            'description' : 'NEW NEW NEW'
        }

        response = self.post_url('/shake/test1/update', arguments=arguments)
        shake = Shake.get("name=%s", 'test1')
        self.assertEqual(arguments['description'], shake.description)

    def test_bad_shake_name_issues_404(self):
        response = self.fetch_url('/asdfasdf')
        self.assertEqual(response.code, 404)

    def test_shake_duplicate_error(self):
        self.user.stripe_plan_id = "mltshp-double"
        self.user.save()
        arguments = {
            'name' : 'asdf',
            'description' : 'Shake 1',
            'title'  : 'got one'
        }
        response = self.post_url('/shake/create', arguments=arguments)

        arguments = {
            'name' : 'asdf',
            'description' : 'Shake 2',
            'title' : 'got one'
        }
        response = self.post_url('/shake/create', arguments=arguments)
        self.assertTrue(response.body.find('That URL is already taken.') > -1)

    def test_subscribe_unsubscribe_works(self):
        user_a = User(name='user_a', email='user_a@example.com', email_confirmed=1, is_paid=1, stripe_plan_id="mltshp-double")
        user_a.set_password('asdfasdf')
        user_a.save()
        self.sign_in('user_a', 'asdfasdf')
        arguments = {
            'name' : 'asdf',
            'description' : 'A shake test.',
            'title' : 'Shake Test',
        }
        self.post_url('/shake/create', arguments=arguments)
        shake = Shake.get('name = %s', 'asdf')

        self.sign_in('admin', 'asdfasdf')
        self.post_url('/shake/%s/subscribe?json=1' % shake.id)

        #subscription #1 is the user subscribing to their own new shake
        subscription = Subscription.get('id=2')
        self.assertEqual(subscription.user_id, 1)
        self.assertEqual(subscription.deleted, 0)

        self.post_url('/shake/%s/unsubscribe?json=1' % shake.id)

        #subscription #1 is the user subscribing to their own new shake
        subscription = Subscription.get('id=2')
        self.assertEqual(subscription.user_id, 1)
        self.assertEqual(subscription.deleted, 1)

    def test_cannot_create_shake_if_not_a_plus_member(self):
        user_a = User(name='user_a', email='user_a@example.com', email_confirmed=1, is_paid=1,
            stripe_plan_id="mltshp-single")
        user_a.set_password('asdfasdf')
        user_a.save()
        self.sign_in('user_a', 'asdfasdf')

        arguments = {
            'name' : 'asdf',
            'description' : 'A shake test.',
            'title' : 'Shake Test',
        }
        response = self.post_url('/shake/create', arguments=arguments)
        self.assertTrue(response.body.find('Create up to 100 group shakes') > -1)

    def test_create_shake_page_works_for_plus_members(self):
        user_a = User(name='user_a', email='user_a@example.com', email_confirmed=1,
            is_paid=1, stripe_plan_id="mltshp-double")
        user_a.set_password('asdfasdf')
        user_a.save()
        self.sign_in('user_a', 'asdfasdf')

        response = self.fetch_url('/shake/create')
        self.assertEqual(response.code, 200)

    def test_rss_feed_works(self):
        """
        Testing that the RSS feed works.
        """
        self.user.stripe_plan_id = "mltshp-double"
        self.user.save()

        arguments = {
            'name' : 'yo',
            'description' : 'My little corner of the world',
            'title' : 'title'
        }
        response = self.post_url('/shake/create', arguments=arguments)
        s = Shake.get('name=%s', 'yo')
        #create a shared file and source file
        sourcefile = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        sourcefile.save()
        sharedfile = Sharedfile(source_id=sourcefile.id, name="the name",user_id=self.user.id, \
            content_type="image/png", description="description", source_url="https://www.mltshp.com/?hi")
        sharedfile.save()
        sharedfile.share_key = lib.utilities.base36encode(sharedfile.id)
        sharedfile.save()
        sharedfile.add_to_shake(s)

        #create a shared file video
        x = json_encode(
                {"provider_url": "https://www.youtube.com/",
                "version": "1.0",
                "title": "YouTube iFrame Embed Option",
                "type": "video",
                "thumbnail_width": 480,
                "height": 334,
                "width": 550,
                "html":
                "<iframe class=\"youtube-player\" type=\"text/html\" width=\"550\" height=\"334\" src=\"https://www.youtube.com/embed/NtzDtV2Jbk8?rnd=0.277468004525&autoplay=0\" frameborder=\"0\" id=\"ytframe\"></iframe>",
                "author_name": "jameslawsonsmith",
                "provider_name": "YouTube",
                "thumbnail_url": "http://i3.ytimg.com/vi/NtzDtV2Jbk8/hqdefault.jpg",
                "thumbnail_height": 360,
                "author_url": "https://www.youtube.com/user/jameslawsonsmith"})
        sourcefile = Sourcefile(width=480,height=620,file_key="qwer",thumb_key="qwer_t", type="link", data=x)
        sourcefile.save()
        sharedfile = Sharedfile(source_id=sourcefile.id, name="another name", user_id=self.user.id, \
            content_type="text/html", description="description", source_url="https://www.youtube.com/watch?v=EmcMG4uxiHk")
        sharedfile.save()
        sharedfile.share_key = lib.utilities.base36encode(sharedfile.id)
        sharedfile.save()
        sharedfile.add_to_shake(s)

        response = self.fetch_url('/shake/yo/rss')
        self.assertEqual(response.headers['Content-Type'], 'application/xml')
        parsed_xml = lib.utilities.parse_xml(response.body)
        self.assertEqual(parsed_xml['rss']['channel']['item']['link'], 'https://mltshp.com/p/1')

    def test_creating_group_shake_creates_subscription(self):
        """
        Create a shake for user admin. Admin should now have a subscription to that shake
        """
        self.user.stripe_plan_id = "mltshp-double"
        self.user.save()

        arguments = {
            'name' : 'yo',
            'description' : 'My little corner of the world',
            'title' : 'title'
        }
        self.post_url('/shake/create', arguments=arguments)
        sh = Shake.get('name=%s', arguments['name'])

        sub = Subscription.get('user_id=%s and shake_id=%s and deleted = 0', self.user.id, sh.id)
        self.assertTrue(sub)

    def test_created_shake_contains_file(self):
        """
        This test creates three users. User A creates a shake (asdf) and adds a file to it.
        User B follows User A
        User C follows User A
        User B follows User A's shake (asdf)

        Getting shared files for B sees file.
        Getting shared files for C does not see file.
        Getting shared files for A does not see file.
        """
        user_a = User(name='user_a', email='user_a@example.com', email_confirmed=1, is_paid=1, stripe_plan_id="mltshp-double")
        user_a.set_password('asdfasdf')
        user_a.save()
        user_b = User(name='user_b', email='user_b@example.com', email_confirmed=1, is_paid=1)
        user_b.set_password('asdfasdf')
        user_b.save()
        user_c = User(name='user_c', email='user_c@example.com', email_confirmed=1, is_paid=1)
        user_c.set_password('asdfasdf')
        user_c.save()

        self.sign_in('user_a', 'asdfasdf')
        arguments = {
            'name' : 'asdf',
            'description' : 'A shake test.',
            'title' : 'Shake Test',

        }
        self.post_url('/shake/create', arguments=arguments)

        self.sign_in('user_b', 'asdfasdf')
        shake = Shake.get('name = %s', 'asdf')
        self.post_url('/shake/%s/subscribe?json=1' % shake.id)

        #create a shared file and source file
        sourcefile = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        sourcefile.save()
        sharedfile = Sharedfile(source_id=sourcefile.id, name="the name",user_id=user_a.id, \
            content_type="image/png", description="description", source_url="https://www.mltshp.com/?hi")
        sharedfile.save()
        sharedfile.share_key = lib.utilities.base36encode(sharedfile.id)
        sharedfile.save()

        new_shake = Shake.get('name=%s', 'asdf')

        sharedfile.add_to_shake(new_shake)

        shared_files = Sharedfile.from_subscriptions(user_b.id)

        self.assertEqual(len(shared_files), 1)
        self.assertEqual(shared_files[0].user_id, user_a.id)

        #contains one sub to their created shake
        self.assertEqual(len(Sharedfile.from_subscriptions(user_a.id)), 1)
        self.assertEqual(len(Sharedfile.from_subscriptions(user_c.id)), 0)

