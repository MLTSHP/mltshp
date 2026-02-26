from lib.utilities import base36decode

import tornado.web
from .base import BaseHandler, require_membership
from models import User, Sharedfile, notification


class IncomingHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self, before_or_after=None, base36_id=None):
        """
        path: /incoming
        """
        current_user_obj = self.get_current_user_object()
        notifications_count = notification.Notification.for_user_count(current_user_obj)

        older_link, newer_link = None, None
        sharedfile_id = None
        if base36_id:
            sharedfile_id = base36decode(base36_id)

        before_id, after_id = None, None
        if sharedfile_id and before_or_after == 'before':
            before_id = sharedfile_id
        elif sharedfile_id and before_or_after == 'after':
            after_id = sharedfile_id

        # We're going to older, so ony use before_id.
        if before_id:
            sharedfiles = Sharedfile.incoming(before_id=before_id,per_page=11)
            # we have nothing on this page, redirect to base incoming page.
            if len(sharedfiles) == 0:
                return self.redirect('/incoming')

            if len(sharedfiles) > 10:
                older_link = "/incoming/before/%s" % sharedfiles[9].share_key
                newer_link = "/incoming/after/%s" % sharedfiles[0].share_key
            else:
                newer_link = "/incoming/after/%s" % sharedfiles[0].share_key

        # We're going to newer
        elif after_id:
            sharedfiles = Sharedfile.incoming(after_id=after_id, per_page=11)
            if len(sharedfiles) <= 10:
                return self.redirect('/incoming')
            else:
                sharedfiles.pop(0)
                older_link = "/incoming/before/%s" % sharedfiles[9].share_key
                newer_link = "/incoming/after/%s" % sharedfiles[0].share_key
        else:
            # clean home page, only has older link
            sharedfiles = Sharedfile.incoming(per_page=11)
            if len(sharedfiles) > 10:
                older_link = "/incoming/before/%s" % sharedfiles[9].share_key

        # Trim to presentation length
        sharedfiles = sharedfiles[0:10]

        # Annotate each file with page position to facilitate navigation.
        for i, file in enumerate(sharedfiles):
            file.first_on_page = (i == 0)
            file.last_on_page = (i == len(sharedfiles) - 1)

        return self.render("incoming/index.html", sharedfiles=sharedfiles,
            current_user_obj=current_user_obj,
            older_link=older_link, newer_link=newer_link,
            notifications_count=notifications_count)
