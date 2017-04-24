from datetime import datetime, timedelta
import re

from tornado import escape
from tornado.options import options
from lib.flyingcow import Model, Property
from lib.utilities import pretty_date
from BeautifulSoup import BeautifulSoup

import user
import notification
import sharedfile
import conversation


class Comment(Model):
    user_id = Property()
    sharedfile_id = Property()
    body    = Property()
    deleted = Property(default=0)
    created_at = Property()
    updated_at = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Comment, self).save(*args, **kwargs)

    def on_create(self):
        """
        Creates a notification for the user that owns the shared file
        (does not create a new notification if you are the user)
        """
        sf = self.sharedfile()
        if self.user_id != sf.user_id:
            notification.Notification.new_comment(self)

        #creates a conversation for a user if one doesn't exist.
        existing_conversation = conversation.Conversation.get('user_id = %s and sharedfile_id = %s', self.user_id, self.sharedfile_id)
        if not existing_conversation:
            new_conversation = conversation.Conversation(user_id = self.user_id, sharedfile_id = self.sharedfile_id)
            new_conversation.save()

        #creates a conversation for sharedfile.user_id if one doesn't exist
        existing_conversation = conversation.Conversation.get('user_id = %s and sharedfile_id=%s', sf.user_id, self.sharedfile_id)
        if not existing_conversation:
            new_conversation = conversation.Conversation(user_id = sf.user_id, sharedfile_id = self.sharedfile_id)
            new_conversation.save()

        # update the SF activity_at
        sf.activity_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        sf.save()

        # find any mentions and create notifciations
        mentions = self.extract_mentions()
        for u in mentions:
            notification.Notification.new_mention(u, self)

    def as_json(self):
        return {
            'body': self.body,
            'user': self.user().as_json(),
            'posted_at' : self.created_at.replace(microsecond=0, tzinfo=None).isoformat() + 'Z',
        }

    def sharedfile(self):
        return sharedfile.Sharedfile.get('id = %s', self.sharedfile_id)

    def chopped_body(self):
        """
        Returns a comment that has its HTML removed, shortened to 15 words, and if it doesn't end in a period, add ...
        """
        new_body  = ''.join(BeautifulSoup(self.body).findAll(text=True))
        new_body = new_body.replace('\n', '')
        body_parts = new_body.split(' ')
        new_body = body_parts[:12]
        new_body = " ".join(new_body)
        if not new_body.endswith(('.', '!', '?')):
            new_body = "%s&hellip;" % new_body
        return new_body

    def user(self):
        """
        Returns comment's user.
        """
        return user.User.get("id = %s", self.user_id)

    def pretty_created_at(self):
        """
        A friendly version of the created_at date.
        """
        return pretty_date(self.created_at)

    def body_formatted(self):
        """
        An escaped and formatted body of the comment with \n replaced by HTML <br>
        """
        #body = escape.xhtml_escape(self.body)
        #print body
        #body = escape.linkify(body, True) #someday?
        #for now use Bleach
        #bl = Bleach()
        #body = bl.linkify(body, nofollow=True)
        #body = body.replace('</a>/', '/</a>')
        #body = body.replace('<a href=', '<a target="_blank" href=')
        body = escape.linkify(self.body, True, extra_params='rel="nofollow" target="_blank"')
        body = body.replace('\n', '<br>')
        return body

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def extract_mentions(self):
        """
        This method extracts all the users mentioned in a body.
        *ONLY* returns valid users and only returns one user per comment.
        """
        user_list = []
        if self.body == None or self.body == '':
            return user_list
        matches = re.findall('@([A-Za-z0-9_\-]+)', self.body)
        for match in matches:
            matching_user = user.User.get('name=%s', match)
            if matching_user and matching_user.id not in [u.id for u in user_list]:
                user_list.append(matching_user)
        return user_list

    def can_user_delete(self, user):
        """
        Determines whether a passed in user can delete the current
        comment. Only the person that owns the comment or the person
        that owns the file the comment references can delete a comment.
        """
        if options.readonly:
            return False
        if self.user_id == user.id:
            return True
        if self.sharedfile().user_id == user.id:
            return True
        return False

    def delete(self):
        self.deleted = 1
        self.save()

    @classmethod
    def add(self, user=None, sharedfile=None, body=None):
        """
        Creates a comment and returns it, or returns None if some conditions
        are not met.
        """
        if not user or not sharedfile or not body:
            return None

        if user.restricted:
            return None

        body = body.strip()
        if len(body) == 0:
            return None

        # Dropping this rule for now, since we will have 100%
        # paying members for commenters...
        # now = datetime.utcnow()
        # if user.created_at > (now - timedelta(hours=24)):
        #     if user.sharedfiles_count() == 0 and user.likes_count() == 0:
        #         if Comment.where_count("user_id = %s", user.id) >= 1:
        #             user.restricted = 1
        #             user.save()
        #             all_comments = Comment.where('user_id=%s', user.id)
        #             for this_comment in all_comments:
        #                 this_comment.delete()

        comment = Comment(user_id=user.id, sharedfile_id=sharedfile.id, body=body)
        comment.save()
        return comment


