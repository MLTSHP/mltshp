#!/usr/bin/env python3

from torndb import Connection
from tornado.options import options
from tasks.timeline import add_posts


def main():
    db1 = Connection(options.database_host, options.database_user, options.database_password)

    #grab all shared files in order
    sfs = db1.query("""SELECT id FROM sharedfile ORDER BY created_at""")
    #for each, get counts

    for sf in sfs:
        likes = 0
        saves = 0
    
        like_counts = db1.query("SELECT count(id) as like_count from favorite where sharedfile_id = %s and deleted=0", (sf.id))
        if like_counts:
            likes = like_counts[0]['like_count']
    
        save_counts =  db1.query("SELECT count(id) AS save_count FROM sharedfile WHERE original_id = %s and deleted = 0", sf.id)
        if save_counts[0]['save_count'] > 0:
            saves = save_counts[0]['save_count']
        else:
            save_counts =  db1.query("SELECT count(id) AS save_count FROM sharedfile WHERE parent_id = %s and deleted = 0", sf.id)
            saves = save_counts[0]['save_count']

        if likes > 0 or saves > 0:
            print("UPDATE sharedfile SET like_count = %s, save_count = %s WHERE id = %s" % (likes, saves, sf.id))
            print(db1.execute("UPDATE sharedfile SET like_count = %s, save_count = %s WHERE id = %s", likes, saves, sf.id))
