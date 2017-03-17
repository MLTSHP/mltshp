import tornado.web

from base import BaseHandler
from models import Conversation, Notification, Comment, Sharedfile

class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, show_only=None, page=None):
        current_user_object = self.get_current_user_object()
        if not page:
            page = 1
        page = int(page)
        if show_only == 'my-files':
            url_format = '/conversations/my-files/%d'
            conversations = Conversation.for_user(current_user_object.id, type='myfiles', page=page)
            conversations_count = Conversation.for_user_count(current_user_object.id, type='myfiles')
        elif show_only == 'my-comments':
            url_format = '/conversations/my-comments/%d'
            conversations = Conversation.for_user(current_user_object.id, type='mycomments', page=page)
            conversations_count = Conversation.for_user_count(current_user_object.id, type='mycomments')
        else:
            show_only = 'all'
            url_format = '/conversations/all/%d'
            conversations = Conversation.for_user(current_user_object.id, page=page)
            conversations_count = Conversation.for_user_count(current_user_object.id)
        
        conversations_marshalled = []
        for conversation in conversations:
            conversations_marshalled.append({
                'sharedfile' : conversation.sharedfile(),
                'comments' : conversation.relevant_comments(),
                'conversation' : conversation
            })
            
        return self.render("conversations/index.html", conversations=conversations_marshalled, \
            page=page, count=conversations_count, url_format=url_format, selected=show_only)

class MuteHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, conversation_id):
        """
        Mutes a conversation for a user and redirects them to /conversations
        """
        current_user_object = self.get_current_user_object()
        conversation = Conversation.get('id = %s and user_id = %s', conversation_id, current_user_object.id)
        if conversation:
            conversation.mute()
        return self.redirect('/conversations')

class MentionsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, page=None):
        current_user_object = self.get_current_user_object()
        if not page:
            page = 1
        page = int(page)
        
        mentions_marshalled = []
        mentions = Notification.mentions_for_user(current_user_object.id, int(page))
        mentions_count = Notification.mentions_for_user_count(current_user_object.id)

        url_format = '/mentions/%d'
        for mention in mentions:
            c = Comment.get('id = %s and deleted = 0', mention.action_id)
            if c:
                sf = Sharedfile.get('id = %s and deleted = 0', c.sharedfile_id)
                if sf:
                    mentions_marshalled.append({
                        'comment': c,
                        'sharedfile': sf,
                    })

        # this clears all mentions. When you visit this page
        ns = Notification.where('type=%s and receiver_id=%s and deleted=0', 'mention', current_user_object.id)
        [n.delete() for n in ns]
        
        return self.render("conversations/mentions.html", mentions=mentions_marshalled, count=mentions_count, \
            page=page, url_format=url_format, selected='mentions')
