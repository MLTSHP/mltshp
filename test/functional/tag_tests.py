import json
from urllib.parse import urlparse

import test.base
import lib.utilities
from models import User, Sourcefile, Sharedfile, Tag, TagSharedfile

class TagTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(TagTests, self).setUp()
        # uploader
        self.admin = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()

        # saver
        self.bob = User(name='bob', email='bob@mltshp.com', email_confirmed=1, is_paid=1)
        self.bob.set_password('asdfasdf')
        self.bob.save()
        
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
            source_url="https://www.mltshp.com/?hi")
        sharedfile.save()
        sharedfile.share_key = lib.utilities.base36encode(sharedfile.id)
        sharedfile.save()
        return sharedfile
    
    def test_create_tag_for_sf_creates_new_tag(self):
        self.sign_in('admin', 'asdfasdf')
        response = self.post_url('/p/%s/create_tag' % self.sharedfile.share_key, {'tag':'asdf'})
        
        all_tags = Tag.all()
        all_tag_shared_files = TagSharedfile.all()
        
        self.assertTrue(len(all_tags) == 1)
        self.assertTrue(all_tags[0].name == 'asdf')
        self.assertTrue(len(all_tag_shared_files) == 1)
        self.assertTrue(all_tag_shared_files[0].sharedfile_id == self.sharedfile.id)
        
    def test_not_signedin_user_cant_creat_tag(self):
        self.sign_in('bob', 'asdfasdf')
        response = self.post_url('/p/%s/create_tag' % self.sharedfile.share_key, {'tag':'asdf'})
        

        print(self.response.code)
        
        all_tags = Tag.all()
        all_tag_shared_files = TagSharedfile.all()
        
        self.assertTrue(len(all_tags) == 0)
        self.assertTrue(len(all_tag_shared_files) == 0)
        
    def test_delete_tag_for_sf(self):
        self.sign_in('admin', 'asdfasdf')
        self.post_url('/p/%s/create_tag' % self.sharedfile.share_key, {'tag':'asdf'})
        
        response = self.post_url('/p/%s/delete_tag' % self.sharedfile.share_key, {'tag':'asdf'})
        
        all_tags = Tag.all()
        all_tag_shared_files = TagSharedfile.all()
        
        self.assertTrue(len(all_tags) == 1)
        self.assertTrue(all_tags[0].name == 'asdf')
        self.assertTrue(len(all_tag_shared_files) == 1)
        self.assertTrue(all_tag_shared_files[0].sharedfile_id == self.sharedfile.id)

    def test_saving_file_carries_over_tags(self):
        self.sign_in('admin', 'asdfasdf')
        self.post_url('/p/%s/create_tag' % self.sharedfile.share_key, {'tag':'asdf'})
        self.post_url('/p/%s/create_tag' % self.sharedfile.share_key, {'tag':'qwer'})
        
        self.sign_in('bob', 'asdfasdf')
        
