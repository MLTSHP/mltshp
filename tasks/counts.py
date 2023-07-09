from torndb import Connection
from tornado.options import options
from datetime import datetime

from tasks import mltshp_task


@mltshp_task()
def calculate_likes(sharedfile_id, **kwargs):
    """
    This task will get all likes for a shared file, count them, then update the sharedfile.like_count
    """
    db = Connection(options.database_host, options.database_name, options.database_user, options.database_password)
    result = db.get("SELECT count(id) as like_count from favorite where sharedfile_id = %s and deleted=0", (sharedfile_id))
    like_count = int(result['like_count'])
    db.execute("UPDATE sharedfile set like_count = %s WHERE id = %s", like_count, sharedfile_id)
    
    tweet_or_magic(db, sharedfile_id, like_count)
    db.close()


def tweet_or_magic(db, sharedfile_id, like_count):
    likes_to_tweet = options.likes_to_tweet
    likes_to_magic = options.likes_to_magic
    if like_count not in (likes_to_tweet, likes_to_magic):
        return

    sf = db.get("SELECT * from sharedfile where id = %s", sharedfile_id)
    if int(sf['original_id']) != 0:
        return

    if like_count == likes_to_magic:
        created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        db.execute("INSERT IGNORE INTO magicfile (sharedfile_id, created_at) VALUES (%s, %s)", sharedfile_id, created_at)

    # The Twitter API is dead.
    # if like_count == likes_to_tweet and not options.debug:
    #     title = ''
    #     if sf['title'] == '' or sf['title'] == None:
    #         title = sf['name']
    #     else:
    #         title = sf['title']

    #     auth = tweepy.OAuthHandler(options.twitter_consumer_key, options.twitter_consumer_secret)
    #     auth.set_access_token(options.twitter_access_key, options.twitter_access_secret)
    #     api = tweepy.API(auth)
    #     via_twitter_account = ""
    #     twitter_account = db.get("SELECT screen_name from externalservice where user_id = %s and deleted=0", sf['user_id'])
    #     if twitter_account:
    #         via_twitter_account = " via @{0}".format(twitter_account['screen_name'])
    #     api.update_status('https://mltshp.com/p/%s "%s"%s' % (sf['share_key'], title[:90], via_twitter_account))


@mltshp_task()
def calculate_saves(sharedfile_id, **kwargs):
    """
    Take the id of a sharedfile that just got saved by another user.

    If this file is an original, meaning it has no original_id set, we can safely calculate the save count by how
    many sharedfiles have the file's id as their original_id.
    
    However if the file has an original, we also need to recalculate the original's count, as well as this file's save count. 
    """
    db = Connection(options.database_host, options.database_name, options.database_user, options.database_password)
    sharedfile = db.get("select original_id from sharedfile where id = %s", sharedfile_id)
    original_id = sharedfile['original_id']        
    
    # If this file is original, calculate it's save count by all sharedfile where this file is the original_id.
    if original_id == 0:
        original_saves =  db.get("SELECT count(id) AS count FROM sharedfile where original_id = %s and deleted = 0", sharedfile_id)
        db.execute("UPDATE sharedfile set save_count = %s WHERE id = %s", original_saves['count'], sharedfile_id)
    # Otherwise, we need to update the original's save count and this file's save count.
    else:
        original_saves =  db.get("SELECT count(id) AS count FROM sharedfile where original_id = %s and deleted = 0", original_id)
        db.execute("UPDATE sharedfile set save_count = %s WHERE id = %s", original_saves['count'], original_id)
        
        # Calc this files new save count, only based on parent since its not original.
        parent_saves =  db.get("SELECT count(id) AS count FROM sharedfile where parent_id = %s and deleted = 0", sharedfile_id)
        db.execute("UPDATE sharedfile set save_count = %s WHERE id = %s", parent_saves['count'], sharedfile_id)
    db.close()
