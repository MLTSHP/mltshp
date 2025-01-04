import lib.flyingcow
from tornado.options import options
from lib.utilities import utcnow


class ExternalRelationship(lib.flyingcow.Model):
    user_id = lib.flyingcow.Property()
    service_id = lib.flyingcow.Property()
    service_type = lib.flyingcow.Property(default=1)
    created_at   = lib.flyingcow.Property()
    updated_at   = lib.flyingcow.Property()
    
    # constants.
    TWITTER = 1
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(ExternalRelationship, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
    @classmethod
    def add_relationship(self, user, service_id, service_type=TWITTER):
        """
        Take a mltshp User an external service_id and service_type. And create a
        new ExternalRelationship record.
        """
        try:
            relationship = ExternalRelationship(user_id=user.id, service_id=service_id, service_type=service_type)
            relationship.save()
        except lib.flyingcow.db.IntegrityError:
            pass
        
