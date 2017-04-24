import tornado.web
from base import BaseHandler, require_membership


class FriendHandler(BaseHandler):
    """
    DEPRECATED
    
    Only here to prevent 404's from user's on the site when
    the URL change goes live.
    
    path: /friends
    """
    @tornado.web.authenticated
    @require_membership
    def get(self, before_or_after=None, base36_id=None):
        if not before_or_after:
            return self.redirect('/')
        
        if before_or_after == 'before':
            return self.redirect('/before/%s' % base36_id)
        else:
            return self.redirect('/after/%s' % base36_id)
