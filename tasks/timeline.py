import os
from torndb import Connection
from tornado.options import options

from tasks import mltshp_task


@mltshp_task()
def add_posts(shake_id=0, sharedfile_id=0, sourcefile_id=0, deleted=0, created_at=None, **kwargs):
    """
    This task will get the subscribers for a shake and insert
    a post for every user. If the sourcefile_id exists in posts
    it will set "seen" equal to 1.
    """
    db = Connection(options.database_host, options.database_name, options.database_user, options.database_password)

    #get subscribers for shake_id
    results = db.query("""SELECT user_id as id FROM subscription WHERE shake_id = %s and deleted = 0""", shake_id)
    for user in results:
        seen = 0
        #does this sourcefile exist in post for this user?
        existing = db.query("""SELECT id FROM post WHERE user_id = %s and sourcefile_id = %s and deleted=0 ORDER BY created_at desc LIMIT 1""", user['id'], sourcefile_id)
        #if so, set seen = 1
        if existing:
            seen = 1
        #if not, insert a new row 
        if created_at:
            db.execute("""INSERT INTO post (user_id, sourcefile_id, sharedfile_id, seen, deleted, shake_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)""", user['id'], sourcefile_id, sharedfile_id, seen, deleted, shake_id, created_at)
        else:
            db.execute("""INSERT INTO post (user_id, sourcefile_id, sharedfile_id, seen, deleted, shake_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())""", user['id'], sourcefile_id, sharedfile_id, seen, deleted, shake_id)
    #now insert a post for the user who originally posted it.
    sharedfile = db.get("""SELECT user_id from sharedfile WHERE id = %s""", sharedfile_id)
    db.execute("""INSERT INTO post (user_id, sourcefile_id, sharedfile_id, seen, deleted, shake_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())""", sharedfile['user_id'], sourcefile_id, sharedfile_id, 1, 0, shake_id)
    db.close()


@mltshp_task()
def delete_posts(sharedfile_id=0, **kwargs):
    """
    This task will update the post table setting any post containing the shared file
    to deleted = 1
    """
    db = Connection(options.database_host, options.database_name, options.database_user, options.database_password)
    db.execute("""UPDATE post SET deleted=1 WHERE sharedfile_id = %s AND deleted=0""", sharedfile_id)
    db.close()
