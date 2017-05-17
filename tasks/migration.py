import os
from torndb import Connection
from tornado.options import options

import logging
logger = logging.getLogger(__name__)

from tasks import mltshp_task
import postmark


@mltshp_task()
def migrate_for_user(user_id=0, **kwargs):
    """
    This tasks handles copying MLKSHK user data over to the MLTSHP tables.

    """
    db = Connection(options.database_host, options.database_name, options.database_user, options.database_password)

    logger.info("Migrating user_id %s..." % str(user_id))

    logger.info("- app records")
    db.execute("""INSERT IGNORE INTO app (id, user_id, title, description, secret, redirect_url, deleted, created_at, updated_at) SELECT ma.id, ma.user_id, ma.title, ma.description, ma.secret, ma.redirect_url, 0, ma.created_at, ma.updated_at FROM mlkshk_app ma WHERE ma.user_id=%s AND ma.deleted=0""", user_id)

    # comments
    logger.info("- comment records")
    db.execute("""INSERT IGNORE INTO comment (id, user_id, sharedfile_id, body, deleted, created_at, updated_at) SELECT mc.id, mc.user_id, mc.sharedfile_id, mc.body, mc.deleted, mc.created_at, mc.updated_at FROM mlkshk_comment mc WHERE mc.user_id=%s AND mc.deleted=0""", user_id)

    # conversation
    logger.info("- conversation records")
    db.execute("""INSERT IGNORE INTO conversation (id, user_id, sharedfile_id, muted, created_at, updated_at) SELECT mc.id, mc.user_id, mc.sharedfile_id, mc.muted, mc.created_at, mc.updated_at FROM mlkshk_conversation mc WHERE mc.user_id=%s""", user_id)

    # favorites
    logger.info("- favorite records")
    db.execute("""INSERT IGNORE INTO favorite (id, user_id, sharedfile_id, deleted, created_at, updated_at) SELECT mf.id, mf.user_id, mf.sharedfile_id, mf.deleted, mf.created_at, mf.updated_at FROM mlkshk_favorite mf WHERE mf.user_id=%s AND mf.deleted=0""", user_id)

    # invitation_request
    logger.info("- invitation_request records")
    db.execute("""INSERT IGNORE INTO invitation_request (id, user_id, manager_id, shake_id, deleted, created_at, updated_at) SELECT mi.id, mi.user_id, mi.manager_id, mi.shake_id, mi.deleted, mi.created_at, mi.updated_at FROM mlkshk_invitation_request mi WHERE mi.user_id=%s AND mi.deleted=0""", user_id)

    # notification
    logger.info("- notification records")
    db.execute("""INSERT IGNORE INTO notification (id, sender_id, receiver_id, action_id, type, deleted, created_at) SELECT mn.id, mn.sender_id, mn.receiver_id, mn.action_id, mn.type, mn.deleted, mn.created_at FROM mlkshk_notification mn WHERE mn.receiver_id=%s AND mn.deleted=0""", user_id)

    # shake
    logger.info("- shake records")
    db.execute("""UPDATE shake SET deleted=0 WHERE type='user' AND user_id=%s""", user_id)
    db.execute("""INSERT IGNORE INTO shake (id, user_id, type, image, name, title, description, recommended, featured, shake_category_id, deleted, created_at, updated_at) SELECT ms.id, ms.user_id, ms.type, ms.image, ms.name, ms.title, ms.description, ms.recommended, ms.featured, ms.shake_category_id, ms.deleted, ms.created_at, ms.updated_at FROM mlkshk_shake ms WHERE ms.user_id=%s AND ms.deleted=0""", user_id)

    # shake_manager
    logger.info("- shake_manager records")
    db.execute("""INSERT IGNORE INTO shake_manager (id, shake_id, user_id, deleted, created_at, updated_at) SELECT ms.id, ms.shake_id, ms.user_id, ms.deleted, ms.created_at, ms.updated_at FROM mlkshk_shake_manager ms WHERE ms.user_id=%s AND ms.deleted=0""", user_id)

    # shakesharedfile
    logger.info("- shakesharedfile records")
    db.execute("""INSERT IGNORE INTO shakesharedfile (id, shake_id, sharedfile_id, deleted, created_at) SELECT ms.id, ms.shake_id, ms.sharedfile_id, ms.deleted, ms.created_at FROM mlkshk_shakesharedfile ms WHERE ms.shake_id IN (SELECT DISTINCT id FROM shake WHERE deleted=0 AND user_id=%s) AND ms.deleted=0""", user_id)

    # sharedfile
    logger.info("- sharedfile records")
    db.execute("""INSERT IGNORE INTO sharedfile (id, source_id, user_id, name, title, source_url, description, share_key, content_type, size, activity_at, parent_id, original_id, deleted, like_count, save_count, view_count, updated_at, created_at) SELECT ms.id, ms.source_id, ms.user_id, ms.name, ms.title, ms.source_url, ms.description, ms.share_key, ms.content_type, ms.size, ms.activity_at, ms.parent_id, ms.original_id, ms.deleted, ms.like_count, ms.save_count, ms.view_count, ms.updated_at, ms.created_at FROM mlkshk_sharedfile ms WHERE ms.user_id=%s AND ms.deleted=0""", user_id)

    # nsfw_log
    logger.info("- nsfw_log records")
    db.execute("""INSERT IGNORE INTO nsfw_log (id, user_id, sharedfile_id, sourcefile_id, created_at) SELECT mn.id, mn.user_id, mn.sharedfile_id, mn.sourcefile_id, mn.created_at FROM mlkshk_nsfw_log mn WHERE mn.user_id=%s""", user_id)

    # magicfile
    logger.info("- magicfile records")
    db.execute("""INSERT IGNORE INTO magicfile (id, sharedfile_id, created_at) SELECT mm.id, mm.sharedfile_id, mm.created_at FROM mlkshk_magicfile mm WHERE mm.sharedfile_id IN (SELECT id FROM sharedfile WHERE user_id=%s)""", user_id)

    # subscription
    logger.info("- subscription records")
    db.execute("""INSERT IGNORE INTO subscription (id, user_id, shake_id, deleted, created_at, updated_at) SELECT ms.id, ms.user_id, ms.shake_id, ms.deleted, ms.created_at, ms.updated_at FROM mlkshk_subscription ms WHERE ms.user_id=%s AND ms.deleted=0""", user_id)

    # tagged_file
    logger.info("- tagged_file records")
    db.execute("""INSERT IGNORE INTO tagged_file (id, tag_id, sharedfile_id, deleted, created_at) SELECT mt.id, mt.tag_id, mt.sharedfile_id, mt.deleted, mt.created_at FROM mlkshk_tagged_file mt WHERE mt.sharedfile_id IN (SELECT DISTINCT id FROM sharedfile WHERE user_id=%s) AND mt.deleted=0""", user_id)

    # special handling for post table migration since that thing is so large (300mm rows)
    logger.info("- post records")
    db.execute("""INSERT IGNORE INTO post (id, user_id, sourcefile_id, sharedfile_id, seen, deleted, shake_id, created_at) SELECT mp.id, mp.user_id, mp.sourcefile_id, mp.sharedfile_id, mp.seen, 0, mp.shake_id, mp.created_at FROM mlkshk_post mp WHERE mp.user_id=%s AND mp.deleted=0""", user_id)

    # this should already be done by the web app, but we may running this
    # via a script
    logger.info("- user/migration_state update")
    db.execute("""UPDATE user SET deleted=0 WHERE deleted=2 and id=%s""", user_id)
    db.execute("""UPDATE migration_state SET is_migrated=1 WHERE user_id=%s""", user_id)

    logger.info("- Migration for user %s complete!" % str(user_id))

    user = db.get("SELECT name, email FROM user WHERE id=%s", user_id)

    db.close()

    if options.postmark_api_key and not options.debug_workers:
        pm = postmark.PMMail(api_key=options.postmark_api_key,
            sender="hello@mltshp.com", to=user["email"],
            subject="MLTSHP restore has finished!",
            text_body=
            """We'll keep this short and sweet. Your data should be available now!\n\n""" +
            ("""Head over to: https://mltshp.com/user/%s and check it out!""" % user["name"]))
        pm.send()
