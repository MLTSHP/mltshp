from lib.flyingcow import Model, Property
from lib.flyingcow.db import connection
from lib.utilities import pretty_date, utcnow
from tornado.options import options

from .sourcefile import Sourcefile
from .sharedfile import Sharedfile
from .post import Post
from .tagged_file import TaggedFile
from .shakesharedfile import Shakesharedfile
from .magicfile import Magicfile
from .fileview import Fileview
from .favorite import Favorite
from .comment import Comment
from .bookmark import Bookmark
from .conversation import Conversation

from lib.s3 import S3Bucket


class DmcaTakedown(Model):
    share_key = Property()
    source_id = Property()
    admin_user_id = Property()
    comment = Property()
    processed = Property(default=0)
    created_at = Property()
    updated_at = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(DmcaTakedown, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def takedown_image(cls, share_key, admin_user_id, comment=""):
        if not admin_user_id:
            raise Exception('admin_user_id is required')

        sharedfile = Sharedfile.get("share_key=%s", share_key)
        if not sharedfile:
            raise Exception('Sharedfile %s not found' % share_key)

        sourcefile = Sourcefile.get("id=%s", sharedfile.source_id)
        if not sourcefile:
            raise Exception('Sourcefile %s not found' % sharedfile.source_id)
        source_id = sourcefile.id

        conn = connection()
        cursor = conn._cursor()
        cursor.execute("START TRANSACTION;")
        try:

            takedown = cls(
                share_key=share_key,
                source_id=source_id,
                admin_user_id=admin_user_id,
                comment=comment)
            takedown.save()

            s3_keys = []
            if sourcefile.file_key:
                s3_keys.append('originals/' + sourcefile.file_key)
            if sourcefile.thumb_key:
                s3_keys.append('thumbnails/' + sourcefile.thumb_key)
            if sourcefile.small_key:
                s3_keys.append('smalls/' + sourcefile.small_key)
            if sourcefile.mp4_flag:
                s3_keys.append('mp4/' + sourcefile.file_key)
            if sourcefile.webm_flag:
                s3_keys.append('webm/' + sourcefile.file_key)

            # delete from S3
            s3 = S3Bucket()
            for s3_key in s3_keys:
                s3.client.delete_object(Bucket=options.aws_bucket, Key=s3_key)

            sharedfiles = Sharedfile.where('source_id=%s AND deleted=0', source_id)
            sharedfile_ids = [sf.id for sf in sharedfiles]

            posts = Post.where('(sourcefile_id=%s OR sharedfile_id IN %s) AND deleted=0', source_id, sharedfile_ids)
            for post in posts:
                post.deleted = 1
                post.save()

            shakesharedfiles = Shakesharedfile.where('sharedfile_id IN %s AND deleted=0', sharedfile_ids)
            for shakesharedfile in shakesharedfiles:
                shakesharedfile.deleted = 1
                shakesharedfile.save()

            tagged_files = TaggedFile.where('sharedfile_id IN %s AND deleted=0', sharedfile_ids)
            for tagged_file in tagged_files:
                tagged_file.deleted = 1
                tagged_file.save()

            favorites = Favorite.where('sharedfile_id IN %s AND deleted=0', sharedfile_ids)
            for favorite in favorites:
                favorite.deleted = 1
                favorite.save()

            Conversation.execute('DELETE FROM conversation WHERE sharedfile_id IN %s', sharedfile_ids)

            comments = Comment.where('sharedfile_id IN %s AND deleted=0', sharedfile_ids)
            for comment in comments:
                comment.deleted = 1
                comment.save()

            Bookmark.execute('DELETE FROM bookmark WHERE (sharedfile_id IN %s OR previous_sharedfile_id IN %s)', sharedfile_ids, sharedfile_ids)
            Magicfile.execute('DELETE FROM magicfile WHERE sharedfile_id IN %s', sharedfile_ids)
            Fileview.execute('DELETE FROM fileview WHERE sharedfile_id IN %s', sharedfile_ids)

            for sharedfile in sharedfiles:
                sharedfile.deleted = 1
                sharedfile.save()

            Sourcefile.execute('DELETE FROM sourcefile WHERE id=%s', source_id)

            takedown.processed = 1
            takedown.save()
            cursor.execute("COMMIT;")
        except Exception as e:
            cursor.execute('ROLLBACK;')
            raise e
