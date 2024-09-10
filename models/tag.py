from lib.flyingcow import Model, Property
from lib.flyingcow.cache import ModelQueryCache
from datetime import datetime
from . import sharedfile
from tornado.options import options


class Tag(ModelQueryCache, Model):
    name = Property()
    created_at = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Tag, self).save(*args, **kwargs)

    def _set_dates(self):
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def path(self):
        return '/%s' % self.name.lower()

    def sharedfiles_paginated(self, per_page=10, since_id=None, max_id=None):
        """
        Pulls a tags's timeline, can key off and go backwards (max_id) and forwards (since_id)
        in time to pull the per_page amount of posts.
        """
        constraint_sql = ""
        order = "desc"
        if max_id:
            constraint_sql = "AND tagged_file.sharedfile_id < %s" % (int(max_id))
        elif since_id:
            order = "asc"
            constraint_sql = "AND tagged_file.sharedfile_id > %s" % (int(since_id))

        sql = """SELECT sharedfile.* FROM sharedfile, tagged_file
                 WHERE tagged_file.tag_id = %s 
                    AND tagged_file.sharedfile_id = sharedfile.id 
                    AND tagged_file.deleted = 0
                 %s
                 ORDER BY tagged_file.sharedfile_id %s limit %s, %s""" % (int(self.id), constraint_sql, order, 0, int(per_page))
        results = sharedfile.Sharedfile.object_query(sql)

        if order == "asc":
            results.reverse()

        return results