from lib.flyingcow import Model, Property
from tornado.options import options

import postmark

import hashlib
import time
from . import user
import datetime

from . import promotion

from lib.utilities import payment_notifications, utcnow


class Voucher(Model):
    # parent Id of a user, if a user offered the
    # voucher
    offered_by_user_id = Property()

    # Id of user who used the voucher
    claimed_by_user_id = Property()
 
    # somewhat secret key to point to voucher
    voucher_key = Property()
 
    # email address that voucher key was sent to
    # if applicable
    email_address = Property()

    # name of person who voucher was meant for
    name = Property()
        
    created_at = Property()
    claimed_at = Property()

    # promotion this voucher relates to
    promotion_id = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Voucher, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def get_promotion(self):
        if self.promotion_id:
            return promotion.Promotion.get("id = %s", self.promotion_id)
        else:
            return None

    @classmethod
    def create_for_email(self, email, user_id):
        """
        Creates a voucher for an email address.
        """
        h = hashlib.sha1()
        h.update("%s" % (time.time()))
        h.update("%s" % (email))
        voucher_key = h.hexdigest()
        sending_user = user.User.get('id = %s', user_id)
        voucher = Voucher(offered_by_user_id=user_id,
            voucher_key=voucher_key, email_address=email,
            claimed_by_user_id=0)
        voucher.save()
        if not options.debug:
            text_body = """Hi there. A user on MLTSHP named %s has sent you this invitation to join the site.

You can claim it at this URL:

https://%s/create-account?key=%s

Be sure to check out the incoming page for fresh files being uploaded, when you find someone you want to keep track of, click the "follow" button on their profile to see their files when you first sign in.

We're adding features and making updates daily so please check back often.

Once you have your account set up, check out:
https://%s/tools/plugins (browser plugins for saving images)
https://%s/tools/twitter (connecting your phone's Twitter app to use MLTSHP instead of Twitpic or yFrog)
https://twitter.com/mltshphq (our twitter account)
https://mltshp.tumblr.com/ (our blog)

- MLTSHP""" % (sending_user.name, options.app_host, voucher_key, options.app_host, options.app_host)
            html_body = """<p>Hi there. A user on MLTSHP named <a href="https://%s/user/%s">%s</a> has sent you this invitation to join the site.</p>

<p>You can claim it at this URL:</p>

<p><a href="https://%s/create-account?key=%s">https://%s/create-account?key=%s</a></p>

<p>Be sure to check out the <a href="https://%s/incoming">incoming</a> page for fresh files being uploaded, when you find someone you want to keep track of, click the "follow" button on their profile to see their files when you first sign in.</p>

<p>We&#39;re adding features and making updates daily so please check back often.</p>

<p>Once you have your account set up, check out:</p>
<p>
<a href="https://%s/tools/plugins">https://%s/tools/plugins</a> (browser plugins for saving images)<br>
<a href="https://%s/tools/twitter">https://%s/tools/twitter</a> (connecting your phone's Twitter app to use MLTSHP instead of Twitpic or yFrog)<br>
<a href="https://twitter.com/mltshphq">https://twitter.com/mltshphq</a> (our twitter account)<br>
<a href="https://mltshphq.tumblr.com/">https://mltshphq.tumblr.com/</a> (our blog)
</p>
<p>
- MLTSHP
</p>""" % (options.app_host, sending_user.name, sending_user.name,
           options.app_host, voucher_key, options.app_host, voucher_key,
           options.app_host, options.app_host, options.app_host, options.app_host,
           options.app_host)

            pm = postmark.PMMail(api_key=options.postmark_api_key, 
                sender="hello@mltshp.com", to=email, 
                subject="An Invitation To MLTSHP", 
                text_body=text_body,
                html_body=html_body)
            pm.send()
        return voucher

    @classmethod
    def by_email_address(self, email):
        """
        Returns voucher where email address matches and is not claimed.  We use a 
        where query here since we don't enforce uniqueness on email address.
        Just returns 1st.
        """
        if not email:
            return None
        vouchers = self.where("email_address = %s and claimed_by_user_id = 0", email)
        try:
            return invitations[0]
        except IndexError:
            return None
    
    @classmethod
    def by_voucher_key(self, key):
        """
        Returns voucher by key.  We use a where query here since we don't enforce
        uniqueness on key. Just returns 1st.

        WILL return a voucher even if it is claimed.
        """
        if not key:
            return None
        vouchers = self.where("voucher_key = %s", key)
        try:
            return vouchers[0]
        except IndexError:
            return None
    
    @classmethod
    def by_user(self, user_):
        """
        Returns all vouchers sent out by user.
        """
        return self.where("offered_by_user_id = %s", user_.id)

    def apply_to_user(self, user_):
        from models import PaymentLog

        promotion = self.get_promotion()

        self.offered_by_user_id = 0

        if not self.offered_by_user_id and promotion is not None:
            shake = promotion.shake()
            if shake is not None:
                # if this promotion is related to a shake
                # associate the voucher with that shake's owner
                self.offered_by_user_id = shake.user_id

        now = utcnow()

        # if the user has a voucher, then we need
        # to apply a credit to their account using
        # payment_log in addition to creating the
        # voucher record and claiming it.
        self.claimed_by_user_id = user_.id
        self.claimed_at = now.strftime("%Y-%m-%d %H:%M:%S")
        self.save()

        # now record to payment_log that this
        # user has claimed a voucher.
        next_date = None
        amount = None

        promotion = self.get_promotion()
        # make a sensible "transaction amount" description
        # that we use for the settings screen
        if promotion is not None \
            and promotion.membership_months > 0:
            months = promotion.membership_months
            days = int((365 * (months/12.0)) + 0.5)
            next_date = now + datetime.timedelta(days=days)
            if months >= 12 and months % 12 == 0:
                years = months / 12
                if years == 1:
                    amount = '1 Year'
                elif years > 1:
                    amount = '%d Years' % years
            elif months == 1:
                amount = '1 Month'
            elif months > 1:
                amount = '%d Months' % months

            pl = PaymentLog(
                user_id                   = user_.id,
                status                    = "credit",
                reference_id              = promotion.id,
                transaction_id            = self.voucher_key,
                operation                 = "redeem",
                transaction_date          = now.strftime("%Y-%m-%d %H:%M:%S"),
                next_transaction_date     = next_date.strftime("%Y-%m-%d %H:%M:%S"),
                buyer_email               = user_.email,
                buyer_name                = (user_.full_name or user_.name),
                transaction_amount        = amount,
                payment_reason            = "MLTSHP Paid Account",
                payment_method            = "voucher",
                processor                 = PaymentLog.VOUCHER,
                transaction_serial_number = 0
            )
            pl.save()

            # update user paid status if necessary
            if user_.is_paid != 1:
                user_.is_paid = 1
                user_.save()
                payment_notifications(user_, "redeemed", amount)
