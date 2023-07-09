from datetime import datetime

from lib.flyingcow import Model, Property
from tornado.options import options

from . import shake
from . import user
from . import post


class Subscription(Model):
    user_id     = Property()
    shake_id    = Property()
    deleted     = Property(default=0)
    created_at  = Property()
    updated_at  = Property()


    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Subscription, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def on_create(self):
        sub_shake = shake.Shake.get('id=%s and deleted=0', self.shake_id)
        sub_user = user.User.get('id = %s and deleted=0', self.user_id)
        shake_owner = user.User.get('id = %s and deleted=0', sub_shake.user_id)

        shared_files = sub_shake.sharedfiles()
        for sf in shared_files:
            existing_post = post.Post.where('user_id = %s and sourcefile_id = %s', sub_user.id, sf.source_id)
            seen = 0
            if existing_post:
                seen = 1
            new_post = post.Post(user_id=sub_user.id, sharedfile_id=sf.id, sourcefile_id=sf.source_id, seen=seen, shake_id=sub_shake.id)
            new_post.save()
            new_post.created_at = sf.created_at
            new_post.save()

    def shake(self):
        return shake.Shake.get("id = %s", self.shake_id)