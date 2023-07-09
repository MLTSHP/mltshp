#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import sys

import asyncio
import tornado.web
import tornado.options
from tornado.options import options
from tornado.httpclient import AsyncHTTPClient

from lib.flyingcow import register_connection
import lib.flyingcow.cache
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
                                      password=options.database_password,
                                      charset="utf8mb4")
        if options.use_query_cache:
            lib.flyingcow.cache.use_query_cache = True
        if options.stripe_secret_key:
            stripe.api_key = options.stripe_secret_key

        super(MltshpApplication, self).__init__(*args, **settings)


async def main():
    mltshpoptions.parse_dictionary(settings)
    tornado.options.parse_command_line()

    app_settings = MltshpApplication.app_settings()

    if options.dump_settings:
        from pprint import pprint
        pprint({'options': dict((k, opt.value())
                                for k, opt in options.items()),
                'app_settings': app_settings})
        sys.exit(0)

    application = MltshpApplication(routes, autoescape=None, **app_settings)
    print("starting on port %s" % (options.on_port))
    application.listen(int(options.on_port))
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
