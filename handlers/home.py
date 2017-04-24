import hashlib

from base import BaseHandler
import models
import lib.utilities

class HomeHandler(BaseHandler):
    """
    Shows the home page if not logged in, otherwise the user's stream.
    path: /
          /before/{share_key}
          /after/{share_key}
    """
    def get(self, before_or_after=None, base36_id=None, returning=None):
        current_user_obj = self.get_current_user_object()
        if not current_user_obj:
            return self.render("home/not-logged-in.html", share_key=None)
        if not current_user_obj.is_paid:
            return self.redirect("/account/membership")

        older_link, newer_link = None, None
        sharedfile_id = None
        if base36_id:
            sharedfile_id = lib.utilities.base36decode(base36_id)

        before_id, after_id = None, None
        if sharedfile_id and before_or_after == 'before':
            before_id = sharedfile_id
        elif sharedfile_id and before_or_after == 'after':
            after_id = sharedfile_id
        
        front_page, notifications_count = False, 0
        notifications = []

        # We're going to older, so ony use before_id.
        if before_id:
            notifications_count = models.Notification.for_user_count(current_user_obj)
            sharedfiles = current_user_obj.sharedfiles_from_subscriptions(before_id=before_id,per_page=11)
            # we have nothing on this page, redirect to home page with out params.
            if len(sharedfiles) == 0:
                return self.redirect('/')

            if len(sharedfiles) > 10:
                older_link = "/before/%s" % sharedfiles[9].share_key
                newer_link = "/after/%s" % sharedfiles[0].share_key
            else:
                newer_link = "/after/%s" % sharedfiles[0].share_key

            bookmarks = models.Bookmark.for_user_between_sharedfiles(current_user_obj, sharedfiles[0:11])
            sharedfiles = models.Bookmark.merge_with_sharedfiles(bookmarks, sharedfiles[0:10])

        # We're going to newer
        elif after_id:
            notifications_count = models.Notification.for_user_count(current_user_obj)
            sharedfiles = current_user_obj.sharedfiles_from_subscriptions(after_id=after_id, per_page=11)
            if len(sharedfiles) <= 10:
                return self.redirect('/')
            else:
                sharedfiles.pop(0)
                older_link = "/before/%s" % sharedfiles[9].share_key
                newer_link = "/after/%s" % sharedfiles[0].share_key

            bookmarks = models.Bookmark.for_user_between_sharedfiles(current_user_obj, sharedfiles[0:11])
            sharedfiles = models.Bookmark.merge_with_sharedfiles(bookmarks, sharedfiles[0:10])
        
        # default / page, only has older link.  Also, where bookmark gets set.
        else:
            front_page = True
            notifications = models.Notification.display_for_user(current_user_obj)
            sharedfiles = current_user_obj.sharedfiles_from_subscriptions(per_page=11)
            # Start Reading.
            first_bookmark = None
            if len(sharedfiles) > 0:
                # Don't set bookmark if it's just Safari making the request to
                # populate it's Top Sites thumbnail, or if it's Mozilla prefetching.
                if ('X-Purpose' in self.request.headers and self.request.headers['X-Purpose'] == 'preview') or \
                    ('X-Moz' in self.request.headers and self.request.headers['X-Moz'] == 'prefetch'):
                    pass
                else:
                    first_bookmark = models.Bookmark.start_reading(current_user_obj, sharedfiles[0])

            if len(sharedfiles) > 10:
                older_link = "/before/%s" % sharedfiles[9].share_key

            bookmarks = models.Bookmark.for_user_between_sharedfiles(current_user_obj, sharedfiles[0:11])
            sharedfiles = models.Bookmark.merge_with_sharedfiles(bookmarks, sharedfiles[0:10])

            if first_bookmark:
                sharedfiles.insert(0, first_bookmark)
        
        show_notice_where_you_were = False
        if returning:
            show_notice_where_you_were = True
        externalservice = models.Externalservice.by_user(current_user_obj, models.Externalservice.TWITTER)
                
        return self.render("home/index.html", current_user_obj=current_user_obj,
            notifications=notifications, sharedfiles=sharedfiles,
            externalservice=externalservice, older_link=older_link,
            newer_link=newer_link, front_page=front_page,
            notifications_count=notifications_count,
            show_notice_where_you_were=show_notice_where_you_were)
