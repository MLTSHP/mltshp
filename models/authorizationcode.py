from lib.flyingcow import Model, Property
from datetime import timedelta
import random
import time
from lib.utilities import base36encode, base36decode, generate_digest_from_dictionary, utcnow
from tornado.options import options


class Authorizationcode(Model):
    user_id      = Property()
    app_id       = Property()
    code         = Property()
    expires_at   = Property()
    redeemed     = Property(default=0)
    redirect_url = Property(default=0)
    created_at   = Property()
    updated_at   = Property()
    
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Authorizationcode, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def generate(app_id, redirect_url, user_id):
        """
        Generate a code based on the app_id, time, and redirect_url
        Set expires_at to be 30 seconds from now.
        """
        code = generate_digest_from_dictionary([app_id, random.random(), time.mktime(utcnow().timetuple())])
        expires_at = utcnow() + timedelta(seconds=30)
        auth_code = Authorizationcode(user_id=user_id, app_id=app_id, code=code, redirect_url=redirect_url,expires_at=expires_at.strftime("%Y-%m-%d %H:%M:%S"))
        auth_code.save()
        return auth_code
        