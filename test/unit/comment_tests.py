from models import Sharedfile, Sourcefile, User, Comment, Conversation
from datetime import datetime, timedelta
import os, shutil
from base import BaseTestCase

class CommentModelTests(BaseTestCase):

    def setUp(self):
        """
        Create a user sourcefile and sharedfile to work with.
        """
        super(CommentModelTests, self).setUp() # register connection.
        self.user = User(name='thename',email='theemail@example.com',verify_email_token='created',email_confirmed=1)
        self.user.save()
        self.sourcefile = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        self.sourcefile.save()
        self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="ok")
        self.sharedfile.save()

        self.visitor = User(name='visitor',email='visitor@example.com',verify_email_token='created',email_confirmed=1)
        self.visitor.save()

    def test_as_json(self):
        """
        Make sure as_json returns comment body and user dict in the dict response.
        """
        comment = Comment.add(user=self.user, sharedfile=self.sharedfile, body='hello')
        comment_j = comment.as_json()
        self.assertEqual(comment_j['body'], comment.body)
        self.assertEqual(comment_j['user'], comment.user().as_json())

    def test_body_formatted(self):
        """
        Comment.body_formatted should escape HTML character as well as replace line breaks (\n)
        with <br>.
        """
        body ="""<hello>
break
"time"""
        body_formatted = """&lt;hello&gt;<br>break<br>&quot;time"""
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.user.id, body=body)
        comment.save()
        self.assertEqual(body_formatted, comment.body_formatted())

    def test_user(self):
        """
        Comment.user should return the user or None, if that user doesn't exist for some
        reason.
        """
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.user.id, body="just a comment")
        comment.save()
        self.assertEqual(comment.user().id, self.user.id)
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=None, body="just a comment")
        comment.save()
        self.assertEqual(None, comment.user())

    def test_creating_comment_creates_conversation_for_commentor(self):
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.visitor.id, body="just a comment")
        comment.save()

        new_conversation = Conversation.get("user_id = %s and sharedfile_id = %s", self.visitor.id, self.sharedfile.id)
        self.assertTrue(new_conversation)

    def test_creating_second_comment_doesnt_create_additional_conversation(self):
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.visitor.id, body="just a comment")
        comment.save()
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.visitor.id, body="another comment")
        comment.save()

        new_conversation = Conversation.where("user_id = %s and sharedfile_id = %s", self.visitor.id, self.sharedfile.id)
        self.assertEqual(len(new_conversation), 1)

    def test_creating_comment_creates_conversation_for_sharedfile_owner(self):
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.visitor.id, body="just a comment")
        comment.save()

        new_conversation = Conversation.get("user_id = %s and sharedfile_id = %s", self.user.id, self.sharedfile.id)

        self.assertTrue(new_conversation)

    def test_creating_second_comment_doesnt_create_additional_conversation_for_sharedfile_owner(self):
        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.visitor.id, body="just a comment")
        comment.save()

        comment = Comment(sharedfile_id=self.sharedfile.id, user_id=self.visitor.id, body="another comment")
        comment.save()

        new_conversation = Conversation.where("user_id = %s and sharedfile_id = %s", self.user.id, self.sharedfile.id)
        self.assertEqual(len(new_conversation), 1)

    def test_comment_chopped_body(self):
        """
        Submits some lengthy comments and predicts their responses.
        """
        c_list = [
        """This is a comment <a href="/">With a url</a> in the middle of it.""",
        """











        """,
        """I am a long comment that really doesn't say much. Sorry. It's long and doesn't really add
anything to the conversation.""",
        """I am a long comment that really doesn't say much. Sorry. Good! and doesn't really add
anything to the conversation.""",
        ]


        new_c = Comment(sharedfile_id=self.sharedfile.id, user_id=self.user.id, body=c_list[0])
        new_c.save()
        self.assertEqual(new_c.chopped_body(), "This is a comment With a url in the middle of it.")

        new_c = Comment(sharedfile_id=self.sharedfile.id, user_id=self.user.id, body=c_list[1])
        new_c.save()
        self.assertEqual(new_c.chopped_body(), "&hellip;")

        new_c = Comment(sharedfile_id=self.sharedfile.id, user_id=self.user.id, body=c_list[2])
        new_c.save()
        self.assertEqual(new_c.chopped_body(), "I am a long comment that really doesn't say much. Sorry. It's&hellip;")

        new_c = Comment(sharedfile_id=self.sharedfile.id, user_id=self.user.id, body=c_list[3])
        new_c.save()
        self.assertEqual(new_c.chopped_body(), "I am a long comment that really doesn't say much. Sorry. Good!")

    def test_comment_mention_extraction(self):
        user_a = User(name='user_a',email='user_a@example.com',verify_email_token='created',email_confirmed=1)
        user_a.save()
        user_b = User(name='userb',email='user_b@example.com',verify_email_token='created',email_confirmed=1)
        user_b.save()
        user_c = User(name='user-c',email='user-c@example.com',verify_email_token='created',email_confirmed=1)
        user_c.save()
        user_d = User(name='Userd',email='Userd@example.com',verify_email_token='created',email_confirmed=1)
        user_d.save()

        body = """@thename hey there @user_a,@user_a
            and @userk and @userd and @userB
            @user-cdub also @user-c there."""
        new_c = Comment(sharedfile_id=self.sharedfile.id, user_id=self.user.id, body=body)
        mentions = new_c.extract_mentions()
        self.assertEqual(self.user.id, mentions[0].id)
        self.assertEqual(user_a.id, mentions[1].id)
        self.assertEqual(user_b.id, mentions[3].id)
        self.assertEqual(user_c.id, mentions[4].id)
        self.assertEqual(user_d.id, mentions[2].id)

