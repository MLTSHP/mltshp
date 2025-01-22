import re
import io
from urllib.parse import urljoin

from tornado.options import options
from lib.s3 import S3Bucket
from PIL import Image

from lib.flyingcow import Model, Property
from lib.flyingcow.cache import ModelQueryCache
from lib.reservedshakenames import reserved_names
from lib.utilities import transform_to_square_thumbnail, s3_url, utcnow

from . import user, shake, shakesharedfile, sharedfile, subscription, shakemanager


class Shake(ModelQueryCache, Model):
    user_id     = Property(name='user_id')
    type        = Property(name='type', default='user')
    title       = Property(name='title')
    name        = Property(name='name')
    image       = Property(name='image', default=0)
    description = Property(name='description')
    recommended = Property(name='recommended', default=0)
    featured    = Property(name='featured', default=0)
    shake_category_id = Property(name='shake_category_id', default=0)
    deleted     = Property(default=0)
    created_at  = Property(name='created_at')
    updated_at  = Property(name='updated_at')

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        if self.type == 'group':
            self._validate_title()
            self._validate_name()
        if len(self.errors) > 0:
            return False
        return super(Shake, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def delete(self):
        """
        Sets the deleted flag to 1 and saves to DB.
        """
        if options.readonly:
            return False

        self.deleted = 1;
        self.save()

    def as_json(self, extended=False):
        base_dict = {
            'id' : self.id,
            'name': self.display_name(),
            'url': 'https://%s%s' % (options.app_host, self.path()),
            'thumbnail_url': self.thumbnail_url(),
            'description': self.description,
            'type': self.type,
            'created_at': self.created_at and self.created_at.replace(microsecond=0, tzinfo=None).isoformat() + 'Z' or None,
            'updated_at': self.updated_at and self.updated_at.replace(microsecond=0, tzinfo=None).isoformat() + 'Z' or None
        }

        if extended:
            base_dict['owner'] = self.owner().as_json()

        return base_dict

    def owner(self):
        return user.User.get('id=%s', self.user_id)

    def on_create(self):
        #create a subscription for the user if this is a group
        if self.type == 'group':
            new_sub = subscription.Subscription(user_id=self.user_id, shake_id=self.id)
            new_sub.save()

    def page_image(self):
        """
        Return's users profile image if it's a user shake or the shake image.
        If no image, returns None.
        """
        if self.type == 'user':
            return self.owner().profile_image_url()
        else:
            if self.image:
                scheme = options.use_cdn and options.cdn_ssl_host and "https" or "http"
                host = (options.use_cdn and options.cdn_ssl_host or options.cdn_host) or options.app_host
                return f"{scheme}://{host}/s3/account/{self.user_id}/shake_{self.name}.jpg"
            else:
                return None

    def thumbnail_url(self):
        if self.type == 'user':
            return self.owner().profile_image_url(include_protocol=True)
        else:
            scheme = options.use_cdn and options.cdn_ssl_host and "https" or "http"
            host = (options.use_cdn and options.cdn_ssl_host or options.cdn_host) or options.app_host
            if self.image:
                return f"{scheme}://{host}/s3/account/{self.user_id}/shake_{self.name}_small.jpg"
            else:
                return f"{scheme}://{host}/static/images/default-icon-venti.svg"

    def path(self):
        """
        Return the path for the shake with a leading slash.
        """
        if self.type == 'user':
            return '/user/%s' % self.owner().name
        else:
            return '/%s' % self.name

    def display_name(self, user=None):
        """
        If it's a user shake returns the user's "name", otherwise return.
        the shake's title.  If a user is passed in and it's the user's main
        shake, it returns "Your Shake".
        """
        if self.type == 'user':
            if user and user.id == self.user_id:
                return "Your Shake"
            return self.owner().display_name()
        else:
            return self.title

    def can_update(self, user_id):
        if options.readonly:
            return False

        if user_id == self.user_id:
            return True

        #do some checking in the shakemanager table to see if this person can
        #contribute to this shake.
        existing_manager = shakemanager.ShakeManager.get("user_id = %s and shake_id = %s and deleted = 0", user_id, self.id)
        if existing_manager:
            return True
        return False

    def _validate_title(self):
        """
        Title can't be blank.
        """
        if self.title == None or self.title == "":
            self.add_error('title', "Title can't be blank.")
            return False

    def _validate_name(self):
        """
        Check that the name being used is valid and not a reserved word
        """
        if self.name == None or self.name == "":
            self.add_error('name', 'That URL is not valid.')
            return False

        if self.name.lower() in reserved_names:
            self.add_error('name', 'That URL is reserved.')
            return False

        if len(self.name) > 0 and len(self.name) > 25:
            self.add_error('name', 'URLs can be 1 to 25 characters long.')
            return False

        if re.search("[^a-zA-Z0-9-]", self.name):
            self.add_error('name', 'Username can only contain letters, numbers, and dashes.')
            return False

        existing_shake = shake.Shake.get("name = %s and deleted <> 1", self.name)
        if existing_shake and existing_shake.id != self.id:
            self.add_error('name', 'That URL is already taken.')
            return False

        return True

    def subscribers(self, page=None):
        sql = """SELECT user.* FROM subscription
                   JOIN user ON user.id = subscription.user_id AND user.deleted = 0
                   WHERE shake_id = %s
                       AND subscription.deleted = 0
                   ORDER BY subscription.id """
        if page is not None and page > 0:
            limit_start = (page-1) * 20
            sql = "%s LIMIT %s, %s" % (sql, limit_start, 20)
        return user.User.object_query(sql, self.id)

    def subscriber_count(self):
        sql = """SELECT count(*) AS subscriber_count FROM subscription
                   JOIN user ON user.id = subscription.user_id AND user.deleted = 0
                   WHERE shake_id = %s
                       AND subscription.deleted = 0"""
        count = user.User.query(sql, self.id)
        return int(count[0]['subscriber_count'])

    def sharedfiles_count(self):
        return shakesharedfile.Shakesharedfile.where_count("shake_id=%s and deleted = 0", self.id)

    def sharedfiles(self, page=1, per_page=10):
        """
        Shared files, paginated.
        """
        limit_start = (page-1) * per_page
        sql = """SELECT sharedfile.* FROM sharedfile, shakesharedfile
                 WHERE shakesharedfile.shake_id = %s and shakesharedfile.sharedfile_id = sharedfile.id and
                       shakesharedfile.deleted = 0 and sharedfile.deleted = 0
                 ORDER BY shakesharedfile.sharedfile_id desc limit %s, %s"""
        return sharedfile.Sharedfile.object_query(sql,self.id, int(limit_start), per_page)

    def sharedfiles_paginated(self, per_page=10, since_id=None, max_id=None):
        """
        Pulls a shake's timeline, can key off and go backwards (max_id) and forwards (since_id)
        in time to pull the per_page amount of posts.
        """
        constraint_sql = ""
        order = "desc"
        if max_id:
            constraint_sql = "AND shakesharedfile.sharedfile_id < %s" % (int(max_id))
        elif since_id:
            order = "asc"
            constraint_sql = "AND shakesharedfile.sharedfile_id > %s" % (int(since_id))

        sql = """SELECT sharedfile.* FROM sharedfile, shakesharedfile
                 WHERE shakesharedfile.shake_id = %s and shakesharedfile.sharedfile_id = sharedfile.id and
                 shakesharedfile.deleted = 0 and sharedfile.deleted = 0
                 %s
                 ORDER BY shakesharedfile.sharedfile_id %s limit %s, %s""" % (int(self.id), constraint_sql, order, 0, int(per_page))
        results = sharedfile.Sharedfile.object_query(sql)

        if order == "asc":
            results.reverse()

        return results

    def add_manager(self, user_to_add=None):
        if options.readonly:
            return False

        if not user_to_add:
            return False

        if user_to_add.id == self.user_id:
            return False

        #was this user a previous manager?
        existing_manager = shakemanager.ShakeManager.get("user_id = %s AND shake_id = %s", user_to_add.id, self.id)
        if existing_manager:
            existing_manager.deleted = 0
            existing_manager.save()
        else:
            new_manager = shakemanager.ShakeManager(shake_id=self.id, user_id=user_to_add.id)
            new_manager.save()
        return True

    def remove_manager(self, user_to_remove=None):
        if options.readonly:
            return False

        if not user_to_remove:
            return False

        if user_to_remove.id == self.user_id:
            return False

        existing_manager = shakemanager.ShakeManager.get("user_id = %s AND shake_id = %s", user_to_remove.id, self.id)
        if existing_manager:
            existing_manager.deleted = 1
            existing_manager.save()
            return True
        else:
            return False

    def managers(self):
        sql = """SELECT user.* FROM shake_manager
                 JOIN user ON user.id = shake_manager.user_id AND user.deleted = 0
                 WHERE shake_manager.shake_id = %s
                    AND shake_manager.deleted = 0
                 ORDER BY user.id""" % (self.id)
        return user.User.object_query(sql)

    def is_owner(self, user):
        """
        A convenience method that accepts a None value or a user
        object and returns True or False if the user owns the shake.
        """
        if not user:
            return False
        if self.user_id != user.id:
            return False
        return True

    def can_edit(self, user):
        """
        Determines whether or not a user can edit a file.  Currently
        only the owner can edit.  Accepts None value.
        """
        if options.readonly:
            return False

        if not user:
            return False
        return self.is_owner(user)

    def set_page_image(self, file_path=None, sha1_value=None):
        thumb_cstr = io.BytesIO()
        image_cstr = io.BytesIO()

        if not file_path or not sha1_value:
            return False

        #generate smaller versions
        if not transform_to_square_thumbnail(file_path, 48*2, thumb_cstr):
            return False

        if not transform_to_square_thumbnail(file_path, 284*2, image_cstr):
            return False

        bucket = S3Bucket()

        try:
            #save thumbnail
            thumb_bytes = thumb_cstr.getvalue()
            bucket.put_object(
                thumb_bytes,
                "account/%s/shake_%s_small.jpg" % (self.user_id, self.name),
                ACL="public-read",
                ContentType="image/jpeg",
            )

            #save small
            image_bytes = image_cstr.getvalue()
            bucket.put_object(
                image_bytes,
                "account/%s/shake_%s.jpg" % (self.user_id, self.name),
                ACL="public-read",
                ContentType="image/jpeg",
            )

            self.image = 1
            self.save()
        except Exception as e:
            return False

        return True

    def feed_date(self):
        """
        Returns a date formatted to be included in feeds
        e.g., Tue, 12 Apr 2005 13:59:56 EST
        """
        return self.created_at and self.created_at.strftime("%a, %d %b %Y %H:%M:%S %Z")

    @classmethod
    def featured_shakes(self, limit=3):
        """
        Return a randomly sorted list of featured shakes.
        """
        return self.where("type = 'group' and featured = 1 order by rand() limit %s", limit)

    @classmethod
    def for_category(self, category):
        """
        Return a randomly sorted list of recommended shakes for a category.
        """
        return self.where("type = 'group' and shake_category_id = %s order by name", category.id)

