import hashlib
import time

import tornado.web
import postmark

from .base import BaseHandler
from models import Sharedfile, User, Shake, Invitation, Waitlist, ShakeCategory, \
    DmcaTakedown, Comment
from lib.utilities import send_slack_notification


class AdminBaseHandler(BaseHandler):
    def prepare(self):
        current_user = self.get_current_user_object()
        if not current_user or not current_user.is_admin():
            raise tornado.web.HTTPError(403)
        else:
            self.admin_user = current_user

    def render_string(self, template_name, **kwargs):
        kwargs['is_superuser'] = self.admin_user.is_superuser()
        kwargs['is_moderator'] = self.admin_user.is_moderator()
        return super(AdminBaseHandler, self).render_string(template_name, **kwargs)


class NewUsers(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        where = "deleted=0 ORDER BY id DESC LIMIT 21"
        before_id = self.get_argument('before', None)
        if before_id is not None:
            where = "id < %d AND %s" % (int(before_id), where)
        users = User.where(where)

        prev_link = None
        next_link = None
        if len(users) == 21:
            next_link = "?before=%d" % users[-1].id

        for user in users[:20]:
            files = user.sharedfiles(per_page=1)
            user.last_sharedfile = len(files) == 1 and files[0] or None

        return self.render("admin/new-users.html", users=users[:20],
            previous_link=prev_link, next_link=next_link)


class IndexHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        return self.render("admin/index.html")


class NSFWUserHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        where = "nsfw=1 AND deleted=0 ORDER BY id DESC LIMIT 21"
        before_id = self.get_argument('before', None)
        if before_id is not None:
            where = "id < %d AND %s" % (int(before_id), where)
        users = User.where(where)

        prev_link = None
        next_link = None
        if len(users) == 21:
            next_link = "?before=%d" % users[-1].id

        for user in users[:20]:
            files = user.sharedfiles(per_page=1)
            user.last_sharedfile = len(files) == 1 and files[0] or None

        return self.render("admin/nsfw-users.html", users=users[:20],
            previous_link=prev_link, next_link=next_link)


class ImageTakedownHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        if not self.admin_user.is_superuser():
            return self.redirect('/admin')

        return self.render(
            "admin/image-takedown.html",
            share_key="",
            confirm_step=False,
            sharedfile=None,
            comment="",
            canceled=self.get_argument('canceled', "0") == "1",
            deleted=self.get_argument('deleted', "0") == "1")

    @tornado.web.authenticated
    def post(self):
        if not self.admin_user.is_superuser():
            return self.redirect('/admin')

        cancel = self.get_argument('cancel', None)
        if cancel:
            return self.redirect("/admin/image-takedown?canceled=1")

        share_key = self.get_argument("share_key", None)
        comment = self.get_argument("comment", "")
        confirmation = self.get_argument('confirm', None) == "1"
        sharedfile = share_key and Sharedfile.get("share_key=%s AND deleted=0", share_key) or None

        if sharedfile and confirmation:
            DmcaTakedown.takedown_image(share_key=share_key, admin_user_id=self.admin_user.id, comment=comment)
            return self.redirect("/admin/image-takedown?deleted=1")
        else:
            confirm_step = bool(sharedfile)
            if not sharedfile:
                self.add_error('share_key', "That share key does not exist.")
                total_instances = 0
                comment_count = 0
            else:
                sharedfiles = Sharedfile.where("source_id=%s and deleted=0", sharedfile.source_id)
                total_instances = len(sharedfiles)
                sharedfile_ids = [sf.id for sf in sharedfiles]
                comment_count = Comment.where_count("sharedfile_id IN %s and deleted=0", sharedfile_ids)
            return self.render(
                "admin/image-takedown.html",
                share_key=share_key or "",
                comment=comment or "",
                canceled=False,
                deleted=False,
                total_instances=total_instances,
                comment_count=comment_count,
                confirm_step=confirm_step,
                sharedfile=sharedfile)


class InterestingStatsHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        total = Sharedfile.where_count("deleted=0")
        return self.render('admin/interesting-stats.html', total_files=total)


class CreateUsersHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        return self.render("admin/create-users.html")

    @tornado.web.authenticated
    def post(self):
        emails = self.get_argument("emails")
        for email in emails.split('\r\n'):
            email = email.strip()
            Invitation.create_for_email(email, self.admin_user.id)
        return self.redirect("/admin")


class WaitlistHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        waiters = Waitlist.where("invited = 0 or invited is NULL")
        return self.render('admin/waitlist.html', waiters=waiters[0:50])

    @tornado.web.authenticated
    def post(self):
        if self.get_argument('waitlist_id', None):
            waitlist_id = self.get_argument('waitlist_id')
            waiter = Waitlist.get('id = %s', waitlist_id)
            invitation = Invitation.create_for_email(waiter.email, self.admin_user.id)
            waiter.invited = 1
            waiter.save()
        return self.redirect('/admin/waitlist')


class DeleteUserHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        if not self.admin_user.is_superuser():
            return self.redirect('/admin')
        return self.render('admin/delete-user.html')
        
    @tornado.web.authenticated
    def post(self):
        user_id = self.get_argument('user_id')
        user_name = self.get_argument('user_name')
        user = User.get('name=%s and id=%s', user_name, user_id)
        user.delete()
        return self.redirect('/user/%s' % user_name)


class FlagNSFWHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self, user_name):
        user = User.get('name = %s', user_name)
        if not user:
            return self.redirect('/')
        
        nsfw = int(self.get_argument("nsfw", 0))
        if nsfw == 1:
            user.flag_nsfw()
        else:
            user.unflag_nsfw()
        user.save()
        send_slack_notification("%s flagged user '%s' as %s" % (self.admin_user.name, user.name, nsfw == 1 and "NSFW" or "SFW"),
            channel="#moderation", icon_emoji=":ghost:", username="modbot")
        return self.redirect("/user/%s" % user.name)


class RecommendedGroupShakeHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self, type=None):
        group_shakes = Shake.where('type=%s ORDER BY recommended', 'group')
        return self.render("admin/group-shake-recommended.html", group_shakes=group_shakes)
    
    @tornado.web.authenticated
    def post(self, type=None):
        shake_to_update = Shake.get("id = %s and type=%s", self.get_argument('shake_id', None), 'group')
        if shake_to_update:
            if type=="recommend":
                shake_to_update.recommended = 1
                shake_to_update.save()
            elif type=='unrecommend':
                shake_to_update.recommended = 0
                shake_to_update.save()
        return self.redirect("/admin/recommend-group-shake")


class GroupShakeListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        group_shakes = Shake.where('type=%s ORDER BY created_at desc', 'group')
        return self.render("admin/group-shake-list.html", group_shakes=group_shakes)


class GroupShakeViewHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self, shake_id=None):
        shake = Shake.get('id=%s and type=%s', shake_id, 'group')
        shake_categories = ShakeCategory.all()
        featured_shakes = Shake.where('featured = 1')
        if not shake:
            return self.redirect("/admin/group-shakes")

        return self.render("admin/group-shake-view.html", shake=shake, 
                            shake_categories=shake_categories, 
                            featured_shakes=featured_shakes)
    
    @tornado.web.authenticated
    def post(self, shake_id=None):
        shake = Shake.get('id=%s and type=%s', shake_id, 'group')
        if self.get_argument('shake_category_id', None):
            shake.shake_category_id = self.get_argument('shake_category_id', 0)
        if self.get_argument('featured', None):
            shake.featured = 1
        else:
            shake.featured = 0
        shake.save()
        return self.redirect('/admin/group-shake/%s' % (shake_id))

                            
class ShakeCategoriesHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        return self.render("admin/shake-categories.html", shake_categories=ShakeCategory.all())
    
    @tornado.web.authenticated
    def post(self):
        category = ShakeCategory(name=self.get_argument('name', ''), short_name=self.get_argument('short_name', ''))
        category.save()
        return self.redirect('/admin/shake-categories')


#class CreateShakeSharedFilesHandler(BaseHandler):
#    @tornado.web.authenticated
#    def get(self):
#        user = self.current_user
#        if user['name'] in ['admin',]:
#            shared_files = Sharedfile.all()
#            for sf in shared_files:
#                user = User.get('id = %s', sf.user_id)
#                user_shake = user.shake()
#                ssf = Shakesharedfile.get("shake_id = %s and sharedfile_id = %s", user_shake.id, sf.id)
#                if not ssf:
#                    ssf = Shakesharedfile(shake_id = user_shake.id, sharedfile_id = sf.id)
#                    ssf.save()
#                else:
#                    shared_file = Sharedfile.get('id=%s', ssf.sharedfile_id)
#                    ssf.created_at = shared_file.created_at
#                    ssf.save()
#        return self.redirect("/")

