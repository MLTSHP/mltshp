#!/usr/bin/env python
#import figleaf
#figleaf.start()
import unittest
from torndb import Connection
from tornado.options import options
from tornado.httpclient import AsyncHTTPClient

import MySQLdb

import mltshpoptions
from settings import test_settings

AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

TEST_MODULES = [
    'test.AccountTests',
    'test.CommentTests',
    'test.ExternalAccountTests',
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

    import tornado.testing
    db = Connection(options.database_host, 'mysql', options.database_user, options.database_password)
    try:
        db.execute("CREATE database %s" % options.database_name)
    except MySQLdb.ProgrammingError, exc:
        if exc.args[0] != 1007:  # database already exists
            raise
    else:
        with open("setup/db-install.sql") as f:
            load_query = f.read()
        db.execute("USE %s" % options.database_name)
        db.execute(load_query)
    tornado.testing.main()

#figleaf.stop()
#figleaf.write_coverage('.figleaf')
