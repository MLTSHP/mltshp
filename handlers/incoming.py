from lib.utilities import base36decode

import tornado.web
from base import BaseHandler
from models import User, Sharedfile

class IncomingHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, before_or_after=None, base36_id=None):
        """
        path: /incoming
        """
        older_link, newer_link = None, None
        sharedfile_id = None
        if base36_id:
            sharedfile_id = base36decode(base36_id)

        before_id, after_id = None, None
        if sharedfile_id and before_or_after == 'before':
            before_id = sharedfile_id
        elif sharedfile_id and before_or_after == 'after':
            after_id = sharedfile_id
        
        #is this user's content filter on
        nsfw_mode = self.get_secure_cookie('nsfw')
        if nsfw_mode == '1':
            filtering = False
        else:
            filtering = True

        # We're going to older, so ony use before_id.
        if before_id:
            sharedfiles = Sharedfile.incoming(before_id=before_id,per_page=11, filter=filtering)
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
            sharedfiles = Sharedfile.incoming(after_id=after_id, per_page=11, filter=filtering)
            if len(sharedfiles) <= 10:
                return self.redirect('/incoming')
            else:
                sharedfiles.pop(0)
                older_link = "/incoming/before/%s" % sharedfiles[9].share_key
                newer_link = "/incoming/after/%s" % sharedfiles[0].share_key
        else:
            # clean home page, only has older link
            sharedfiles = Sharedfile.incoming(per_page=11, filter=filtering)
            if len(sharedfiles) > 10:
                older_link = "/incoming/before/%s" % sharedfiles[9].share_key

        current_user_obj = self.get_current_user_object()
        return self.render("incoming/index.html", sharedfiles=sharedfiles[0:10],
            current_user_obj=current_user_obj,
            older_link=older_link, newer_link=newer_link, filtering=filtering)
