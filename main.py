#!/usr/bin/env python
import os.path
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import torndb
from tornado.options import define, options
from tornado.httpclient import AsyncHTTPClient

from lib.flyingcow import register_connection
import lib.flyingcow.cache
import tornadotoad
from routes import routes
import lib.uimodules
import mltshpoptions
from settings import settings
import stripe

AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")


class MltshpApplication(tornado.web.Application):

    @classmethod
    def app_settings(cls):
        dirname = os.path.dirname(os.path.abspath(__file__))
        return {
            "debug": options.debug,
            "cookie_secret": options.cookie_secret,
            "xsrf_cookies": options.xsrf_cookies,
            "twitter_consumer_key": options.twitter_consumer_key,
            "twitter_consumer_secret": options.twitter_consumer_secret,

            # invariant settings
            "login_url": "/sign-in",
            "static_path": os.path.join(dirname, "static"),
            "template_path":  os.path.join(dirname, "templates"),
            "ui_modules": lib.uimodules,
        }

    def __init__(self, *args, **settings):
        self.db = register_connection(host=options.database_host,
                                      name=options.database_name,
                                      user=options.database_user,
                                      password=options.database_password)
        if options.use_query_cache:
            lib.flyingcow.cache.use_query_cache = True
        if options.hoptoad_enabled:
            environment = 'development' if options.debug else 'production'
            tornadotoad.register(api_key=options.hoptoad_api_key,
                                 environment=environment)

        if options.stripe_secret_key:
            stripe.api_key = options.stripe_secret_key

        super(MltshpApplication, self).__init__(*args, **settings)

if __name__ == "__main__":
    mltshpoptions.parse_dictionary(settings)
    tornado.options.parse_command_line()

    if options.dump_settings:
        from pprint import pprint
        pprint({'options': dict((k, opt.value())
                                for k, opt in options.iteritems()),
                'app_settings': app_settings})
        sys.exit(0)

    app_settings = MltshpApplication.app_settings()
    application = MltshpApplication(routes, autoescape=None, **app_settings)
    http_server = tornado.httpserver.HTTPServer(application)

    print "starting on port %s" % (options.on_port)
    http_server.listen(int(options.on_port))
    tornado.ioloop.IOLoop.instance().start()
