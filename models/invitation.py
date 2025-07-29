from lib.flyingcow import Model, Property
from lib.utilities import utcnow
from tornado.options import options

import postmark

import hashlib
import time
from . import user


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
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    
    @classmethod
    def create_for_email(self, email, user_id):
        """
        Creates an invitation for an email address.
        """
        h = hashlib.sha1()
        h.update(("%s" % (time.time())).encode('ascii'))
        h.update(("%s" % (email)).encode('ascii'))
        invitation_key = h.hexdigest()
        sending_user = user.User.get('id = %s', user_id)
        invitation = Invitation(user_id=user_id, invitation_key=invitation_key, email_address=email, claimed_by_user_id=0)
        invitation.save()
        if not options.debug:
            text_body = """Hi there. A user on MLTSHP named %s has sent you this invitation to join the site.

You can claim it at this URL:

https://%s/create-account?key=%s

Be sure to check out the incoming page for fresh files being uploaded, when you find someone you want to keep track of, click the "follow" button on their profile to see their files when you first sign in.

We're adding features and making updates daily so please check back often.

Once you have your account set up, check out:
https://%s/tools/plugins (browser plugins for saving images)
https://mefi.social/@best_of_mltshp (our Mastodon account)
https://mltshphq.tumblr.com/ (our blog)

- MLTSHP""" % (sending_user.name, options.app_host, invitation_key, options.app_host, options.app_host)
            html_body = """<p>Hi there. A user on MLTSHP named <a href="https://%s/user/%s">%s</a> has sent you this invitation to join the site.</p>

<p>You can claim it at this URL:</p>

<p><a href="https://%s/create-account?key=%s">https://%s/create-account?key=%s</a></p>

<p>Be sure to check out the <a href="https://%s/incoming">incoming</a> page for fresh files being uploaded, when you find someone you want to keep track of, click the "follow" button on their profile to see their files when you first sign in.</p>

<p>We&#39;re adding features and making updates daily so please check back often.</p>

<p>Once you have your account set up, check out:</p>
<p>
<a href="https://%s/tools/plugins">https://%s/tools/plugins</a> (browser plugins for saving images)<br>
<a href="https://mefi.social/@best_of_mltshp">https://mefi.social/@best_of_mltshp</a> (our Mastodon account)<br>
<a href="https://mltshphq.tumblr.com/">https://mltshp.tumblr.com/</a> (our weblog)
</p>
<p>
- MLTSHP
</p>""" % (options.app_host, sending_user.name, sending_user.name,
           options.app_host, invitation_key, options.app_host, invitation_key,
           options.app_host, options.app_host, options.app_host, options.app_host, options.app_host)

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
            
