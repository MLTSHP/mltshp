from lib.flyingcow import Model, Property
from datetime import datetime
from lib.utilities import pretty_date
from . import user, notification
from tornado.options import options


class CommentLike(Model):
    user_id = Property()
    comment_id = Property()
    deleted = Property(default=0)
    created_at = Property()
    updated_at = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(CommentLike, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def on_create(self):
        u = user.User.get('id = %s', self.user_id)
        n = notification.Notification.new_comment_like(self,u)
        n.save()

