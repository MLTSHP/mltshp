from lib.flyingcow import Model, Property
from tornado.options import options


class Fileview(Model):
    user_id = Property()
    sharedfile_id = Property()
    created_at  = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        return super(Fileview, self).save(*args, **kwargs)

    @classmethod
    def last(cls):
        return cls.get("1 order by id desc limit 1")
    
    @classmethod
    def sharedfile_ids(cls, after_id=None):
        """
        Return sharedfile_ids that have had views logged to them.
        
        Limit results to fileview's > passed in after_id.
        """
        sql = "select sharedfile_id from fileview "
        if after_id:
            sql = sql + " where id > %s" % int(after_id)
        sql += " group by sharedfile_id"
        return [result['sharedfile_id'] for result in cls.query(sql)]


