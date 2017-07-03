from datetime import datetime

from lib.flyingcow import Model, Property
from lib.flyingcow.db import IntegrityError
from lib.utilities import pretty_date, base36encode
from tornado.options import options


class Bookmark(Model):
    user_id = Property()
    created_at   = Property()
    sharedfile_id = Property()
    previous_sharedfile_id = Property()

    def __str__(self):
        return "Bookmark - id: %s, user_id: %s, created_at: %s" % (self.id, self.user_id, self.created_at)

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Bookmark, self).save(*args, **kwargs)

    def on_create(self):
        existing_previous_bookmark = Bookmark.where('user_id=%s and id < %s ORDER BY id desc LIMIT 1', self.user_id, self.id)
        if existing_previous_bookmark and existing_previous_bookmark[0].sharedfile_id > 0:
            self.previous_sharedfile_id = existing_previous_bookmark[0].sharedfile_id
            self.save()

    def _set_dates(self):
        """
        Sets the created_at field unless it's already set.
        """
        if self.id is None and self.created_at is None:
            self.created_at = datetime.utcnow()

    def pretty_created_at(self):
        """
        A friendly version of the created_at date.
        """
        return pretty_date(self.created_at)

    def feed_date(self):
        """
        Returns a date formatted to be included in feeds
        e.g., Tue, 12 Apr 2005 13:59:56 EST
        """
        return self.created_at.strftime("%a, %d %b %Y %H:%M:%S %Z")

    def sharedfile_key(self):
        return base36encode(self.sharedfile_id)

    def previous_sharedfile_key(self):
        return base36encode(self.previous_sharedfile_id)

    @classmethod
    def start_reading(self, user, sharedfile):
        """
        Check if there is a bookmark newer than the sharedfile passed in, if not
        create a new one with current timestamp. Returns the newest bookmark.

        If no sharedfile passed in, no bookmark gets created.
        """
        if not sharedfile:
            return None
        sharedfile_created_at = sharedfile.created_at.strftime("%Y-%m-%d %H:%M:%S")
        bookmark = Bookmark.get("user_id = %s and created_at >= %s limit 1", user.id, sharedfile_created_at)
        if not bookmark:
            try:
                bookmark = Bookmark(user_id=user.id, sharedfile_id=sharedfile.id, created_at=datetime.utcnow())
                bookmark.save()
            except IntegrityError:
                pass
        return bookmark

    @classmethod
    def for_user_between_sharedfiles(self, user, sharedfiles):
        """
        Return list of bookmarks for a user between a list of ordered sharedfiles.

        Method accepts a list of sharedfiles, ordered newer to older.
        We want a list of bookmarks that is in between or equal to the date range passed in.

        We need at least two sharedfiles.  Bookmarks can't intersect with what start_reading
        would return.
        """
        if len(sharedfiles) < 2:
            return []

        newest_date = sharedfiles[0].created_at.strftime("%Y-%m-%d %H:%M:%S")
        oldest_date = sharedfiles[-1].created_at.strftime("%Y-%m-%d %H:%M:%S")
        return self.where("user_id = %s and created_at < %s and created_at >= %s order by created_at",
            user.id, newest_date, oldest_date)

    @classmethod
    def merge_with_sharedfiles(self, bookmarks, sharedfiles):
        """
        Sorts a list of bookmarks with a list of sharedfiles based on created_at.
        Bookmark will come before sharedfile if date is the same..
        """
        def compare_created_at(x, y):
            if x.created_at > y.created_at:
                return -1
            elif x.created_at < y.created_at:
                return 1
            else:
                x_name = x.__class__.__name__
                y_name = y.__class__.__name__
                if x_name == 'Bookmark' and y_name == 'Sharedfile':
                    return -1
                return 0

        composite_list = sharedfiles + bookmarks
        composite_list.sort(compare_created_at)
        return composite_list
