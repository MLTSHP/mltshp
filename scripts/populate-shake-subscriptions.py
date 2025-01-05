#!/usr/bin/env python3

from torndb import Connection
from tornado.options import options


def main():
    db1 = Connection(options.database_host, options.database_user, options.database_password)

    #grab all group shakes
    shakes = db1.query("""SELECT id, user_id FROM shake WHERE type=%s""", "group")

    for shake in shakes:
        db1.execute("""INSERT IGNORE INTO subscription (user_id, shake_id, deleted, created_at, updated_at)
                        VALUES (%s, %s, 0, NOW(), NOW())""", shake['user_id'], shake['id'])
        #print """INSERT INTO subscription (user_id, shake_id, deleted, created_at, updated_at)
        #                VALUES (%s, %s, 0, NOW(), NOW())""" % (shake['user_id'], shake['id'])
