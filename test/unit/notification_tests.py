from models import Notification, User, Sourcefile, Sharedfile, Comment, Subscription
from base import BaseTestCase
from settings import test_settings as settings

class NotificationModelTests(BaseTestCase):
    def setUp(self):
        """
        Create a user, source and shared file.
        """
        super(NotificationModelTests, self).setUp()
        self.user = User(name='example',email='user1@example.com',
            verify_email_token = 'created', password='examplepass', email_confirmed=1,
            is_paid=1)
        self.user.save()
        self.user2 = User(name='example2',email='user2@example.com',
            verify_email_token = 'created', password='examplepass', email_confirmed=1,
            is_paid=1)
        self.user2.save()


        self.sourcefile = Sourcefile(width=20,height=20,file_key="asdf", \
            thumb_key="asdf_t")
        self.sourcefile.save()
        self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file", \
            user_id=self.user.id, content_type="image/png", share_key="ok")
        self.sharedfile.save()

    def test_new_subscriber_notification(self):
        #generate a notification
        new_sub = Subscription(user_id=self.user2.id, shake_id=1)
        new_sub.save()

        notification = Notification.new_subscriber(sender=self.user2, receiver=self.user, action_id=new_sub.id)

        sent_notification = Notification.get("id=%s", notification.id)
        self.assertEqual(sent_notification.id, notification.id)
        self.assertEqual(sent_notification.sender_id, self.user2.id)
        self.assertEqual(sent_notification.receiver_id, self.user.id)
        self.assertEqual(sent_notification.action_id, new_sub.id)
        self.assertEqual(sent_notification.type, 'subscriber')

        
    def test_new_favorite_notification(self):
        notification = Notification.new_favorite(sender=self.user2, sharedfile=self.sharedfile)
        
        sent_notification = Notification.get("id=%s", notification.id)
        self.assertEqual(sent_notification.id, notification.id)
        self.assertEqual(sent_notification.sender_id, self.user2.id)
        self.assertEqual(sent_notification.receiver_id, self.user.id)
        self.assertEqual(sent_notification.action_id, 1)
        self.assertEqual(sent_notification.type, 'favorite')
    
    def test_deleting_favorite_notification(self):
        notification = Notification.new_favorite(sender=self.user2, sharedfile=self.sharedfile)
        
        sent_notification = Notification.get("id=%s", notification.id)
        sent_notification.delete()
        check_delete_notification = Notification.get("id=%s", notification.id)
        self.assertTrue(check_delete_notification.deleted)
        
    def test_new_save_notification(self):
        notification = Notification.new_save(sender=self.user2, sharedfile=self.sharedfile)
        
        sent_notification = Notification.get("id=%s", notification.id)
        self.assertEqual(sent_notification.id, notification.id)
        self.assertEqual(sent_notification.sender_id, self.user2.id)
        self.assertEqual(sent_notification.receiver_id, self.user.id)
        self.assertEqual(sent_notification.action_id, 1)
        self.assertEqual(sent_notification.type, 'save')
        
    def test_new_comment_notification(self):
        new_comment = Comment(user_id=self.user2.id, sharedfile_id = self.sharedfile.id, body="Testing comment")
        new_comment.save()

        sent_notification = Notification.get("id=%s", 1)

        self.assertEqual(sent_notification.sender_id, self.user2.id)
        self.assertEqual(sent_notification.receiver_id, self.user.id)
        self.assertEqual(sent_notification.action_id, 1)
        self.assertEqual(sent_notification.type, 'comment')
        
    def test_new_comment_doesnt_store_for_same_user(self):
        new_comment = Comment(user_id=self.user.id, sharedfile_id = self.sharedfile.id, body="Testing comment")
        new_comment.save()

        sent_notification = Notification.get("id=%s", 1)

        self.assertFalse(sent_notification)
