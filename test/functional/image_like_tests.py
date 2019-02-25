import json

import test.base
import lib.utilities
from models import User, Favorite, Sourcefile, Sharedfile, Notification

class ImageLikeTests(test.base.BaseAsyncTestCase):
    """
    Tests: /p/{share_key}/like & /p/{share_key}/unlike
    """
    def setUp(self):
        """
        Create users to test different liking situations.
        """
        super(ImageLikeTests, self).setUp()
        self.admin = User(name='admin', email='admin@example.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()

        self.joe = User(name='joe', email='joe@example.com', email_confirmed=1, is_paid=1)
        self.joe.set_password('asdfasdf')
        self.joe.save()

        self.bill = User(name='bill', email='bill@example.com', email_confirmed=1, is_paid=1)
        self.bill.set_password('asdfasdf')
        self.bill.save()

        self.frank = User(name='frank', email='frank@example.com', email_confirmed=1, is_paid=1)
        self.frank.set_password('asdfasdf')
        self.frank.save()


    def _create_sharedfile(self, user):
        """
        Utility to create a stub sharedfile for the user.
        """
        sourcefile = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        sourcefile.save()
        sharedfile = Sharedfile(source_id=sourcefile.id, name="the name",user_id=user.id, \
            content_type="image/png", description="description", source_url="https://www.mltshp.com/?hi")
        sharedfile.save()
        sharedfile.share_key = lib.utilities.base36encode(sharedfile.id)
        sharedfile.save()
        return sharedfile

    def test_liking_image(self):
        """
        admin creates a sharedfile.  Joe (authenticated) likes it.

        Response should be successful and include following fields:

            {
             'response' : 'ok',
             'count' : 1,
             'share_key', 1
            }

        A new entry should be present in favorites table.  like_count on the sharedfile
        should be incremented.
        """
        sharedfile = self._create_sharedfile(self.admin)
        self.sign_in('joe', 'asdfasdf')
        favorite = Favorite.get('user_id = %s and sharedfile_id = %s' % (self.joe.id, sharedfile.id))
        self.assertEqual(None, favorite)
        self.assertEqual(0, sharedfile.like_count)

        response = self.post_url('/p/%s/like?json=1' % sharedfile.share_key)
        json_response = json.loads(response.body)
        self.assertEqual(json_response['response'], 'ok')
        self.assertEqual(json_response['count'], 1)
        self.assertEqual(json_response['share_key'], sharedfile.share_key)
        favorite = Favorite.get('user_id = %s and sharedfile_id = %s' % (self.joe.id, sharedfile.id))
        self.assertTrue(favorite)
        sharedfile_fetched = Sharedfile.get("id = %s", sharedfile.id)
        self.assertEqual(1, sharedfile_fetched.like_count)

    def test_unliking_image(self):
        """
        admin creates a sharedfile. Joe likes it. Then, joe decides to unlike it.

        Unliking an already liked image, should result in following response:

            {
             'response' : 'ok',
             'count' : 0,
             'share_key', 1
            }

        An entry should still be present in Favorites table, with deleted = 1.
        Like count should be reset on the sharedfile.
        """
        sharedfile = self._create_sharedfile(self.admin)
        self.joe.add_favorite(sharedfile)
        sharedfile_fetched = Sharedfile.get("id = %s", sharedfile.id)
        self.assertEqual(1, sharedfile_fetched.like_count)

        self.sign_in('joe', 'asdfasdf')
        response = self.post_url('/p/%s/unlike?json=1' % sharedfile.share_key)
        json_response = json.loads(response.body)
        self.assertEqual(json_response['response'], 'ok')
        self.assertEqual(json_response['count'], 0)
        self.assertEqual(json_response['share_key'], sharedfile.share_key)

        favorite = Favorite.get('user_id= %s and sharedfile_id = 1' % self.joe.id)
        self.assertTrue(favorite)
        self.assertTrue(favorite.deleted)
        sharedfile_fetched = Sharedfile.get("id = %s", sharedfile.id)
        self.assertEqual(0, sharedfile_fetched.like_count)

    def test_like_unlike_not_signed_in(self):
        """
        Liking or unliking something should return a 403 if user is not
        signed in.  No Favorites should be created.
        """
        sharedfile = self._create_sharedfile(self.admin)
        response = self.post_url('/p/%s/like?json=1' % sharedfile.share_key)

        self.assertEqual(response.code, 403)
        favorites = Favorite.all()
        self.assertEqual(len(favorites), 0)
        response = self.post_url('/p/%s/unlike?json=1' % sharedfile.share_key)
        self.assertEqual(response.code, 403)

    def test_cannot_like_own(self):
        """
        Liking own image should return a 200 response with an 'error' as one
        of the response keys.
        """
        sharedfile = self._create_sharedfile(self.admin)
        self.sign_in('admin', 'asdfasdf')
        response = self.post_url('/p/%s/like?json=1' % sharedfile.share_key)
        json_response = json.loads(response.body)

        self.assertEqual(response.code, 200)
        self.assertTrue(json_response.has_key('error'))
        favorite = Favorite.get('user_id= %s and sharedfile_id = %s', self.admin.id, sharedfile.id)
        self.assertFalse(favorite)

    def test_like_creates_notification(self):
        """
        Liking an image for first time should create notification.  We
        check on the correctness of notifications too here, but we should
        probably check this in a unit test.
        """
        sharedfile = self._create_sharedfile(self.admin)
        self.sign_in('joe', 'asdfasdf')
        response = self.post_url('/p/%s/like?json=1' % sharedfile.share_key)

        notifications = Notification.all()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].sender_id, self.joe.id)
        self.assertEqual(notifications[0].receiver_id, self.admin.id)
        self.assertEqual(notifications[0].type, 'favorite')
        self.assertEqual(notifications[0].action_id, 1)

    def test_like_gives_like_to_parent_and_original(self):
        """
        This tests that if user A posts a file, user B saves it and
        user C likes it, both user A and B shared file receives a like.
        """
        sharedfile = self._create_sharedfile(self.admin)
        joe_sharedfile = sharedfile.save_to_shake(self.joe)
        bill_sharedfile = joe_sharedfile.save_to_shake(self.bill)

        self.sign_in('frank', 'asdfasdf')
        response = self.post_url('/p/%s/like?json=1' % bill_sharedfile.share_key)

        self.assertEqual(len(Favorite.all()), 3)

    def test_unlike_removes_likes_from_parent_and_original(self):
        """
        A test of unliking a file and the likes being removed
        from parent and original.
        """
        sharedfile = self._create_sharedfile(self.admin)
        joe_sharedfile = sharedfile.save_to_shake(self.joe)
        bill_sharedfile = joe_sharedfile.save_to_shake(self.bill)

        self.sign_in('frank', 'asdfasdf')
        response = self.post_url('/p/%s/like?json=1' % bill_sharedfile.share_key)

        response = self.post_url('/p/%s/unlike?json=1' % bill_sharedfile.share_key)

        un_favorites = Favorite.where('deleted=1')
        self.assertEqual(len(un_favorites),3)


    def test_reliking_undeletes_parent_and_original(self):
        """
        A test that reliking a file that was previously unliked
        will undelete the likes above it.
        """
        sharedfile = self._create_sharedfile(self.admin)
        joe_sharedfile = sharedfile.save_to_shake(self.joe)
        bill_sharedfile = joe_sharedfile.save_to_shake(self.bill)

        self.sign_in('frank', 'asdfasdf')
        response = self.post_url('/p/%s/like?json=1' % bill_sharedfile.share_key)
        response = self.post_url('/p/%s/unlike?json=1' % bill_sharedfile.share_key)
        response = self.post_url('/p/%s/like?json=1' % bill_sharedfile.share_key)

        self.assertEqual(len(Favorite.all()), 3)

    def test_like_does_not_go_to_original_file_if_liker_is_poster(self):
        """
        This tests that if user A posts a file, user B saves it and then
        user A likes user B's file, user A does not receive a like.
        """
        sharedfile = self._create_sharedfile(self.admin)
        joe_sharedfile = sharedfile.save_to_shake(self.joe)

        self.sign_in('admin', 'asdfasdf')
        response = self.post_url('/p/%s/like?json=1' % joe_sharedfile.share_key)

        self.assertEqual(len(Favorite.all()), 1)

    def test_unlike_of_shared_file_with_deleted_parents(self):
        """
        This tests that if you delete the original and parents of a file
        and then unlike the file, it doesn't choke on there not being existing
        ids
        """
        sharedfile = self._create_sharedfile(self.admin)
        joe_sharedfile = sharedfile.save_to_shake(self.joe)
        bill_sharedfile = joe_sharedfile.save_to_shake(self.bill)

        self.sign_in('frank', 'asdfasdf')
        response = self.post_url('/p/%s/like?json=1' % bill_sharedfile.share_key)

        self.assertEqual(len(Favorite.all()), 3)
        sharedfile.delete()
        joe_sharedfile.delete()

        response = self.post_url('/p/%s/unlike?json=1' % bill_sharedfile.share_key)

        self.assertEqual(len(Favorite.where('deleted = 1')), 3)

    def test_like_of_shared_file_with_deleted_parents(self):
        """
        Tests that if a file is liked and its parents are deleted
        they should not get likes
        """
        sharedfile = self._create_sharedfile(self.admin)
        joe_sharedfile = sharedfile.save_to_shake(self.joe)
        bill_sharedfile = joe_sharedfile.save_to_shake(self.bill)

        sharedfile.delete()
        joe_sharedfile.delete()

        self.sign_in('frank', 'asdfasdf')
        response = self.post_url('/p/%s/like?json=1' % bill_sharedfile.share_key)

        self.assertEqual(len(Favorite.all()), 1)



