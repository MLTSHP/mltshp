import io
import time
import hashlib
import calendar
import random
import re
import urllib.parse
from datetime import datetime

from lib.s3 import S3Bucket
import postmark
from tornado.options import define, options

from lib.utilities import email_re, s3_authenticated_url, s3_url, transform_to_square_thumbnail
from lib.flyingcow import Model, Property
from lib.flyingcow.cache import ModelQueryCache
from lib.flyingcow.db import IntegrityError
from tasks.counts import calculate_likes
from tasks.migration import migrate_for_user
from lib.badpasswords import bad_list

from . import notification
from . import subscription
from . import shake
from . import invitation
from . import sharedfile
from . import externalservice
from . import invitation_request
from . import shakemanager
# we use models.favorite due to some weird edge case where the reference
# to the module gets lost.  To recreate, rename to "import favorite" and
# change references from models.favorite to just favorite.  You can then
# like an image on the site to see error. -- IK
import models.favorite
from models.payment_log import PaymentLog

import stripe


class User(ModelQueryCache, Model):
    name = Property()
    email = Property()
    hashed_password = Property()
    email_confirmed = Property(default=0)
    full_name = Property(default='')
    about = Property(default='')
    website = Property(default='')
    nsfw = Property(default=0)
    recommended = Property(default=0)
    is_paid = Property(default=0)
    deleted = Property(default=0)
    restricted = Property(default=0)
    tou_agreed = Property(default=0)
    show_naked_people = Property(default=0)
    show_stats = Property(default=0)
    disable_autoplay = Property(default=0)
    verify_email_token = Property()
    reset_password_token = Property()
    profile_image = Property()
    invitation_count = Property(default=0)
    disable_notifications = Property(default=0)
    stripe_customer_id = Property()
    stripe_plan_id = Property()
    stripe_plan_rate = Property()
    created_at = Property()
    updated_at = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        if not self._validate_name():
            return False
        if not self._validate_email():
            return False
        if not self._validate_full_name():
            return False
        if not self._validate_about():
            return False
        if not self._validate_website():
            return False
        if not self.saved():
            # only run email and name validations on create for now
            if not self._validate_name_uniqueness():
                return False
            if not self._validate_email_uniqueness():
                return False

        # Since we add errors / validate outside the save method
        # see set_and_confirm password.
        if len(self.errors) > 0:
            return False
        self._set_dates()
        return super(User, self).save(*args, **kwargs)

    def on_create(self):
        new_shake = shake.Shake(user_id=self.id, type='user', description='New Shake')
        new_shake.save()

    def as_json(self, extended=False):
        base_dict = {
            'name' :self.name,
            'id' : self.id,
            'profile_image_url' : self.profile_image_url(include_protocol=True)
        }

        if extended:
            base_dict['about'] = self.about
            base_dict['website'] = self.website
            shakes = self.shakes()
            base_dict['shakes'] = []
            for shake in shakes:
                base_dict['shakes'].append(shake.as_json())

        return base_dict

    def set_and_confirm_password(self, password, confirm_password):
        if password == None or password == "":
            self.add_error('password', "Passwords can't be blank.")
            return False
        if password != confirm_password:
            self.add_error('password', "Passwords don't match.")
            return False

        if password in bad_list:
            self.add_error('password', "That is not a good password. <a target=\"_blank\" href=\"/faq/#bad_password\">Why?</a>")
            return False

        self.set_password(password)
        return True

    def is_plus(self):
        return self.stripe_plan_id == "mltshp-double"

    def is_member(self):
        return self.is_paid

    def set_password(self, password):
        """
        Sets the hashed_password correctly.
        """
        self.hashed_password = self.generate_password_digest(password)

    def add_invitations(self, count=0):
        """
        Adds invitations to a user's account
        """
        self.invitation_count = int(count)
        self.save()

    def send_invitation(self, email_address):
        if self.invitation_count > 0:
            if (email_address != None) and (email_address != '') and email_re.match(email_address):
                if invitation.Invitation.create_for_email(email_address, self.id):
                    self.invitation_count -= 1
                    self.save()
                    return True
        return False


    def invalidate_email(self):
        self.email_confirmed = 0
        h = hashlib.sha1()
        h.update(str(time.time()).encode("ascii"))
        h.update(str(random.random()).encode("ascii"))
        self.verify_email_token = h.hexdigest()
        self.save()
        if not options.debug:
            pm = postmark.PMMail(api_key=options.postmark_api_key,
                sender="hello@mltshp.com", to=self.email,
                subject="[mltshp] Please verify your email address",
                text_body="Hi there, could you visit this URL to verify your email address for us? Thanks. \n\nhttps://%s/verify-email/%s" % (
                    options.app_host, self.verify_email_token))
            pm.send()
            return True
        return False

    def create_reset_password_token(self):
        """
        This function will set the reset token and email the user
        """

        h = hashlib.sha1()
        h.update(str(time.time()).encode("ascii"))
        h.update(str(random.random()).encode("ascii"))
        self.reset_password_token = h.hexdigest()
        self.save()
        body = """
Hi there,

We just received a password reset request for this email address (user: %s). If you want to change your password just click this link:
https://%s/account/reset-password/%s

Thanks for using the site!
hello@mltshp.com

(If you're having problems with your account, please mail us! We are happy to help.)
""" % (self.name, options.app_host, self.reset_password_token)
        if not options.debug:
            pm = postmark.PMMail(api_key=options.postmark_api_key,
                sender="hello@mltshp.com", to=self.email,
                subject="[mltshp] Password change request",
                text_body=body)
            pm.send()

    def sharedimages(self):
        """
        This is a bit of a hack, but I wanted it in the model so I could fix it up later.
        This simply pulls all the shared images and adds one new field,
        which is a signed url to the amazon s3 thumbnail rather than through the server.
        Does not include deleted images.
        """
        images = self.connection.query("SELECT sf.id, sf.title, sf.name, sf.share_key, src.file_key, \
            src.thumb_key FROM sharedfile as sf, sourcefile as src \
            WHERE src.id = sf.source_id AND sf.user_id = %s and sf.deleted = 0 ORDER BY sf.created_at DESC limit 3", self.id)
        for image in images:
            file_path = "thumbnails/%s" % (image['thumb_key'])
            authenticated_url = s3_authenticated_url(options.aws_key, options.aws_secret, \
                bucket_name=options.aws_bucket, file_path=file_path)
            image['thumbnail_url'] = authenticated_url
        return images

    def set_profile_image(self, file_path, file_name, content_type, skip_s3=False):
        """
        Takes a local path, name and content-type, which are parameters passed in by
        nginx upload module.  Converts to RGB, resizes to thumbnail and uploads to S3.
        Returns False if some conditions aren't met, such as error making thumbnail
        or content type is one we don't support.
        """
        valid_content_types = ('image/gif', 'image/jpeg', 'image/jpg', 'image/png',)
        if content_type not in valid_content_types:
            return False

        destination = io.BytesIO()
        if not transform_to_square_thumbnail(file_path, 100*2, destination):
            return False

        if not skip_s3:
            bucket = S3Bucket()
            bucket.put_object(
                destination.getvalue(),
                "account/%s/profile.jpg" % self.id,
                ContentType="image/jpeg",
                CacheControl="max-age=86400",
                ACL="public-read"
            )
        self.profile_image = 1
        self.save()
        return True

    def profile_image_url(self, include_protocol=False):
        protocol = ''
        if self.profile_image:
            host = options.app_host
            if options.app_host == 'mltshp.com':
                host = options.cdn_ssl_host
            else:
                host = options.use_cdn and options.cdn_host or host
            if include_protocol:
                if options.app_host == 'mltshp.com':
                    protocol = 'https:'
                else:
                    protocol = 'http:'
            if options.app_host == 'mltshp.com':
                aws_url = "%s//%s/s3" % (protocol, host)
            else:
                # must be running for development. use the /s3 alias
                aws_url = "/s3"
            return "%s/account/%s/profile.jpg" % (aws_url, self.id)
        else:
            if include_protocol:
                if options.app_host == 'mltshp.com':
                    return "https://%s/static/images/default-icon-venti.svg" % options.cdn_ssl_host
                elif options.use_cdn and options.cdn_host:
                    return "http://%s/static/images/default-icon-venti.svg" % options.cdn_host
            return "/static/images/default-icon-venti.svg"

    def sharedfiles(self, page=1, per_page=10):
        """
        Shared files, paginated.
        """
        limit_start = (page-1) * per_page
        #return Sharedfile.where("user_id = %s and deleted=0 order by id desc limit %s, %s ", self.id, int(limit_start), per_page)
        user_shake = self.shake()
        return user_shake.sharedfiles(page=page, per_page=per_page)

    def sharedfiles_count(self):
        """
        Count of all of a user's saved sharedfiles, excluding deleted.
        """
        #return Sharedfile.where_count("user_id = %s and deleted=0", self.id)
        user_shake = self.shake()
        return user_shake.sharedfiles_count()

    def likes(self, before_id=None, after_id=None, per_page=10, q=None):
        """
        User's likes, paginated.
        """
        return Sharedfile.favorites_for_user(self.id, before_id=before_id, after_id=after_id, per_page=per_page, q=q)

    def likes_count(self):
        """
        Count of all of a user's saved sharedfiles, excluding deleted.
        """
        return models.favorite.Favorite.where_count("user_id = %s and deleted=0", self.id)

    def sharedfiles_from_subscriptions(self, before_id=None, after_id=None, per_page=10, q=None):
        """
        Shared files from subscriptions, paginated.
        """
        return Sharedfile.from_subscriptions(user_id=self.id, before_id=before_id, after_id=after_id, per_page=per_page, q=q)

    def has_favorite(self, sharedfile):
        """
        Returns True if user has already favorited the sharedfile, False otherwise.
        """
        if models.favorite.Favorite.get('user_id = %s and sharedfile_id = %s and deleted = 0' % (self.id, sharedfile.id)):
            return True
        else:
            return False

    def saved_sharedfile(self, sharedfile):
        """
        Return sharedfile if they have saved the file, otherwise None.

        We limit the get query to 1, because theroetically a user could have saved
        the same files multiple times, since we never enforced it, and .get throws
        exception when more than one returned.
        """
        saved = Sharedfile.get('user_id = %s and parent_id=%s and deleted = 0 limit 1' % (self.id, sharedfile.id))
        if saved:
            return saved
        else:
            return None

    def add_favorite(self, sharedfile):
        """
        Add a sharedfile as a favorite for the user.

        Will return False when one can't favorite a shared file:
         - it's deleted
         - it belongs to current user
         - already favorited

        Will return True if favoriting succeeds.
        """
        if sharedfile.deleted:
            return False
        if sharedfile.user_id == self.id:
            return False

        existing_favorite = models.favorite.Favorite.get('user_id = %s and sharedfile_id=%s' % (self.id, sharedfile.id))
        if existing_favorite:
            if existing_favorite.deleted == 0:
                return False
            existing_favorite.deleted = 0
            existing_favorite.save()
        else:
            favorite = models.favorite.Favorite(user_id=self.id, sharedfile_id=sharedfile.id)
            try:
                favorite.save()
            # This can only happen in a race condition, when request gets
            # sent twice (like during double click).  We just assume it worked
            # the first time and return a True.
            except IntegrityError:
                return True
            notification.Notification.new_favorite(self, sharedfile)

        calculate_likes.delay_or_run(sharedfile.id)
        return True


    def remove_favorite(self, sharedfile):
        """
        Remove a favorite. If there is no favorite or if it's already been remove, return False.
        """
        existing_favorite = models.favorite.Favorite.get('user_id= %s and sharedfile_id = %s and deleted=0' % (self.id, sharedfile.id))
        if not existing_favorite:
            return False
        if existing_favorite.deleted:
            return False
        existing_favorite.deleted = 1
        existing_favorite.save()

        calculate_likes.delay_or_run(sharedfile.id)
        return True

    def subscribe(self, to_shake):
        """
        Subscribe to a shake. If subscription already exists, then just mark deleted as 0.
        If this is a new subscription, send notification email.
        """
        if to_shake.deleted != 0:
            return False

        if to_shake.user_id == self.id:
            #you can't subscribe to your own shake, dummy!
            return False

        existing_subscription = subscription.Subscription.get('user_id = %s and shake_id = %s', self.id, to_shake.id)
        if existing_subscription:
            existing_subscription.deleted = 0
            existing_subscription.save()
        else:
            try:
                new_subscription = subscription.Subscription(user_id=self.id, shake_id=to_shake.id)
                new_subscription.save()
                notification.Notification.new_subscriber(sender=self, receiver=to_shake.owner(), action_id=new_subscription.id)
            # if we get an integrity error, means we already subscribed successfully, so carry along.
            except IntegrityError:
                pass
        return True

    def unsubscribe(self, from_shake):
        """
        Mark a subscription as deleted. If it doesn't exist, just return
        """
        if from_shake.user_id == self.id:
            #you can't unsubscribe to your own shake, dummy!
            return False

        existing_subscription = subscription.Subscription.get('user_id = %s and shake_id = %s', self.id, from_shake.id)
        if existing_subscription:
            existing_subscription.deleted = 1
            existing_subscription.save()
        return True

    def subscribe_to_user(self, shake_owner):
        """
        When a user hits a follow button by a user's name, will follow the users' main shake.
        """
        if self.id == shake_owner.id:
            return False

        shake_owners_shake = shake.Shake.get('user_id = %s and type=%s and deleted=0', shake_owner.id, 'user')
        return self.subscribe(shake_owners_shake)

    def total_file_stats(self):
        """
        Returns the file like, save, and view counts
        """
        counts = sharedfile.Sharedfile.query("SELECT sum(like_count) as likes, sum(save_count) as saves, sum(view_count) as views from sharedfile where user_id = %s AND deleted=0", self.id)
        counts = counts[0]
        for key, value in list(counts.items()):
            if not value:
                counts[key] = 0
        return counts


    def unsubscribe_from_user(self, shake_owner):
        """
        When a user hits the unfollow button by a user's name, will  unfollow the users' main shake.
        """
        if self.id == shake_owner.id:
            return False

        shake_owners_shake = shake.Shake.get('user_id = %s and type=%s and deleted=0', shake_owner.id, 'user')
        return self.unsubscribe(shake_owners_shake)

    def has_subscription(self, user):
        """
        Returns True if a user subscribes to user's main shake
        """
        users_shake = shake.Shake.get('user_id = %s and type = %s and deleted=0', user.id, 'user')
        return self.has_subscription_to_shake(users_shake)

    def has_subscription_to_shake(self, shake):
        """
        This should replace the above method completely.
        """
        if not shake:
            return False

        existing_subscription = subscription.Subscription.get('user_id = %s and shake_id = %s and deleted = 0', self.id, shake.id)
        if existing_subscription:
            return True
        else:
            return False

    def can_create_shake(self):
        """
        To create a shake a user needs to be paid and can only create
        ten shakes.
        """
        if options.readonly:
            return False
        if not self.is_plus():
            return False
        if len(self.shakes(include_only_group_shakes=True)) <= 100:
            return True
        return False

    def create_group_shake(self, title=None, name=None, description=None):
        """THERE IS NO (except for name) ERROR CHECKING HERE"""
        new_shake = None
        if not name:
            return None

        current_shakes = self.shakes()

        if len(current_shakes) == 1 or self.is_admin():
            new_shake = shake.Shake(user_id=self.id, type='group', title=title, name=name, description=description)
            new_shake.save()

        return new_shake

    def delete(self):
        if options.readonly:
            return False

        self.deleted = 1
        self.email = 'deleted-%s@mltshp.com' % (self.id)
        self.hashed_password = 'deleteduseracct'
        self.nsfw = 1
        self.verify_email_token = 'deleted'
        self.reset_password_token= 'deleted'
        self.profile_image = 0
        self.disable_notifications = 1
        self.invitation_count = 0

        if self.stripe_customer_id:
            # cancel any existing subscription
            customer = None
            try:
                customer = stripe.Customer.retrieve(self.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
            if customer and not getattr(customer, 'deleted', False):
                # deleting the customer object will also delete
                # active subscriptions
                customer.delete()

        self.save()

        external_services = externalservice.Externalservice.where("user_id=%s and deleted=0", self.id)
        for service in external_services:
            service.deleted = 1
            service.save()

        user_shake = self.shake()
        subscriptions = subscription.Subscription.where("user_id=%s or shake_id=%s", self.id, user_shake.id)
        for sub in subscriptions:
            sub.deleted = 1
            sub.save()

        shakemanagers = shakemanager.ShakeManager.where("user_id=%s and deleted=0", self.id)
        for sm in shakemanagers:
            sm.delete()

        shakes = shake.Shake.where("user_id = %s and deleted=0", self.id)
        for s in shakes:
            s.deleted = 1
            s.save()

        comments = models.comment.Comment.where('user_id=%s and deleted=0', self.id)
        for com in comments:
            com.deleted = 1
            com.save()

        favorites = models.favorite.Favorite.where('user_id=%s and deleted=0', self.id)
        for fav in favorites:
            fav.deleted = 1
            fav.save()

        notifications = models.notification.Notification.where('sender_id=%s and deleted=0', self.id)
        for no in notifications:
            no.deleted = 1
            no.save()

        shared_files = sharedfile.Sharedfile.where('user_id=%s and deleted=0', self.id)
        for sf in shared_files:
            sf.delete()

        return True

    def shake(self):
        return shake.Shake.get('user_id=%s and type=%s and deleted=0', self.id, 'user')

    def shakes(self, include_managed=False, include_only_group_shakes=False):
        """
        Returns all the shakes this user owns. That is, has a user_id = self.id
        in the shake table. If include_managed is True, also return those shakes
        this user manages in the manage table.  If include_only_group_shakes is True
        it will not return any 'user' shakes that the user owns.
        """
        managed_shakes = []
        if include_managed:
            sql = """SELECT shake.* from shake, shake_manager
                        WHERE shake_manager.user_id = %s
                            AND shake.id = shake_manager.shake_id
                            AND shake.deleted = 0
                            AND shake_manager.deleted = 0
                        ORDER BY shake_manager.shake_id
            """
            managed_shakes = shake.Shake.object_query(sql, self.id)
        user_shakes_sql = 'user_id=%s ORDER BY id'
        if include_only_group_shakes:
            user_shakes_sql = "user_id=%s and type='group' and deleted=0 ORDER BY id"
        return shake.Shake.where(user_shakes_sql, self.id) + managed_shakes

    _has_multiple_shakes = None
    def has_multiple_shakes(self):
        """
        A method we call when we render uimodule.Image to determine if user
        can save to more than one shake, thus giving them a different "save this"
        interaction.  We cache the results to cut down on the DB queries.
        """
        if self._has_multiple_shakes is None:
            if len(self.shakes()) > 1:
                self._has_multiple_shakes = True
            else:
                self._has_multiple_shakes = False
        return self._has_multiple_shakes

    def following_count(self):
        sql = """
          SELECT count(user.id) as following_count
            FROM subscription, user, shake
              WHERE subscription.user_id = %s
              AND subscription.shake_id = shake.id
              AND user.id = shake.user_id
              AND shake.deleted = 0
              AND subscription.deleted = 0
        """ % self.id
        count = self.query(sql)
        return int(count[0]['following_count'])

    def following(self, page=None):
        """
        This needs to be refactored, but it would be so slow if we
        were grabbing user objects for each user on 1,000 users.
        """
        select = """
          SELECT user.id as user_id, user.name as user_name, user.profile_image as user_image,
                    shake.name as shake_name, shake.type as shake_type , shake.image as shake_image,
                    shake.id as shake_id
            FROM subscription, user, shake
              WHERE subscription.user_id = %s
              AND subscription.shake_id = shake.id
              AND user.id = shake.user_id
              AND shake.deleted = 0
              AND subscription.deleted = 0
        """ % self.id

        if page is not None and page > 0:
            limit_start = (page-1) * 20
            select = "%s LIMIT %s, %s" % (select, limit_start, 20)

        users_and_shakes = User.query(select)

        us_list = []
        for us in users_and_shakes:
            this_follow = {}
            this_follow['image'] = '/static/images/default-icon-venti.svg'
            if us['shake_type'] == 'user':
                this_follow['id'] = us['user_id']
                this_follow['path'] = '/user/%s' % (us['user_name'])
                this_follow['name'] = us['user_name']
                this_follow['type'] = 'user'
                if us['user_image']:
                    this_follow['image'] = s3_url("account/%s/profile.jpg" % us['user_id'])
            else:
                this_follow['id'] = us['shake_id']
                this_follow['path'] = '/%s' % (us['shake_name'])
                this_follow['name'] = us['shake_name']
                this_follow['type'] = 'shake'
                if us['shake_image']:
                    this_follow['image'] = s3_url("account/%s/shake_%s.jpg" % (us['user_id'], us['shake_name']))

            us_list.append(this_follow)
        return us_list


    def can_follow(self, shake):
        """
        A user can follow a shake only if it doesn't belong
        to them.
        """
        if options.readonly:
            return False
        if not self.is_paid:
            return False
        if shake.deleted != 0:
            return False
        if shake.user_id == self.id:
            return False
        return True

    def display_name(self):
        if self.full_name:
            return self.full_name
        else:
            return self.name

    def flag_nsfw(self):
        """
        Set the nsfw flag for user.
        """
        self.nsfw = True
        return self.save()

    def unflag_nsfw(self):
        """
        Remove the nsfw flag for user.
        """
        self.nsfw = False
        return self.save()

    def is_superuser(self):
        """
        Return True if user is a superuser administrator.
        """
        return self.name in options.superuser_list.split(',')

    def is_moderator(self):
        """
        Return True if user is a moderator.
        """
        return self.name in options.moderator_list.split(',')

    def is_admin(self):
        """
        Return True if user is a superuser or moderator.
        """
        return self.is_superuser() or self.is_moderator()

    def update_email(self, email):
        """
        Since updating an email is a bit tricky, call this method instead of
        assigning to the property directly.  Validates the name and email
        address and will assign errors if its already taken, which will
        prevent saving.
        """
        email = email.strip().lower()
        if email != self.email:
            self.email = email
            self._validate_email_uniqueness()

    def uploaded_kilobytes(self, start_time=None, end_time=None):
        """
        Returns the total number of kilobytes uploaded for the time period specified
        If no time period specified, returns total of all time.
        """

        start_string = ''
        end_string = ''
        if start_time:
            start_string = " AND created_at >= '%s 00:00:00'" % (start_time)

        if end_time:
            end_string = " AND created_at <= '%s 23:59:59'" % (end_time)

        sql = "SELECT SUM(size) as total_bytes FROM sharedfile WHERE user_id = %s " + start_string + end_string
        response = self.query(sql, self.id)

        if not response[0]['total_bytes'] or int(response[0]['total_bytes']) == 0:
            return 0
        else:
            return int(response[0]['total_bytes'] / 1024)

    def can_post(self):
        return self.can_upload_this_month()

    def can_upload_this_month(self):
        """
        Returns if this user can upload this month.
        If is_paid or under the max_mb_per_month setting: True
        """
        if not self.is_paid:
            return False

        if self.is_plus():
            return True

        month_days = calendar.monthrange(datetime.utcnow().year,datetime.utcnow().month)
        start_time = datetime.utcnow().strftime("%Y-%m-01")
        end_time = datetime.utcnow().strftime("%Y-%m-" + str(month_days[1]) )

        total_bytes = self.uploaded_kilobytes(start_time=start_time, end_time=end_time)

        if total_bytes == 0:
            return True

        total_megs = total_bytes / 1024

        if total_megs > options.max_mb_per_month:
            return False
        else:
            return True

    def can_request_invitation_to_shake(self, shake_id):
        if options.readonly:
            return False

        #shake exists
        s = shake.Shake.get('id = %s and deleted=0', shake_id)
        if not s:
            return False

        #not a manager of the shake
        for manager in s.managers():
            if manager.id == self.id:
                return False

        #is not owner of the shake
        if self.id == s.user_id:
            return False

        #no notification exists
        no = notification.Notification.get('sender_id = %s and receiver_id = %s and action_id = %s and type = %s and deleted = 0', self.id, s.user_id, s.id, 'invitation_request')
        if no:
            return False

        return True

    def request_invitation_to_shake(self, shake_id):
        s = shake.Shake.get('id=%s and deleted=0', shake_id)
        if s:
            manager = s.owner()
            no = notification.Notification.new_invitation_to_shake(self, manager, s.id)

    def active_paid_subscription(self):
        if self.stripe_customer_id is not None:
            # fetch customer then find active plan
            customer = None
            try:
                customer = stripe.Customer.retrieve(self.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
            if customer and not getattr(customer, 'deleted', False):
                subs = []
                if customer.subscriptions.total_count > 0:
                    subs = [s for s in customer.subscriptions.data
                        if s.status == "active" and s.plan.id in ("mltshp-single", "mltshp-double")]
                if subs:
                    return {
                        "processor_name": "Stripe",
                        "id": subs[0].id,
                        "start_date": datetime.fromtimestamp(subs[0].current_period_start).strftime("%Y-%m-%d %H:%M:%S"),
                        "end_date": datetime.fromtimestamp(subs[0].current_period_end).strftime("%Y-%m-%d %H:%M:%S"),
                    }
        else:
            processors = {
                PaymentLog.VOUCHER: {
                    "name": "Voucher",
                },
                PaymentLog.STRIPE: {
                    "name": "Stripe",
                },
            }
            pl = PaymentLog.last_payments(1, user_id=self.id)
            if pl and pl[0].processor in processors:
                return {
                    "processor_name": processors[pl[0].processor]["name"],
                    "start_date": pl[0].transaction_date,
                    "end_date": pl[0].next_transaction_date,
                    "id": pl[0].subscription_id,
                }
        return None

    def _validate_name_uniqueness(self):
        """
        Validation only run on creation, for now, also needs to
        run if value has changed
        """
        if self.get("name = %s", self.name):
            self.add_error('name', 'Username has already been taken.')
            return False
        return True

    def _validate_email_uniqueness(self):
        """
        Validation only run on creation, for now, also needs to
        run if value has changed
        """
        email = self.email.strip().lower()
        if self.get("email = %s", email):
            self.add_error('email', 'This email already has an account.')
            return False
        return True

    def _validate_name(self):
        """
        At some point, this and the below validations belong in the model.
        """
        if self.name == None or self.name == "":
            self.add_error('name', 'You definitely need a username')
            return False

        if len(self.name) > 30:
            self.add_error('name', 'Username should be less than 30 characters.')
            return False

        if re.search("[^a-zA-Z0-9\-\_]", self.name):
            self.add_error('name', 'Username can only contain letters, numbers, dash and underscore characters.')
            return False
        return True

    def _validate_email(self):
        """
        Borrowed from Django's email validation.
        """
        if self.email == None or self.email == "":
            self.add_error('email', "You'll need an email to verify your account.")
            return False

        if not email_re.match(self.email):
            self.add_error('email', "Email doesn't look right.")
        return True

    def _validate_full_name(self):
        if len(self.full_name) > 100:
            self.add_error('full_name', "Name is too long for us.")
            return False
        return True

    def _validate_about(self):
        if len(self.about) > 255:
            self.add_error('about', "The about text needs to be shorter than 255 characters.")
            return False
        return True

    def _validate_website(self):
        if len(self.website) > 255:
            self.add_error('website', "The URL is too long.")
            return False
        if self.website != '':
            parsed = urllib.parse.urlparse(self.website)
            if parsed.scheme not in ('http', 'https',):
                self.add_error('website', "Doesn't look to be a valid URL.")
                return False
            if parsed.netloc == '':
                self.add_error('website', "Doesn't look to be a valid URL.")
                return False
        return True

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @classmethod
    def random_recommended(self, limit):
        """
        Return a randomized list of users that have recommended flag set.
        """
        return self.where("recommended = 1 and deleted = 0 order by rand() limit %s", limit)

    @classmethod
    def recommended_for_user(self, user):
        """
        Returns a list of users that the passed in user doesn't follow, but
        maybe should.
        """
        following_sql = """
            select user.id from user
                left join shake
                on shake.user_id = user.id and shake.deleted=0
                left join subscription
                on subscription.shake_id = shake.id
                where user.deleted = 0 and subscription.user_id  = %s and subscription.deleted=0
        """
        following = self.query(following_sql, user.id)
        following = [somebody['id'] for somebody in following]

        all_users_sql = """
            select id from user where deleted=0
        """
        all_users = self.query(all_users_sql)
        all_users = [somebody['id'] for somebody in all_users]

        not_following = set(all_users) - set(following)

        users_that_favorited_sql = """
            select s1.user_id as s1_user, s2.user_id as s2_user from sharedfile as s1
            left join sharedfile s2
            on s1.parent_id = s2.id
            left join favorite
            on favorite.sharedfile_id = s1.id
            where favorite.deleted = 0
            and favorite.user_id = %s
            limit 1000
        """
        users_that_favorited_result = self.query(users_that_favorited_sql, user.id)
        users_that_favorited = [somebody['s1_user'] for somebody in users_that_favorited_result] + \
                               [somebody['s2_user'] for somebody in users_that_favorited_result if somebody]

        not_following_favorited = not_following & set(users_that_favorited)

        if len(not_following_favorited) == 0:
            return []

        if len(not_following_favorited) < 5:
            sample_size = len(not_following_favorited)
        else:
            sample_size = 5

        samples = random.sample(not_following_favorited, sample_size)
        users = []
        for user_id in samples:
            fetched_user = User.get("id = %s and deleted = 0", user_id)
            if fetched_user:
                users.append(fetched_user)

        return users

    @classmethod
    def find_by_name_fragment(self, name=None, limit=10):
        """
        Finds the user by using a fragment of their name. Name must start
        with the fragment.
        """
        if name == '' or name == None:
            return []
        name = name + '%'
        return User.where("name like %s and deleted=0 limit %s", name, limit)

    @staticmethod
    def authenticate(name, password):
        """
        Returns User object or None.
        """
        hashed_password = User.generate_password_digest(password)
        return User.get("name = %s and hashed_password = %s and deleted = 0", name, hashed_password)

    @staticmethod
    def find_unmigrated_user(name, password):
        """
        Returns a non-migrated User object or None.

        This code is part of the MLKSHK->MLTSHP migration project. It can be removed
        once the migration is over. We are tracking unmigrated users as deleted records,
        with a deleted value of 2.
        """
        hashed_password = User.generate_password_digest(password)
        return User.get("name = %s and hashed_password = %s and deleted = 2", name, hashed_password)

    @staticmethod
    def generate_password_digest(password):
        secret = options.auth_secret
        h = hashlib.sha1()
        h.update(password.encode(encoding="UTF-8"))
        h.update(secret.encode(encoding="UTF-8"))
        return h.hexdigest()

from .sharedfile import Sharedfile
