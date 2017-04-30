
from models import User, Sharedfile, Sourcefile, Shake, Favorite, Comment, Conversation
from base import BaseTestCase

class ConversationModelTests(BaseTestCase):

    def setUp(self):
        """
        Create a user, a source file and a shared file to user in tests.
        """
        super(ConversationModelTests, self).setUp()
        self.user = User(name='example',email='example@example.com',
            verify_email_token = 'created', password='examplepass', email_confirmed=1,
            is_paid=1)
        self.user.save()
        self.another_user = User(name='somethingelse',email='another_user@example.com',
            verify_email_token = 'created', password='examplepass', email_confirmed=1,
            is_paid=1)
        self.another_user.save()
        self.sourcefile = Sourcefile(width=20,height=20,file_key="asdf", \
            thumb_key="asdf_t")
        self.sourcefile.save()
        self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file", \
            user_id=self.user.id, content_type="image/png", share_key="ok")
        self.sharedfile.save()

    def test_relevant_comments(self):
        """
        Conversation.relevant_comments returns all the comments for the conversation at hand.
        """
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.another_user.id, body='test')
        comment.save()

        another_user_conversation = Conversation.get('user_id = %s', self.another_user.id)
        self.assertEqual(1, len(another_user_conversation.relevant_comments()))

        comment2 = Comment(sharedfile_id=self.sharedfile.id, user_id=self.another_user.id, body='two')
        comment2.save()
        self.assertEqual(2, len(another_user_conversation.relevant_comments()))

    def test_for_user_doesnt_return_muted_conversations(self):
        """
        When we create a Comment, conversation gets created for the sharedfile owner and the
        commenter.  The conversation should appear for the commenter, unless the conversation
        gets muted, in which case it doesn't get returned.
        """
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.another_user.id, body='test')
        comment.save()

        another_user_conversation = Conversation.get('user_id = %s', self.another_user.id)
        self.assertEqual(0, another_user_conversation.muted)
        self.assertEqual(1, len(Conversation.for_user(self.another_user.id)))

        another_user_conversation.muted = 1
        another_user_conversation.save()
        self.assertEqual(0, len(Conversation.for_user(self.another_user.id)))

