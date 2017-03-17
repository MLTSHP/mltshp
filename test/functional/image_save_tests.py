import json
from urlparse import urlparse

import test.base
import lib.utilities
from models import User, Sourcefile, Sharedfile, Notification, Shakesharedfile, Post

class ImageSaveTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(ImageSaveTests, self).setUp()
        # uploader
        self.admin = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()

        # saver
        self.bob = User(name='bob', email='bob@mltshp.com', email_confirmed=1)
        self.bob.set_password('asdfasdf')
        self.bob.save()

        # saver
        self.tom = User(name='tom', email='tom@mltshp.com', email_confirmed=1)
        self.tom.set_password('asdfasdf')
        self.tom.save()

        # unconfirmed user
        self.jim = User(name='jim', email='jim@mltshp.com', email_confirmed=0)
        self.jim.set_password('asdfasdf')
        self.jim.save()
        
        # uploader's file.
        self.sharedfile = self._create_sharedfile(self.admin)

    def _create_sharedfile(self, user):
        """
        Utility to create a stub sharedfile for the user.
        """
        sourcefile = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        sourcefile.save()
        sharedfile = Sharedfile(source_id=sourcefile.id, name="the name",user_id=user.id, \
            content_type="image/png", title='the title', description="the description", \
            source_url="http://www.mltshp.com/?hi")
        sharedfile.save()
        sharedfile.share_key = lib.utilities.base36encode(sharedfile.id)
        sharedfile.save()
        return sharedfile
    
    def test_non_authenticated_save_returns_403(self):
        response = self.post_url('/p/%s/save' % self.sharedfile.share_key)
        self.assertEqual(403, response.code)
    
    def test_saving_non_existant_file_returns_404(self):
        self.sign_in('bob', 'asdfasdf')
        response = self.post_url('/p/admin3000/save')
        self.assertEqual(404, response.code)
    
    def test_saving_file_response(self):
        """
        Saving a file should redirect to the new file URL, unless json=1 is 
        passed in. In which case response should contain original share_key,
        new_share_key and count.
        
        Test is a bit fragile because it assume we only have only the original
        shared file to start.
        """
        self.sign_in('bob', 'asdfasdf')
        response = self.post_url('/p/%s/save' % self.sharedfile.share_key)
        self.assertEqual(200, response.code)        
        self.assertEqual('/p/2', urlparse(response.effective_url).path)
        
        arguments = {'json' : 1}
        response = self.post_url('/p/%s/save' % self.sharedfile.share_key, arguments=arguments)
        self.assertEqual(200, response.code)
        json_response = json.loads(response.body)
        # because previous save still exists, id should be 3 and count should be 2.
        self.assertEqual('3', json_response['new_share_key'])
        self.assertEqual(self.sharedfile.share_key, json_response['share_key'])
        self.assertEqual(2, json_response['count'])
    
    def test_saving_original_file_populates_parent_id_original_id_correctly(self):
        """
        Bob should be able to save admin's original file.  The parent_id should
        point to admin's file and so should original_id.
        
        Tom can save bob's file.  Tom's parent_id will be bobs file, while the
        original id will be admin's file.
        """
        #bob saves admin's original file
        self.sign_in("bob", "asdfasdf")
        response = self.post_url('/p/%s/save' % self.sharedfile.share_key)
        
        #bob's saves file points to admin's shared file as the parent and admin's shared file as the original id
        bobs_file = Sharedfile.get("share_key= %s and user_id = %s", 2, self.bob.id)        
        self.assertEqual(bobs_file.parent_id, self.sharedfile.id)
        self.assertEqual(bobs_file.original_id, self.sharedfile.id)
        
        #tom saves bob's file
        self.sign_in("tom", "asdfasdf")
        response = self.post_url('/p/%s/save' % bobs_file.share_key)
        
        #tom's saves file points to bob's as the parent and admin's shared file as the original id
        toms_file = Sharedfile.get("share_key=%s and user_id = %s", 3, self.tom.id)
        self.assertEqual(toms_file.parent_id, bobs_file.id)
        self.assertEqual(toms_file.original_id, self.sharedfile.id)

    def test_saving_file_creates_shakesharedfile(self):
        """
        When bob saves admin's original file, an entry gets created in Shakesharedfile.
        
        We assume file that gets saved has id of 2.
        """
        self.sign_in("bob", "asdfasdf")
        self.post_url('/p/%s/save' % self.sharedfile.id)
        bob_shake = self.bob.shake()
        ssf = Shakesharedfile.where('shake_id = %s', bob_shake.id)
        self.assertEqual(1, len(ssf))
        self.assertEqual(2, ssf[0].sharedfile_id)

    def test_saving_file_creates_post_for_user(self):
        """
        When bob saves admin's original file, an entry gets created Post with
        bob's user id.
        """
        self.sign_in("bob", "asdfasdf")
        self.post_url('/p/%s/save' % self.sharedfile.id)
        posts = Post.where('user_id = %s', self.bob.id)
        self.assertEqual(1, len(posts))
        self.assertTrue(posts[0].seen)
        self.assertEqual(2, posts[0].sharedfile_id)
        self.assertEqual(1, posts[0].sourcefile_id)

    def test_saving_file_creates_notification_for_user(self):
        """
        When bob saves admin's original file, a entry gets created in Notification
        table with following attributes:

        - bob should be the sender_id
        - admin the receiver id
        - and action_id should point to sharedfile
        - type should be save
        """
        self.sign_in("bob", "asdfasdf")
        self.post_url('/p/%s/save' % self.sharedfile.id)
        notifications = Notification.all()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].sender_id, self.bob.id)
        self.assertEqual(notifications[0].receiver_id, self.admin.id)
        self.assertEqual(notifications[0].action_id, self.sharedfile.id)
        self.assertEqual(notifications[0].type, 'save')
        
    def test_saving_file_copies_title_and_source_url_and_description(self):
        """
        Saving sharedfile should transfer over the title, description and source fields.
        
        Assume only one file to begin with.
        """
        sid = self.sign_in("bob", "asdfasdf")
        self.post_url('/p/%s/save' % self.sharedfile.id)
        sharedfile = Sharedfile.get("share_key = %s and user_id = %s", 2, self.bob.id)
        self.assertEqual(sharedfile.source_url, 'http://www.mltshp.com/?hi')
        self.assertEqual(sharedfile.title, 'the title')
        self.assertEqual(sharedfile.description, 'the description')

