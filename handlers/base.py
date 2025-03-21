import time
from functools import wraps
import re

import tornado.web
from tornado.options import define, options

from lib.flyingcow.cache import RequestHandlerQueryCache
import models

SESSION_COOKIE = "sid"


def require_membership(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        user = self.get_current_user_object()
        if user and not user.is_paid:
            return self.redirect("/account/membership?join=1")
        return f(self, *args, **kwargs)
    return wrapper


class _Errors(dict):
    """
    A light wrapper for a dict, so we can test for existance of field errors in templates
    without getting AttributeErrors. We access keys as attributes.
    """
    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            return None


class BaseHandler(RequestHandlerQueryCache, tornado.web.RequestHandler):
    def initialize(self):
        self._errors = _Errors()
        self.approved_content_types =  ['image/gif', 'image/jpeg', 'image/jpg', 'image/png']
        self.db = self.application.db
        self.start_time = time.time()

        super(BaseHandler, self).initialize()

    def finish(self, chunk=None):
        proc_time = round((time.time() - self.start_time) * 1000, 2)
        self.set_header('x-proc-time',"%s" % (proc_time))
        super(BaseHandler, self).finish(chunk)

    def static_url(self, *args, **kwargs):
        base_url = ""
        if options.use_cdn:
            base_url = "https://%s" % options.cdn_host
        return base_url + super(BaseHandler, self).static_url(*args, **kwargs)

    def get_current_user(self):
        sid = self.get_secure_cookie(SESSION_COOKIE)
        if sid:
            return tornado.escape.json_decode(sid)
        else:
            return None

    def get_current_user_object(self):
        """
        Return current user as an object rather than light hash we store
        in cookie.
        """
        current_user = self.get_current_user()
        if not current_user:
            return None
        return models.User.get("id = %s", current_user['id'])

    def render_string(self, template_name, **kwargs):
        current_user_object = self.get_current_user_object()
        kwargs['errors'] = self._errors
        kwargs['settings'] = self.settings
        kwargs['host_banner'] = options.host_banner
        kwargs['app_host'] = options.app_host or self.request.host
        kwargs['app_scheme'] = (options.use_cdn and options.cdn_host and "https") or "http"
        kwargs['cdn_host'] = options.cdn_host
        kwargs['current_user_object'] = current_user_object
        kwargs['site_is_readonly'] = options.readonly == 1
        kwargs['disable_signups'] = options.disable_signups == 1
        kwargs['xsrf_token'] = self.xsrf_token
        # site merchandise promotions are shown to members
        kwargs['show_promos'] = options.show_promos and (
            current_user_object and current_user_object.is_paid == 1)

        return super(BaseHandler, self).render_string(template_name, **kwargs)

    def render(self, template_name, **kwargs):
        template_name = "%s/%s" % (self.settings['template_path'], template_name)
        return super(BaseHandler, self).render(template_name, **kwargs)

    def add_error(self, key, message):
        self._errors[key] = message

    def add_errors(self, errors_dict):
        for error_key in list(errors_dict.keys()):
            self.add_error(error_key, errors_dict[error_key])

    def log_user_in(self, user):
        """
        Accepts a User model, sets secure cookie w / user details.
        """
        sid = {'id':user.id, 'name':user.name}
        # 2^31-1 = 2147483647, the maximum time for an cookie expiration in 32bit;
        # Tue, 19 Jan 2038 03:14:07 GMT
        self.set_secure_cookie(
            SESSION_COOKIE, tornado.escape.json_encode(sid),
            expires=2147483647, domain=re.sub(":\\d+", "", options.app_host))

    def log_out(self):
        """
        Clears out any session keys.
         sid stores a dict representing user.
        """
        self.clear_cookie(SESSION_COOKIE, domain=re.sub(":\\d+", "", options.app_host))

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            if self.__class__.__name__ == 'ShowRawHandler':
                page_type = 'image'
            elif self.__class__.__name__ == 'ShakeHandler':
                page_type = 'shake'
            else:
                page_type = 'page'
            return self.finish(self.render_string("404.html", page_type=page_type))
        if status_code == 403:
            return self.finish(self.render_string("403.html"))
        return self.finish(self.render_string("500.html"))
