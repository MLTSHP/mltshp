from lib.flyingcow import Model, Property
from tornado.options import options

import postmark

import hashlib
import time
import user
from datetime import datetime


class Invitation(Model):
    # Id of user who sent the invitation out
    user_id = Property()

    # Id of user who used the invitation
    claimed_by_user_id = Property()
 
    # somewhat secret key to point to invitation
    invitation_key = Property()
 
    # email address that invitation key was sent to
    email_address = Property()

    # name of person who invitation was meant for
    name = Property()
        
    created_at = Property()
    claimed_at = Property()
    
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Invitation, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    
    @classmethod
    def create_for_email(self, email, user_id):
        """
        Creates an invitation for an email address.
        """
        h = hashlib.sha1()
        h.update("%s" % (time.time()))
        h.update("%s" % (email))
        invitation_key = h.hexdigest()
        sending_user = user.User.get('id = %s', user_id)
        invitation = Invitation(user_id=user_id, invitation_key=invitation_key, email_address=email, claimed_by_user_id=0)
        invitation.save()
        if not options.debug:
            text_body = """Hi there. A user on MLTSHP named %s has sent you this invitation to join the site.

You can claim it at this URL:

http://mltshp.com/create-account?key=%s

Be sure to check out the incoming page for fresh files being uploaded, when you find someone you want to keep track of, click the "follow" button on their profile to see their files when you first sign in.

We're adding features and making updates daily so please check back often.

Once you have your account set up, check out:
http://mltshp.com/tools/plugins (browser plugins for saving images)
http://mltshp.com/tools/twitter (connecting your phone's Twitter app to use MLTSHP instead of Twitpic or yFrog)
http://twitter.com/mltshp (our twitter account)
http://mltshp.tumblr.com/ (our blog)

- MLTSHP""" % (sending_user.name, invitation_key)
            html_body = """<p>Hi there. A user on MLTSHP named <a href="http://mltshp.com/user/%s">%s</a> has sent you this invitation to join the site.</p>

<p>You can claim it at this URL:</p>

<p><a href="http://mltshp.com/create-account?key=%s">http://mltshp.com/create-account?key=%s</a></p>

<p>Be sure to check out the <a href="http://mltshp.com/incoming">incoming</a> page for fresh files being uploaded, when you find someone you want to keep track of, click the "follow" button on their profile to see their files when you first sign in.</p>

<p>We&#39;re adding features and making updates daily so please check back often.</p>

<p>Once you have your account set up, check out:</p>
<p>
<a href="http://mltshp.com/tools/plugins">http://mltshp.com/tools/plugins</a> (browser plugins for saving images)<br>
<a href="http://mltshp.com/tools/twitter">http://mltshp.com/tools/twitter</a> (connecting your phone's Twitter app to use MLTSHP instead of Twitpic or yFrog)<br>
<a href="http://twitter.com/mltshp">http://twitter.com/mltshp</a> (our twitter account)<br>
<a href="http://mltshp.tumblr.com/">http://mltshp.tumblr.com/</a> (our weblog)
</p>
<p>
- MLTSHP
</p>""" % (sending_user.name,sending_user.name, invitation_key,invitation_key)

            pm = postmark.PMMail(api_key=options.postmark_api_key, 
                sender="hello@mltshp.com", to=email, 
                subject="An Invitation To MLTSHP", 
                text_body=text_body,
                html_body=html_body)
            pm.send()
        return invitation


    @classmethod
    def by_email_address(self, email):
        """
        Returns invitation where email address matches and is not claimed.  We use a 
        where query here since we don't enforce uniqueness on email address. Just returns 1st.
        """
        if not email:
            return None
        invitations = self.where("email_address = %s and claimed_by_user_id = 0", email)
        try:
            return invitations[0]
        except IndexError:
            return None
    
    @classmethod
    def by_invitation_key(self, key):
        """
        Returns invitation where email address matches and is not claimed.  We use a 
        where query here since we don't enforce uniqueness on key. Just returns 1st.
        """
        if not key:
            return None
        invitations = self.where("invitation_key = %s and claimed_by_user_id = 0", key)
        try:
            return invitations[0]
        except IndexError:
            return None
    
    @classmethod
    def by_user(self, user_):
        """
        Returns all invitations sent out by user.
        """
        return self.where("user_id = %s", user_.id)
            
