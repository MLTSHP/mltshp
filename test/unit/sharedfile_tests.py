from models import Sharedfile, Sourcefile, User, Comment, Conversation, Shake, Shakesharedfile, Favorite, NSFWLog, Tag, TaggedFile
from datetime import datetime, timedelta
import os, shutil, calendar
from base import BaseTestCase

class SharedfileModelTests(BaseTestCase):

    def setUp(self):
        """
        Create a user sourcefile and sharedfile to work with.
        """
        super(SharedfileModelTests, self).setUp() # register connection.
        self.user = User(name='thename',email='theemail@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        self.user.set_password('pass')
        self.user.save()
        self.sourcefile = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        self.sourcefile.save()
        self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="1", description="some\ndescription\nhere", source_url="http://www.mltshp.com/?hi")
        self.sharedfile.save()

    def test_file_size_is_saved_in_newly_uploaded_file(self):
        """
        Tests that a brand new file upload saves the file size
        """
        file_name = '1.png'
        file_content_type = 'image/png'
        file_path = os.path.abspath("test/files/1.png")
        file_sha1 = Sourcefile.get_sha1_file_key(file_path)
        file_size = os.path.getsize(file_path)

        sf = Sharedfile.create_from_file(
            file_path = file_path,
            file_name = file_name,
            sha1_value = file_sha1,
            content_type = file_content_type,
            user_id = self.user.id)
        self.assertEqual(sf.size, 69)

    def test_file_size_is_not_saved_in_a_simple_share(self):
        """
        Tests that just saving a file does not create a file size record
        """
        new_user = User(name='newguy',email='newguy@example.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        new_user.set_password('pass')
        new_user.save()

        new_sharedfile = self.sharedfile.save_to_shake(new_user)
        self.assertEqual(new_sharedfile.size, 0)

    def test_attributes_are_saved(self):
        """
        Just a test to check that description and source-url are being saved.
        """
        sf = Sharedfile.get('id=1')
        self.assertEqual(sf.description, "some\ndescription\nhere")
        self.assertEqual(sf.source_url, "http://www.mltshp.com/?hi")

    def test_can_save(self):
        """
        A Sharedfile not owned by the user should be be saveable.
        If a Sharedfile already belongs to user, should not be saveable.
        Sharedfile.can_save should return False when no user specified.
        """
        self.assertFalse(self.sharedfile.can_save(self.user))
        user = User(name='newuser',email='newemail@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        user.save()
        self.assertTrue(self.sharedfile.can_save(user))
        self.assertFalse(self.sharedfile.can_save(None))
        self.assertFalse(self.sharedfile.can_save())

    def test_can_delete(self):
        """
        A Sharedfile should only be deletable if belongs to the user.
        Sharedfile.can_delete should return False when no user specified.
        """
        new_user = User(name='thename',email='theemail@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        new_user.save()
        self.assertEqual(self.user.id, self.sharedfile.user_id)
        self.assertTrue(self.sharedfile.can_delete(self.user))
        self.assertFalse(self.sharedfile.can_delete(new_user))
        self.assertFalse(self.sharedfile.can_delete(None))
        self.assertFalse(self.sharedfile.can_delete())

    def test_can_favor(self):
        """
        A Sharedfile is favorable if it doesn't belong to the user and
        it has not been favorited in the past.
        Sharedfile.can_save should return False when no user specified.
        """
        self.assertFalse(self.sharedfile.can_favor(self.user))

        # Create a new shared file that doesn't belong to user.
        new_user = User(name='new_email',email='new_email_address@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        new_user.save()
        self.assertTrue(self.sharedfile.can_favor(new_user))
        new_user.add_favorite(self.sharedfile)
        self.assertFalse(self.sharedfile.can_favor(new_user))

        self.assertFalse(self.sharedfile.can_favor(None))
        self.assertFalse(self.sharedfile.can_favor())

    def test_can_unfavor(self):
        """
        Sharedfile.can_unfavor only if the Sharedfile is already favorited.

        Should return False if no user is passed in, or never been favorited
        in the first place.
        """
        # Create a new shared file that doesn't belong to user.
        new_user = User(name='new_email',email='new_email_address@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        new_user.save()
        self.assertFalse(self.sharedfile.can_unfavor(new_user))
        new_user.add_favorite(self.sharedfile)
        self.assertTrue(self.sharedfile.can_unfavor(new_user))

        self.assertFalse(self.sharedfile.can_unfavor(None))
        self.assertFalse(self.sharedfile.can_unfavor())

    def test_can_edit(self):
        """
        Sharedfile.can_edit should return True only if Sharedfile belongs to user

        Should return false if no user is passed in.
        """
        self.assertEqual(self.sharedfile.user_id, self.user.id)
        self.assertTrue(self.sharedfile.can_edit(self.user))
        new_user = User(name='new_email',email='new_email_address@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        new_user.save()
        self.assertFalse(self.sharedfile.can_edit(new_user))

        self.assertFalse(self.sharedfile.can_edit(None))
        self.assertFalse(self.sharedfile.can_edit())


    def test_save_file_to_user(self):
        """
        When saving file to another user, it creates an exact copy of sharedfile with following conditions:

         * id, user_id and share_key will be different.
         * name, content_type and source_id should be the same.
         * parent_id should point to original sharedfile's id
         * original_id should point to the shared file id if it was 0 (in this case it is)
         * user id of new file should belong to new user.

        Returns an instance of the new shared file.
        """
        user = User(name='newuser',email='newemail@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        user.save()
        new_file = self.sharedfile.save_to_shake(user)

        # make sure id is not None, meaning it's saved.
        self.assertNotEqual(new_file.id, None)

        # id is not the same as old id (pretty impossible)
        self.assertNotEqual(new_file.id, self.sharedfile.id)
        self.assertNotEqual(new_file.share_key, self.sharedfile.share_key)

        # original_id should be the id of the share it was saved from
        # since that was the original share
        self.assertEqual(new_file.original_id, self.sharedfile.id)

        # User id of new file should be user id of user it's saved to.
        self.assertEqual(new_file.user_id, user.id)

        self.assertEqual(new_file.name, self.sharedfile.name)
        self.assertEqual(new_file.content_type, self.sharedfile.content_type)
        self.assertEqual(new_file.source_id, self.sharedfile.source_id)

        # parent_shared_file_id should point to original
        self.assertEqual(new_file.parent_id, self.sharedfile.id)

        #final test, a share of a share needs to still point to original_id of the first share
        user = User(name='anotheruser',email='another@example.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        user.save()
        newer_file = new_file.save_to_shake(user)

        self.assertEqual(newer_file.parent_id, new_file.id)
        self.assertEqual(newer_file.original_id, self.sharedfile.id)

    def test_parent(self):
        new_sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="another_share_key", parent_id=self.sharedfile.id)
        new_sharedfile.save()
        parent = new_sharedfile.parent()
        self.assertEqual(parent.id, self.sharedfile.id)

    def test_parent_user(self):
        """
        Creates new user and sharedfile, pointing to the sharedfile in setUp.
        """
        user = User(name='anewusername',email='anewuser@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        user.save()
        new_sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=user.id, \
            content_type="image/png", share_key="another_share_key", parent_id=self.sharedfile.id)
        new_sharedfile.save()
        parent_user = new_sharedfile.parent_user()
        self.assertEqual(parent_user.id, self.sharedfile.user_id)

    def test_source_file(self):
        """
        The Sourcefile object returned should match the one we associated.
        """
        fetched_sourcefile = self.sharedfile.sourcefile()
        self.assertEqual(fetched_sourcefile.id, self.sourcefile.id)

    def test_user(self):
        """
        The User object returned should match the one we associated.
        """
        fetched_user = self.sharedfile.user()
        self.assertEqual(fetched_user.id, self.user.id)

    def test_get_by_share_key(self):
        """
        The Sharedfile object should match the object with the same share_key created in setUp.
        """
        fetched_sharedfile = Sharedfile.get_by_share_key("1")
        self.assertEqual(fetched_sharedfile.id, self.sharedfile.id)

    def test_get_by_share_key_deleted(self):
        """
        If sharedfile is deleted should not be returned by get_by_share_key().
        """
        self.sharedfile.delete()
        fetched_sharedfile = Sharedfile.get_by_share_key("ok")
        self.assertEqual(fetched_sharedfile, None)

    def test_saving_sets_the_created_and_updated_at(self):
        """
        When we saved sharedfile, it's created and updated_at should be set in UTC.
        We check the date to make sure it's within last 5 seconds.
        """
        created_at =  self.sharedfile.created_at
        updated_at = self.sharedfile.updated_at
        five_seconds = timedelta(seconds=5)
        if (datetime.utcnow() - created_at) < five_seconds:
            created_at_is_recent = True
        else:
            created_at_is_recent = False
        self.assertTrue(created_at_is_recent)

        if (datetime.utcnow() - updated_at) < five_seconds:
            modified_at_is_recent = True
        else:
            modified_at_is_recent = False
        self.assertTrue(created_at_is_recent)

    def test_incoming(self):
        """
        Sharedfile.incoming should return only last 10 added sharedfiles.
        """
        # Adding 50 sharedfiles.
        for i in range(50):
            share_key = "%s" % i
            self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
                content_type="image/png", share_key=share_key)
            self.sharedfile.save()

        # should have 26 including file created in setUp.
        all_files = Sharedfile.all()
        self.assertEqual(len(all_files), 51)

        # only returns 10.
        incoming = Sharedfile.incoming()
        self.assertEqual(len(incoming), 10)

        # in order of last added -- biggest id to smallest
        last_seen = None
        for incoming_file in incoming:
            if not last_seen:
                last_seen = incoming_file.id
                continue
            if incoming_file.id < last_seen:
                less_then = True
            else:
                less_then = False
            self.assertTrue(less_then)

    def test_incoming_doesnt_include_deleted(self):
        """
        Sharedfile.incoming should should not return any deleted files.
        """
        self.assertEqual(len(Sharedfile.incoming()), 1)
        self.sharedfile.delete()
        self.assertEqual(len(Sharedfile.incoming()), 0)

    def test_incoming_doesnt_include_nsfw_users(self):
        """
        Sharedfile.incoming should not return files from users marked nsfw
        """
        # Adding 10 sharedfiles.
        for i in range(10):
            share_key = "%s" % i
            self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
                content_type="image/png", share_key=share_key)
            self.sharedfile.save()


        self.user.nsfw = 1
        self.user.save()

        # should return 0
        incoming = Sharedfile.incoming()
        self.assertEqual(len(incoming), 0)

        self.user.nsfw = 0
        self.user.save()

        # should return 10
        incoming = Sharedfile.incoming()
        self.assertEqual(len(incoming), 10)

    def test_incoming_includes_nsfw_users_if_asked(self):
        """
        Sharedfile.incoming should NOT return files from users marked nsfw if the include_nsfw is True
        """
        # Adding 10 sharedfiles.
        for i in range(10):
            share_key = "%s" % i
            self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
                content_type="image/png", share_key=share_key)
            self.sharedfile.save()

        self.user.nsfw = 1
        self.user.save()

        # should return 10
        incoming = Sharedfile.incoming()
        self.assertEqual(len(incoming), 0)


    def test_delete(self):
        """
        A regular sharedfile created without deleted parameter specified (as in setUp)
        will have that flag set to 0.  Calling delete() changes flag to 1 and persists to DB.
        """
        self.assertEqual(self.sharedfile.deleted, 0)
        self.sharedfile.delete()
        self.assertEqual(self.sharedfile.deleted, 1)
        fetched_sharedfile = Sharedfile.get("id= %s", self.sharedfile.id)
        self.assertEqual(fetched_sharedfile.deleted, 1)

    def test_deleting_sharedfile_also_mutes_conversations(self):
        new_comment = Comment(user_id=self.user.id, sharedfile_id=self.sharedfile.id)
        new_comment.save()
        self.sharedfile.delete()

        muted_conversation = Conversation.get('user_id=%s and sharedfile_id=%s and muted = 1', self.user.id, self.sharedfile.id)
        self.assertTrue(muted_conversation)

    def test_sharedfile_from_existing_file(self):
        test_files = os.path.join(os.path.dirname(os.path.dirname(__file__)), "files")
        file_key = Sourcefile.get_sha1_file_key(test_files + "/1.png")
        shutil.copyfile("%s/1.png" % (test_files), "/tmp/%s" % (file_key))

        shared_file1 = Sharedfile.create_from_file("/tmp/%s" % (file_key),"1.png", file_key, "image/png", self.user.id)
        shared_file2 = Sharedfile.create_from_file("/tmp/%s" % (file_key),"1.png", file_key, "image/png", self.user.id)

        self.assertEqual(shared_file1.source_id, shared_file2.source_id)

    def test_sharedfile_from_new_file(self):
        test_files = os.path.join(os.path.dirname(os.path.dirname(__file__)), "files")
        file_key = Sourcefile.get_sha1_file_key(test_files + "/1.png")
        shutil.copyfile("%s/1.png" % (test_files), "/tmp/%s" % (file_key))
        shared_file = Sharedfile.create_from_file("/tmp/%s" % (file_key),"1.png", file_key, "image/png", self.user.id)
        self.assertEqual(shared_file.id, 2)
        self.assertEqual(shared_file.source_id, 2)

    def test_get_title(self):
        """
        If there is no title or title is blank, Sharedfile.get_title should return
        the name, otherwise returns title.

        if sans_quotes argument set to True, all quotes should be escaped. Off by default
        """
        self.assertEqual(self.sharedfile.title, None)
        self.assertEqual(self.sharedfile.get_title(), self.sharedfile.name)
        self.sharedfile.title = ''
        self.sharedfile.save()
        self.assertEqual(self.sharedfile.get_title(), self.sharedfile.name)
        self.sharedfile.title = 'New title'
        self.sharedfile.save()
        self.assertEqual(self.sharedfile.get_title(), 'New title')
        self.sharedfile.title = 'New "title" and "junk"'
        self.assertEqual(self.sharedfile.get_title(), 'New "title" and "junk"')
        self.assertEqual(self.sharedfile.get_title(sans_quotes=True), 'New &quot;title&quot; and &quot;junk&quot;')

    def test_calculate_view_count(self):
        """
        View count should return all views for an image, should not count
        user views as equal.
        """
        self.assertEqual(0, self.sharedfile.calculate_view_count())
        self.sharedfile.add_view()
        self.sharedfile.add_view()
        self.sharedfile.add_view()
        self.sharedfile.add_view(user_id=self.user.id)
        self.assertEqual(3, self.sharedfile.calculate_view_count())

    def test_save_count(self):
        """
        Should return a total count of direct saves of the images, combined with
        how many people saved the original (parent) sharedfile.

        A = self.sharedfile
        self.user = uploads A
        new_user = saves A, into B -- A: 1, b: 0
        new_user2 = saves B, into C -- A: 2, b: 1, c: 0
        new_user3 = saves C, into D -- A: 3, b: 1, c: 1
        """
        # Set up users we'll need.
        new_user = User(name='new_user',email='new_user@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        new_user.save()
        new_user2 = User(name='new_user_2',email='new_user2@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        new_user2.save()
        new_user3 = User(name='new_user_3',email='new_user3@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        new_user3.save()
        a = self.sharedfile
        self.assertEqual(0, a.save_count())
        b = a.save_to_shake(new_user)
        self.assertEqual(1, a.save_count())
        self.assertEqual(0, b.save_count())
        c = b.save_to_shake(new_user2)
        self.assertEqual(2, a.save_count())
        self.assertEqual(1, b.save_count())
        self.assertEqual(0, c.save_count())
        d = c.save_to_shake(new_user3)
        self.assertEqual(3, a.save_count())
        self.assertEqual(1, b.save_count())
        self.assertEqual(1, c.save_count())

    def test_favorites_for_user(self):
        """
        Returns favorites for user, sorted in reverse order of when they were added.

        TODO: test the before_id & after_id parameters.
        """
        new_user = User(name='new_user',email='new_user@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        new_user.save()
        another_sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="ok", description="some\ndescription\nhere", source_url="http://www.mltshp.com/?hi")
        another_sharedfile.save()

        #one favorite shared file
        new_user.add_favorite(self.sharedfile)
        new_user.add_favorite(another_sharedfile)

        #this should only return one, since we don't dupe source_ids
        sfs = Sharedfile.favorites_for_user(new_user.id)
        self.assertEqual(sfs[0].id, self.sharedfile.id)

        #but really, underneath we should have two favorites
        fs = Favorite.where('user_id = %s', new_user.id)

        self.assertEqual(2, len(fs))






    def test_sharedfile_saved_to_group_shake(self):
        test_files = os.path.join(os.path.dirname(os.path.dirname(__file__)), "files")
        file_key = Sourcefile.get_sha1_file_key(test_files + "/1.png")
        shutil.copyfile("%s/1.png" % (test_files), "/tmp/%s" % (file_key))

        #create a new shake
        group_shake = Shake(user_id=self.user.id, type='group', title='asdf', name='asdf')
        group_shake.save()

        a_shared_file = Sharedfile.create_from_file("/tmp/%s" % (file_key),"1.png", file_key, "image/png", self.user.id, group_shake.id)
        self.assertTrue(group_shake.can_update(self.user.id))

        a_shared_file.add_to_shake(self.user.shake())

        ssfs = Shakesharedfile.all()
        for ssf in ssfs:
            self.assertEqual(ssf.sharedfile_id, a_shared_file.id)

    def test_can_user_delete_from_shake(self):
        """
        A user can only delete from a shake if they are the owner of the sharedfile
        or the owner of the shake.
        """
        user_shake = self.user.shake()
        self.sharedfile.add_to_shake(user_shake)
        self.assertEqual(True, self.sharedfile.can_user_delete_from_shake(self.user, user_shake))

        # A user that doesn't own the sharedfile
        new_user = User(name='new_user',email='new_user@mltshp.com',verify_email_token='created', email_confirmed=0, is_paid=1)
        new_user.save()
        self.assertEqual(False, self.sharedfile.can_user_delete_from_shake(new_user, user_shake))

        # Owner of a group shake, but file doesn't belong to them.
        group_shake = Shake(user_id=new_user.id, type='group', title='Bears', name='bears')
        group_shake.save()
        self.sharedfile.add_to_shake(group_shake)
        self.assertEqual(True, self.sharedfile.can_user_delete_from_shake(new_user, group_shake))
        # owner of file, but not of shake.
        self.assertEqual(True, self.sharedfile.can_user_delete_from_shake(self.user, group_shake))


    def test_delete_from_shake(self):
        """
        Deleting a sharedfile from a shake sets the shakesharedfile 'deleted' to 1.

        Sharedfile.delete_from_shake retuns True if delete successful or False otherwise.
        """
        user_shake = self.user.shake()
        self.sharedfile.add_to_shake(user_shake)
        ssf = Shakesharedfile.get("sharedfile_id = %s", self.sharedfile.id)
        # original file is not deleted
        self.assertEqual(ssf.deleted, 0)
        # delete should work
        self.assertEqual(True, self.sharedfile.delete_from_shake(user_shake))
        ssf = Shakesharedfile.get("sharedfile_id = %s", self.sharedfile.id)
        self.assertEqual(ssf.deleted, 1)


    #def test_favorite_count(self):
    #    """
    #    Should return total favorite count for current image. Should not
    #    count removed favorites.
    #    """
    #    self.assertEqual(0, self.sharedfile.favorite_count())
    #    # Create some users to save images to.
    #    new_user = User(name='new_user',email='new_user@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
    #    new_user.save()
    #    new_user2 = User(name='new_user_2',email='new_user2@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
    #    new_user2.save()
    #    new_user.add_favorite(self.sharedfile)
    #    self.assertEqual(1, self.sharedfile.favorite_count())
    #    new_user2.add_favorite(self.sharedfile)
    #    self.assertEqual(2, self.sharedfile.favorite_count())
    #    new_user2.remove_favorite(self.sharedfile)
    #    self.assertEqual(1, self.sharedfile.favorite_count())

    def test_comment_count(self):
        """
        Comment count should return the number of comments belonging to
        shard file. Should not count deleted comments.
        """
        self.assertEqual(0, self.sharedfile.comment_count())
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.user.id, body="just a comment")
        comment.save()
        self.assertEqual(1, self.sharedfile.comment_count())
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.user.id, body="just a comment", deleted=True)
        comment.save()
        self.assertEqual(1, self.sharedfile.comment_count())

    def test_set_nsfw(self):
        """
        When a user flags an image as NSFW, a new NSFWLog entry is created with
        that user's id and sharedfile's id, with current timestamp.  The NSFW
        flag on the sharedfile's sourcefile also gets flipped to 1.
        """
        sourcefile = self.sharedfile.sourcefile()
        self.assertEqual(0, self.sourcefile.nsfw)
        self.assertEqual(0, len(NSFWLog.all()))
        self.sharedfile.set_nsfw(self.user)
        fetched_sf = Sharedfile.get("id = %s", self.sharedfile.id)
        fetched_source = fetched_sf.sourcefile()
        self.assertEqual(1, fetched_source.nsfw)
        self.assertEqual(1, len(NSFWLog.all()))
        log_entry = NSFWLog.all()[0]
        self.assertEqual(self.user.id, log_entry.user_id)
        self.assertEqual(self.sharedfile.id, log_entry.sharedfile_id)
        self.assertEqual(fetched_source.id, log_entry.sourcefile_id)
        self.assertTrue(log_entry.created_at - datetime.utcnow() <= timedelta(seconds=2))


    def test_as_json_with_user_context(self):
        """
        as_json should return the correct 'saved' and 'liked' flags
        if user_context is provided.
        """
        new_user = User(name='newuser', email='newuser@mltshp.com', verify_email_token='created', email_confirmed=0, is_paid=1)
        new_user.save()
        sf_dict = self.sharedfile.as_json(user_context=new_user)
        self.assertEqual(False, sf_dict['saved'])
        self.assertEqual(False, sf_dict['liked'])

        self.sharedfile.save_to_shake(new_user)
        sf_dict = self.sharedfile.as_json(user_context=new_user)
        self.assertEqual(True, sf_dict['saved'])
        self.assertEqual(False, sf_dict['liked'])

        new_user.add_favorite(self.sharedfile)
        sf_dict = self.sharedfile.as_json(user_context=new_user)
        self.assertEqual(True, sf_dict['saved'])
        self.assertEqual(True, sf_dict['liked'])


    def test_likers_list(self):
        """
        Tests that likers are returned. Should not include deleted likers.
        """
        pass

    def test_save_count(self):
        """
        Tests that people who saved it are returned. Should not included deleted saves.
        """
        pass

    def test_tag_search(self):
        self.sharedfile.description = """#here #is some #tags that I got for #you. 
            #here is another word that #is not to be duplicated."""
        tags = self.sharedfile.find_tags()
        self.assertEqual(tags, set(['is', 'you', 'here', 'tags']))

    def test_tags_are_not_too_long(self):
        self.sharedfile.description = """#asdfasdfasdfasdfasdf is twenty and 
        this is 21 #asdfasdfasdfasdfasdfz and this is 22 #asdfasdfasdfasdfasdfxx"""
        tags = self.sharedfile.find_tags()
        self.assertEqual(tags, set(['asdfasdfasdfasdfasdf']))

    def test_tags_dont_find_urls(self):
        self.sharedfile.description = """#cool Some descriptions have urls in them like
            this one here http://cnn.com/#bad and this 
            http://www.cnn.com/?canada#worse #great?"""
        tags = self.sharedfile.find_tags()
        self.assertEqual(tags, set(['cool', 'great']))

    def test_tags_dont_include_nonchars(self):
        self.sharedfile.description = """#cool-bad #cool-good 
            #cool #cool?dunno 234238273#238023osidjf waht e#e can I do? i dunno
            """
        tags = self.sharedfile.find_tags()
        self.assertEqual(tags, set(['cool']))
        
    def test_tags_dont_exist(self):
        self.sharedfile.description = """234238273#238023osidjf e#e 
        https://twitter.com/#!/jJIe 
            """
        tags = self.sharedfile.find_tags()
        self.assertEqual(tags, set([]))

    def test_tags_created_on_save(self):
        self.sharedfile.description = """#here #is some #tags that I got for #you. 
            #here is another word that #is not to be duplicated."""

        self.sharedfile.save()
        tags = Tag.all()
        for tag in tags:
            self.assertTrue(tag.name in ['is', 'you', 'here', 'tags'])

    def test_tags_assigned_on_save(self):
        self.sharedfile.description = """#here #is some #tags that I got for #you. 
            #here is another word that #is not to be duplicated."""

        self.sharedfile.save()

        tags = self.sharedfile.tags()
        for tag in tags:
            self.assertTrue(tag.name in ['is', 'you', 'here', 'tags'])

        
    def test_tags_become_deleted_on_overwrite(self):
        #create a file with tags
        self.sharedfile.description = """#here #is some #tags that I got for #you. 
            #here is another word that #is not to be duplicated."""
        self.sharedfile.save()

        #load the file back up and change the description
        self.sharedfile = Sharedfile.get("id = %s", self.sharedfile.id)
        self.sharedfile.description = "some #all #newtags #not #old"
        self.sharedfile.save()

        #save the file and check that the new tags are only returned
        tags = self.sharedfile.tags()
        for tf in tags:
            self.assertTrue(tf.name in ['all', 'newtags', 'not', 'old'])

        #load the deleted tags and check that they are the same as the original
        tagged_files = TaggedFile.where("deleted = 1")
        for tf in tagged_files:
            t = Tag.get('id = %s', tf.tag_id)
            self.assertTrue(t.name in ['here', 'is', 'tags', 'you'])


    def test_tags_completely_disappear_on_clearing(self):
        #create a new sharedfile
        #set the description with tags
        self.sharedfile.description = """#here #is some #tags that I got for #you. 
            #here is another word that #is not to be duplicated."""
        self.sharedfile.save()
        
        #set a new description that has no tags
        self.sharedfile.description = "I have no tags."
        self.sharedfile.save()

        #verify tags() is empty.
        tags = self.sharedfile.tags()
        self.assertEqual(tags, [])

        #verify the original tags are all deleted=1
        tagged_files = TaggedFile.all()
        for tf in tagged_files:
            self.assertEqual(tf.deleted, 1)

    def test_tags_with_numbers_are_created(self):
        self.sharedfile.description = """#here1 #is2 some #tags3 that I got for #you4. 
            #here1 is another word that #is2 not to be duplicated."""

        self.sharedfile.save()
        tags = self.sharedfile.tags()
        for tag in tags:
            self.assertTrue(tag.name in ['is2', 'you4', 'here1', 'tags3'])


    def test_tags_with_different_case(self):
        self.sharedfile.description = """This #TAG should only appear #tag once in
        this #tAg list and also #YES1YES #yes1yes."""

        self.sharedfile.save()
        tags = self.sharedfile.tags()
        for tag in tags:
            self.assertTrue(tag.name in ['tag', 'yes1yes'])
        
    def test_saving_a_file_from_someone_doesnt_run_tagging(self):
        self.sharedfile.description = """This #TAG should only appear #tag once in
            this #tAg list and also #YES1YES #yes1yes."""
        self.sharedfile.save(ignore_tags=True)

        self.assertEqual([], self.sharedfile.tags())

    def test_deleting_shared_file_deletes_tags(self):
        self.sharedfile.description = """#here1 #is2 some #tags3 that I got for #you4. 
            #here1 is another word that #is2 not to be duplicated."""
        self.sharedfile.save()

        self.sharedfile.delete()

        tf = TaggedFile.all()
        for t in tf:
            self.assertEqual(t.deleted, 1)
