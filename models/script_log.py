from lib.flyingcow import Model, Property
from lib.utilities import utcnow
from tornado.options import options

class ScriptLog(Model):
    name = Property(default='')
    result = Property(default='')
    success = Property(default=0)
    started_at = Property()
    finished_at = Property()
    
    def start_running(self):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self.started_at = utcnow()
    
    def save(self, *args, **kwargs):
        self._set_dates()
        return super(ScriptLog, self).save(*args, **kwargs)
    
    def _set_dates(self):
        if self.id is None or self.created_at is None:
            self.finished_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    @classmethod
    def last_successful(cls, name):
        return cls.get("name = %s and success = 1 order by id desc limit 1", name)
