from models import User, Sharedfile, Sourcefile, Shake, Favorite, invitation, Shakesharedfile, Subscription, ShakeManager
from base import BaseTestCase
import random, os, calendar
from datetime import datetime
from tornado.options import options

class UserModelTests(BaseTestCase):

    def setUp(self):
        """
        Create a user, a source file and a shared file to user in tests.
        """
        super(UserModelTests, self).setUp()
        self.user = User(name='example',email='example@example.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        self.user.save()
        self.sourcefile = Sourcefile(width=20,height=20,file_key="asdf", \
            thumb_key="asdf_t")
        self.sourcefile.save()
        self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file", \
            user_id=self.user.id, content_type="image/png", share_key="ok")
        self.sharedfile.save()
        self.user_shake = self.user.shake()
        self.sharedfile.add_to_shake(self.user_shake)

    def test_user_uniqueness(self):
        """
        Can't create a user with same user name or email.  Save should return False, no new
        users should be added.
        """
        user = User(name='unique_user',email='unique_user@example.com',verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        user.save()
        users_in_db = User.all("where name = '%s'" % ('unique_user'))
        self.assertEqual(1, len(users_in_db))

        # same name, different email shouldn't save.
        user = User(name='unique_user',email='different_email@example.com',verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        self.assertFalse(user.save())
        users_in_db = User.all("where name = '%s'" % ('unique_user'))
        self.assertEqual(1, len(users_in_db))

        # same email, different name
        user = User(name='different_name',email='unique_user@example.com',verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        self.assertFalse(user.save())
        users_in_db = User.all("where email = '%s'" % ('unique_user@example.com'))
        self.assertEqual(1, len(users_in_db))

        # both different, should save.
        user = User(name='different_name',email='different_email@example.com',verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        self.assertTrue(user.save())
        users_in_db = User.all("where email = %s and name = %s", 'different_email@example.com', 'different_name')
        self.assertEqual(1, len(users_in_db))

    def test_user_password_storage(self):
        """
        Tests that a set of passwords correctly get set as the hashed_password
        """
        options.auth_secret = 'ne4om9og3maw8orp2ot9quos5ed8aj3lam6up3ja'
        passwords = [
                        ('asdf1234', 'f9d7082750f934412bb8e86c83432a027f2e92fb'),
                        ('k23(jsdjfsdlk''wlkj\nfpbd)', '0ccc0cbce78403de22b5065a81238d9ab0a82f1f'),
                        ('$55233234234', '8b57e7ee9feab3d7083debc1f2c97810329ed3bb')
                    ]
        for password in passwords:
            u = User(name=self.generate_string_of_len(random.randint(1,30)), email=self.generate_string_of_len(6) + '@example.com', email_confirmed=1, is_paid=1)
            u.set_and_confirm_password(password[0],password[0])
            u.save()
            self.assertEqual(u.hashed_password, password[1])

    #def test_existing_user_and_password_are_upgraded_to_bcrypt(self):
    #    """
    #    Tests that a set of users with existing hashed password get upgraded on calling authenticate
    #    """
    #    options.auth_secret = 'ne4om9og3maw8orp2ot9quos5ed8aj3lam6up3ja'
    #    passwords = [
    #                    ('asdf1234', 'f9d7082750f934412bb8e86c83432a027f2e92fb'),
    #                    ('k23(jsdjfsdlk''wlkj\nfpbd)', '0ccc0cbce78403de22b5065a81238d9ab0a82f1f'),
    #                    ('$55233234234', '8b57e7ee9feab3d7083debc1f2c97810329ed3bb')
    #                ]
    #    for password in passwords:
    #        this_user = self.generate_string_of_len(random.randint(1,30))
    #        u = User(name=this_user, email=self.generate_string_of_len(6) + '@example.com', email_confirmed=1, is_paid=1)
    #        u.set_and_confirm_password(password[0],password[0])
    #        u.save()
    #        u.authenticate(this_user, password[0])
    #        u = User.get(u.id)
    #        self.assertNotEqual(u.hashed_password, password[1])
    #        #YOU WERE HERE TESTING THAT CALLING AUTH UPGRADES TO BCRYPT


    def test_user_name_is_unique(self):
        name = self.generate_string_of_len(random.randint(1,30))
        password = self.generate_string_of_len(10)

        first_user = User(name=name, email=self.generate_string_of_len(6) + '@example.com', email_confirmed=1, is_paid=1)
        first_user.set_and_confirm_password(password, password)
        first_user.save()

        second_user = User(name=name, email=self.generate_string_of_len(6) + '@example.com', email_confirmed=1, is_paid=1)
        second_user.set_and_confirm_password(password, password)
        self.assertFalse(second_user.save())

    def test_email_verifier(self):
        invalid_emails = ['asdfasd@', 'asdfi 234@lskdf.net', 'ijoafd', 'sdfdsfsijof@dslkfj']
        valid_emails = ['admin@mltshp.com', 'joe@test.com', 'someone@nu.com', 'another@uber.nu', 'bladlfksj+wefwe@sdlkfjl.com']

        for i_email in invalid_emails:
            invalid_user = User(name=self.generate_string_of_len(random.randint(1,30)), email=i_email, email_confirmed=1, is_paid=1)
            self.assertFalse(invalid_user.save())

        for v_email in valid_emails:
            valid_user = User(name=self.generate_string_of_len(random.randint(1,30)), email=v_email, email_confirmed=1, is_paid=1)
            self.assertTrue(valid_user.save())

    def test_shared_files_count_ignores_deleted(self):
        """
        This test checks that an account with deleted files will not return them in the
        User.sharedfiles() or User.sharedfiles_count() methods
        """
        # User should have one sharedfile have one from the setUp
        self.assertEqual(self.user.sharedfiles_count(), 1)

        missing_ids = []
        for i in range(50):
            sf = Sharedfile(source_id = self.sourcefile.id, user_id = self.user.id, name="shgaredfile.png", title='shared file', share_key='asdf', content_type='image/png')
            sf.save()
            sf.add_to_shake(self.user_shake)
            if i and (50 % i) == 0: #2 5 10 and 25
                sf.delete()
                missing_ids.append(sf.id)


        self.assertEqual(self.user.sharedfiles_count(), 46)

        users_shared_files = self.user.sharedfiles()
        for f in users_shared_files:
            self.assertTrue(f.id not in missing_ids)

    def test_subscription_timeline_shows_appropriate_images(self):
        """
        We have a user subscribe to the shakes of 2 other users.  The users
        that are being subscribed to have one sharedfile each, both pointing
        to same source file.

        When a user subscribes, his timeline will be populated with last 10
        posts from user being subscribed to.  In this case, timeline will
        suppress dupes.
        """
        user1 = User(name='user', email='user@hi.com', is_paid=1)
        user1.save()

        source_file = Sourcefile(width=10, height=10, file_key='mumbles', thumb_key='bumbles')
        source_file.save()
        users = ['user2', 'user3', 'user4']
        for name in users:
            user = User(name=name, email='%s@mltshp.com' % (name), is_paid=1)
            user.save()
            sf = Sharedfile(source_id=source_file.id, user_id = user.id, name='%s file.jpg' % (name), \
                title='%s file' % (name), share_key='%s' % (name), content_type='image/jpg', deleted=0)
            sf.save()
            sf.add_to_shake(user.shake())

        # have user follow two users' shakes
        user2 = User.get('name=%s', 'user2')
        user3 = User.get('name=%s', 'user3')
        user1.subscribe(user2.shake())
        user1.subscribe(user3.shake())

        shared_files = user1.sharedfiles_from_subscriptions()
        self.assertEqual(1, len(shared_files))
        self.assertEqual(shared_files[0].source_id, source_file.id)

        shared_files[0].deleted = 1
        shared_files[0].save()

        # they should no longer see the shared file since it
        # was deleted.
        shared_files = user1.sharedfiles_from_subscriptions()
        self.assertEqual(0, len(shared_files))

    def test_profile_image_url(self):
        """
        If there is no user.profile_image, or set to False, should return the default.

        Otherwise, should return an Amazon URL.
        """
        self.assertEqual(None,self.user.profile_image)
        self.assertEqual('/static/images/default-icon-venti.svg', self.user.profile_image_url())

        self.user.profile_image = False
        self.user.save()
        self.assertEqual('/static/images/default-icon-venti.svg', self.user.profile_image_url())

        self.user.profile_image = True
        self.user.save()
        self.assertEqual(1, self.user.profile_image_url().count('amazonaws.com/account/1/profile.jpg'))


    def test_add_favorite(self):
        """
        A user should be able to favorite a sharedfile if:
         - it belongs to another user
         - it's not already favorited
         - if it's been favorited, but favorite was "deleted"

        A user shouldn't be able to favorite a sharedfile if they own it.
        """
        # Create new user with their own sharedfile.
        new_user = User(name='newuser',email='newuser@example.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        new_user.save()
        new_sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file", \
            user_id=new_user.id, content_type="image/png", share_key="ok")
        new_sharedfile.save()

        # One should be able to favorite another user's sharedfile
        self.assertTrue(self.user.add_favorite(new_sharedfile))
        favorites = Favorite.all("where user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, new_sharedfile.id)
        self.assertEqual(1, len(favorites))

        # Can't favorite an already favorited sharedfile.
        self.assertFalse(self.user.add_favorite(new_sharedfile))
        favorites = Favorite.all("where user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, new_sharedfile.id)
        self.assertEqual(1, len(favorites))

        # A favorite with "deleted" flag set, should have flag unset and
        # return True when add_favorite called
        favorite = Favorite.get("user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, new_sharedfile.id)
        favorite.deleted = True
        favorite.save()
        self.assertTrue(self.user.add_favorite(new_sharedfile))
        favorites = Favorite.all("where user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, new_sharedfile.id)
        self.assertEqual(1, len(favorites))

        # Can't favorite one's own sharedfile.
        self.assertTrue(self.sharedfile.user_id, self.user.id)
        self.assertFalse(self.user.add_favorite(self.sharedfile))
        favorites = Favorite.all("where user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, self.sharedfile.id)
        self.assertEqual(0, len(favorites))

    def test_add_favorite_deleted_sharedfile(self):
        """
        User.add_favorite should return False if sharedfile is deleted
        and no Favorite entries should be logged.
        """
        # Create new user with their own sharedfile.
        new_user = User(name='newuser',email='newuser@example.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        new_user.save()
        new_sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file", \
            user_id=new_user.id, content_type="image/png", share_key="ok")
        new_sharedfile.save()

        new_sharedfile.delete()
        self.assertFalse(self.user.add_favorite(new_sharedfile))
        favorites = Favorite.all("where user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, new_sharedfile.id)
        self.assertEqual(0, len(favorites))

    def test_remove_favorite(self):
        """
        User.remove_favorite should return False if the sharedfile has never been favorited or
        has been removed.

        Should return true if removing favorite succeeds
        """
        # Create new user with their own sharedfile.
        new_user = User(name='newuser',email='newuser@example.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        new_user.save()
        new_sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file", \
            user_id=new_user.id, content_type="image/png", share_key="ok")
        new_sharedfile.save()

        # remove_favorite should return false when sharedfile not already favorited.
        favorites = Favorite.all("where user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, new_sharedfile.id)
        self.assertEqual(0, len(favorites))
        self.assertFalse(self.user.remove_favorite(new_sharedfile))

        # remove_favorite should return True when unfavoring succeeds, deleted
        # flag on Favorite should be set to 0.  Should return false on a subsequent
        # attempt on remove_favorite
        self.user.add_favorite(new_sharedfile)
        favorites = Favorite.all("where user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, new_sharedfile.id)
        self.assertEqual(1, len(favorites))
        self.assertTrue(self.user.remove_favorite(new_sharedfile))
        favorites = Favorite.all("where user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, new_sharedfile.id)
        self.assertEqual(0, len(favorites))

        # remove_favorite on deleted favorite should return False.
        favorites = Favorite.all("where user_id = %s and sharedfile_id = %s and deleted = 1", \
            self.user.id, new_sharedfile.id)
        self.assertEqual(1, len(favorites))
        self.assertFalse(self.user.remove_favorite(new_sharedfile))


    def test_has_favorite(self):
        """
        User.has_favorite should return True if a user has favorited a file.  Should return
        False if no entry exists, or if entry is marked as "deleted"
        """
        # Create new user with their own sharedfile.
        new_user = User(name='newuser',email='newuser@example.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        new_user.save()
        new_sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file", \
            user_id=new_user.id, content_type="image/png", share_key="ok")
        new_sharedfile.save()

        self.assertFalse(self.user.has_favorite(new_sharedfile))
        self.user.add_favorite(new_sharedfile)
        self.assertTrue(self.user.has_favorite(new_sharedfile))

        favorite = Favorite.get("user_id = %s and sharedfile_id = %s and deleted = 0", \
            self.user.id, new_sharedfile.id)
        favorite.deleted = True
        favorite.save()
        self.assertFalse(self.user.has_favorite(new_sharedfile))

    def test_saved_sharedfile(self):
        """
        User.saved_sharedfile should return None if no
        sharedfile saved, otherwisew will return the sharedfile
        if it was saved by user.  If more than one shardfile saved
        by user, it will still return 1.
        """
        # Create new user to be doing the saving, and its own sharedfile.
        new_user = User(name='newuser',email='newuser@example.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        new_user.save()

        self.assertEqual(None, new_user.saved_sharedfile(self.sharedfile))
        self.sharedfile.save_to_shake(new_user)
        # check to make sure we get a Sharedfile object back, not None
        self.assertEqual(type(self.sharedfile), type(new_user.saved_sharedfile(self.sharedfile)))
        # save another file to user
        self.sharedfile.save_to_shake(new_user)
        self.assertEqual(type(self.sharedfile), type(new_user.saved_sharedfile(self.sharedfile)))


    def test_use_invitation(self):
        """
        user.send_invitation() should send two invitations out and create them with messages saying they are from
        that user.
        """
        self.user.add_invitations(5)

        self.user.send_invitation('j@example.com')
        self.user.send_invitation('k@example.com')

        self.assertEqual(self.user.invitation_count, 3)

        invitations_sent = invitation.Invitation.all()
        self.assertEqual(len(invitations_sent), 2)
        for i in invitations_sent:
            self.assertEqual(i.user_id, self.user.id)
            self.assertTrue(i.email_address in ['j@example.com', 'k@example.com'])

    def test_flag_nsfw(self):
        """
        User.flag_nsfw flag should set the nsfw field to 1 in DB.
        """
        self.assertEqual(self.user.nsfw, False)
        self.user.flag_nsfw()
        fetched_user = User.get('id = %s', self.user.id)
        self.assertEqual(self.user.nsfw, True)


    def test_unflag_nsfw(self):
        """
        User.unflag_nsfw should set the nsfw field to 0 in DB.
        """
        self.user.nsfw = True
        self.user.save()
        fetched_user = User.get('id = %s', self.user.id)
        self.assertEqual(self.user.nsfw, True)
        self.user.unflag_nsfw()
        fetched_user = User.get('id = %s', self.user.id)
        self.assertEqual(self.user.nsfw, False)


    def test_shakes_method_returns_managed_and_owned(self):
        """
        Tests that the shakes method returns the correct shake counts
        when called with managed and without.
        """

        #a new person with a shake
        shake_owner = User(name='user1', email='user1@example.com', email_confirmed=1, is_paid=1)
        shake_owner.set_password('asdfasdf')
        shake_owner.save()
        group_shake = shake_owner.create_group_shake(title='asdf', name='asdf', description='adsf')

        personal_shake = self.user.create_group_shake(title='qwer', name='qwer', description='qwer')

        #here's the cool part
        group_shake.add_manager(self.user)

        shakes_managed = self.user.shakes(include_managed=True)
        self.assertEqual(len(shakes_managed), 3)

        shakes_owned = self.user.shakes()
        self.assertEqual(len(shakes_owned), 2)
        self.assertEqual(shakes_owned[0].type, 'user')
        self.assertEqual(shakes_owned[1].type, 'group')

    def test_cannot_upload_if_over_file_upload_limit_unpaid(self):
        """
        Tests whether a user can upload a file if they are over the limit for this month.
        """
        self.user.stripe_plan_id = "mltshp-single"
        self.user.save()

        file_name = 'red.gif'
        file_content_type = 'image/gif'
        file_path = os.path.abspath("test/files/%s" % (file_name))
        file_sha1 = Sourcefile.get_sha1_file_key(file_path)

        sf = Sharedfile.create_from_file(
            file_path = file_path,
            file_name = file_name,
            sha1_value = file_sha1,
            content_type = file_content_type,
            user_id = self.user.id)
        sf.size = 410000000
        sf.save()

        self.assertFalse(self.user.can_upload_this_month())

    def test_can_upload_if_over_file_upload_limit_paid(self):
        """
        Tests whether a user can upload a file if they are over the limit and have paid
        for the double scoop plan.
        """
        self.user.stripe_plan_id = "mltshp-double"
        self.user.save()

        file_name = 'red.gif'
        file_content_type = 'image/gif'
        file_path = os.path.abspath("test/files/%s" % (file_name))
        file_sha1 = Sourcefile.get_sha1_file_key(file_path)

        sf = Sharedfile.create_from_file(
            file_path = file_path,
            file_name = file_name,
            sha1_value = file_sha1,
            content_type = file_content_type,
            user_id = self.user.id)
        sf.size = 310000000
        sf.save()

        self.assertTrue(self.user.can_upload_this_month())

    def test_total_file_count_for_this_month(self):
        """
        tests that the current amount of new files uploaded for the current month is correct
        """
        images = ['red.gif', 'blue.gif', 'green.gif', 'love.gif']
        for image in images:
            file_name = image
            file_content_type = 'image/gif'
            file_path = os.path.abspath("test/files/%s" % (file_name))
            file_sha1 = Sourcefile.get_sha1_file_key(file_path)

            sf = Sharedfile.create_from_file(
                file_path = file_path,
                file_name = file_name,
                sha1_value = file_sha1,
                content_type = file_content_type,
                user_id = self.user.id)

        month_days = calendar.monthrange(datetime.utcnow().year,datetime.utcnow().month)
        start_time = datetime.utcnow().strftime("%Y-%m-01")
        end_time = datetime.utcnow().strftime("%Y-%m-" + str(month_days[1]) )

        self.assertEqual(self.user.uploaded_kilobytes(start_time=start_time, end_time=end_time), 72)

    def test_is_admin(self):
        """
        Only user's with the name admin should return True when User.is_admin is called.
        """
        admin = User(name='admin',email='admin@mltshp.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        admin.save()
        someone_else = User(name='someoneelse',email='someoneelse@mltshp.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        someone_else.save()
        self.assertTrue(admin.is_admin())
        self.assertFalse(someone_else.is_admin())


    def test_find_by_name_fragment(self):
        """
        User.find_by_name_fragment should return empty array
        if None or '' is passed in.  Otherwise, should search and find
        usernames.
        """
        admin = User(name='admin',email='admin@mltshp.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        admin.save()
        another_user = User(name='another',email='another@mltshp.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, is_paid=1)
        another_user.save()

        self.assertEqual([], User.find_by_name_fragment('nothing'));
        self.assertEqual([], User.find_by_name_fragment());

        self.assertEqual(2, len(User.find_by_name_fragment('a')))
        self.assertEqual('admin', User.find_by_name_fragment('ad')[0].name)

        # test limit
        self.assertEqual(1, len(User.find_by_name_fragment('a', limit=1)))

    def test_user_delete(self):
        self.user.create_group_shake(title='balrag', name="blahr", description="affafa")

        another_user = User(name='example2',email='example2@example.com', \
            verify_email_token = 'created', password='examplepass', email_confirmed=1, paid=1)
        another_user.save()
        new_group_shake = another_user.create_group_shake(title='weiurywiuer', name="werqwerew", description="affafa")

        self.user.subscribe_to_user(another_user)


        new_group_shake.add_manager(self.user)

        self.user.delete()
        user = User.get('name=%s', 'example')
        self.assertEqual(user.email, 'deleted-%s@mltshp.com' % (user.id))
        self.assertEqual(user.hashed_password, 'deleteduseracct')
        self.assertEqual(user.about, '')
        self.assertEqual(user.website, '')
        self.assertEqual(user.nsfw, 1)
        self.assertEqual(user.recommended, 0)
        self.assertEqual(user.is_paid, 1)
        self.assertEqual(user.deleted, 1)
        self.assertEqual(user.verify_email_token, 'deleted')
        self.assertEqual(user.reset_password_token, 'deleted')
        self.assertEqual(user.profile_image, 0)
        self.assertEqual(user.disable_notifications, 1)
        self.assertEqual(user.invitation_count, 0)

        shared_files = Sharedfile.all()
        for shared_file in shared_files:
            self.assertEqual(shared_file.deleted, 1)

        ssfs = Shakesharedfile.all()
        for ssf in ssfs:
            self.assertEqual(ssf.deleted, 1)

        subscriptions = Subscription.where("user_id = %s", self.user.id)
        for sub in subscriptions:
            self.assertEqual(sub.deleted, 1)

        managing = ShakeManager.where("user_id = %s", self.user.id)
        for m in managing:
            self.assertEqual(m.deleted, 1)

