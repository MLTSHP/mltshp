import sys
from torndb import Connection
from tornado.options import options

from models import User
from tasks.migration import migrate_for_user

import logging
logging.basicConfig(level=logging.INFO)


def main():
    names = sys.argv[2:]

    options.use_workers = False
    for name in names:
        user = User.get("name=%s and deleted=2", name)
        if user is not None:
            print "Migrating %s..." % name
            migrate_for_user.delay_or_run(user.id)
        else:
            print "Could not find user named: %s" % name
