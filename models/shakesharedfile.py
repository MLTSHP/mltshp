from lib.flyingcow import Model, Property
from lib.utilities import utcnow
from tornado.options import options


class Shakesharedfile(Model):
    shake_id = Property()
    sharedfile_id = Property()
    deleted = Property(default=0)
    created_at  = Property()
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Shakesharedfile, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def delete(self):
        self.deleted =1
        self.save()
