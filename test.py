#!/usr/bin/env python

import unittest
import logging

from torndb import Connection
from tornado.options import options
from tornado.httpclient import AsyncHTTPClient
from tornado.options import options

import MySQLdb

import mltshpoptions
from settings import test_settings

# If test.AccountTests fails to import, it should fail loudly...
import test.AccountTests


AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

TEST_MODULES = [
    'test.AccountTests',
    'test.CommentTests',
    # 'test.ExternalAccountTests',
    'test.FileTests',
    'test.SimpleTests',
    'test.SiteFunctionTests',

    'test.unit.app_tests',
    'test.unit.comment_tests',
    'test.unit.externalservice_tests',
    'test.unit.notification_tests',
    'test.unit.shake_tests',
    'test.unit.sharedfile_tests',
    'test.unit.sourcefile_tests',
    'test.unit.task_tests',
    'test.unit.user_tests',
    'test.unit.conversation_tests',
    'test.unit.external_relationship_tests',
    'test.unit.bookmark_tests',
    'test.unit.fileview_tests',
    'test.unit.script_log_tests',

    'test.functional.account_tests',
    'test.functional.account_settings_tests',
    'test.functional.admin_user_tests',
    'test.functional.conversations_tests',
    'test.functional.error_tests',
    'test.functional.image_like_tests',
    'test.functional.image_nsfw_tests',
    'test.functional.image_comment_tests',
    'test.functional.invite_member_tests',
    'test.functional.misc_tests',
    'test.functional.payments_tests',
    'test.functional.request_invitation_tests',
    'test.functional.shake_crud_tests',
    'test.functional.tools_find_people_tests',
    'test.functional.image_save_tests',
    'test.functional.invite_member_tests',
    'test.functional.home_tests',
    'test.functional.create_account_tests',
    'test.functional.verify_email_tests',
    'test.functional.api_tests',
    'test.functional.voucher_tests',

    'test.scripts.calculate_views_tests',
]

def all():
    return unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)

if __name__ == '__main__':

    mltshpoptions.parse_dictionary(test_settings)
    if not options.tornado_logging:
        options.logging = None
        logging.getLogger("tornado.access").disabled = True
        logging.getLogger("tornado.application").disabled = True
        logging.getLogger("tornado.general").disabled = True

    import tornado.testing
    db = Connection(options.database_host, 'mysql', options.database_user, options.database_password)
    try:
        db.execute("CREATE database %s" % options.database_name)
    except MySQLdb.ProgrammingError as exc:
        if exc.args[0] != 1007:  # database already exists
            raise
    else:
        with open("setup/db-install.sql") as f:
            load_query = f.read()
        db.execute("USE %s" % options.database_name)
        statements = load_query.split(";")
        for statement in statements:
            # Utilize in-memory tables for faster tests.
            # Note there are some differences here with InnoDB, but
            # they shouldn't materially affect our tests.
            cmd = statement.replace("InnoDB", "MEMORY").strip()
            if cmd != "":
                db.execute(cmd)
    tornado.testing.main()
