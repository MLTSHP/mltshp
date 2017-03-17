from datetime import datetime

from lib.flyingcow import Model, Property
from tornado.options import options


class ShakeCategory(Model):
    name = Property(default='')
    short_name = Property(default='')
    created_at = Property()
    updated_at = Property()
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(ShakeCategory, self).save(*args, **kwargs)
    
    def _set_dates(self):
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
