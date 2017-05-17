from tornado.options import options

from models import User, Shake, Sourcefile, Sharedfile, ShakeManager
from base import BaseTestCase


class ShakeModelTests(BaseTestCase):
    def setUp(self):
        super(ShakeModelTests, self).setUp()
        self.user = User(name='admin', email='admin@example.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()

        self.shake = Shake(user_id = self.user.id, name='asdf', type='group',
            title='My Test Shake', description='Testing this shake test.')
        self.shake.save()

    def test_correct_owner_is_returned(self):
        """
        Verifies the owner is correctly returned
        """
        self.assertEqual(self.user.id, self.shake.user_id)

    def test_correct_page_image_is_returned(self):
        """
        If an image exists, it should return the correct path.
        """
        self.assertEqual(None, self.shake.page_image())
        self.assertEqual('/static/images/default-icon-venti.svg', self.user.shake().page_image())
        self.shake.image = 1
        self.shake.save
        self.assertEqual('https://%s.s3.amazonaws.com/account/1/shake_asdf.jpg' % options.aws_bucket, self.shake.page_image())

    def test_correct_thumbnail_url_is_returned(self):
        """
        If an image exists, it should return the correct thumbnail path
        """
        self.assertEqual('https://mltshp-cdn.com/static/images/default-icon-venti.svg', self.shake.thumbnail_url())
        self.assertEqual('https://mltshp-cdn.com/static/images/default-icon-venti.svg', self.user.shake().thumbnail_url())
        self.shake.image = 1
        self.shake.save()
        self.assertEqual('https://%s.s3.amazonaws.com/account/1/shake_asdf_small.jpg' % options.aws_bucket, self.shake.thumbnail_url())

    def test_correct_path_is_returned(self):
        """
        Simply returns the correct path for the shake
        """
        self.assertEqual('/asdf',self.shake.path())
        self.assertEqual('/user/admin', self.user.shake().path())

    def test_correct_display_name_is_returned(self):
        """
        Display name or title is returned if set.
        """
        self.assertEqual('My Test Shake', self.shake.display_name())
        self.assertEqual('admin', self.user.shake().display_name())

    def test_user_can_update_shake(self):
        """
        Tests that a user can and cannot update a certain shake
        """
        user1 = User(name='user1', email='user1@example.com', email_confirmed=1, is_paid=1)
        user1.set_password('asdfasdf')
        user1.save()
        user2 = User(name='user2', email='user2@example.com', email_confirmed=1, is_paid=1)
        user2.set_password('asdfasdf')
        user2.save()

        self.shake.add_manager(user1)

        self.assertTrue(self.shake.can_update(user1.id))
        self.assertTrue(self.shake.can_update(self.user.id))
        self.assertFalse(self.shake.can_update(user2.id))


    def test_saving_validates_title(self):
        """
        Creates shakes with valid and invalid titles
        """
        valid_titles=['asdf', 'This is a test.']
        invalid_titles = ['', None]
        identifier = 1

        for title in valid_titles:
            self.assertTrue(Shake(user_id=self.user.id, title=title, name='testing%s' % (identifier), type='group').save())
            identifier+=1
        for title in invalid_titles:
            self.assertFalse(Shake(user_id=self.user.id, title=title, name='testing%s' % (identifier), type='group').save())
            identifier+=1

    def test_saving_validates_name(self):
        """
        Creates shakes with valid and invalid names
        """
        valid_names = ['a-b-c', 'qwerty','1234', '2a93sfj', 'asdfgasdfgasdfgasdfgasdfg']
        invalid_names = ['', None, 'a x', 'AsDf', 'static',  #asdf exists in the setup, static is reserved
            'asdfgasdfgasdfgasdfgasdfgx'] #too long

        for name in valid_names:
            self.assertTrue(Shake(user_id=self.user.id, title="some text", name=name, type='group').save())
        for name in invalid_names:
            self.assertFalse(Shake(user_id=self.user.id, title="some text", name=name, type='group').save())

    def test_subscribers(self):
        """
        Tests whether subscribers returned are the subscribers to a particular shake.
        """
        user1 = User(name='user1', email='user1@example.com', email_confirmed=1, is_paid=1)
        user1.set_password('asdfasdf')
        user1.save()
        user2 = User(name='user2', email='user2@example.com', email_confirmed=1, is_paid=1)
        user2.set_password('asdfasdf')
        user2.save()

        user1.subscribe(self.shake)
        user2.subscribe(self.shake)

        self.assertTrue(user1.id in [s.id for s in self.shake.subscribers()])
        self.assertTrue(user2.id in [s.id for s in self.shake.subscribers()])

        user1.unsubscribe(self.shake)
        self.assertFalse(user1.id in [s.id for s in self.shake.subscribers()])

        user1.subscribe(self.shake)
        self.assertTrue(user1.id in [s.id for s in self.shake.subscribers()])

    def test_paginated_sharedfiles_and_count(self):
        """
        Tests both the pagination of a shake's shared files and the count
        """
        sharedfiles = []
        sourcefile = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        sourcefile.save()

        for i in range(31):
            sf = Sharedfile(source_id=sourcefile.id, name="my shared file",
                user_id=self.user.id, content_type="image/png", share_key="1",
                description="some\ndescription\nhere", source_url="https://www.mltshp.com/?hi")
            sf.save()
            sf.add_to_shake(self.shake)
            sharedfiles.append(sf)

        self.assertEqual(len(self.shake.sharedfiles()), 10) #default
        self.assertEqual(len(self.shake.sharedfiles(page=1)), 10)
        self.assertEqual(len(self.shake.sharedfiles(page=2)), 10)
        self.assertEqual(len(self.shake.sharedfiles(page=3)), 10)
        self.assertEqual(len(self.shake.sharedfiles(page=4)), 1)

        self.assertEqual(len(self.shake.sharedfiles(page=1, per_page=31)), 31)


    def test_adding_manager(self):
        """
        Verifies adding a new manager works
        """
        user1 = User(name='user1', email='user1@example.com', email_confirmed=1, is_paid=1)
        user1.set_password('asdfasdf')
        user1.save()

        self.shake.add_manager(user1)
        self.assertTrue(user1.id in [m.id for m in self.shake.managers()])
        self.shake.remove_manager(user1)
        self.assertFalse(user1.id in [m.id for m in self.shake.managers()])
        self.shake.add_manager(user1)
        self.assertTrue(user1.id in [m.id for m in self.shake.managers()])


    def test_can_edit(self):
        """
        Tests whether a user has the ability to edit a shake
        """
        user1 = User(name='user1', email='user1@example.com', email_confirmed=1, is_paid=1)
        user1.set_password('asdfasdf')
        user1.save()

        self.assertTrue(self.shake.can_edit(self.user))
        self.assertFalse(self.shake.can_edit(user1))


## should have a test here for testing set page image.
