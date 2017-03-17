from lib.flyingcow import Model, Property
from lib.flyingcow.cache import ModelQueryCache
from tornado.options import options

from models import Shake


class Promotion(ModelQueryCache, Model):
    # Name of promotion
    name = Property()

    # Shake this promotion relates to
    # (used for a profile pic and link to
    # the promotion shake)
    promotion_shake_id = Property()

    # Number of Pro membership months this
    # promotion is good for
    membership_months = Property()
 
    # a link to a web page about this promotion
    promotion_url = Property()

    # date that the promotion expires on
    expires_at = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        return super(Promotion, self).save(*args, **kwargs)

    def shake(self):
        return Shake.get('id=%s', self.promotion_shake_id)

    @classmethod
    def active(cls):
        return cls.where("expires_at > now() order by rand()")
