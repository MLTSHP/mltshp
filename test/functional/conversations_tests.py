import time
from tornado.httpclient import HTTPRequest
from tornado.escape import url_escape

import test.base
from models import User, Sharedfile, Sourcefile, Conversation, Comment

class ConversationTests(test.base.BaseAsyncTestCase):
    def setUp(self):
        super(ConversationTests, self).setUp()
        self.admin = User(name='admin', email='admin@mltshp.com', email_confirmed=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()
        
        self.user2 = User(name='user2', email='user2@example.com', email_confirmed=1)
        self.user2.set_password('asdfasdf')
        self.user2.save()
        
        self.sid = self.sign_in('user2', 'asdfasdf')
        self.xsrf = self.get_xsrf()

        self.src = Sourcefile(width=1, height=1, file_key='asdf', thumb_key='qwer')
        self.src.save()
        self.shf = Sharedfile(source_id=self.src.id, user_id=self.admin.id, name='shared.jpg', title='shared', share_key='1', content_type='image/jpg')
        self.shf.save()
    
    def test_creating_a_new_comment_creates_a_conversation(self):
        request = HTTPRequest(self.get_url('/p/%s/comment' % self.shf.share_key), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, "body=%s&_xsrf=%s" % (url_escape("a comment"), self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        
        conversations = Conversation.all()
        self.assertEqual(len(conversations), 2)

    def test_creating_a_new_comment_does_not_create_a_duplicate_conversation(self):
        request = HTTPRequest(self.get_url('/p/%s/comment' % self.shf.share_key), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, "body=%s&_xsrf=%s" % (url_escape("a comment"), self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        request = HTTPRequest(self.get_url('/p/%s/comment' % self.shf.share_key), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, "body=%s&_xsrf=%s" % (url_escape("a second comment"), self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        
        conversations = Conversation.all()
        self.assertEqual(len(conversations), 2)

        
    def test_another_user_commenting_will_update_the_files_activity_at(self):
        request = HTTPRequest(self.get_url('/p/%s/comment' % self.shf.share_key), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, "body=%s&_xsrf=%s" % (url_escape("a comment"), self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        time.sleep(1)

        
        sf = Sharedfile.get('id=%s', self.shf.id)
        activity_one = sf.activity_at

        request = HTTPRequest(self.get_url('/p/%s/comment' % self.shf.share_key), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, "body=%s&_xsrf=%s" % (url_escape("a second comment"), self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        
        sf = Sharedfile.get('id=%s', self.shf.id)
        activity_two = sf.activity_at

        self.assertTrue(activity_two > activity_one)

    
    def test_deleting_a_file_will_set_conversation_to_muted(self):
        request = HTTPRequest(self.get_url('/p/%s/comment' % self.shf.share_key), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, "body=%s&_xsrf=%s" % (url_escape("a comment"), self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        request = HTTPRequest(self.get_url('/p/%s/comment' % self.shf.share_key), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, "body=%s&_xsrf=%s" % (url_escape("a second comment"), self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()

        self.shf.delete()
        
        conversations = Conversation.all()
        self.assertEqual(conversations[0].muted, 1)
        self.assertEqual(conversations[1].muted, 1)
        
    
    def test_muting_conversation(self):
        """
        Add a comment, which will create a conversation for the commenter (user2) and sharedfile owner (admin).
                
        When user2 tries to mute admin's conversation, it should fail and admin's conversation state will remain 
        unchanged.  When muting own converastion, "muted" flag should change to true.
        
        Contingent on user2 being signed in. (see setUp)
        """
        comment = Comment(sharedfile_id=self.shf.id, user_id=self.user2.id, body='test')
        comment.save()
        
        admin_conversation = Conversation.get('user_id = %s', self.admin.id)
        user2_conversation = Conversation.get('user_id = %s', self.user2.id)
        self.assertEqual(admin_conversation.muted, 0)
        self.assertEqual(user2_conversation.muted, 0)
        
        request = HTTPRequest(self.get_url('/conversations/%s/mute' % admin_conversation.id), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
        request = HTTPRequest(self.get_url('/conversations/%s/mute' % user2_conversation.id), 'POST', {'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, "_xsrf=%s" % (self.xsrf))
        self.http_client.fetch(request, self.stop)
        response = self.wait()
                
        # refetch from DB, and verify mute flags remain 0.
        admin_conversation = Conversation.get('user_id = %s', self.admin.id)
        user2_conversation = Conversation.get('user_id = %s', self.user2.id)
        self.assertEqual(admin_conversation.muted, 0)
        self.assertEqual(user2_conversation.muted, 1)
        
        
    def test_order_of_conversations_changes_when_new_comment_is_created(self):
        pass
