import test.base
import test.factories
import models

class ImageCommentTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(ImageCommentTests, self).setUp()
        # uploader
        self.admin = models.User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()

        # commenter 1
        self.bob = models.User(name='bob', email='bob@mltshp.com', email_confirmed=1, is_paid=1)
        self.bob.set_password('asdfasdf')
        self.bob.save()
        
    def test_a_non_logged_in_user_cant_delete_comments(self):
        """
        Posting to delete a comment if you're not logged in should result
        in a 403 error.  All comments remain intact.
        """
        sharedfile = test.factories.sharedfile(self.admin)
        comment = models.Comment(user_id=self.admin.id, sharedfile_id=sharedfile.id, body="just a comment")
        comment.save()
        response = self.post_url("/p/%s/comment/%s/delete" % (sharedfile.share_key, comment.id))
        self.assertEqual(response.code, 403)
        self.assertEqual(comment.id, models.Comment.get("id = %s and deleted = 0", comment.id).id)
        self.assertEqual(None, models.Comment.get("id = %s and deleted = 1", comment.id))
        
    def test_can_delete_own_comment(self):
        """
        A user should be able to delete their comment on another's sharedfile.
        """
        admins_sharedfile = test.factories.sharedfile(self.admin)
        comment = models.Comment(user_id=self.bob.id, sharedfile_id=admins_sharedfile.id, body="just a comment")
        comment.save()
        self.sign_in('bob', 'asdfasdf')
        self.assertEqual(None, models.Comment.get("id = %s and deleted = 1", comment.id))
        response = self.post_url("/p/%s/comment/%s/delete" % (admins_sharedfile.share_key, comment.id))
        self.assertEqual(comment.id, models.Comment.get("id = %s and deleted = 1", comment.id).id)
    
    def test_delete_anothers_comment_on_own_file(self):
        """
        A user can delete another's comment on their own sharedfile.
        """
        admins_sharedfile = test.factories.sharedfile(self.admin)
        comment = models.Comment(user_id=self.bob.id, sharedfile_id=admins_sharedfile.id, body="just a comment")
        comment.save()
        self.sign_in('admin', 'asdfasdf')
        self.assertEqual(None, models.Comment.get("id = %s and deleted = 1", comment.id))
        response = self.post_url("/p/%s/comment/%s/delete" % (admins_sharedfile.share_key, comment.id))
        self.assertEqual(comment.id, models.Comment.get("id = %s and deleted = 1", comment.id).id)

    def test_can_not_delete_anothers_sharedfile(self):
        """
        A user can not delete someone else's comment if it's on a sharedfile they
        don't own.
        """
        admins_sharedfile = test.factories.sharedfile(self.admin)
        comment = models.Comment(user_id=self.bob.id, sharedfile_id=admins_sharedfile.id, body="just a comment")
        comment.save()
        self.sign_in('tom', 'asdfasdf')
        self.assertEqual(None, models.Comment.get("id = %s and deleted = 1", comment.id))
        response = self.post_url("/p/%s/comment/%s/delete" % (admins_sharedfile.share_key, comment.id))
        self.assertEqual(None, models.Comment.get("id = %s and deleted = 1", comment.id))

    
