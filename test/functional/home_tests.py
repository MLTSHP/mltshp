import random

import test.base
import test.factories
from models import User, Sourcefile, Sharedfile, Shakesharedfile, Bookmark
from lib.utilities import base36encode

class HomeTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(HomeTests, self).setUp()
        self.admin = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()
        self.sign_in('admin', 'asdfasdf')

    def test_not_logged_in(self):
        """
        Should be no error when accessing home page when not logged in.
        MLTSHP splash page should show.
        """
        self.sign_out()
        response = self.fetch_url('/')
        self.assertEqual(200, response.code)
        self.assertTrue(response.body.find('Save, Share &amp;&nbsp;Discover') > -1)

    def test_home_page_no_sharedfiles(self):
        """
        Accessing friend page with no files
        - Should not error.
        - No bookmarks should be created.
        - Introduction to mltshp should show.
        """
        response = self.fetch_url('/friends')
        self.assertEqual(200, response.code)
        self.assertEqual(0, len(Bookmark.all()))

    def test_home_page_with_friends(self):
        """
        Creates ten users, user 1 follows five of them, each user uploads a file,
        result from hitting /friends will return five files.

        When we go to friends for first time, bookmark will be set. If done multiple times,
        still will only have one bookmark if no files have been uploaded between visits.
        """
        for x in range(10):
            user = User(name='test%s' % (x), email='test%s@example.com' % (x), email_confirmed=1, is_paid=1)
            user.save()
            sf = test.factories.sharedfile(user)
            sf.add_to_shake(user.shake())
            if (x % 2) == 0:
                self.admin.subscribe(user.shake())

        ssf = Shakesharedfile.all()
        self.assertEqual(len(ssf), 10)
        self.assertEqual(len(self.admin.sharedfiles_from_subscriptions()), 5)

        response = self.fetch_url('/friends')
        self.assertEqual(response.code, 200)
        self.assertEqual(1, len(Bookmark.all()))

        response = self.fetch_url('/friends')
        self.assertEqual(response.code, 200)
        self.assertEqual(1, len(Bookmark.all()))


    def test_paginating_home_stream(self):
        """
        Test going back and forward in the timeline using /before/{share_key}
        and /after/{share_key} addresses.

        We create new user (user2), which admin subscribes to. They create
        15 files, and then we have admin user go backwards and forward in his stream.
        We check the stream for correctness by checking for presence of sharefile
        titles that appear on the page.
        """
        user = User(name='user2', email='user2@example.com', email_confirmed=1, is_paid=1)
        user.save()
        self.admin.subscribe(user.shake())

        saved_files = []
        for x in range(15):
            sf = test.factories.sharedfile(user)
            sf.add_to_shake(user.shake())
            saved_files.append(sf)

        response = self.fetch_url('/before/%s' % saved_files[5].share_key)
        self.assertEqual(response.code, 200)
        self.assertTrue(response.body.find('sharedfile_0.png'))
        self.assertTrue(response.body.find('sharedfile_1.png'))
        self.assertTrue(response.body.find('sharedfile_2.png'))
        self.assertTrue(response.body.find('sharedfile_3.png'))
        self.assertTrue(response.body.find('sharedfile_4.png'))
        self.assertTrue(response.body.find('sharedfile_5.png'))
        self.assertEqual(-1, response.body.find('sharedfile_6.png'))
        response = self.fetch_url('/after/%s' % saved_files[10].share_key)
        self.assertEqual(response.code, 200)
        self.assertTrue(response.body.find('sharedfile_11.png'))
        self.assertTrue(response.body.find('sharedfile_12.png'))
        self.assertTrue(response.body.find('sharedfile_13.png'))
        self.assertTrue(response.body.find('sharedfile_14.png'))
        self.assertEqual(-1, response.body.find('sharedfile_10.png'))

    def test_home_page_non_user_request(self):
        """
        Safari, Firefox and other browsers like to fetch pages to create
        preview images (i.e. Safari's Top Sites) feature.  Or prefetch
        for speeding up future render times. When we can detect that
        the request is not user-intiated, we want to make sure
        we don't set any bookmarks for the user.

        When a browser bot accesses the home page, no bookmarks should be
        set.
        """
        user = User(name='user2', email='user2@example.com', email_confirmed=1, is_paid=1)
        user.save()
        self.admin.subscribe(user.shake())

        saved_files = []
        for x in range(5):
            sf = test.factories.sharedfile(user)
            sf.add_to_shake(user.shake())
            saved_files.append(sf)

        response = self.fetch_url('/friends', headers={"X-Purpose": "preview"})
        self.assertEqual(response.code, 200)
        self.assertEqual(0, len(Bookmark.all()))

        response = self.fetch_url('/friends', headers={"X-Moz": "prefetch"})
        self.assertEqual(response.code, 200)
        self.assertEqual(0, len(Bookmark.all()))

        response = self.fetch_url('/friends', )
        self.assertEqual(response.code, 200)
        self.assertEqual(1, len(Bookmark.all()))



