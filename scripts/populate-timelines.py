#!/usr/bin/env python3

from torndb import Connection
from tornado.options import options
from tasks.timeline import add_posts


def main():
    db1 = Connection(options.database_host, options.database_user, options.database_password)

    db1.execute("DELETE FROM post WHERE 1")
    ssfs = db1.query("""SELECT shake_id, sharedfile_id from shakesharedfile order by created_at""")
    for shakesharedfile in ssfs:
        sf = db1.get("""SELECT id, source_id, name, deleted, created_at FROM sharedfile WHERE id = %s""", shakesharedfile['sharedfile_id'])
        print("%s. Adding posts for sharedfile: %s created at %s." % (sf.id, sf.name, sf.created_at))
        add_posts(shake_id=shakesharedfile['shake_id'], sharedfile_id=sf['id'], sourcefile_id=sf['source_id'], deleted=sf['deleted'], created_at=sf['created_at'])
