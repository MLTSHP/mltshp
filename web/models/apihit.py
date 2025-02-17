from lib.flyingcow import Model, Property
from lib.flyingcow.db import connection
from lib.utilities import utcnow
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
            self.hour_start = utcnow().strftime("%Y-%m-%d %H:00:00")

    @classmethod
    def hit(cls, accesstoken_id, ts=None):
        if ts is None:
            ts = utcnow()
        hour_start = ts.strftime('%Y-%m-%d %H:00:00')

        sql = """INSERT INTO apihit (accesstoken_id, hits, hour_start) VALUES (%s, 1, %s)
                 ON DUPLICATE KEY UPDATE hits = hits + 1"""
        args = (accesstoken_id, hour_start)
        kwargs = ()

        conn = connection()
        cursor = conn._cursor()
        try:
            conn._execute(cursor, sql, args, kwargs)
            conn._execute(cursor,
                "SELECT hits FROM apihit WHERE accesstoken_id=%s AND hour_start=%s",
                args, kwargs)
            (hits,) = cursor.fetchone()
        finally:
            cursor.close()

        return hits
