import tornado.web
from tornado import escape
import torndb
from tornado.options import options
import requests

from .base import BaseHandler, require_membership
from models import Shake, User, Notification, ShakeManager, MigrationState
from lib.utilities import base36decode

import logging
logger = logging.getLogger("mltshp")


def _invitations(shake, current_user):
    invitation = None
    invitation_requests = []

    if current_user:
        notification = Notification.invitation_to_shake_for_user(shake, current_user)
        if notification:
            sender = notification.sender()
            related_object = notification.related_object()
            invitation = {'sender' : sender, 'related_object' : related_object, 'id' : notification.id}

    if current_user and current_user.id == shake.user_id:
        notifications = Notification.where('type = %s and receiver_id = %s and action_id = %s and deleted = 0', 'invitation_request', current_user.id, shake.id)
        if notifications:
            for notification in notifications:
                sender = notification.sender()
                related_object = notification.related_object()
                invitation_requests.append({'sender' : sender, 'related_object' : related_object, 'id' : notification.id})

    return (invitation, invitation_requests,)


class ShakeHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self, shake_name=None, before_or_after=None, base36_id=None):
        shake = Shake.get("name=%s", shake_name)
        older_link, newer_link = None, None
        sharedfile_id = None
        shared_files = []
        if base36_id:
            sharedfile_id = base36decode(base36_id)

        max_id, since_id = None, None
        if sharedfile_id and before_or_after == 'before':
            max_id = sharedfile_id
        elif sharedfile_id and before_or_after == 'after':
            since_id = sharedfile_id

        current_user = self.get_current_user_object()
        if not shake:
            raise tornado.web.HTTPError(404)

        invitation, invitation_requests = _invitations(shake, current_user)

        # We're going to older, so ony use max_id.
        if max_id:
            shared_files = shake.sharedfiles_paginated(max_id=max_id,per_page=11)
            # we have nothing on this page, redirect to home page with out params.
            if len(shared_files) == 0:
                return self.redirect(shake.path())

            if len(shared_files) > 10:
                older_link = "%s/before/%s" % (shake.path(), shared_files[9].share_key)
                newer_link = "%s/after/%s" % (shake.path(), shared_files[0].share_key)
            else:
                newer_link = "%s/after/%s" % (shake.path(), shared_files[0].share_key)

        # We're going to newer
        elif since_id:
            shared_files = shake.sharedfiles_paginated(since_id=since_id, per_page=11)
            if len(shared_files) <= 10:
                return self.redirect(shake.path())
            else:
                shared_files.pop(0)
                older_link = "%s/before/%s" % (shake.path(), shared_files[9].share_key)
                newer_link = "%s/after/%s" % (shake.path(), shared_files[0].share_key)
        else:
            # clean home page, only has older link
            shared_files = shake.sharedfiles_paginated(per_page=11)
            if len(shared_files) > 10:
                older_link = "%s/before/%s" % (shake.path(), shared_files[9].share_key)

        #is this user a shake manager?
        managers = shake.managers()
        is_shake_manager = False
        if managers and current_user:
            for manager in managers:
                if manager.id == current_user.id:
                    is_shake_manager = True
                    break

        followers = shake.subscribers()
        follower_count = len(followers)

        return self.render("shakes/shake.html", shake=shake,
            shared_files=shared_files[0:10],
            current_user_obj=current_user, invitation=invitation,
            invitation_requests=invitation_requests,
            older_link=older_link,newer_link=newer_link,
            shake_editor=shake.owner(), managers=managers,
            is_shake_manager=is_shake_manager, followers=followers[:10],
            base36_id=base36_id,
            sharedfile_id=sharedfile_id,
            since_id=since_id,
            max_id=max_id,
            follower_count=follower_count)


class CreateShakeHandler(BaseHandler):
    """
    Creates a shake.
    """
    @tornado.web.authenticated
    @require_membership
    def get(self):
        user_object = self.get_current_user_object()

        if not user_object.is_plus():
            return self.redirect('/account/membership?upgrade=1')

        if len(user_object.shakes()) < 100:
            new_shake = Shake(name='', title='', description='')
            return self.render("shakes/create.html", shake=new_shake)
        else:
            return self.render("shakes/no-create.html")

    @tornado.web.authenticated
    @require_membership
    def post(self):
        name = self.get_argument("name", '')
        description = self.get_argument("description", '')
        title = self.get_argument("title", '')
        user_object = self.get_current_user_object()

        if not user_object.is_plus():
            return self.redirect('/account/membership?upgrade=1')

        if len(user_object.shakes()) < 101:
            new_shake = Shake(name=name, title=title, description=description, user_id=user_object.id, type='group')
            try:
                if new_shake.save():
                    return self.redirect('/%s' % new_shake.name)
            except torndb.IntegrityError:
                # This is a rare edge case, so we handle it lazily -- IK.
                pass
            self.add_errors(new_shake.errors)
            return self.render("shakes/create.html", shake=new_shake)
        else:
            return self.render("shakes/no-create.html")


class QuickDetailsHandler(BaseHandler):
    """
    path: /shake/{shake.name}/quick-details
    """
    @tornado.web.authenticated
    @require_membership
    def get(self, shake_name):
        shake = Shake.get("name=%s and deleted=0", shake_name)
        if not shake:
            raise tornado.web.HTTPError(404)

        value = {
            'title' : escape.xhtml_escape(shake.title) if shake.title else '',
            'title_raw' : shake.title if shake.title else '',
            'description' : escape.xhtml_escape(shake.description) if shake.description else '',
            'description_raw' : shake.description if shake.description else ''
        }
        # prevents IE from caching ajax requests.
        self.set_header("Cache-Control","no-store, no-cache, must-revalidate");
        self.set_header("Pragma","no-cache");
        self.set_header("Expires", 0);
        return self.write(value)

    @tornado.web.authenticated
    @require_membership
    def post(self, shake_name):
        current_user = self.get_current_user_object()
        shake_to_update = Shake.get('name=%s and user_id=%s and type=%s and deleted=0', shake_name, current_user.id, 'group')
        new_title = self.get_argument('title', None)
        new_description = self.get_argument('description', None)

        if not shake_to_update:
            return self.write({'error':'No permission to update shake.'})

        if new_title:
            shake_to_update.title = new_title
        if new_description:
            shake_to_update.description = new_description
        shake_to_update.save()

        return self.redirect('/shake/%s/quick-details' % shake_to_update.name)


class UpdateShakeHandler(BaseHandler):
    """
    path: /shake/{shake.name}/update
          OR /shake/internalupdate (called through nginx with a 'shake_name' argument)
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_name=None):
        current_user = self.get_current_user_object()
        if current_user.email_confirmed != 1:
            return self.write({'error':'You must confirm your email address to save this post.'})

        if shake_name is None:
            # Also accept shake name via argument (for nginx uploads)
            shake_name = self.get_argument('shake_name', None)
        shake_to_update = Shake.get('name=%s and user_id=%s and type=%s and deleted=0', shake_name, current_user.id, 'group')
        json = self.get_argument('json', None)
        new_title = self.get_argument('title', None)
        new_description = self.get_argument('description', None)
        file_path = self.get_argument("file_path", None)
        file_name = self.get_argument("file_name", None)
        sha1_value = self.get_argument("file_sha1", None)
        content_type = self.get_argument("file_content_type", None)
        skip_s3 = self.get_argument("skip_s3", None)
        json_response = {}

        if not shake_to_update:
            if json:
                return self.write({'error':'No permission to update shake.'})
            else:
                return self.redirect("/")

        if new_title:
            shake_to_update.title = new_title

        if new_description:
            shake_to_update.description = new_description

        if file_name and not skip_s3:
            shake_to_update.set_page_image(file_path, sha1_value)

            # issue PURGE command for shake image URLs
            if not skip_s3 and \
                options.use_cdn:
                try:
                    urls = [s for s in [
                        shake_to_update.page_image(),
                        shake_to_update.page_image().replace("/s3", ""),
                        shake_to_update.thumbnail_url(),
                        shake_to_update.thumbnail_url().replace("/s3", ""),
                    ] if "default-icon" not in s]

                    for url in urls:
                        response = requests.request("PURGE", url)
                        if response.status_code != 200:
                            logger.warning("PURGE failed: %s" % response.text)
                except Exception as e:
                    logger.error("PURGE exception: %s" % str(e))

        shake_to_update.save()

        if json:
            return self.write({'ok':'Saved it!'})
        else:
            return self.redirect("/%s" % shake_name)


class SubscribeShakeHandler(BaseHandler):
    """
    This subscribes to a specific shake, not a user shake.
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_id):
        is_json = self.get_argument('json', None)
        user = self.get_current_user_object()

        shake = Shake.get('id=%s and deleted=0', shake_id)
        if not shake:
            if is_json:
                return self.write({'error':'Shake not found.'})
            else:
                return self.redirect(shake.path())

        if not user.subscribe(shake):
            if is_json:
                return self.write({'error':'error'})
            else:
                return self.redirect(shake.path())
        else:
            if is_json:
                return self.write({'subscription_status': True})
            else:
                return self.redirect(shake.path())


class UnsubscribeShakeHandler(BaseHandler):
    """
    This unsubscribes from a shake.
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_id):
        is_json = self.get_argument('json', None)
        user = self.get_current_user_object()

        shake = Shake.get('id=%s and deleted=0', shake_id)
        if not shake:
            if is_json:
                return self.write({'error':'Shake not found.'})
            else:
                return self.redirect(shake.path())

        if not user.unsubscribe(shake):
            if is_json:
                return self.write({'error':'error'})
            else:
                return self.redirect(shake.path())
        else:
            if is_json:
                return self.write({'subscription_status': False})
            else:
                return self.redirect(shake.path())


class InviteMemberHandler(BaseHandler):
    """
    This method creates an invitation notification for a user.
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_name):
        shake = Shake.get('name=%s and type=%s', shake_name, "group")
        if not shake:
            raise tornado.web.HTTPError(404)
        sender = self.get_current_user_object()
        receiver = User.get('name=%s and deleted=0', self.get_argument('name', None))
        is_json = self.get_argument('json', None)

        if not receiver:
            if is_json:
                return self.write({'error':'error'})
            else:
                return self.redirect('/%s' % shake_name)
        Notification.new_invitation(sender, receiver, shake.id)

        if is_json:
            return self.write({'invitation_status':True})
        else:
            return self.redirect('/%s' % shake_name)


class AcceptInvitationHandler(BaseHandler):
    """
    This method accepts invitations, clears all related notifications, and sends
    an email to the invitor that the invitation was accepted.
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_name):
        is_json = self.get_argument('json', None)
        current_user_object = self.get_current_user_object()
        invitation_notification = Notification.get('id = %s and receiver_id = %s and type = %s and deleted = 0',
            self.get_argument('id', 0), current_user_object.id, 'invitation')

        if not invitation_notification:
            if is_json:
                return self.write({'error':'error'})
            else:
                return self.redirect("/")

        shake_object = Shake.get('id = %s', invitation_notification.action_id)
        shake_manager = ShakeManager.get('user_id = %s and shake_id = %s', current_user_object.id, shake_object.id)
        if shake_manager:
            shake_manager.deleted = 0
            shake_manager.save()
        else:
            shake_manager = ShakeManager(user_id=current_user_object.id, shake_id=shake_object.id)
            shake_manager.save()

        invitation_notification.deleted = 1
        invitation_notification.save()

        #send email to owner of shake

        #set all invitation notifications for this shake, user, to deleted
        all_notifications = Notification.where('sender_id = %s and action_id = %s and receiver_id = %s and deleted = 0',
            invitation_notification.sender_id, invitation_notification.action_id, invitation_notification.receiver_id)
        for n in all_notifications:
            n.deleted = 1
            n.save()

        if is_json:
            remaining_notifications_count = Notification.where_count("type = %s and receiver_id = %s and deleted = 0", \
                                                                     "invitation", current_user_object.id)
            return self.write({'response' : 'ok',
                                'count' : remaining_notifications_count})
        else:
            return self.redirect("/%s" % shake_object.name)


class RequestInvitationHandler(BaseHandler):
    """
    Creates a request object if one does not already exist.
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_name=None):
        shake = Shake.get('name=%s and deleted=0', shake_name)
        current_user_object = self.get_current_user_object()

        if not shake:
            raise tornado.web.HTTPError(404)

        if current_user_object.can_request_invitation_to_shake(shake.id):
            current_user_object.request_invitation_to_shake(shake.id)
            if self.get_argument('json', None):
                return self.write({'status':'ok'})
            else:
                return self.redirect('/%s' % shake.name)
        else:
            if self.get_argument('json', None):
                return self.write({'status':'error', 'message':'not allowed'})
            else:
                return self.redirect('/')


class ApproveInvitationHandler(BaseHandler):
    """
    Approve an invitation request
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_name=None):
        shake = Shake.get('name=%s and deleted=0', shake_name)
        current_user_object = self.get_current_user_object()
        requestor = User.get('id = %s', self.get_argument('user_id', None))

        if not shake:
            raise tornado.web.HTTPError(404)

        if not requestor:
            if self.get_argument('json', None):
                return self.write({'status':'error'})
            else:
                return self.redirect('/%s' % shake.name)

        no = Notification.get('sender_id = %s and receiver_id = %s and action_id = %s and deleted = 0', requestor.id, current_user_object.id, shake.id)

        if not no:
            if self.get_argument('json', None):
                return self.write({'status':'error'})
            else:
                return self.redirect('/%s' % shake.name)

        if shake.add_manager(user_to_add=requestor):
            no.delete()

            Notification.new_invitation_request_accepted(current_user_object, requestor, shake)
            if self.get_argument('json', None):
                return self.write({'status':'ok', 'count' : Notification.count_for_user_by_type(current_user_object.id, 'invitation_request')})
            else:
                return self.redirect('/%s' % shake.name)
        else:
            if self.get_argument('json', None):
                return self.write({'status':'error'})
            else:
                return self.redirect('/%s' % shake.name)


class DeclineInvitationHandler(BaseHandler):
    """
    Decline an invitation request
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_name=None):
        shake = Shake.get('name=%s and deleted=0', shake_name)
        current_user_object = self.get_current_user_object()
        requestor = User.get('id = %s', self.get_argument('user_id', None))

        if not shake:
            raise tornado.web.HTTPError(404)

        if not requestor:
            if self.get_argument('json', None):
                return self.write({'status':'error'})
            else:
                return self.redirect('/%s' % shake.name)

        no = Notification.get('sender_id = %s and receiver_id = %s and action_id = %s and deleted = 0', requestor.id, current_user_object.id, shake.id)

        if not no:
            if self.get_argument('json', None):
                return self.write({'status':'error'})
            else:
                return self.redirect('/%s' % shake.name)

        no.delete()

        if self.get_argument('json', None):
            return self.write({'status':'ok', 'count' : Notification.count_for_user_by_type(current_user_object.id, 'invitation_request')})
        else:
            return self.redirect('/%s' % shake.name)


class RSSFeedHandler(BaseHandler):
    """
    This method returns RSS for this shake's last
        20 posts
    """
    def get(self, shake_name=None):
        shake = Shake.get("name=%s and deleted=0", shake_name)
        if not shake:
            raise tornado.web.HTTPError(404)
        build_date = shake.feed_date()
        sharedfiles = shake.sharedfiles(per_page=20)
        if sharedfiles:
            build_date = sharedfiles[0].feed_date()

        self.set_header("Content-Type", "application/xml")
        return self.render("shakes/rss.html",
            cdn_host=options.cdn_host,
            app_host=options.app_host, shake=shake,
            sharedfiles=sharedfiles, build_date=build_date)


class FollowerHandler(BaseHandler):
    """
    Returns followers for this shake
    """
    @tornado.web.authenticated
    @require_membership
    def get(self, shake_name=None, page=None):
        shake_object = Shake.get("name=%s", shake_name)
        if not page:
            page = 1

        page = int(page)

        if not shake_object:
            raise tornado.web.HTTPError(404)

        followers = shake_object.subscribers(page=page)
        follower_count = shake_object.subscriber_count()
        url_format = '/shake/%s/followers/' % shake_object.name
        url_format = url_format + '%d'
        return self.render("shakes/followers.html", followers=followers,
            shake_info=shake_object,
            url_format=url_format, follower_count=follower_count,
            page=page)


class MembersHandler(BaseHandler):
    """
    path: /shake/{name}/members

    Render list of members and provide control for removing members.
    """
    @tornado.web.authenticated
    @require_membership
    def get(self, shake_name):
        shake = Shake.get("name=%s and deleted=0", shake_name)
        if not shake:
            raise tornado.web.HTTPError(404)

        current_user = self.get_current_user_object()
        invitation, invitation_requests = _invitations(shake, current_user)

        #is this user a shake manager?
        managers = shake.managers()
        is_shake_manager = False
        if managers and current_user:
            for manager in managers:
                if manager.id == current_user.id:
                    is_shake_manager = True
                    break

        followers = shake.subscribers()
        follower_count = shake.subscriber_count()

        return self.render("shakes/members.html", shake=shake, invitation=invitation,
            managers=shake.managers(), current_user_obj=current_user,
            invitation_requests=invitation_requests, shake_editor=shake.owner(),
            is_shake_manager=is_shake_manager, followers=followers,
            follower_count=follower_count)


class QuitHandler(BaseHandler):
    """
    This method only allows POST requests. It finds the manager record
    for this user and marks it as deleted.
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_name=None):
        shake = Shake.get("name=%s and deleted=0", shake_name)
        if not shake:
            raise tornado.web.HTTPError(404)
        current_user_object = self.get_current_user_object()
        sm = ShakeManager.get('user_id=%s and shake_id=%s and deleted = 0', current_user_object.id, shake.id)
        if sm:
            sm.delete()
        return self.redirect(shake.path())


class RemoveMemberHandler(BaseHandler):
    """
    This method only allows POST request. It finds a manager record
    for the shake that is owned by this user.
    """
    @tornado.web.authenticated
    @require_membership
    def post(self, shake_name=None):
        shake = Shake.get('name=%s and user_id = %s and deleted=0', shake_name, self.current_user['id'])

        if not shake:
            raise tornado.web.HTTPError(404)

        sm = ShakeManager.get('user_id = %s and shake_id = %s and deleted = 0', self.get_argument('user_id', 0), shake.id)

        if sm:
            sm.delete()
            former_member = User.get('id=%s', self.get_argument('user_id'))
            Notification.send_shake_member_removal(shake, former_member)

            return self.write({'status':'ok'})

        raise tornado.web.HTTPError(403)
