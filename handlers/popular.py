from datetime import datetime
from datetime import timedelta

import tornado.web
from tornado.options import options
from base import BaseHandler, require_membership

from models import sharedfile, notification, user


class IndexHandler(BaseHandler):
    def get(self):
        current_user_obj = self.get_current_user_object()
        now = datetime.utcnow()
        then = now - timedelta(hours=24)
        notifications_count = 0

        if current_user_obj:
            notifications_count = notification.Notification.for_user_count(current_user_obj)
            self.set_header("Cache-Control", "private")
        else:
            self.set_header("Cache-Control", "s-maxage=600, max-age=60")

        last_sf = sharedfile.Sharedfile.get('1 ORDER BY id desc LIMIT 1')
        if last_sf is not None:
            last_sf_id = last_sf.id - 1000
        else:
            last_sf_id = 0
        #sharedfiles = sharedfile.Sharedfile.where("original_id = 0 and created_at > %s ORDER BY like_count desc LIMIT 25", then)

        sharedfiles = sharedfile.Sharedfile.object_query("""SELECT *, (like_count)/(TIMESTAMPDIFF(minute, created_at, utc_timestamp())+3)^1.5 AS adjusted 
                                                            FROM sharedfile 
                                                            WHERE deleted=0 AND original_id = 0 AND like_count > 5 AND id > %s 
                                                            ORDER BY adjusted DESC LIMIT 30""", last_sf_id)

        best_of_user = user.User.get("name=%s", options.best_of_user_name)
        best_of_shake = best_of_user.shake()
        return self.render("popular/index.html", 
            sharedfiles=sharedfiles, 
            notifications_count=notifications_count,
            current_user_obj=current_user_obj,
            best_of_user=best_of_user,
            best_of_shake=best_of_shake)
