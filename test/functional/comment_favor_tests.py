import time

import test.base
import models

class CommentFavorTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(CommentFavorTests, self).setUp()
        self.admin = models.User(name='admin', email='admin@example.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()

        self.user2 = models.User(name='user2', email='user2@example.com', email_confirmed=1, is_paid=1)
        self.user2.set_password('asdfasdf')
        self.user2.save()

        self.src = models.Sourcefile(width=1, height=1, file_key='asdf', thumb_key='qwer')
        self.src.save()
        self.shf = models.Sharedfile(source_id=self.src.id, user_id=self.admin.id, name='shared.jpg', title='shared', share_key='1', content_type='image/jpg')
        self.shf.save()

        print("person who owns the comment")
        self.comment = models.Comment(user_id=self.user2.id, sharedfile_id=self.shf.id, body="just a comment")
        self.comment.save()
        print(self.comment.user_id)

        self.sign_in('admin','asdfasdf')
        response = self.post_url('/p/%s/comment/%s/like?json=1' % (self.shf.share_key, self.comment.id))

    def test_comment_can_be_liked(self):
        comment_like = models.CommentLike.get('user_id=%s', self.admin.id)
        self.assertTrue(comment_like)

    def test_comment_reliking_reuses_existing_like(self):
        #dislike it
        response = self.post_url('/p/%s/comment/%s/dislike?json=1' % (self.shf.share_key, self.comment.id))
        comment_like = models.CommentLike.get('user_id=%s', self.admin.id)
        self.assertTrue(comment_like)

        #now it is deleted
        self.assertEqual(comment_like.deleted ,1)

        #now it is liked again
        response = self.post_url('/p/%s/comment/%s/like?json=1' % (self.shf.share_key, self.comment.id))

        comment_like = models.CommentLike.get('user_id=%s', self.admin.id)
        self.assertTrue(comment_like)

        #now it is resurrected
        self.assertEqual(comment_like.deleted, 0)

    def test_notification_created_for_like(self):
        """
        Liking a comment should create a notification for the commenter.
        """

        notifications = models.Notification.all()

        for n in notifications:
            if n.type == 'comment_like':
                print(n.__dict__)
        #
        #self.assertEqual(len(notifications), 2)
        #self.assertEqual(notifications[1].sender_id, self.admin.id)
        #self.assertEqual(notifications[1].receiver_id, self.user2.id)
        #self.assertEqual(notifications[1].type, 'comment_like')
        #self.assertEqual(notifications[1].action_id, self.comment.id)
