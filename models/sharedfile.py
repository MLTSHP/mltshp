import re
from os import path
import hashlib
from datetime import timedelta

from tornado import escape
from tornado.options import options

from lib.flyingcow import Model, Property
from lib.flyingcow.cache import ModelQueryCache
from lib.flyingcow.db import IntegrityError
from lib.utilities import base36encode, base36decode, pretty_date, s3_url, rfc822_date, utcnow

from . import user
from . import sourcefile
from . import fileview
from . import favorite
from . import shakesharedfile
from . import shake
from . import comment
from . import notification
from . import conversation

import models.post
import models.nsfw_log
import models.tag
import models.tagged_file

from tasks.timeline import add_posts, delete_posts
from tasks.counts import calculate_saves
from tasks.transcode import transcode_sharedfile


class Sharedfile(ModelQueryCache, Model):
    source_id = Property()
    user_id = Property()
    name = Property()
    title = Property()
    description = Property()
    alt_text = Property()
    source_url = Property()
    share_key = Property()
    content_type = Property()
    size = Property(default=0)
    # we set default to 0, since DB does not accept Null values
    like_count = Property(default=0)
    save_count = Property(default=0)
    view_count = Property(default=0)
    deleted = Property(default=0)
    parent_id = Property(default=0)
    original_id = Property(default=0)
    created_at = Property()
    updated_at = Property()
    activity_at = Property()

    def get_title(self, sans_quotes=False):
        """
        Returns title, escapes double quotes if sans_quotes is True, used
        for rendering title inside fields.
        """
        title = self.title
        if title is None:
            title = ''
        if sans_quotes:
            title = re.sub('"', '&quot;', title)
        return title.strip()

    def get_description(self, raw=False):
        """
        Returns desciption, escapes double quotes if sans_quotes is True, used
        for rendering description inside fields.
        """
        description = self.description
        if description is None:
            description = ''

        scheme = (options.use_cdn and "https") or "http"

        if not raw:
            extra_params = 'target="_blank" rel="nofollow"'

            description = escape.linkify(description, True,
                extra_params=extra_params)

            description = re.sub(
                r'(\A|\s)#(\w+)',
                r'\1<a href="' + scheme + '://' + options.app_host + r'/tag/\2">#\2</a>',
                description)
            description = description.replace('\n', '<br>')
        return description.strip()

    def get_alt_text(self, raw=False):
        """
        Returns alt text, converts new lines to <br> unless raw is True, used
        for rendering alt text inside textarea fields.
        """
        alt_text = self.alt_text
        if alt_text is None:
            alt_text = ''

        if not raw:
            alt_text = escape.xhtml_escape(alt_text)
            alt_text = alt_text.replace('\n', '<br>')

        return alt_text.strip()

    def save(self, *args, **kwargs):
        """
        Sets the dates before saving.
        """
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        ignore_tags = False

        #we dont want to set tags if this is a save from a shared file
        if 'ignore_tags' in kwargs and kwargs['ignore_tags']:
            ignore_tags = True

        if 'ignore_tags' in kwargs:
            del(kwargs['ignore_tags'])

        super(Sharedfile, self).save(*args, **kwargs)

        if ignore_tags:
            return

        # clear out all tags
        all_tagged_files = models.TaggedFile.where('sharedfile_id = %s', self.id)
        for tf in all_tagged_files:
            tf.deleted = 1
            tf.save()

        # extract tags
        tags = self.find_tags()
        for t in tags:
            tag = models.Tag.get("name = %s", t)
            if not tag:
                tag = models.Tag(name=t)
                tag.save()

            tagged_file = models.TaggedFile.get('sharedfile_id = %s and tag_id = %s',
                self.id, tag.id)
            if tagged_file and tagged_file.deleted:
                tagged_file.deleted = 0
                tagged_file.save()
            else:
                tagged_file = models.TaggedFile(sharedfile_id=self.id,
                    tag_id = tag.id, deleted=0)
                tagged_file.save()


    def can_save(self, user_check=None):
        """
        Can only save the file if the user is different.

        Also, if we haven't already saved it.
        """
        if options.readonly:
            return False
        if not user_check:
            return False
        if self.user_id == user_check.id:
            return False
        else:
            return True

    def can_delete(self, user_check=None):
        """
        Can only delete if the file belongs to the user.
        """
        if options.readonly:
            return False
        if not user_check:
            return False
        if self.user_id == user_check.id:
            return True
        else:
            return False

    def can_favor(self, user_check=None):
        """
        Can favor any image a user hasn't favorited, except
        if it's your image.
        """
        if options.readonly:
            return False
        if not user_check:
            return False
        if self.user_id == user_check.id:
            return False
        return not user_check.has_favorite(self)

    def can_unfavor(self, user_check=None):
        """
        Any use can favorite if they've already favored.
        """
        if options.readonly:
            return False
        if not user_check:
            return False
        if self.user_id == user_check.id:
            return False
        return user_check.has_favorite(self)

    def can_edit(self, user_check=None):
        """
        Checks if a user can edit the sharedfile. Can only edit the shardfile
        if the sharedfile belongs to them.
        """
        if options.readonly:
            return False
        if not user_check:
            return False
        if self.user_id == user_check.id:
            return True
        else:
            return False

    def save_to_shake(self, for_user, to_shake=None):
        """
        Saves this file to a user's shake, or to the to_shake
        if it is provided.
        """
        new_sharedfile = Sharedfile()
        new_sharedfile.user_id = for_user.id
        new_sharedfile.name = self.name
        new_sharedfile.title = self.title
        new_sharedfile.content_type = self.content_type
        new_sharedfile.source_url = self.source_url
        new_sharedfile.source_id = self.source_id
        new_sharedfile.parent_id = self.id
        new_sharedfile.description = self.description
        new_sharedfile.alt_text = self.alt_text

        if self.original_id == 0:
            new_sharedfile.original_id = self.id
        else:
            new_sharedfile.original_id = self.original_id
        new_sharedfile.save(ignore_tags=True)
        new_sharedfile.share_key = base36encode(new_sharedfile.id)
        new_sharedfile.save(ignore_tags=True)

        if to_shake:
            shake_to_save = to_shake
        else:
            shake_to_save = for_user.shake()
        new_sharedfile.add_to_shake(shake_to_save)

        #create a notification to the sharedfile owner
        notification.Notification.new_save(for_user, self)

        calculate_saves.delay_or_run(self.id)
        return new_sharedfile

    def render_data(self, user=None, store_view=True):
        user_id = None
        if user:
            user_id = user.id
        source = self.sourcefile()
        oembed = escape.json_decode(source.data)
        if store_view:
            self.add_view(user_id)

        html = oembed['html'] or ""

        # force https for any URLs in the html
        html = html.replace('http://', 'https://')

        extra_attributes = ""

        # Allows iframe to trigger full-screen display
        if 'allowfullscreen' not in html:
            extra_attributes += " allowfullscreen"

        # Enable sandbox; only permit scripting (most rich embeds will need this)
        # allow-popups is needed for opening links to original content (ie, YouTube embeds)
        # allow-popups-to-escape-sandbox frees the popped up window from any
        # restrictions mltshp decides to enforce.
        # Related: https://github.com/MLTSHP/mltshp/issues/746
        if 'sandbox=' not in html:
            extra_attributes += ' sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-presentation"'

        # Prevent referrer leaks to third parties
        if 'referrerpolicy=' not in html:
            extra_attributes += ' referrerpolicy="no-referrer-when-downgrade"'

        if 'allow=' not in html:
            extra_attributes += ' allow="encrypted-media"'

        # Force lazy loading
        if 'loading=' not in html:
            extra_attributes += ' loading="lazy"'

        # Force low priority fetching
        if 'fetchpriority=' not in html:
            extra_attributes += ' fetchpriority="low"'

        if extra_attributes:
            html = html.replace('<iframe ', '<iframe ' + extra_attributes)

        html = html.replace('autoplay=0', '')

        return html

    def post_url(self, relative=False):
        if relative:
            return '/p/%s' % (self.share_key)
        else:
            scheme = (options.use_cdn and "https") or "http"
            return '%s://%s/p/%s' % (scheme, options.app_host, self.share_key)

    def as_json(self, user_context=None):
        """
        If user_context is provided, adds a couple of fields to
        the returned dict representation, such as 'saved' and 'liked'.
        """
        u = self.user()
        source = self.sourcefile()

        scheme = (options.use_cdn and "https") or "http"
        json_object = {
            'user': u.as_json(),
            'nsfw' : source.nsfw_bool(),
            'pivot_id' : self.share_key,
            'sharekey' : self.share_key,
            'name' : self.name,
            'views' : self.view_count,
            'likes' : self.like_count,
            'saves' : self.save_count,
            'comments' : self.comment_count(),
            'width' : source.width,
            'height' : source.height,
            'title' : self.title,
            'description' : self.description,
            'alt_text' : self.alt_text,
            'posted_at' : self.created_at.replace(microsecond=0, tzinfo=None).isoformat() + 'Z',
            'permalink_page' : self.post_url(),
        }

        if user_context:
            json_object['saved'] = bool(user_context.saved_sharedfile(self))
            json_object['liked'] = user_context.has_favorite(self)

        if(source.type == 'link'):
            json_object['url'] = self.source_url
        else:
            json_object['original_image_url'] = '%s://s.%s/r/%s' % (scheme, options.app_host, self.share_key)
        return json_object

    def sourcefile(self):
        """
        Returns sharedfile's Sourcefile.
        """
        return sourcefile.Sourcefile.get("id = %s", self.source_id)

    def can_user_delete_from_shake(self, user, from_shake):
        """
        A user can delete a sharedfile from a shake if they are the owner of the sharedfile
        or if they are the shake owner.
        """
        if options.readonly:
            return False
        if self.user_id == user.id:
            return True
        if from_shake.is_owner(user):
            return True
        return False

    def delete_from_shake(self, from_shake):
        """
        Removes a file from a shake.  Make sure we find the shakesharedfile entry and only mark it as
        deleted if it's in another shake (2 or more shakes when this action was initiated).
        """
        if options.readonly:
            return False
        ssf = shakesharedfile.Shakesharedfile.get("shake_id = %s and sharedfile_id = %s and deleted=0", from_shake.id, self.id)
        if not ssf:
            return False
        ssf.deleted = 1
        if ssf.save():
            return True
        else:
            return False

    def add_to_shake(self, to_shake):
        """
        Takes any shake and adds this shared file to it.
            - TODO: need to check if has permission
        """
        if options.readonly:
            return False
        ssf = shakesharedfile.Shakesharedfile.get("shake_id = %s and sharedfile_id = %s and deleted=0", to_shake.id, self.id)
        if not ssf:
            ssf = shakesharedfile.Shakesharedfile(shake_id=to_shake.id, sharedfile_id=self.id)
        ssf.deleted = 0
        ssf.save()
        if ssf.saved():
            add_posts.delay_or_run(shake_id=to_shake.id, sharedfile_id=self.id, sourcefile_id=self.source_id)

    def shakes(self):
        """
        The shakes this file is in.
        """
        select = """
            select shake.* from shake
            left join shakesharedfile on
            shakesharedfile.shake_id = shake.id
            where shake.deleted = 0
            and shakesharedfile.sharedfile_id = %s
            and shakesharedfile.deleted = 0;
        """
        return shake.Shake.object_query(select, self.id)

    def user(self):
        """
        Returns sharedfile's user.
        """
        return user.User.get("id = %s and deleted=0", self.user_id)

    def parent(self, include_deleted=False):
        """
        Returns the parent object if it's set, otherwise returns None.
        """
        if not bool(self.parent_id):
            return None
        if include_deleted:
            deleted_clause = ''
        else:
            deleted_clause = ' and deleted=0'
        return self.get("id = %s" + deleted_clause, self.parent_id)

    def original(self, include_deleted=False):
        """
        Returns the original object if it's set, otherwise returns None.
        """
        if not bool(self.original_id):
            return None
        if include_deleted:
            deleted_clause = ''
        else:
            deleted_clause = ' and deleted=0'
        return self.get("id = %s" + deleted_clause, self.original_id)

    def parent_user(self):
        """
        If a sharedfile has a parent_sharedfile_id set, returns user of the
        parent sharedfile.
        """
        parent = self.parent()
        if not parent:
            return None
        return parent.user()

    def original_user(self):
        """
        If a sharedfile has an original_id, this returns the user who
        originally shared that file
        """
        original = self.original()
        if not original:
            return None
        return original.user()

    def delete(self):
        """
        Sets the deleted flag to 1 and saves to DB.
        """
        if options.readonly:
            return False

        self.deleted = 1;
        self.save()

        tags = models.TaggedFile.where('sharedfile_id = %s', self.id)
        for tag in tags:
            tag.deleted = 1
            tag.save()

        delete_posts.delay_or_run(sharedfile_id=self.id)

        if self.original_id > 0:
            calculate_saves.delay_or_run(self.original_id)
        if self.parent_id > 0:
            calculate_saves.delay_or_run(self.original_id)

        #mute conversations
        conversations = conversation.Conversation.where('sharedfile_id = %s', self.id)
        [c.mute() for c in conversations]

        ssfs = shakesharedfile.Shakesharedfile.where('sharedfile_id = %s', self.id)
        [ssf.delete() for ssf in ssfs]


    def add_view(self, user_id=None):
        """
        Increments a view for the image.
        """
        if options.readonly:
            return False

        if not user_id:
            user_id = 0
        self.connection.execute("INSERT INTO fileview (user_id, sharedfile_id, created_at) VALUES (%s, %s, NOW())", user_id, self.id)

    def pretty_created_at(self):
        """
        A friendly version of the created_at date.
        """
        return pretty_date(self.created_at)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow()
        self.updated_at = utcnow()

    def increment_view_count(self, amount):
        """
        Update view_count field for current sharedfile.
        """
        view_count = self.view_count or 0
        self.update_attribute('view_count', view_count + amount)

    def calculate_view_count(self, last_fileview=0):
        """
        Calculate count of all views for the sharedfile.
        """
        count = fileview.Fileview.query(
            """SELECT count(*) AS result_count FROM fileview
               WHERE sharedfile_id = %s and user_id != %s""", self.id, self.user_id)
        return int(count[0]['result_count'])

    def livish_view_count(self):
        """
        If a file is recent, show its live view count.
        """
        if utcnow() - self.created_at < timedelta(hours=24):
            return (self.view_count or 0) + self.calculate_view_count()
        else:
            # if a file is not recent and also has zero
            # then try to pull a live count anyway.
            if self.view_count == 0:
                return self.calculate_view_count()
            else:
                return self.view_count

    def saves(self):
        """
        Retrieve all saves of this file.
        """
        original =  self.where("original_id = %s and deleted = 0", self.id)
        if len(original) > 0:
            return original
        else:
            return self.where("parent_id = %s and deleted = 0", self.id)

    def favorites(self):
        """
        Retrieve all saves of this file.
        """
        return favorite.Favorite.where("sharedfile_id = %s and deleted = 0 ORDER BY id", self.id)

    def calculate_save_count(self):
        """
        Count of all saves for the images.  If the file is the original for other
        sharedfiles, then the save count is the total of all files where it's the
        original.  If the file is not an original, only count direct saves, ala
        parent_id.
        """
        original =  self.where_count("original_id = %s and deleted = 0", self.id)
        if original > 0:
            return original
        else:
            return self.where_count("parent_id = %s and deleted = 0", self.id)

    def calculate_like_count(self):
        """
        Count of all favorites, excluding deleted favorites.
        """
        return favorite.Favorite.where_count("sharedfile_id = %s and deleted = 0", self.id)

    def comment_count(self):
        """
        Counts all comments, excluding deleted favorites.
        """
        return comment.Comment.where_count("sharedfile_id = %s and deleted = 0", self.id)

    def comments(self):
        """
        Select comments for a sharedfile.
        """
        return comment.Comment.where('sharedfile_id=%s and deleted = 0', self.id)

    def feed_date(self):
        """
        Returns a date formatted to be included in feeds
        e.g., Tue, 12 Apr 2005 13:59:56 EST
        """
        return rfc822_date(self.created_at)

    def thumbnail_url(self, direct=False):
        # If we are running on Fastly, then we can use the Image Optimizer to
        # resize a given image. Thumbnail size is 100x100. This size is used
        # for the conversations page.
        sourcefile = self.sourcefile()
        size = 0
        if sourcefile.type == 'image':
            if self.original_id > 0:
                original = self.original()
                if original:
                    size = original.size
            else:
                size = self.size
        # Fastly I/O won't process images > 50mb, so condition for that
        if sourcefile.type == 'image' and options.use_fastly and size > 0 and size < 50_000_000:
            if direct:
                return f"https://{options.cdn_host}/s3/originals/{sourcefile.file_key}?width=100"
            else:
                return f"https://{options.cdn_host}/r/{self.share_key}?width=100"
        else:
            return s3_url(options.aws_key, options.aws_secret, options.aws_bucket, \
                file_path="thumbnails/%s" % (sourcefile.thumb_key), seconds=3600)

    def small_thumbnail_url(self, direct=False):
        # If we are running on Fastly, then we can use the Image Optimizer to
        # resize a given image. Small thumbnails are 270-wide at most. This size is
        # currently only used within the admin UI.
        sourcefile = self.sourcefile()
        size = 0
        if sourcefile.type == 'image':
            if self.original_id > 0:
                original = self.original()
                if original: size = original.size
            else:
                size = self.size
        # Fastly I/O won't process images > 50mb, so condition for that
        if sourcefile.type == 'image' and options.use_fastly and size > 0 and size < 50_000_000:
            if direct:
                return f"https://{options.cdn_host}/s3/originals/{sourcefile.file_key}?width=270"
            else:
                return f"https://{options.cdn_host}/r/{self.share_key}?width=270"
        else:
            return s3_url(options.aws_key, options.aws_secret, options.aws_bucket, \
                file_path="smalls/%s" % (sourcefile.small_key), seconds=3600)

    def type(self):
        source = sourcefile.Sourcefile.get("id = %s", self.source_id)
        return source.type

    def set_nsfw(self, set_by_user):
        """
        Process a request to set the nsfw flag on the sourcefile.  Also logs the
        the user, sharedfile and sourcefile in the NSFWLog table.
        """
        sourcefile = self.sourcefile()
        log_entry = models.nsfw_log.NSFWLog(user_id=set_by_user.id, sharedfile_id=self.id,
                                            sourcefile_id=sourcefile.id)
        log_entry.save()
        if sourcefile.nsfw == 0:
            sourcefile.update_attribute('nsfw', 1)

    def find_tags(self):
        if not self.description:
            return []
        candidates = set(part[1:] for part in self.description.split() if part.startswith('#'))
        candidates = [re.search(r'[a-zA-Z0-9]+', c).group(0) for c in candidates]
        return set([c.lower() for c in candidates if len(c) < 21])

    def tags(self):
        #return models.TaggedFile.where("sharedfile_id = %s and deleted = 0", self.id)
        return [models.Tag.get('id = %s', tf.tag_id) for tf in models.TaggedFile.where("sharedfile_id = %s and deleted = 0", self.id)]

    @classmethod
    def from_subscriptions(self, user_id, per_page=10, before_id=None, after_id=None, q=None):
        """
        Pulls the user's timeline, can key off and go backwards (before_id) and forwards (after_id)
        in time to pull the per_page amount of posts.  Always returns the files in reverse
        chronological order.

        We split out the join from the query and only pull the sharedfile_id because MySQL's
        query optimizer does not use the index consistently. -- IK
        """
        constraint_sql = ""
        order = "desc"
        if before_id:
            constraint_sql = "AND post.sharedfile_id < %s" % (int(before_id))
        elif after_id:
            order = "asc"
            constraint_sql = "AND post.sharedfile_id > %s" % (int(after_id))

        select_args = []
        if q is not None:
            constraint_sql += " AND MATCH (sharedfile.title, sharedfile.description, sharedfile.alt_text) AGAINST (%s IN BOOLEAN MODE)"
            select_args.append(q)

        # We aren't joining on sharedfile using the deleted column since that
        # causes the query to run more slowly, particulary when looking for
        # ranges when paginating. We apply a delete filter for the post records,
        # which should suffice (post records are deleted when an image is deleted).
        select = """SELECT sharedfile_id, shake_id FROM post
                    JOIN sharedfile on sharedfile.id = sharedfile_id
                    WHERE post.user_id = %s
                    AND post.seen = 0
                    AND post.deleted = 0
                    %s
                    ORDER BY post.sharedfile_id %s limit %s, %s""" % (int(user_id), constraint_sql, order, 0, per_page)

        posts = self.query(select, *select_args)
        results = []
        for post in posts:
            sf = Sharedfile.get('id=%s', post['sharedfile_id'])
            sf.shake_id = post['shake_id']
            results.append(sf)
        if order == "asc":
            results.reverse()
        return results


    @classmethod
    def subscription_time_line(self, user_id, page=1, per_page=10):
        """
        DEPRACATED: We no longer paginate like this. instead we use Sharedfile.from_subscription
        """
        limit_start = (page-1) * per_page
        select = """SELECT sharedfile.* FROM sharedfile, post
                  WHERE post.user_id = %s
                  AND post.sharedfile_id = sharedfile.id
                  AND post.seen = 0
                  AND post.deleted = 0
                  AND sharedfile.deleted = 0
                  ORDER BY post.created_at desc limit %s, %s""" % (int(user_id), int(limit_start), per_page)
        return self.object_query(select)


    @classmethod
    def favorites_for_user(self, user_id, before_id=None, after_id=None, per_page=10, q=None):
        """
        A user likes (i.e. Favorite).
        """
        constraint_sql = ""
        order = "desc"

        if before_id:
            constraint_sql = "AND favorite.id < %s" % (int(before_id))
        elif after_id:
            order = "asc"
            constraint_sql = "AND favorite.id > %s" % (int(after_id))

        select_args = []
        if q is not None:
            constraint_sql += " AND MATCH (sharedfile.title, sharedfile.description, sharedfile.alt_text) AGAINST (%s IN BOOLEAN MODE)"
            select_args.append(q)

        # The `GROUP BY source_id`` constrains the result so it is only returning a single row
        # per source_id. MySQL server cannot have ONLY_FULL_GROUP_BY present in sql_mode
        # to allow this query.
        select = """SELECT sharedfile.*, favorite.id as favorite_id
        	FROM favorite
	        JOIN sharedfile on sharedfile.id = favorite.sharedfile_id and sharedfile.deleted = 0
            WHERE favorite.user_id = %s and favorite.deleted = 0
            %s
            GROUP BY sharedfile.source_id
            ORDER BY favorite.id %s limit 0, %s"""  % (int(user_id), constraint_sql, order, per_page)
        files = self.object_query(select, *select_args)
        if order == "asc":
            files.reverse()
        return files


    @classmethod
    def get_by_share_key(self, share_key):
        """
        Returns a Sharedfile by its share_key. Deleted files don't get returned.
        """
        sharedfile_id = base36decode(share_key)
        return self.get("id = %s and deleted = 0", sharedfile_id)

    @classmethod
    def incoming(self, before_id=None, after_id=None, per_page=10):
        """
        Fetches the per_page amount of incoming files.  Filters out any files where
        the user is marked as nsfw.
        """
        constraint_sql = ""
        order = "desc"

        if before_id:
            constraint_sql = "AND sharedfile.id < %s" % (int(before_id))
        elif after_id:
            order = "asc"
            constraint_sql = "AND sharedfile.id > %s" % (int(after_id))

        select = """SELECT sharedfile.* FROM sharedfile, user
                    WHERE sharedfile.deleted = 0
                    AND sharedfile.parent_id = 0
                    AND sharedfile.original_id = 0
                    AND sharedfile.user_id = user.id
                    AND user.nsfw = 0
                    %s
                    ORDER BY id %s LIMIT %s""" % (constraint_sql, order, per_page)
        files = self.object_query(select)
        if order == "asc":
            files.reverse()
        return files


    @staticmethod
    def get_sha1_file_key(file_path):
        try:
            fh = open(file_path, 'r')
            file_data = fh.read()
            fh.close()
            h = hashlib.sha1()
            h.update(file_data)
            return h.hexdigest()
        except Exception as e:
            return None

    @staticmethod
    def create_from_file(file_path, file_name, sha1_value, content_type, user_id, title=None, shake_id=None, skip_s3=None):
        """
        TODO: Must only accept acceptable content-types after consulting a list.
        """
        if len(sha1_value) != 40:
            return None

        if user_id == None:
            return None

        if content_type not in ['image/gif', 'image/jpeg', 'image/jpg', 'image/png']:
            return None

        # If we have no shake_id, drop in user's main shake. Otherwise, validate that the specififed
        # shake is a group shake that the user has permissions for.
        if not shake_id:
            destination_shake = shake.Shake.get('user_id = %s and type=%s and deleted=0', user_id, 'user')
        else:
            destination_shake = shake.Shake.get('id=%s and deleted=0', shake_id)
            if not destination_shake:
                return None
            if not destination_shake.can_update(user_id):
                return None

        sf = sourcefile.Sourcefile.get_from_file(file_path, sha1_value, skip_s3=skip_s3, content_type=content_type)

        if sf:
            shared_file = Sharedfile(user_id = user_id, name=file_name, content_type=content_type, source_id=sf.id, title=title, size=path.getsize(file_path))
            shared_file.save()
            if shared_file.saved():
                shared_file.share_key = base36encode(shared_file.id)
                shared_file.save()
                shared_file.add_to_shake(destination_shake)

                if options.use_workers and content_type == "image/gif":
                    transcode_sharedfile.delay_or_run(shared_file.id)
                return shared_file
            else:
                return None
        else:
            return None
