from lib.flyingcow import Model, Property
from tornado.options import options
from datetime import datetime, timedelta
import postmark

from . import sharedfile
from . import user
from . import comment
from . import shake
from . import invitation
from . import subscription


class Notification(Model):
    sender_id   = Property()
    receiver_id = Property()
    action_id   = Property()
    type        = Property() # favorite, save, subscriber
    deleted     = Property(default=0)
    created_at  = Property()
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Notification, self).save(*args, **kwargs)
    
    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")            

    def delete(self):
        self.deleted = 1
        self.save()
        
    def sender(self):
        return user.User.get("id=%s", self.sender_id)
        
    def receiver(self):
        return user.User.get("id=%s", self.receiver_id)
    
    def related_object(self):
        """
        Return the object this notification relates to. In the case of a favorite
        or a like, it should return shared file. In the case of a follow, the user
        that followed.
        """
        if self.type in ['favorite', 'save']:
            return sharedfile.Sharedfile.get("id=%s and deleted=0", self.action_id)
        elif self.type == 'comment':
            return comment.Comment.get("id=%s and deleted=0", self.action_id)
        elif self.type in ['invitation', 'invitation_request', 'invitation_approved']:
            return shake.Shake.get("id=%s and deleted=0", self.action_id)
        elif self.type == 'subscriber':
            subscription_ = subscription.Subscription.get("id = %s and deleted=0", self.action_id)
            return subscription_ and subscription_.shake()
        else:
            return user.User.get("id = %s and deleted=0", self.sender_id)
    
    @classmethod
    def invitation_to_shake_for_user(self, shake, user):
        """
        Returns outstanding invitation notification to a shake for a user.
        """
        return self.get("type = 'invitation' and action_id = %s and receiver_id = %s and deleted = 0 LIMIT 1", shake.id, user.id)

    @classmethod
    def mentions_for_user(self, user_id, page=1, per_page=10):
        limit_start = (page-1) * per_page
        select = """
          SELECT * from notification 
            WHERE receiver_id = %s
            AND type = 'mention'
            ORDER BY id desc
          LIMIT %s, %s
        """ % (user_id, limit_start, per_page)
        notifications = self.object_query(select)
        return notifications 

    @classmethod
    def mentions_for_user_count(self, user_id):
        select = """
          SELECT count(id) as count from notification 
            WHERE receiver_id = %s
            AND type = 'mention'
        """ % (user_id)
        result = self.query(select)
        return result[0]['count'] 

    @classmethod
    def count_for_user_by_type(self, user_id, _type='invitation'):
        """
        Count of outstanding notifications for a specified user, by 
        notification type.
        """
        return self.where_count("receiver_id = %s and type = %s and deleted = 0", user_id, _type)

    @classmethod
    def display_for_user(cls, user):
        """
        Returns a data structure used in display all open notifications
        for a specified user.  Collapses likes and follows into one
        notification if they reference same image.
        """
        notifications = { 'like' : {'count' : 0, 'items' : {}}, 
                          'save' : {'count' : 0, 'items' : {}}, 
                          'follow' : [] , 
                          'comment' : [], 
                          'mention': [], 
                          'invitation':[],
                          'invitations': [], # TODO: kill this ambiguity - IK
                          'invitation_request' : [],
                          'invitation_approved' : []
                        }
        for notification in cls.for_user(user):
            sender = notification.sender()
            related_object = notification.related_object()
            if not related_object:
                continue

            _notification = {'sender' : sender, 'related_object' : related_object, 'id' : notification.id}
            
            if notification.type == 'favorite':
                if related_object.id not in notifications['like']['items']:
                    notifications['like']['items'][related_object.id] = []
                notifications['like']['items'][related_object.id].append(_notification)
                notifications['like']['count'] += 1
                
            elif notification.type == 'subscriber':
                _notification['post_name_text'] = " is now following " + related_object.display_name(user)
                notifications['follow'].append(_notification)
                
            elif notification.type == 'save':
                if related_object.id not in notifications['save']['items']:
                    notifications['save']['items'][related_object.id] = []
                notifications['save']['items'][related_object.id].append(_notification)
                notifications['save']['count'] += 1

            elif notification.type == 'comment':
                notifications['comment'].append(_notification)

            elif notification.type == 'mention':
                notifications['mention'].append(_notification)

            elif notification.type == 'invitation':
                notifications['invitation'].append(_notification)
            
            elif notification.type == 'invitation_request':
                notifications['invitation_request'].append(_notification)
            
            elif notification.type == 'invitation_approved':
                notifications['invitation_approved'].append(_notification)
            
        #for invitation_ in invitation.Invitation.by_user(user):
        #    notifications['invitations'].append(invitation_.email_address)
        return notifications
        
    @classmethod
    def for_user(cls, user, deleted=False):
        """
        Notifications for user. Defaults to open,
        i.e. non-deleted notifications.
        """
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        return cls.where("receiver_id = %s and deleted = %s and created_at > %s order by created_at desc", 
                                   user.id, deleted, one_week_ago.strftime("%Y-%m-%d %H:%M:%S"))

    @classmethod
    def for_user_count(cls, user, deleted=False):
       """
       Count of all notifications for user.  Defaults to open,
       i.e. non-deleted notifications.
       """
       one_week_ago = datetime.utcnow() - timedelta(days=7)
       return cls.where_count("receiver_id = %s and deleted = %s and created_at > %s order by created_at desc", 
                                        user.id, deleted, one_week_ago.strftime("%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def new_favorite(sender, sharedfile):
        """
        sender - user who created the favorite
        sharedfile - the file that was favorited. 
            the receiver in this case is the sharedfile.user_id
        """
        n = Notification(sender_id=sender.id, receiver_id=sharedfile.user_id, action_id=sharedfile.id, type='favorite')
        n.save()
        return n
    
    @staticmethod
    def new_save(sender, sharedfile):
        """
        sender - user who created the sharedfile
        sharedfile - the originating file that was saved from.
            the receiver in this case is the sharedfile.user_id
        """
        n = Notification(sender_id=sender.id, receiver_id=sharedfile.user_id, action_id=sharedfile.id, type='save')
        n.save()
        return n

    @staticmethod
    def new_comment(comment):
        """
        sender - person leaving the comment
        sharedfile - the file that was commented on
        comment - the comment being left
        """
        sf = sharedfile.Sharedfile.get('id=%s', comment.sharedfile_id)
        n = Notification(sender_id=comment.user_id, receiver_id=sf.user_id, action_id=comment.id, type='comment')
        n.save()
        return n
    
    @staticmethod
    def new_comment_like(comment, sender):
        """
        sender - person doing the liking
        comment - the comment that was liked
        receiver - the person who received the like
        """
        n = Notification(sender_id=sender.id, receiver_id=comment.user_id,
                action_id=comment.id, type='comment_like')
        n.save()
        return n

    @staticmethod
    def new_mention(receiver, comment):
        """
        receiver - user who is mentioned
        comment - the comment it appeared in
        """
        n = Notification(sender_id=comment.user_id, receiver_id=receiver.id, action_id=comment.id, type='mention')
        n.save()
        return n
        
    @staticmethod
    def new_invitation_request_accepted(sender, receiver, shake):
        """
        sender - user who granted invitation
        receiver - user who was invited in
        shake
        """
        n = Notification(sender_id=sender.id, receiver_id=receiver.id, action_id=shake.id, type='invitation_approved')
        n.save()

    @staticmethod
    def new_invitation_to_shake(sender, receiver, action_id):
        """
        sender - user making request
        receiver - user who owns the shake
        action_id - the shake_id
        """
        the_shake = shake.Shake.get('id=%s', action_id)
        
        n = Notification(sender_id=sender.id, receiver_id=receiver.id, action_id=action_id, type='invitation_request')
        text_message = """Hi, %s.
%s has requested to join "%s". This means they will be able to put files into the "%s" shake.

If you want to let %s do this, simply visit your shake and approve the request:

https://%s/%s

You can also ignore the request by deleting the notification.
""" % (receiver.display_name(), sender.display_name(), the_shake.display_name(), the_shake.display_name(),
       sender.display_name(), options.app_host, the_shake.name)
        html_message = """<p>Hi, %s.</p>
<p><a href="https://%s/user/%s">%s</a> has requested to join "<a href="https://%s/%s">%s</a>". This means they will be able to put files into the "%s" shake.</p>

<p>If you want to let %s do this, simply visit your shake and approve the request:</p>

<p><a href="https://%s/%s">https://%s/%s</a></p>

You can also ignore the request by deleting the notification.
""" % (receiver.display_name(), options.app_host, sender.name, sender.display_name(),
       options.app_host, the_shake.name, the_shake.display_name(), the_shake.display_name(),
       sender.display_name(), options.app_host, the_shake.name, options.app_host, the_shake.name)

        n.save()
        if not receiver.disable_notifications and not options.debug:
            pm = postmark.PMMail(api_key=options.postmark_api_key, 
                sender="hello@mltshp.com", to=receiver.email, 
                subject="%s has requested an invitation to %s!" % (sender.display_name(), the_shake.display_name()), 
                text_body=text_message, 
                html_body=html_message)
            pm.send()
        return n

    @staticmethod
    def new_invitation(sender, receiver, action_id):
        """
        sender - user who created invitation
        receiver - user who is being invited
        action_id - the shake_id
        """
        new_shake = shake.Shake.get('id = %s', action_id)
        n = Notification(sender_id=sender.id, receiver_id=receiver.id, action_id=action_id, type='invitation')
        text_message = """Hi, %s.
We wanted to let you know %s has invited you to join "%s". Being a member of "%s" means you can upload files to the shake with others who are members.

You can agree to join here:

https://%s/%s

If you do join you'll notice a new shake name when you upload or save files.
""" % (receiver.name, sender.display_name(), new_shake.display_name(), new_shake.display_name(),
       options.app_host, new_shake.name)
        html_message = """<p>Hi, %s.</p>
<p>We wanted to let you know <a href="https://%s/user/%s">%s</a> has invited you to join "<a href="https://%s/%s">%s</a>".
Being a member of "<a href="https://%s/%s">%s</a>" means you can upload files to the shake along with others who are members.</p>

<p>
You can agree to join here:
</p>
<p>
<a href="https://%s/%s">https://%s/%s</a>
</p>
<p>
If you do join you'll notice a new shake name when you upload or save files.
</p>
""" % (receiver.name, options.app_host, sender.name, sender.display_name(), options.app_host,
       new_shake.name, new_shake.display_name(), options.app_host, new_shake.name,
       new_shake.display_name(), options.app_host, new_shake.name, options.app_host, new_shake.name)
            
        n.save()

        if not receiver.disable_notifications and not options.debug:
            pm = postmark.PMMail(api_key=options.postmark_api_key, 
                sender="hello@mltshp.com", to=receiver.email, 
                subject="%s has invited you to join %s!" % (sender.display_name(), new_shake.display_name()), 
                text_body=text_message, 
                html_body=html_message)
            pm.send()
        return n
        
    @staticmethod
    def new_subscriber(sender, receiver, action_id):
        """
        sender - user who created the subscription
        receiver - user who is being followed (their shake is)
        action_id - the subscription id
        """
        new_subscription = subscription.Subscription.get('id = %s', action_id)
        target_shake = shake.Shake.get('id = %s', new_subscription.shake_id)
        subscription_line = ""
        if target_shake.type == 'group':
            subscription_line = " called '%s'" % (target_shake.name)
        
        n = Notification(sender_id=sender.id, receiver_id=receiver.id, action_id=action_id, type='subscriber')

        text_message = """Hi, %s.
We wanted to let you know %s is now following your shake%s. If you want to check out their shake you can do so here:

https://%s/user/%s

You can change your preferences for receiving notifications on your settings page: https://%s/account/settings

Have a good day.
- MLTSHP
""" % (receiver.name, sender.name, subscription_line, options.app_host, sender.name, options.app_host)
        html_message = """<p>Hi, %s.</p>
<p>                        
We wanted to let you know <a href="https://%s/user/%s">%s</a> is now following your shake%s. If you want to check out their shake you can do so here:
</p>
<p>
<a href="https://%s/user/%s">https://%s/user/%s</a>
</p>
<p>
You can change your preferences for receiving notifications on your settings page: <a href="https://%s/account/settings">https://%s/account/settings</a>.
</p>
<p>
Have a good day.<br>
- MLTSHP
</p>
""" % (receiver.name, options.app_host, sender.name, sender.name, subscription_line,
       options.app_host, sender.name, options.app_host, sender.name, options.app_host,
       options.app_host)

        n.save()
        
        if not receiver.disable_notifications and not options.debug:
            pm = postmark.PMMail(api_key=options.postmark_api_key, 
                sender="hello@mltshp.com", to=receiver.email, 
                subject="%s is now following your shake!" % (sender.name), 
                text_body=text_message, 
                html_body=html_message)
            pm.send()
        return n
        
    @staticmethod
    def send_shake_member_removal(former_shake, former_member):
        """
        Sends an email informing someone they were removed from a shake.
        """
        text_message = """Hi %s.
This is a note to let you know you were removed as a member of "%s". 

You can still follow the shake, but the editor has decided to remove you as an image contributor.

Editors remove members for various reasons. Either the shake is shutting down or they want to do something different with it.

Thank you,
- MLTSHP
""" % (former_member.display_name(), former_shake.display_name())
        if not former_member.disable_notifications and not options.debug:
            pm = postmark.PMMail(api_key=options.postmark_api_key, 
                sender="hello@mltshp.com", to=former_member.email, 
                subject="Removal from %s shake" % (former_shake.display_name()), 
                text_body=text_message)
            pm.send()
        
