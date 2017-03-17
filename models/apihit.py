from lib.flyingcow import Model, Property
from lib.flyingcow.db import connection
from datetime import datetime
from tornado.options import options


class Apihit(Model):
    accesstoken_id = Property()
    hits = Property()
    hour_start = Property()

    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        return super(Apihit, self).save(*args, **kwargs)

    def _set_dates(self):
        if self.id is None or self.hour_start is None:
            self.hour_start = datetime.utcnow().strftime("%Y-%m-%d %H:00:00")

    @classmethod
    def hit(cls, accesstoken_id, utcnow=None):
        if utcnow is None:
            utcnow = datetime.utcnow()
        hour_start = utcnow.strftime('%Y-%m-%d %H:00:00')

        sql = """SET @total_hits := 1;
                 INSERT INTO apihit (accesstoken_id, hits, hour_start) VALUES (%s, 1, %s)
                 ON DUPLICATE KEY
                    UPDATE hits = (@total_hits := (hits + 1));
                 SELECT @total_hits AS hits;"""
        args = (accesstoken_id, hour_start)
        kwargs = ()

        conn = connection()
        cursor = conn._cursor()
        try:
            conn._execute(cursor, sql, args, kwargs)
            # The SELECT was in the third statement, so the value is the third result set.
            cursor.nextset()
            cursor.nextset()
            (hits,) = cursor.fetchone()
        finally:
            cursor.close()

        return hits
