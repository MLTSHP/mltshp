import tornado
from . import base

class NotFoundHandler(base.BaseHandler):
    def check_xsrf_cookie(self):
        pass

    def get(self):
        raise tornado.web.HTTPError(404)
    
    def post(self):
        raise tornado.web.HTTPError(404)
