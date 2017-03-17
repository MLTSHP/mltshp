from lib.flyingcow import Model, Property
from datetime import datetime
from tornado.options import options

import user


class Externalservice(Model):
    user_id        = Property()
    service_id     = Property()
    screen_name    = Property()
    type           = Property()
    service_key    = Property()
    service_secret = Property()
    deleted        = Property(default=0)
    created_at     = Property()
    updated_at     = Property()

    TWITTER = 1
    FACEBOOK = 2
    
    @staticmethod
    def by_user(user, type):
        """
        Returns an external service for a user and type.
        """
        if not type:
            return None
            
        if not user:
            return None
            
        return Externalservice.get("user_id = %s and type = %s", user.id, type)

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Externalservice, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    def find_mltshp_users(self):
        """
        Find mltshp Users whose external service (twitter, etc.) friends overlap
        with current user. 
        """
        sql = """ select user.* from user
                  left join externalservice
                  on externalservice.user_id = user.id
                  left join external_relationship
                  on external_relationship.service_id = externalservice.service_id
                  where external_relationship.user_id = %s
                  and external_relationship.service_type = %s
                  order by id desc"""
        return user.User.object_query(sql, self.user_id, self.TWITTER)

