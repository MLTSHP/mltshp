import tornado.web
from tornado.escape import json_encode
from tornado import escape

from base import BaseHandler, require_membership
from models import Tag, TaggedFile
from lib.utilities import base36decode


class TagHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self, tag_name=None, before_or_after=None, base36_id=None):
        tag = Tag.get("name=%s", tag_name.lower())
        older_link, newer_link = None, None
        sharedfile_id = None
        shared_files = []

        if not tag:
            raise tornado.web.HTTPError(404)

        if base36_id:
            sharedfile_id = base36decode(base36_id)

        max_id, since_id = None, None
        if sharedfile_id and before_or_after == 'before':
            max_id = sharedfile_id
        elif sharedfile_id and before_or_after == 'after':
            since_id = sharedfile_id

        current_user = self.get_current_user_object()

        # We're going to older, so ony use max_id.
        if max_id:
            shared_files = tag.sharedfiles_paginated(max_id=max_id, per_page=11)
 
            # we have nothing on this page, redirect to home page with out params.
            if len(shared_files) == 0:
                return self.redirect("/tag" + tag.path())

            if len(shared_files) > 10:
                older_link = "/tag%s/before/%s" % (tag.path(), shared_files[9].share_key)
                newer_link = "/tag%s/after/%s" % (tag.path(), shared_files[0].share_key)
            else:
                newer_link = "/tag%s/after/%s" % (tag.path(), shared_files[0].share_key)

        # We're going to newer
        elif since_id:
            shared_files = tag.sharedfiles_paginated(since_id=since_id, per_page=11)
            if len(shared_files) <= 10:
                return self.redirect("/tag" + tag.path())
            else:
                shared_files.pop(0)
                older_link = "/tag%s/before/%s" % (tag.path(), shared_files[9].share_key)
                newer_link = "/tag%s/after/%s" % (tag.path(), shared_files[0].share_key)
        else:
            # clean home page, only has older link
            shared_files = tag.sharedfiles_paginated(per_page=11)
            if len(shared_files) > 10:
                older_link = "/tag%s/before/%s" % (tag.path(), shared_files[9].share_key)

        return self.render("tags/tag.html", tag=tag, shared_files=shared_files[0:10],
            current_user_obj=current_user, older_link=older_link,newer_link=newer_link)