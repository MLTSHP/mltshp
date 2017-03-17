from lib.flyingcow import Model, Property
from tornado.options import options

import models


class Magicfile(Model):
    sharedfile_id = Property()
    created_at = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        super(Magicfile, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def sharedfile(self):
        """
        Returns the associated sharedfile object.
        """
        if not bool(self.sharedfile_id):
            return None
        return models.Sharedfile.get("id = %s", self.sharedfile_id)

    @classmethod
    def sharedfiles_paginated(self, before_id=None, after_id=None, per_page=10):
        """
        Returns a list of "Magicfile" Sharedfiles, with the "magicfile_id"
        property set for each object.
        """
        constraint_sql = ""
        order = "desc"

        if before_id:
            constraint_sql = "AND magicfile.id < %s" % (int(before_id))
        elif after_id:
            order = "asc"
            constraint_sql = "AND magicfile.id > %s" % (int(after_id))

        select = """SELECT sharedfile.*, magicfile.id AS magicfile_id FROM magicfile
                    LEFT JOIN sharedfile
                    ON magicfile.sharedfile_id = sharedfile.id
                    WHERE sharedfile.deleted = 0
                    %s
                    ORDER BY magicfile.id %s LIMIT 0, %s""" % (constraint_sql, order, per_page)
        files = models.Sharedfile.object_query(select)
        if order == "asc":
            files.reverse()
        return files;