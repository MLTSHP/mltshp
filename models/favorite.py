from lib.flyingcow import Model, Property
from datetime import datetime
from lib.utilities import pretty_date
from . import user
from tornado.options import options


class Favorite(Model):
    user_id = Property()
    sharedfile_id = Property()
    deleted = Property(default=0)
    created_at = Property()
    updated_at = Property()
    
    def user(self):
        return user.User.get('id = %s', self.user_id)
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Favorite, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def pretty_created_at(self):
        """
        A friendly version of the created_at date.
        """
        return pretty_date(self.created_at)
