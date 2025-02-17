#!/usr/bin/env python3

from torndb import Connection
from tornado.options import options


def main():
    db1 = Connection(options.database_host, options.database_user, options.database_password)
    db1.execute("UPDATE shakesharedfile SET deleted = 1 WHERE deleted = 0 AND sharedfile_id IN (SELECT id FROM sharedfile WHERE deleted = 1)")
