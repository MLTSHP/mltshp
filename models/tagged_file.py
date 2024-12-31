from lib.flyingcow import Model, Property
from lib.flyingcow.cache import ModelQueryCache
from lib.utilities import utcnow
from tornado.options import options


class TaggedFile(ModelQueryCache, Model):
    sharedfile_id = Property()
    tag_id = Property()
    deleted = Property()
    created_at = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(TaggedFile, self).save(*args, **kwargs)

    def _set_dates(self):
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
