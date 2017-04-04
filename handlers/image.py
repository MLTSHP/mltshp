import tempfile
import re
from urlparse import urlparse
import time
from datetime import datetime, timedelta
import tornado.web
from tornado import escape
from tornado.escape import json_encode
from tornado.options import options

from base import BaseHandler
from models import Favorite, User, Sharedfile, Sourcefile, Comment, Shake, Externalservice
import models
from lib.utilities import s3_authenticated_url, uses_a_banned_phrase


class SaveHandler(BaseHandler):
    """
    path: /p/{share_key}/save

    Used primarily as an Ajax request when clicking "save" button
    for an image.  We want to return the newly saved file's share
    key to build the link to it, as well as the old share_key and save
    count to update stats on the page in real time.
    """
    @tornado.web.authenticated
    def post(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        if not sharedfile:
            raise tornado.web.HTTPError(404)

        current_user = self.get_current_user_object()
        if not current_user:
            raise tornado.web.HTTPError(403)

        json = self.get_arguments('json', False)
        if not sharedfile.can_save(current_user):
            if json:
                return self.write({'error' : "Can't save that file."})
            else:
                return self.redirect("/p/%s" % sharedfile.share_key)

        count = sharedfile.save_count

        shake_id = self.get_argument('shake_id', None)
        if shake_id:
            shake = Shake.get("id = %s", shake_id)
            if shake and shake.can_update(current_user.id):
                new_sharedfile = sharedfile.save_to_shake(current_user, shake)
            else:
                return self.write({'error' : "Can't save that file."})
        else:
            new_sharedfile = sharedfile.save_to_shake(current_user)
        if json:
            return self.write({
                'new_share_key' : new_sharedfile.share_key,
                'share_key' : sharedfile.share_key,
                'count' : count + 1
            })
        else:
            return self.redirect("/p/%s" % new_sharedfile.share_key)


class ShowHandler(BaseHandler):
    """
    path: /p/{share_key}

    The image permalink page.
    """
    def post(self, share_key):
        return self.redirect("/p/{0}".format(share_key))

    def get(self, share_key):
        if not share_key:
            return self.redirect("/")

        sharedfile = Sharedfile.get_by_share_key(share_key)
        if not sharedfile:
            raise tornado.web.HTTPError(404)

        current_user = self.get_current_user_object()
        sourcefile = sharedfile.sourcefile()
        sharedfile_owner = sharedfile.user()
        owner_twitter_account = Externalservice.by_user(sharedfile_owner, Externalservice.TWITTER)
        comments = sharedfile.comments()
        view_count = sharedfile.livish_view_count()
        save_count = sharedfile.save_count
        heart_count = sharedfile.like_count
        can_delete = sharedfile.can_delete(current_user)
        can_comment = current_user and current_user.email_confirmed == 1 and not options.readonly
        in_these_shakes = sharedfile.shakes()
        if current_user:
            user_shakes = current_user.shakes(include_managed=True)
        else:
            user_shakes = []
        add_to_shakes = []
        for user_shake in user_shakes:
            found = False
            for in_shake in in_these_shakes:
                if in_shake.id == user_shake.id:
                    found = True
            if found == False:
                add_to_shakes.append(user_shake)
        can_add_to_shakes = (can_delete and len(add_to_shakes) > 0)

        if owner_twitter_account:
            owner_twitter_account = owner_twitter_account.screen_name
        else:
            owner_twitter_account = 'mltshp'

        image_url = "/r/%s" % (sharedfile.share_key)
        if options.debug:
            file_path =  "originals/%s" % (sourcefile.file_key)
            image_url = s3_authenticated_url(options.aws_key, options.aws_secret, options.aws_bucket, file_path=file_path, seconds=3600)
        thumb_url = s3_authenticated_url(options.aws_key, options.aws_secret, options.aws_bucket, file_path="thumbnails/%s" % (sourcefile.thumb_key), seconds=3600)
        jsonp = 'jsonp%s' % int(time.mktime(sharedfile.created_at.timetuple()))

        return self.render("image/show.html", sharedfile=sharedfile, thumb_url=thumb_url,
            sharedfile_owner=sharedfile_owner, image_url=image_url, jsonp=jsonp,
            view_count=view_count, can_delete=can_delete, save_count=save_count,
            heart_count=heart_count, comments=comments, current_user_obj=current_user,
            sourcefile=sourcefile, in_these_shakes=in_these_shakes, user_shakes=user_shakes,
            add_to_shakes=add_to_shakes, can_add_to_shakes=can_add_to_shakes,
            can_comment=can_comment,
            owner_twitter_account=owner_twitter_account)


class ShowLikesHandler(BaseHandler):
    """
    path: /p/{share_key}/likes
    """
    def get(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        if not sharedfile:
            return {'error': 'Invalid file key.'}

        response_data = []
        for sharedfile in sharedfile.favorites():
            user = sharedfile.user()
            response_data.append({
                'user_name' : user.name,
                'user_profile_image_url' :  user.profile_image_url(),
                'posted_at_friendly' : sharedfile.pretty_created_at()
            })

        return self.write({'result' : response_data, 'count' : len(response_data)})


class ShowSavesHandler(BaseHandler):
    """
    path: /p/{share_key}/saves
    """
    def get(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        if not sharedfile:
            return {'error': 'Invalid file key.'}

        response_data = []
        for sharedfile in sharedfile.saves():
            user = sharedfile.user()
            response_data.append({
                'user_name' : user.name,
                'user_profile_image_url' :  user.profile_image_url(),
                'posted_at_friendly' : sharedfile.pretty_created_at()
            })

        return self.write({'result' : response_data, 'count' : len(response_data)})


class QuickCommentsHandler(BaseHandler):
    """
    path: /p/{share_key}/quick-comments

    Expects an AJAX request, returns an HTML fragment.
    """
    def get(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        if not sharedfile:
            raise tornado.web.HTTPError(404)

        expanded = self.get_argument("expanded", False)
        if expanded:
            expanded = True

        # Prevent IE from caching AJAX requests
        self.set_header("Cache-Control","no-store, no-cache, must-revalidate");
        self.set_header("Pragma","no-cache");
        self.set_header("Expires", 0);

        user = self.get_current_user_object()
        can_comment = user and user.email_confirmed == 1 and not options.readonly

        comments = sharedfile.comments()
        html_response = self.render_string("image/quick-comments.html", sharedfile=sharedfile,
            comments=comments, current_user=user,
            can_comment=can_comment,
            expanded=expanded)
        return self.write({'result' : 'ok', 'count' : len(comments), 'html' : html_response })


class ShowRawHandler(BaseHandler):
    """
    path: /r/{id}
    this header should be sent for saving, but can't be used normally because it forces IE to download the file
    set_header("Content-Disposition", "attachment: filename=\"%s\"" % (sharedfile.name))
    """

    def get(self, share_key):
        if not share_key:
            raise tornado.web.HTTPError(404)

        sharedfile = Sharedfile.get_by_share_key(share_key)
        if not sharedfile:
            raise tornado.web.HTTPError(404)

        # check if we have logged in user.
        user = self.get_current_user()
        if user:
            user_id = user['id']
        else:
            user_id = None

        # count view
        sharedfile.add_view(user_id)

        # determine if we are to serve via CDN or direct from S3:
        if self.request.host == ("s.%s" % options.app_host) and options.use_cdn:
            # s = static; serve through CDN for "s.mltshp.com" requests

            # Amazon's ELB will set this header to inform us what scheme is in use
            # Fallback to checking Tornado's protocol if it is absent
            using_https = self.request.headers.get("X-Forwarded-Proto",
                self.request.protocol) == "https"

            # construct a URL to the CDN-hosted image
            # http://cdn.mltshp.com/r/share_key
            if using_https:
                cdn_url = "https://%s" % options.cdn_ssl_host
            else:
                cdn_url = "http://%s" % options.cdn_host

            cdn_url += "/r/%s" % share_key

            self.redirect(cdn_url)
        else:
            # piece together headers to be picked up by nginx to proxy file from S3
            sourcefile = sharedfile.sourcefile()

            file_path =  "originals/%s" % (sourcefile.file_key)
            authenticated_url = s3_authenticated_url(options.aws_key, options.aws_secret,
                options.aws_bucket, file_path=file_path, seconds=3600)
            (uri, query) = authenticated_url.split('?')

            self.set_header("Content-Type", sharedfile.content_type)
            self.set_header("Surrogate-Control", "max-age=86400")
            self.set_header("X-Accel-Redirect", "/s3/%s?%s" % (sourcefile.file_key, query))

        return

    def head(self, share_key):
        if not share_key:
            raise tornado.web.HTTPError(404)

        sharedfile = Sharedfile.get_by_share_key(share_key)
        if not sharedfile:
            raise tornado.web.HTTPError(404)

        # piece together headers to be picked up by nginx to proxy file from S3
        self.set_header("Content-Type", sharedfile.content_type)
        self.set_header("Surrogate-Control", "max-age=86400")        
        self.set_header("Connection", "close")
        return


class AddToShakesHandler(BaseHandler):
    """
    path: /p/{share_key}/delete
    """
    @tornado.web.authenticated
    def post(self, share_key):
        current_user = self.get_current_user_object()
        sharedfile = Sharedfile.get_by_share_key(share_key)
        if not sharedfile:
            raise tornado.web.HTTPError(404)
        if current_user.id != sharedfile.user_id:
            raise tornado.web.HTTPError(403)
        shakes = self.get_arguments('shakes', [])
        for shake_id in shakes:
            shake = Shake.get("id = %s", shake_id)
            if shake.can_update(current_user.id):
                sharedfile.add_to_shake(shake)
        return self.redirect("/p/%s" % sharedfile.share_key)


class DeleteFromShake(BaseHandler):
    """
    path: /p/{share_key}/shakes/{shake_id}/delete
    """
    @tornado.web.authenticated
    def post(self, share_key, shake_id):
        current_user = self.get_current_user_object()
        sharedfile = Sharedfile.get_by_share_key(share_key)
        shake = Shake.get("id = %s", shake_id)
        if not sharedfile:
            raise tornado.web.HTTPError(404)
        if not shake:
            raise tornado.web.HTTPError(404)
        if not sharedfile.can_user_delete_from_shake(current_user, shake):
            raise tornado.web.HTTPError(403)
        sharedfile.delete_from_shake(shake)
        redirect_to = self.get_argument("redirect_to", None)
        if redirect_to:
            return self.redirect(redirect_to)
        else:
            return self.redirect("/p/%s" % sharedfile.share_key)


class DeleteHandler(BaseHandler):
    """
    path: /p/{share_key}/delete
    """
    @tornado.web.authenticated
    def post(self, share_key):
        user = self.get_current_user()
        sf = Sharedfile.get("share_key=%s and user_id=%s", share_key, user['id'])
        if sf:
            sf.delete()
        return self.redirect("/")


class QuickEditTitleHandler(BaseHandler):
    """
    path: /p/{share_key}/quick-edit-title

    Called on the client side, returns JSON response with the title
    and raw (unescaped) title.
    """
    @tornado.web.authenticated
    def post(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        user = self.get_current_user_object()
        if sharedfile.can_edit(user):
            title = self.get_argument('title', '')
            if user.is_paid or not uses_a_banned_phrase(title):
                sharedfile.title = title
                sharedfile.save()
        return self.redirect("/p/%s/quick-edit-title" % share_key)

    def get(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        value = {
            'title' : escape.xhtml_escape(sharedfile.get_title()),
            'title_raw' : sharedfile.get_title()
        }
        # prevents IE from caching ajax requests.
        self.set_header("Cache-Control","no-store, no-cache, must-revalidate");
        self.set_header("Pragma","no-cache");
        self.set_header("Expires", 0);
        return self.write(escape.json_encode(value))


class QuickEditDescriptionHandler(BaseHandler):
    """
    path: /p/{share_key}/quick-edit-description

    Called on the client side, returns JSON response with the description
    and raw (unescaped) description.
    """
    @tornado.web.authenticated
    def post(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        user = self.get_current_user_object()
        if sharedfile.can_edit(user):
            description = self.get_argument('description', '')
            if user.is_paid or not uses_a_banned_phrase(description):
                sharedfile.description = description
                sharedfile.save()
        return self.redirect("/p/%s/quick-edit-description" % share_key)

    def get(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        value = {
            'description' : sharedfile.get_description(),
            'description_raw' : sharedfile.get_description(raw=True)
        }
        # prevents IE from caching ajax requests.
        self.set_header("Cache-Control","no-store, no-cache, must-revalidate");
        self.set_header("Pragma","no-cache");
        self.set_header("Expires", 0);
        return self.write(escape.json_encode(value))


class QuickEditSourceURLHandler(BaseHandler):
    """
    path: /p/{share_key}/quick-edit-source-url

    Called on the client side, returns JSON response with the source_url
    and raw (unescaped) source_url.
    """
    @tornado.web.authenticated
    def post(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        user = self.get_current_user_object()
        if sharedfile.can_edit(user):
            sharedfile.source_url = self.get_argument('source_url', '')
            sharedfile.save()
        return self.redirect("/p/%s/quick-edit-source-url" % share_key)

    def get(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        source_url = ''
        if sharedfile.source_url:
            source_url = sharedfile.source_url
        value = {
            'source_url' : escape.xhtml_escape(source_url),
            'source_url_raw' : source_url
        }
        return self.write(escape.json_encode(value))


class LikeHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, sharedfile_key):
        is_json = self.get_argument('json', None)
        user = self.get_current_user_object()

        sharedfile = Sharedfile.get_by_share_key(sharedfile_key)
        if not sharedfile:
            if is_json:
                return self.write(json_encode({'error':"Not a valid image."}))
            else:
                return self.redirect('/p/%s' % (sharedfile_key))

        #Attempt to add favorites for the parent and original
        original_sf = sharedfile.original()
        parent_sf = sharedfile.parent()
        if original_sf and not original_sf.deleted:
            user.add_favorite(original_sf)
        if parent_sf and not parent_sf.deleted and parent_sf.user_id != original_sf.user_id:
            user.add_favorite(parent_sf)

        if not user.add_favorite(sharedfile):
            if is_json:
                return self.write(json_encode({'error':"Cant like the image, probably already liked."}))
            else:
                return self.redirect('/p/%s' % (sharedfile_key))
        count = sharedfile.like_count + 1

        if is_json:
            return self.write(json_encode({'response':'ok', 'count': count, 'share_key' : sharedfile.share_key, 'like' : True }))
        else:
            return self.redirect('/p/%s' % (sharedfile_key))


class UnlikeHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, sharedfile_key):
        is_json = self.get_argument('json', None)
        user = self.get_current_user_object()

        sharedfile = Sharedfile.get_by_share_key(sharedfile_key)
        if not sharedfile:
            if is_json:
                return self.write(json_encode({'error':'Not a valid image.'}))
            else:
                return self.redirect('/p/%s' % (sharedfile_key))

        #Attempt to remove favorites for the parent and original
        original_sf = sharedfile.original()
        parent_sf = sharedfile.parent()
        if original_sf:
            user.remove_favorite(original_sf)
        if parent_sf and parent_sf.user_id != original_sf.user_id:
            user.remove_favorite(parent_sf)

        if not user.remove_favorite(sharedfile):
            if is_json:
                return self.write(json_encode({'error':"Cant unlike the image, probably not liked to begin with."}))
            else:
                return self.redirect('/p/%s' % (sharedfile_key))
        count = sharedfile.like_count - 1

        if is_json:
            return self.write(json_encode({'response':'ok', 'count' : count, 'share_key' : sharedfile.share_key, 'like' : False}))
        else:
            return self.redirect('/p/%s' % (sharedfile_key))


class OEmbedHandler(BaseHandler):
    """
    <link rel="alternate" type="application/json+oembed"
        href="http://mltshp.com/services/oembed?url=http%3A//mltshp.com/p/LMN0p&jsoncallback=jsonp123456789"
        title="Image xyz by abc." />

        Leaving the jsoncallbackp123456789 method off the call will result in no callback being sent.
    """

    def get(self):
        parsed_url = None
        try:
            parsed_url = urlparse(self.get_argument('url', None))
        except:
            raise tornado.web.HTTPError(404)
        if parsed_url.netloc not in [options.app_host, 'localhost:8000', 'localhost:81', 'www.' + options.app_host]:
            raise tornado.web.HTTPError(404)
        share_key = re.search("/p/([A-Za-z0-9]+)", parsed_url.path)
        if not share_key:
            raise tornado.web.HTTPError(404)

        include_embed = self.get_argument('include_embed', False)

        sharedfile = Sharedfile.get_by_share_key(share_key.group(1))
        sourcefile = sharedfile.sourcefile()
        sharedfile_owner = User.get("id=%s", sharedfile.user_id)

        jsonp = None
        if self.get_argument('jsoncallback', None):
            jsonp=self.get_argument('jsoncallback')
            match = re.search('^[A-Za-z0-9]+$', jsonp)
            if not match:
                jsonp = None

        if jsonp:
            self.set_header("Content-Type", "application/json")
        else:
            self.set_header("Content-Type", "application/javascript")
        self.render("services/oembed.json", sharedfile=sharedfile, sourcefile=sourcefile,
                    sharedfile_owner=sharedfile_owner, jsonp=jsonp,
                    include_embed=include_embed, app_host=options.app_host,
                    cdn_host=options.use_cdn and options.cdn_host or options.app_host)


class CommentHandler(BaseHandler):
    """
    path: /p/{share_key}/comment

    Adds a comment for a particular shared file.
    """
    @tornado.web.authenticated
    def post(self, share_key):
        shared_file = Sharedfile.get_by_share_key(share_key)
        if not shared_file:
            raise tornado.web.HTTPError(404)

        ajax = self.get_argument('ajax', False)
        body = self.get_argument('body', None)

        redirect_suffix = ""
        if ajax:
            # Prevent IE cache.
            self.set_header("Cache-Control","no-store, no-cache, must-revalidate");
            self.set_header("Pragma","no-cache");
            self.set_header("Expires", 0);
            redirect_suffix = "/quick-comments?expanded=1"

        user = self.get_current_user_object()
        if user and user.email_confirmed == 1:
            comment = Comment.add(user=user, sharedfile=shared_file, body=body)
        return self.redirect("/p/%s%s" % (share_key, redirect_suffix))


class CommentDeleteHandler(BaseHandler):
    """
    path: /p/{share_key}/comment/{{comment_id}}/delete (POST)

    Deletes a comment if user has permission to do so.
    """
    @tornado.web.authenticated
    def post(self, share_key, comment_id):
        shared_file = Sharedfile.get_by_share_key(share_key)
        if not shared_file:
            raise tornado.web.HTTPError(404)

        ajax = self.get_argument('ajax', False)
        redirect_suffix = ""
        if ajax:
            # Prevent IE cache.
            self.set_header("Cache-Control","no-store, no-cache, must-revalidate");
            self.set_header("Pragma","no-cache");
            self.set_header("Expires", 0);
            redirect_suffix = "/quick-comments?expanded=1"

        user = self.get_current_user_object()
        comment = Comment.get("id = %s", comment_id)
        if comment.can_user_delete(user):
            comment.delete()
        return self.redirect("/p/%s%s" % (share_key, redirect_suffix))


class CommentLikeHandler(BaseHandler):
    """
    path /p/{share_key}/comment/{{comment_id}}/like (POST)

    Creates or updates a CommentLike on an entry in the db.
    """
    @tornado.web.authenticated
    def post(self, share_key, comment_id):
        shared_file = models.Sharedfile.get_by_share_key(share_key)
        user = self.get_current_user_object()
        comment = Comment.get("id=%s", comment_id)

        if not shared_file or not comment:
            raise tornado.web.HTTPError(404)

        existing_comment_like = models.CommentLike.get("comment_id = %s and user_id = %s",
                comment.id, user.id)

        if existing_comment_like:
            existing_comment_like.deleted = 0
            existing_comment_like.save()
        else:
            new_comment_like = models.CommentLike(user_id=user.id,
                    comment_id=comment.id)
            new_comment_like.save()

        json = self.get_argument("json", False)
        if json:
            self.set_header("Cache-Control","no-store, no-cache, must-revalidate");
            self.set_header("Pragma","no-cache");
            self.set_header("Expires", 0);
            count = models.CommentLike.where_count("comment_id = %s", comment.id)
            return self.write(json_encode({'response':'ok', 'count': count, 'like' : True }))
        else:
            return self.redirect("/p/%s?salty" % (share_key,))


class CommentDislikeHandler(BaseHandler):
    """
    path /p/{share_key}/comment/{comment_id}/dislike (POST)

    Sets an existing comment_like to deleted.
    """
    @tornado.web.authenticated
    def post(self, share_key, comment_id):
        shared_file = models.Sharedfile.get_by_share_key(share_key)
        user = self.get_current_user_object()
        comment = Comment.get("id=%s", comment_id)

        if not shared_file or not comment:
            raise tornado.web.HTTPError(404)

        existing_comment_like = models.CommentLike.get("comment_id = %s and user_id = %s",
                comment.id, user.id)

        if existing_comment_like:
            existing_comment_like.deleted = 1
            existing_comment_like.save()

        json = self.get_argument("json", False)
        if json:
            self.set_header("Cache-Control","no-store, no-cache, must-revalidate");
            self.set_header("Pragma","no-cache");
            self.set_header("Expires", 0);
            count = models.CommentLike.where_count("comment_id = %s", comment.id)
            return self.write(json_encode({'response':'ok', 'count': count, 'like' : True }))
        else:
            return self.redirect("/p/%s?salty" % (share_key,))


class NSFWHandler(BaseHandler):
    """
    path: /p/{share_key}/nsfw (POST)

    Sets the NSFW flag on an image.
    """
    @tornado.web.authenticated
    def post(self, share_key):
        sharedfile = Sharedfile.get_by_share_key(share_key)
        if not sharedfile:
            raise tornado.web.HTTPError(404)

        ajax = self.get_argument('ajax', False)
        if ajax:
            # Prevent IE cache.
            self.set_header("Cache-Control","no-store, no-cache, must-revalidate");
            self.set_header("Pragma","no-cache");
            self.set_header("Expires", 0);

        user = self.get_current_user_object()
        sharedfile.set_nsfw(user)
        return self.redirect("/p/%s" % sharedfile.share_key)

