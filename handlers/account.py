import datetime
import re
import json
from urllib import urlencode

import tornado.httpclient
import tornado.web
from tornado.escape import json_encode, xhtml_escape
from tornado.options import define, options
import torndb
import postmark
from recaptcha.client import captcha

from base import BaseHandler, require_membership
from models import User, Invitation, Shake, Notification, Conversation, Invitation,\
    App, PaymentLog, Voucher, Promotion, MigrationState
from lib.utilities import email_re, base36decode, is_valid_voucher_key,\
    payment_notifications, uses_a_banned_phrase, plan_name
import stripe
from tasks.migration import migrate_for_user


class VerifyEmailHandler(BaseHandler):
    def get(self, verification_key):
        user = User.get("email_confirmed=0 and verify_email_token=%s", verification_key)
        if user:
            self.db.execute("UPDATE user SET email_confirmed=1, verify_email_token='' WHERE id = %s", user.id)
            # sync any confirmed email address change to the stripe account,
            # if they have one.
            if user.stripe_customer_id:
                customer = None
                try:
                    customer = stripe.Customer.retrieve(user.stripe_customer_id)
                except stripe.error.InvalidRequestError:
                    pass
                if customer and not hasattr(customer, 'deleted'):
                    customer.email = user.email
                    customer.save()
        return self.redirect("/")


class AccountImagesHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self, user_name=None, page=None):
        if not user_name:
            raise tornado.web.HTTPError(404)

        user = User.get("name = %s", user_name)
        if not user or user.deleted:
            raise tornado.web.HTTPError(404)

        can_follow = False
        current_user = self.get_current_user_object()
        can_follow = not current_user.has_subscription(user)

        # we get None for page argument when non specified,
        # otherwise we get a string.
        if not page:
            page = 1
        page = int(page)
        url_format = '/user/%s/' % user.name
        url_format = url_format + '%d'

        following_shakes = user.following()
        following_shakes_count = len(following_shakes)

        user_shake = user.shake()
        followers = user_shake.subscribers()
        follower_count = len(followers)
        count = user_shake.sharedfiles_count()
        images = user_shake.sharedfiles(page=page)

        has_data_to_migrate = False
        if current_user.id == user.id:
            # if the user is looking at their own shake, then
            # check to see if they haven't migrated yet; remind
            # them at the top of their shake if they do...
            has_data_to_migrate = not MigrationState.has_migrated(current_user.id)

        other_shakes = user.shakes(include_managed=False, include_only_group_shakes=True)

        if not images and page != 1:
            raise tornado.web.HTTPError(404)
        return self.render("account/index.html", images=images, user=user,
            current_user_obj=current_user, count=count, page=page,
            url_format=url_format, can_follow=can_follow,
            following_shakes=following_shakes[:10],
            following_shakes_count=following_shakes_count, followers=followers[:10],
            follower_count=follower_count, other_shakes=other_shakes,
            has_data_to_migrate=has_data_to_migrate)


class UserLikesHandler(BaseHandler):
    """
    All of a user's likes, paginated with Older / Newer links.

    path: /user/{name}/likes
          /user/{name}/likes/before/{id}
          /user/{name}/likes/after/{id}
    """
    @tornado.web.authenticated
    @require_membership
    def get(self, user_name=None, before_or_after=None, favorite_id=None):
        user = User.get("name = %s", user_name)
        if not user:
            raise tornado.web.HTTPError(404)
        current_user_obj = self.get_current_user_object()

        older_link, newer_link = None, None

        before_id, after_id = None, None
        if favorite_id and before_or_after == 'before':
            before_id = favorite_id
        elif favorite_id and before_or_after == 'after':
            after_id = favorite_id

        # We're going to older, so ony use before_id.
        if before_id:
            sharedfiles = user.likes(before_id=before_id,per_page=11)
            # we have nothing on this page, redirect to base incoming page.
            if len(sharedfiles) == 0:
                return self.redirect('/user/%s/likes' % user.name)

            if len(sharedfiles) > 10:
                older_link = "/user/%s/likes/before/%s" % (user.name, sharedfiles[9].favorite_id)
                newer_link = "/user/%s/likes/after/%s" % (user.name, sharedfiles[0].favorite_id)
            else:
                newer_link = "/user/%s/likes/after/%s" % (user.name, sharedfiles[0].favorite_id)

        # We're going to newer
        elif after_id:
            sharedfiles = user.likes(after_id=after_id, per_page=11)
            if len(sharedfiles) <= 10:
                return self.redirect('/user/%s/likes' % user.name)
            else:
                sharedfiles.pop(0)
                older_link = "/user/%s/likes/before/%s" % (user.name, sharedfiles[9].favorite_id)
                newer_link = "/user/%s/likes/after/%s" % (user.name, sharedfiles[0].favorite_id)
        else:
            # Main page only has older link
            sharedfiles = user.likes(per_page=11)
            if len(sharedfiles) > 10:
                older_link = "/user/%s/likes/before/%s" % (user.name, sharedfiles[9].favorite_id)

        following_shakes = user.following()
        following_shakes_count = len(following_shakes)

        followers = user.shake().subscribers()
        follower_count = len(followers)

        return self.render("account/likes.html", sharedfiles=sharedfiles[0:10],
            current_user_obj=current_user_obj,
            following_shakes=following_shakes[:10],
            following_shakes_count=following_shakes_count,
            followers=followers[:10], follower_count=follower_count,
            older_link=older_link, newer_link=newer_link, user=user)


class SettingsHandler(BaseHandler):
    """
    path: /account/settings

    View and update basic account settings.
    """
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_object()
        payments = []
        if user.is_paid:
            payments = []
            if user.stripe_customer_id:
                customer_id = user.stripe_customer_id
                charges = stripe.Charge.list(limit=5, customer=customer_id)
                for charge in charges.data:
                    payments.append({
                        "transaction_amount": "USD %0.2f" % (charge.amount / 100.0,),
                        "refund_amount": charge.refunded and "USD %0.2f" % (charge.amount_refunded / 100.0,) or "",
                        "created_at": datetime.datetime.fromtimestamp(charge.created),
                        "status": "charged",
                        "is_pending": charge.status == "pending",
                        "is_failed": charge.status == "failed",
                        "is_success": charge.status == "succeeded",
                        "is_refund": charge.refunded,
                    })
            else:
                log = PaymentLog.last_payments(count=5, user_id = user.id)
                for payment in log:
                    payments.append({
                        "transaction_amount": payment.transaction_amount,
                        "refund_amount": "",
                        "created_at": payment.created_at,
                        "status": payment.status,
                        "is_pending": False,
                        "is_success": True,
                        "is_failed": False,
                        "is_refund": False,
                    })


        already_requested = self.get_secure_cookie("image_request")
        cancel_flag = "canceled" in (user.stripe_plan_id or "")
        updated_flag = self.get_argument("update", "") == "1"
        migrated_flag = self.get_argument("migrated", 0)
        past_due = False
        source_card_type = None
        source_last_4 = None
        source_expiration = None

        promotions = Promotion.active()

        has_data_to_migrate = not MigrationState.has_migrated(user.id)

        if user.stripe_customer_id:
            customer = None
            try:
                customer = stripe.Customer.retrieve(user.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
            if customer and not hasattr(customer, 'deleted'):
                if customer.subscriptions.total_count >= 1:
                    subscriptions = [sub for sub in customer.subscriptions.data
                        if sub.plan.id == user.stripe_plan_id]
                    if subscriptions:
                        subscription = subscriptions[0]
                        past_due = subscription.status == "past_due"
                        if customer.sources.total_count > 0:
                            if customer.sources.data[0].object == "card":
                                card = customer.sources.data[0]
                            elif customer.sources.data[0].object == "source":
                                card = customer.sources.data[0].card
                            source_card_type = card.brand
                            source_last_4 = card.last4
                            source_expiration = "%d/%d" % (card.exp_month, card.exp_year)

        return self.render("account/settings.html", user=user, payments=payments,
            already_requested=already_requested, promotions=promotions,
            plan_name=plan_name(user.stripe_plan_id),
            past_due=past_due,
            stripe_public_key=options.stripe_public_key,
            source_card_type=source_card_type,
            source_last_4=source_last_4,
            source_expiration=source_expiration,
            has_data_to_migrate=has_data_to_migrate,
            updated_flag=updated_flag,
            migrated_flag=migrated_flag,
            cancel_flag=cancel_flag)

    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_object()
        email = self.get_argument('email', None)
        disable_notifications = self.get_argument('disable_notifications', 0)
        show_naked_people = self.get_argument('show_naked_people', 0)
        show_stats = self.get_argument('show_stats', 0)
        disable_autoplay = self.get_argument('disable_autoplay', 0)

        if email != user.email and email != None:
            user.update_email(email)
            user.invalidate_email()

        if disable_notifications:
            user.disable_notifications = 1
        else:
            user.disable_notifications = 0

        if show_naked_people:
            user.show_naked_people = 1
        else:
            user.show_naked_people = 0

        if show_stats:
            user.show_stats = 1
        else:
            user.show_stats = 0

        if disable_autoplay:
            user.disable_autoplay = 1
        else:
            user.disable_autoplay = 0

        if user.save():
            return self.redirect("/account/settings")

        promotions = Promotion.active()

        self.add_errors(user.errors)
        return self.render("account/settings.html", user=user, errors=self._errors,
            promotions=promotions)


class SettingsProfileHandler(BaseHandler):
    """
    path: /account/settings/profile

    View and update profile settings.
    """
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_object()
        return self.render("account/settings-profile.html", user=user)

    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_object()
        full_name = self.get_argument('full_name', '')
        about = self.get_argument('about', '')
        website = self.get_argument('website', '')

        photo_content_type = self.get_argument("photo_content_type", None)
        photo_path = self.get_argument("photo_path", None)
        photo_name = self.get_argument("photo_name", None)

        profile_image_saved = True
        if photo_content_type and photo_path:
            profile_image_saved = user.set_profile_image(photo_path, photo_name, photo_content_type)

        if user.is_paid or not uses_a_banned_phrase(full_name):
            user.full_name = full_name
        if user.is_paid or not uses_a_banned_phrase(about):
            user.about = about
        user.website = website
        if user.save() and profile_image_saved:
            return self.redirect("/account/settings/profile")
        else:
            self.add_errors(user.errors)
            return self.render("/account/settings-profile.html", user=user)


class SettingsConnectionsHandler(BaseHandler):
    """
    path: /account/settings/connections

    View and update profile settings.
    """
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_object()
        apps = App.authorized_by_user(user)
        return self.render("account/settings-connections.html", user=user, apps=apps)

    @tornado.web.authenticated
    def post(self, app_id=None):
        """
        Handles AJAX post request to disconnect an app from a user.
        """
        user = self.get_current_user_object()
        app = App.get("id = %s", app_id)
        if not app:
            return {'error' : 'Invalid request.'}
        app.disconnect_for_user(user)
        return {'result' : 'ok'}


class ForgotPasswordHandler(BaseHandler):
    def get(self):
        current_user = self.get_current_user()
        if current_user:
            return self.redirect("/sign-out?next=/account/forgot-password")

        return self.render("account/forgot-password.html", email="")

    def post(self):
        email = self.get_argument("email", None)
        if email:
            user = User.get("email = %s", email)
            if user:
                user.create_reset_password_token()
                return self.render("account/forgot-password-sent.html")
        else:
            email = ""

        self.add_error('email', "That email address doesn't have an account.")

        return self.render("account/forgot-password.html", email=email)


class ResetPasswordHandler(BaseHandler):
    def get(self, token=""):
        current_user = self.get_current_user()
        if current_user:
            return self.redirect("/sign-out?next=/account/reset-password/%s" % token)
        user = User.get("reset_password_token = %s", token)
        if user:
            return self.render("account/reset-password.html", reset_password_token=token)
        else:
            raise tornado.web.HTTPError(404)

    def post(self, token=""):
        current_user = self.get_current_user()
        if current_user:
            return self.redirect("/sign-out?next=/account/reset-password/%s", self.get_argument(""))
        user = User.get("reset_password_token = %s", token)
        if not user:
            raise tornado.web.HTTPError(404)

        if self.get_argument("password", None) and self.get_argument("password_again", None) :
            if user.set_and_confirm_password(self.get_argument("password"), self.get_argument("password_again")):
                user.reset_password_token = ""
                user.save()
                return self.redirect("/sign-in")
        self.add_error("password", "Those passwords didn't match, or are invalid. Please try again.")
        return self.render("account/reset-password.html", reset_password_token=token)


class SignInHandler(BaseHandler):

    def prepare(self):
        self.use_template = "account/sign-in.html"

        if self.get_argument("next", None):
            self.next = self.get_argument("next")
            if self.next.startswith("/tools/p"):
                self.use_template = "tools/sign-in.html"
        else:
            self.next = ""

    def get(self):
        """
        If user is already logged in, redirect to home. Otherwise, render the sign-in page.
        """
        if self.get_current_user():
            return self.redirect("/")
        else:
            return self.render(self.use_template, name="", next=self.next)

    def post(self):
        password = self.get_argument('password', "")
        name = self.get_argument('name', "")
        if password == "" or name == "":
            self.add_error('name', "I could not find that user name and password combination.")
            return self.render(self.use_template, name=name, next=self.next)

        user = User.authenticate(name, password)
        if user:
            self.log_user_in(user)
            if self.next:
                return self.redirect(self.next)
            else:
                return self.redirect("/")
        else:
            unmigrated_user = User.find_unmigrated_user(name, password)
            if unmigrated_user:
                # undelete the user account and log them in...
                unmigrated_user.deleted = 0
                unmigrated_user.save()

                # also, find their personal shake and restore that
                # specifically. does not restore any images within it--
                # the user will need to invoke a migration for that.
                shake = Shake.get(
                    'user_id=%s and type=%s and deleted=2', unmigrated_user.id, 'user')
                if shake is not None:
                    shake.deleted = 0
                    shake.save()

                self.log_user_in(unmigrated_user)
                return self.redirect("/account/welcome-to-mltshp")

            self.add_error('name', "I could not find that user name and password combination.")
            return self.render(self.use_template, name=name, next=self.next)


class WelcomeToMltshp(BaseHandler):
    def prepare(self):
        self.use_template = "account/welcome-to-mltshp.html"

    @tornado.web.authenticated
    def get(self):
        """
        If user is not logged in, redirect to the sign-in page.
        """
        user = self.get_current_user_object()
        return self.render(self.use_template, name=user.name)


class MlkshkMigrationHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self):
        user = self.get_current_user_object()
        state = MigrationState.has_migrated(user.id)
        return self.render(
            "account/migrate.html",
            name=user.name, has_migrated=state)

    @tornado.web.authenticated
    @require_membership
    def post(self):
        user = self.get_current_user_object()
        state = MigrationState.has_migrated(user.id)

        if not state:
            migrate_for_user.delay_or_run(user.id)

        return self.redirect("/account/settings?migrated=1")


class SignOutHandler(BaseHandler):
    def get(self):
        self.log_out()
        if self.get_argument("next", None):
            return self.redirect(self.get_argument("next"))
        else:
            return self.redirect("/")


class ConfirmAccountHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        vid = self.get_argument('vid', None)
        shake = None
        promotion = None
        voucher = None
        user = self.get_current_user_object()
        if vid is not None:
            voucher = Voucher.get("id=%s", vid)
            if voucher is not None and voucher.claimed_by_user_id == user.id:
                if voucher.promotion_id:
                    promotion = Promotion.get("id=%s", voucher.promotion_id)
                    if promotion is not None:
                        shake = promotion.shake()
        return self.render(
            "account/confirm.html", promotion=promotion,
            promotion_shake=shake, voucher=voucher, current_user_obj=user)


class SubscribeHandler(BaseHandler):
    """
    path: /user/{user_name}/subscribe
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, user_name):
        is_json = self.get_argument('json', None)
        user = self.get_current_user_object()

        shake_owner = User.get('name="%s"' % (user_name))
        if not shake_owner:
            raise tornado.web.HTTPError(404)

        if not user.subscribe_to_user(shake_owner):
            if is_json:
                return self.write(json_encode({'error':'error'}))
            else:
                return self.redirect('/user/%s' % (user_name))
        else:
            if is_json:
                return self.write(json_encode({'subscription_status': True}))
            else:
                return self.redirect('/user/%s' % (user_name))


class UnsubscribeHandler(BaseHandler):
    """
    path: /user/{user_name}/unsubscribe
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, user_name):
        is_json = self.get_argument('json', None)
        user = self.get_current_user_object()

        shake_owner = User.get('name="%s"' % (user_name))
        if not shake_owner:
            raise tornado.web.HTTPError(404)

        if not user.unsubscribe_from_user(shake_owner):
            if is_json:
                return self.write(json_encode({'error':'error'}))
            else:
                return self.redirect('/user/%s' % (user_name))
        else:
            if is_json:
                return self.write(json_encode({'subscription_status': False}))
            else:
                return self.redirect('/user/%s' % (user_name))


class ClearNotificationHandler(BaseHandler):
    def check_xsrf_cookie(self):
        return

    @tornado.web.authenticated
    def post(self):
        """
        can be run four ways:
        . type=single and id=# will delete a single notification
        . type=favorite will delete all favorites
        . type=save will delete all saves
        . type=comment will clear all comments
        . type=subscriber will delete all subscription notifications
        """
        current_user = self.get_current_user()
        _type = self.get_argument('type', None)

        if _type == 'single':
            id = self.get_argument('id', 0)
            n = Notification.get('id=%s and receiver_id=%s', id, current_user['id'])
            notification_type = None
            if n:
                notification_type = n.type
                n.delete()
            else:
                return self.write(json_encode({'error' : 'Can\'t find that notification'}))
        elif _type in ['favorite', 'save', 'subscriber', 'comment', 'invitation_approved']:
            ns = Notification.where('type=%s and receiver_id=%s and deleted=0', _type, current_user['id'])
            [n.delete() for n in ns]
        else:
            return self.write(json_encode({'error' : 'I dont\'t understand that message.'}))

        if _type == 'favorite':
            response = {'response' : "0 new likes"}
        elif _type == 'save':
            response = {'response' : "0 new saves"}
        elif _type == 'subscriber':
            response = {'response' : "You have 0 new followers"}
        elif _type == 'comment':
            response = {'response' : "0 new comments"}
        elif _type == 'invitation_approved':
            response = {'response' : "0 new shake memberships"}
        elif _type == 'single' and notification_type == 'invitation':
            count = Notification.count_for_user_by_type(current_user['id'], 'invitation')
            response = {'response' : 'ok', 'count' : count }
        else:
            response = {'response' : 'ok'}

        return self.write(response)


class CreateAccountHandler(BaseHandler):
    def get(self):
        """
        Logged in users not allowed here.
        """
        if self.get_current_user():
            return self.redirect("/")

        if options.disable_signups:
            return self.write("Sorry! Signups Are Closed.")

        # voucher key
        key_value = self.get_argument('key', '')

        promotions = Promotion.active()

        # If we're using mltshp-cdn.com, we know that we can use
        # https; if something else is configured, check the
        # X-Forwarded-Proto header and fallback to the protocol
        # of the request
        using_https = options.cdn_ssl_host == "mltshp-cdn.com" or \
            self.request.headers.get("X-Forwarded-Proto",
                self.request.protocol) == "https"

        #recaptcha hot fix
        if options.recaptcha_public_key:
            captcha_string = captcha.displayhtml(
                options.recaptcha_public_key,
                use_ssl=using_https
            )
        else:
            captcha_string = ""
        return self.render("account/create.html", name="", email="",
            key=key_value,
            promotions=promotions,
            recaptcha=captcha_string)

    def post(self):
        if options.disable_signups:
            return

        name_value = self.get_argument('name', '')
        email_value = self.get_argument('email', '')
        key_value = self.get_argument('key', '')
        has_errors = False
        voucher = None

        if key_value != '':
            voucher = is_valid_voucher_key(key_value)
            if voucher is None:
                has_errors = True
                self.add_error('key', 'Invalid discount code')

        new_user = User(name=name_value, email=email_value, email_confirmed=0)
        new_user.set_and_confirm_password(self.get_argument('password', ""),
             self.get_argument('password_again', ""))

        skip_recaptcha = self.get_argument('_skip_recaptcha_test_only', False)
        if not options.recaptcha_private_key:
            skip_recaptcha = True

        #recaptcha hotfix
        if not skip_recaptcha:
            response = captcha.submit(
               self.get_argument('recaptcha_challenge_field'),
               self.get_argument('recaptcha_response_field'),
               options.recaptcha_private_key,
               self.request.remote_ip
            )

            if not response.is_valid:
                has_errors = True
                self.add_error('recaptcha', 'Invalid captcha')

        if not has_errors:
            try:
                # create form asserts the user agress to terms of use
                new_user.tou_agreed = 1

                if new_user.save():
                    if options.postmark_api_key:
                        # i'd like to NOT invalidate_email in the
                        # case of using a voucher, but the person
                        # may use a different email for MLTSHP than
                        # they used for receiving their voucher, so...
                        new_user.invalidate_email()
                    else:
                        # we have no way to send a verification
                        # email, so we're gonna trust 'em
                        new_user.email_confirmed = 1
                        new_user.save()

                    query_str = ''
                    if voucher is not None:
                        voucher.apply_to_user(new_user)
                        query_str = '?vid=%s' % str(voucher.id)

                    self.log_user_in(new_user)
                    if new_user.email_confirmed:
                        return self.redirect('/')
                    else:
                        return self.redirect('/confirm-account%s' % query_str)
            except torndb.IntegrityError:
                #This is a rare edge case, so we handle it lazily -- IK.
                pass
            has_errors = True
            self.add_errors(new_user.errors)

        #recaptcha hot fix
        captcha_string = captcha.displayhtml(
            options.recaptcha_public_key
        )
        promotions = Promotion.active()
        return self.render("account/create.html", name=name_value,
            email=email_value, key=key_value, recaptcha=captcha_string,
            promotions=promotions)


class RedeemHandler(BaseHandler):

    def get(self):
        """
        Logged out users not allowed here.
        """
        # voucher key
        key_value = self.get_argument('key', '')

        user = self.get_current_user_object()
        if user is None:
            if key_value != '':
                query = "?" + urlencode({"key": key_value})
            return self.redirect("/create-account%s" % query)

        if user.is_paid:
            # pro users can't redeem
            return self.redirect("/account/settings")

        promotions = Promotion.active()

        return self.render("account/redeem.html",
            key=key_value, promotions=promotions)

    @tornado.web.authenticated
    def post(self):
        key_value = self.get_argument('key', '')

        voucher = is_valid_voucher_key(key_value)

        user = self.get_current_user_object()
        if voucher is not None:
            if not voucher.claimed_by_user_id:
                voucher.apply_to_user(user)
                return self.redirect("/account/settings")

        promotions = Promotion.active()

        self.add_error('key', 'Invalid discount code')
        return self.render("account/redeem.html",
            key=key_value, promotions=promotions)


class QuickNotificationsHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        """
        path: /account/quick-notifications

        Returns an HTML fragment that populates the user's sidebar on their home
        page with a list of notifications.

        The marshalled values passed to the template needs be synchronized with
        the HomeHandler.
        """
        current_user_obj = self.get_current_user_object()
        notifications = Notification.display_for_user(current_user_obj)
        return self.render("account/quick-notifications.html", notifications=notifications,
                            current_user_obj=current_user_obj)


class QuickSendInvitationHandler(BaseHandler):

    @tornado.web.authenticated
    @require_membership
    def post(self):
        """
        Ajax call to send an invitation on behalf of a user.

        path: /account/quick-send-initation
        """
        current_user_obj = self.get_current_user_object()
        if current_user_obj.invitation_count < 0: #free day
            return self.write({'error': 'No invitations left'})

        email_address = self.get_argument('email_address', None)
        if not email_address:
            return self.write({'error': 'You need to specify an email.'})

        if not email_re.match(email_address):
            return self.write({'error': 'That email doesn\'t look right.'})

        Invitation.create_for_email(email_address, current_user_obj.id)
        current_user_obj.invitation_count = current_user_obj.invitation_count - 1
        current_user_obj.save()

        message = "<p>You've sent invitations to:</p> <ul>"
        for invitation in Invitation.by_user(current_user_obj):
            message += "<li>%s</li>" % invitation.email_address
        message += "</ul>"

        return self.write({'response' : 'ok', 'count' : current_user_obj.invitation_count, 'message' : message})


class AnnouncementHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, page=None):
        """
        A notice to have people agree to the new terms of use.
        """
        current_user_obj = self.get_current_user_object()

        if self.get_arguments('agree', None):
            current_user_obj.tou_agreed = True
            current_user_obj.save()
            return self.redirect("/")

        if page == 'tou':
            return self.render("account/announcement-tou.html")
        else:
            return self.redirect("/")


class RequestImageZipFileHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        """
        A method that sends an email requesting a
        zip file of all images.
        """
        user = self.get_current_user_object()

        self.set_secure_cookie('image_request', '1', expires_days=365)
        pm = postmark.PMMail(api_key=options.postmark_api_key,
            sender="hello@mltshp.com", to="hello@mltshp.com",
        subject="{0} requests images.".format(user.name),
        text_body="{0} requests images".format(user.name))
        pm.send()

        return self.redirect("/account/settings")


class SetContentFilterHandler(BaseHandler):
    def post(self, mode=None):
        """
        This method sets a secure cookie called "nsfw" if mode is off.
        """
        if mode == 'on':
            self.clear_cookie("nsfw")
        else:
            self.set_secure_cookie("nsfw", "1", expires=2147483647)

        return self.redirect("/incoming")


class QuickNameSearch(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        """
        An AJAX method that returns JSON response of user names that
        match the "name" argument.
        """
        current_user = self.get_current_user_object();
        name = self.get_argument('name', '')
        users = []

        for user in User.find_by_name_fragment(name, limit=10):
            if user.name != current_user.name:
                users.append({
                    'id' : user.id,
                    'name' : user.name,
                    'profile_image_url' : user.profile_image_url()
                })
        return self.write({'users': users})


class MembershipHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        current_user = self.get_current_user_object()

        # if a token is provided, pass through for subscription
        # any creation/update (user may be updating their credit card info)
        token_id = self.get_argument("token")

        if current_user.stripe_customer_id is None:
            if token_id is None:
                # invalid request; token must be present for new subscribers
                raise Exception("Invalid request")

        plan_id = self.get_argument("plan_id")
        if plan_id not in ("mltshp-single", "mltshp-double"):
            raise Exception("Invalid request")

        quantity = 1
        if plan_id == "mltshp-double":
            quantity = int(float(self.get_argument("quantity")))
            if quantity < 24 or quantity > 500:
                raise "Invalid request"

        customer = None
        sub = None
        stripe_customer_id = current_user.stripe_customer_id
        if stripe_customer_id is not None:
            try:
                customer = stripe.Customer.retrieve(stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
            if customer and getattr(customer, "deleted", False):
                customer = None

        try:
            if customer is None:
                if token_id is None:
                    # FIXME: handle this more gracefully...
                    raise "Invalid request"

                # create a new customer object for this subscription
                customer = stripe.Customer.create(
                    description="MLTSHP user %s" % current_user.name,
                    email=current_user.email,
                    metadata={"mltshp_user": current_user.name},
                    source=token_id,
                )
            else:
                # if a token is provided for an existing customer, update the
                # source (affecting their default payment source too)
                if token_id is not None:
                    customer.source = token_id
                    customer.save()

            # if this works, we should have a customer with 1 subscription, this one
            if customer.subscriptions.total_count > 0:
                sub = customer.subscriptions.data[0]
                if sub.plan != plan_id:
                    sub.plan = plan_id
                    if plan_id == "mltshp-double":
                        sub.quantity = quantity
                    else:
                        sub.quantity = 1
                    sub.save()
            else:
                if plan_id == "mltshp-double":
                    sub = customer.subscriptions.create(
                        plan=plan_id, quantity=quantity)
                else:
                    sub = customer.subscriptions.create(
                        plan=plan_id)
        except stripe.error.CardError as ex:
            return self.render("account/return-subscription-error.html",
                error_message=ex.user_message)

        if not sub:
            raise Exception("Error issuing subscription")

        amount = "USD %0.2f" % ((sub.plan.amount / 100.0) * quantity)
        payment_log = PaymentLog(
            processor                 = PaymentLog.STRIPE,
            user_id                   = current_user.id,
            status                    = "subscribed",
            reference_id              = sub.id, # ??
            transaction_id            = sub.id, # ??
            operation                 = "order",
            transaction_date          = datetime.datetime.fromtimestamp(sub.current_period_start).strftime("%Y-%m-%d %H:%M:%S"),
            next_transaction_date     = datetime.datetime.fromtimestamp(sub.current_period_end).strftime("%Y-%m-%d %H:%M:%S"),
            buyer_email               = current_user.email,
            buyer_name                = current_user.display_name(),
            recipient_email           = "hello@mltshp.com",
            recipient_name            = "MLTSHP, Inc.",
            payment_reason            = "MLTSHP Membership",
            transaction_serial_number = 1,
            subscription_id           = sub.id,
            payment_method            = "CC",
            transaction_amount        = amount,
        )
        payment_log.save()
        current_user.is_paid = 1
        current_user.stripe_plan_id = plan_id
        if plan_id == "mltshp-double":
            current_user.stripe_plan_rate = quantity
        else:
            current_user.stripe_plan_rate = None

        if current_user.stripe_customer_id != customer.id:
            current_user.stripe_customer_id = customer.id

        current_user.save()

        if options.postmark_api_key:
            pm = postmark.PMMail(api_key=options.postmark_api_key,
                sender="hello@mltshp.com", to="hello@mltshp.com",
                subject="%s has created a subscription" % (payment_log.buyer_name),
                text_body="Subscription ID: %s\nBuyer Name:%s\nBuyer Email:%s\nUser ID:%s\n" % (payment_log.subscription_id, payment_log.buyer_name, payment_log.buyer_email, current_user.id))
            pm.send()

        payment_notifications(current_user, "subscription", amount)

        has_data_to_migrate = not MigrationState.has_migrated(current_user.id)

        return self.render("account/return-subscription-completed.html",
                has_data_to_migrate=has_data_to_migrate)

    @tornado.web.authenticated
    def get(self):
        current_user = self.get_current_user_object()
        return self.render('account/membership.html',
            current_plan=current_user.stripe_plan_id,
            current_plan_rate=current_user.stripe_plan_rate,
            stripe_customer_id=current_user.stripe_customer_id,
            stripe_public_key=options.stripe_public_key)


class RSSFeedHandler(BaseHandler):
    """
    This method returns RSS for this shake's last
        20 posts
    """
    def get(self, user_name=None):
        user_object = User.get("name=%s", user_name)
        if not user_object:
            raise tornado.web.HTTPError(404)

        if not user_object.is_paid:
            raise tornado.web.HTTPError(404)

        shake = user_object.shake()
        build_date = shake.feed_date()
        if not shake:
            raise tornado.web.HTTPError(404)
        sharedfiles = shake.sharedfiles(per_page=20)
        if sharedfiles:
            build_date = sharedfiles[0].feed_date()

        self.set_header("Content-Type", "application/xml")
        return self.render("shakes/rss.html", shake=shake, sharedfiles=sharedfiles,
            app_host=options.app_host, build_date=build_date)


class PaymentUpdateHandler(BaseHandler):
    """
    Handles updating the Stripe payment source for a member.

    """
    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_object()
        if user.stripe_customer_id:
            token_id = self.get_argument("token")
            try:
                customer = stripe.Customer.retrieve(user.stripe_customer_id)
                if customer:
                    customer.source = token_id
                    customer.save()

                    if options.postmark_api_key:
                        pm = postmark.PMMail(api_key=options.postmark_api_key,
                            sender="hello@mltshp.com", to="hello@mltshp.com",
                            subject="%s has updated their payment info" % (user.display_name()),
                            text_body="Buyer Name:%s\nBuyer Email:%s\nUser ID:%s\n" % (user.display_name(), user.email, user.id))
                        pm.send()

                    return self.redirect('/account/settings?update=1')

            except stripe.error.InvalidRequestError:
                pass

        return self.redirect('/account/settings')

    @tornado.web.authenticated
    def get(self):
        return self.redirect('/account/settings')


class PaymentCancelHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_object()
        if user.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(user.stripe_customer_id)
                if customer and customer.subscriptions.total_count > 0:
                    subscription = customer.subscriptions.data[0]
                    if subscription:
                        subscription.delete(at_period_end=True)
                        if user.stripe_plan_id and ("-canceled" not in user.stripe_plan_id):
                            user.stripe_plan_id = user.stripe_plan_id + "-canceled"
                        user.stripe_plan_rate = None
                        user.save()

                        if options.postmark_api_key:
                            pm = postmark.PMMail(api_key=options.postmark_api_key,
                                sender="hello@mltshp.com", to="hello@mltshp.com",
                                subject="%s has canceled a subscription" % (user.display_name()),
                                text_body="Subscription ID: %s\nBuyer Name:%s\nBuyer Email:%s\nUser ID:%s\n" % (subscription.id, user.display_name(), user.email, user.id))
                            pm.send()

                        payment_notifications(user, 'cancellation')
            except stripe.error.InvalidRequestError:
                pass
        return self.redirect('/account/settings?cancel=1')

    @tornado.web.authenticated
    def get(self):
        return self.render('account/payment-cancel.html')


class ResendVerificationEmailHandler(BaseHandler):
    """
    Simply resends an email to verify your email address.
    """
    @tornado.web.authenticated
    def post(self):
        current_user_object = self.get_current_user_object()
        if current_user_object.email_confirmed:
            return self.redirect("/account/settings")
        current_user_object.invalidate_email()
        return self.render("account/resend-verification-email.html")

    def get(self):
        return self.redirect("/")


class FollowerHandler(BaseHandler):
    """
    Returns all followers for this user
    """
    @tornado.web.authenticated
    def get(self, user_name=None, page=None):
        user_object = User.get("name=%s", user_name)
        if not page:
            page = 1

        page = int(page)

        if user_object:
            user_shake = user_object.shake()
            followers = user_shake.subscribers(page=page)
            follower_count = user_shake.subscriber_count()
            url_format = '/user/%s/followers/' % user_object.name
            url_format = url_format + '%d'
            return self.render("account/followers.html", followers=followers, user_info=user_object,
                url_format=url_format, follower_count=follower_count, page=page)
        else:
            raise tornado.web.HTTPError(404)


class FileCountHandler(BaseHandler):

    def get(self, name):
        user_object = User.get('name = %s and deleted = 0', name)
        if not user_object:
            raise tornado.web.HTTPError(404)

        stats = user_object.total_file_stats()
        return self.write({'likes':int(stats['likes']), 'saves':int(stats['saves']), 'views':int(stats['views'])})


class FollowingHandler(BaseHandler):
    """
    Returns all people this user is following
    """
    @tornado.web.authenticated
    def get(self, user_name=None, page=None):
        user_object = User.get("name=%s", user_name)
        if not page:
            page = 1

        page = int(page)

        if user_object:
            following = user_object.following(page=page)
            following_objects = []
            for f in following:
                if f['type'] == 'user':
                    f['related_object'] = User.get('id=%s', f['id'])
                elif f['type'] == 'shake':
                    f['related_object'] = Shake.get('id=%s', f['id'])
                following_objects.append(f)

            following_count = user_object.following_count()

            url_format = '/user/%s/following/' % user_object.name
            url_format = url_format + '%d'
            return self.render("account/following.html", following=following_objects, user_info=user_object,
                url_format=url_format, following_count=following_count, page=page)
        else:
            raise tornado.web.HTTPError(404)


class ShakesHandler(BaseHandler):
    """
    path: /account/shakes

    Returns a JSON list of shakes belonging to authenticated user.
    """
    @tornado.web.authenticated
    def get(self):
        current_user = self.get_current_user_object()
        group_shakes = current_user.shakes(include_managed=True)

        response = {'result' : []}
        for shake in group_shakes:
            response['result'].append({'id' : shake.id, 'name' : xhtml_escape(shake.display_name(current_user))})
        return self.write(response)
