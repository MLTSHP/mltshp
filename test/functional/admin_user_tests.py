from contextlib import contextmanager
import test.base
from models import User, Sharedfile, Sourcefile, Conversation, Comment


@contextmanager
def test_option(name, value):
    old_value = getattr(options, name)
    setattr(options, name, value)
    yield
    setattr(options, name, old_value)


class AdminUserFlagNSFWTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(AdminUserFlagNSFWTests, self).setUp()
        self.admin = User(name='admin', email='admin@example.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()        
        self.sign_in('admin', 'asdfasdf')

    def test_prevent_non_admin_from_accessing(self):
        """
        A non-admin user should not be able to post.
        """
        self.non_admin = User(name='nonadmin', email='nonadmin@example.com', email_confirmed=1, is_paid=1)
        self.non_admin.set_password('asdfasdf')
        self.non_admin.save()
        self.sign_in('nonadmin', 'asdfasdf')

        offensive_user = User(name='offensive', email='offensive@example.com', is_paid=1)
        offensive_user.save()
        offensive_user = User.get("id = %s",  offensive_user.id)
        self.assertEqual(offensive_user.nsfw, False)

        result = self.post_url("/admin/user/offensive/flag-nsfw", arguments={'nsfw' : 1})
        self.assertEqual(result.code, 403)
        offensive_user = User.get("id = %s",  offensive_user.id) 
        self.assertEqual(offensive_user.nsfw, False)


    def test_flag_nsfw(self):
        """
        Posting to /admin/user/{user_name}/flag-nsfw with POST parameter "nsfw" set to 1, sets the nsfw flag on a user.
        """
        offensive_user = User(name='offensive', email='offensive@example.com', is_paid=1)
        offensive_user.save()
        offensive_user = User.get("id = %s",  offensive_user.id)
        self.assertEqual(offensive_user.nsfw, False)

        self.post_url("/admin/user/offensive/flag-nsfw", arguments={'nsfw' : 1})
        offensive_user = User.get("id = %s",  offensive_user.id) 
        self.assertEqual(offensive_user.nsfw, True)

        self.post_url("/admin/user/offensive/flag-nsfw", arguments={'nsfw' : 0})
        offensive_user = User.get("id = %s",  offensive_user.id)
        self.assertEqual(offensive_user.nsfw, False)


class AdminDeleteUserTest(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(AdminDeleteUserTest, self).setUp()
        self.admin = User(name='admin', email='admin@example.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()        
        self.sign_in('admin', 'asdfasdf')

    def test_delete_user(self):
        user_to_del = User(name='user_delete', email='delete@example.com', email_confirmed=1, is_paid=1)
        user_to_del.set_password('asdfasdf')
        user_to_del.save()  

        sourcefile = Sourcefile(width=20,height=20,file_key="asdf", thumb_key="asdf_t")
        sourcefile.save()
        sharedfile = Sharedfile(source_id=sourcefile.id, name="my shared file", user_id=user_to_del.id, content_type="image/png", share_key="ok")
        sharedfile.save()
        user_shake = user_to_del.shake()
        sharedfile.add_to_shake(user_shake)

        with test_option('use_workers', False):
            self.post_url('/admin/delete-user', arguments={'user_id':user_to_del.id, 'user_name':user_to_del.name})

        deleted_user = User.get('id = %s and name = %s', user_to_del.id, user_to_del.name)
        self.assertEqual(deleted_user.deleted, 1)

        sf = Sharedfile.get('id=%s', sharedfile.id)
        self.assertEqual(sf.deleted, 1)
