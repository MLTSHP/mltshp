import tornado.web
from tornado.escape import xhtml_escape

from .base import BaseHandler
from models import Sharedfile, User, Shake, ShakeCategory, \
    DmcaTakedown, Comment, Favorite, PaymentLog, ShakeManager
from lib.utilities import send_slack_notification, pretty_date
from tasks.admin import delete_account


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


class UserHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self, user_name):
        plan_names = {
            "mltshp-single-canceled": "Single Scoop - Canceled",
            "mltshp-single": "Single Scoop",
            "mltshp-double-canceled": "Double Scoop - Canceled",
            "mltshp-double": "Double Scoop",
        }
        user = User.get('name=%s', user_name)
        if not user:
            return self.redirect('/admin?error=User%20not%20found')

        post_count = "{:,d}".format(Sharedfile.where_count("user_id=%s and deleted=0", user.id))
        shake_count = "{:,d}".format(Shake.where_count("user_id=%s and deleted=0", user.id))
        comment_count = "{:,d}".format(Comment.where_count("user_id=%s and deleted=0", user.id))
        like_count = "{:,d}".format(Favorite.where_count("user_id=%s and deleted=0", user.id))
        last_activity_date = user.get_last_activity_date()
        pretty_last_activity_date = last_activity_date and pretty_date(last_activity_date) or "None"
        subscribed = bool(user.is_paid)
        subscription = subscribed and user.active_paid_subscription()
        subscription_level = plan_names.get(user.stripe_plan_id) or None
        subscription_start = subscription and subscription['start_date']
        subscription_end = subscription and subscription['end_date']
        all_payments = PaymentLog.where("user_id=%s", user.id)
        total_payments = 0.00
        for payment in all_payments:
            if payment.status == "payment":
                total_payments = total_payments + float(payment.transaction_amount.split(" ")[1])
        uploaded_all_time_mb = "{:,.2f}".format(user.uploaded_kilobytes() / 1024)
        uploaded_this_month_mb = "{:,.2f}".format(user.uploaded_this_month() / 1024)
        # select all _original_ posts from this user; we care less about reposts for this view
        recent_posts = Sharedfile.where("user_id=%s and original_id=0 order by created_at desc limit 50", user.id)
        recent_comments = Comment.where("user_id=%s order by created_at desc limit 100", user.id)
        shakes = [s for s in user.shakes() if s.type == "group"]

        return self.render(
            "admin/user.html",
            user=user,
            user_name=user_name,
            post_count=post_count,
            shakes=shakes,
            shake_count=shake_count,
            comment_count=comment_count,
            like_count=like_count,
            uploaded_all_time_mb=uploaded_all_time_mb,
            uploaded_this_month_mb=uploaded_this_month_mb,
            total_payments=total_payments,
            subscribed=subscribed,
            subscription_level=subscription_level,
            subscription_start=subscription_start,
            subscription_end=subscription_end,
            last_activity_date=last_activity_date,
            pretty_last_activity_date=pretty_last_activity_date,
            recent_posts=recent_posts,
            recent_comments=recent_comments,)


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

        share_key = self.get_argument("share_key", None)
        if share_key:
            sharedfile = Sharedfile.get("share_key=%s AND deleted=0", share_key)
        else:
            sharedfile = None

        return self.render(
            "admin/image-takedown.html",
            share_key=share_key or "",
            confirm_step=False,
            sharedfile=sharedfile,
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


class DeleteUserHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        # Only a superuser can delete users
        if not self.admin_user.is_superuser():
            return self.write({'error': 'not allowed'})

        user_name = self.get_argument('user_name')
        user = None
        if user_name:
            user = User.get('name=%s', user_name)

        if user:
            # admin users cannot be deleted (moderator or superuser)
            if user.is_admin():
                return self.write({'error': 'cannot delete admin'})

            # Flag as deleted; send full deletion work to the background
            user.deleted = 1
            user.save()

            delete_account.delay_or_run(user_id=user.id)
            return self.write({'response': 'ok' })
        else:
            return self.write({'error': 'user not found'})


class FlagNSFWHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self, user_name):
        user = User.get('name = %s', user_name)
        if not user:
            return self.redirect('/')
        
        json = int(self.get_argument("json", 0))
        nsfw = int(self.get_argument("nsfw", 0))
        if nsfw == 1:
            user.flag_nsfw()
        else:
            user.unflag_nsfw()
        user.save()
        send_slack_notification("%s flagged user '%s' as %s" % (self.admin_user.name, user.name, nsfw == 1 and "NSFW" or "SFW"),
            channel="#moderation", icon_emoji=":ghost:", username="modbot")
        if json == 1:
            return self.write({'response': 'ok' })
        else:
            return self.redirect("/user/%s" % user.name)


class RecommendedGroupShakeHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self, shake_id, type):
        json = int(self.get_argument("json", 0))
        shake_to_update = Shake.get("id = %s and type=%s and deleted=0", shake_id, 'group')
        if shake_to_update:
            if type=="recommend":
                shake_to_update.recommended = 1
                shake_to_update.save()
            elif type=='unrecommend':
                shake_to_update.recommended = 0
                shake_to_update.save()
            if json == 1:
                return self.write({'response': 'ok' })
        if json == 1:
            return self.write({'error': 'invalid shake id' })
        else:
            return self.redirect("/admin/group-shakes?sort=recommended")


class GroupShakeListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        offset = 0
        q = self.get_argument("q", "")
        q_prop = ("*" in q and q or ("*" + q + "*")).replace("*", "%")
        if q:
            search_clause = "and (shake.title like %s or shake.name like %s or shake.description like %s)"
        else:
            search_clause = ""
        sort_order = self.get_argument("sort", "members")
        if sort_order == "members":
            query = f"""
                select shake.*, count(distinct subscription.user_id) as member_count
                from shake
                left join subscription on subscription.shake_id = shake.id and subscription.deleted=0
                where shake.type=%s and shake.deleted=0 {search_clause}
                group by shake.id
                order by member_count DESC
                limit %s, 20
                """
        elif sort_order == "last-activity":
            query = f"""
                select shake.*, max(shakesharedfile.created_at) as last_activity
                from shake
                left join shakesharedfile on shakesharedfile.shake_id = shake.id and shakesharedfile.deleted=0
                where shake.type=%s and shake.deleted=0 {search_clause}
                group by shake.id
                order by last_activity DESC
                limit %s, 20
                """
        elif sort_order == "posts":
            query = f"""
                select shake.*, count(distinct shakesharedfile.sharedfile_id) as post_count
                from shake
                left join shakesharedfile on shakesharedfile.shake_id = shake.id and shakesharedfile.deleted=0
                where shake.type=%s and shake.deleted=0 {search_clause}
                group by shake.id
                order by post_count DESC
                limit %s, 20
                """
        elif sort_order == "recommended":
            query = f"""
                select shake.*
                from shake
                where shake.type=%s and shake.deleted=0 and shake.recommended=1 {search_clause}
                order by title
                limit %s, 20
                """
        else:
            sort_order = ""

        page = self.get_argument("page", 1)
        offset = 20 * (int(page) - 1)

        params = ['group']
        if q:
            params.extend([q_prop, q_prop, q_prop])
        group_shakes = Shake.object_query(query, *params, offset)

        if sort_order == "recommended":
            group_count = Shake.where_count(f"type=%s AND deleted=0 and recommended=1 {search_clause}", *params)
        else:
            group_count = Shake.where_count(f"type=%s AND deleted=0 {search_clause}", *params)

        return self.render(
            "admin/group-shake-list.html", group_shakes=group_shakes,
            sort_order=sort_order, q=q,
            page=page, group_count=group_count, url_format="?page=%d&q=" + xhtml_escape(q) + "&sort=" + sort_order)


class GroupShakeViewHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self, shake_id=None):
        shake = Shake.get('id=%s and type=%s and deleted=0', shake_id, 'group')
        if not shake:
            return self.redirect("/admin/group-shakes")
        shake_categories = ShakeCategory.all()
        featured_shakes = Shake.where('id <> %s and deleted=0 and featured=1', shake.id)
        if shake.shake_category_id > 0:
            category_shakes = Shake.where('id <> %s and deleted=0 and shake_category_id=%s', shake.id, shake.shake_category_id)
        else:
            category_shakes = []
        managers = shake.managers()

        return self.render(
            "admin/group-shake-view.html",
            shake=shake,
            shake_editor=shake.owner(),
            managers=managers,
            shake_categories=shake_categories, 
            featured_shakes=featured_shakes,
            category_shakes=category_shakes)
    
    @tornado.web.authenticated
    def post(self, shake_id=None):
        shake = Shake.get('id=%s and type=%s and deleted=0', shake_id, 'group')
        shake.shake_category_id = self.get_argument('shake_category_id', 0)
        if self.get_argument('featured', None) == "1":
            shake.featured = 1
        else:
            shake.featured = 0
        if self.get_argument('recommended', None) == "1":
            shake.recommended = 1
        else:
            shake.recommended = 0
        shake.save()
        return self.redirect('/admin/group-shake/%s' % (shake_id))


class GroupShakeEditorHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self, shake_id, user_id):
        shake = Shake.get('id=%s and type=%s and deleted=0', shake_id, 'group')
        user = User.get('id=%s', user_id)
        if not shake or not user:
            return self.write({ 'error': 'invalid shake or user' })
        current_owner = shake.owner()
        manager = ShakeManager.get('shake_id=%s and user_id=%s and deleted=0', shake.id, user.id)
        if not current_owner or (current_owner and current_owner.id != user.id):
            shake.user_id = user.id
            shake.save()
            if current_owner:
                # make former owner a manager
                shake.add_manager(current_owner)
            if manager:
                manager.delete()
            self.write({ 'response': 'ok' })
        else:
            self.write({ 'error': 'invalid shake or user' })


class DeleteShakeHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        if not self.admin_user.is_superuser():
            return self.write({'error': 'not allowed'})
        shake_id = self.get_argument('shake_id')
        shake = Shake.get('id=%s and type=%s and deleted=0', shake_id, 'group')
        if not shake:
            return self.write({'error': 'invalid shake'})
        shake.delete()
        return self.write({'response': 'ok' })


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

