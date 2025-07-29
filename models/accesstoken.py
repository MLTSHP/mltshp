from lib.flyingcow import Model, Property
from tornado.options import options
from datetime import datetime, timedelta
from . import authorizationcode

from hashlib import sha224
from lib.utilities import base36encode, utcnow
import uuid
import time


class Accesstoken(Model):
    user_id      = Property(name='user_id')
    app_id       = Property(name='app_id')
    consumer_key = Property(name='consumer_key')
    consumer_secret = Property(name='consumer_secret')
    deleted = Property(name='deleted', default=0)
    created_at   = Property(name='created_at')
    updated_at   = Property(name='updated_at')
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Accesstoken, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    def delete(self):
        """
        Sets deleted flag to true and saves.
        """
        self.deleted = True
        return self.save()
    
    @staticmethod
    def generate(authorization_id):
        """
        Generate an access token based on an (unexpired) authorization id.
        """
        auth = authorizationcode.Authorizationcode.get('id=%s', authorization_id)
        consumer_key = uuid.uuid3(uuid.NAMESPACE_DNS, base36encode(auth.id) + '-' + base36encode(auth.app_id))
        consumer_secret = sha224(("%s%s" % (str(uuid.uuid1()), time.time())).encode("ascii")).hexdigest()

        if auth.expires_at > utcnow():
            access_token = Accesstoken(user_id=auth.user_id, app_id=auth.app_id, consumer_key=str(consumer_key), consumer_secret=str(consumer_secret))
            access_token.save()
            return access_token
        else:
            return None
