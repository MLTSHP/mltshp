from lib.flyingcow import Model, Property
from datetime import datetime
from tornado.options import options


class NSFWLog(Model):
    user_id = Property()
    sharedfile_id = Property()
    sourcefile_id = Property()
    created_at = Property()
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(NSFWLog, self).save(*args, **kwargs)

    def _set_dates(self):
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow()
    