from urllib.parse import urlparse, parse_qs
import os
import re
import random
import json
import io

from tornado.httpclient import HTTPRequest
import tornado.auth
import tornado.web
from tornado.escape import json_decode
from tornado.options import options

from models import Externalservice, User, Sourcefile, Sharedfile, Shake, ShakeCategory
from .base import BaseHandler, require_membership
from lib.utilities import base36encode

import logging
logger = logging.getLogger("mltshp")


class PickerPopupHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self):
        url = self.get_argument('url', None)
        source_url = self.get_argument('source_url', '')
        alt_text = self.get_argument('alt', '')
        file_name = self.get_argument('title', '')
        current_user = self.get_current_user_object()

        if not url:
            raise tornado.web.HTTPError(404)

        #Hide filepile URLs
        if source_url and (source_url.find('filepile.org') > -1):
            source_url = ''

        #If this is a Google Image URL, extract the referer
        if source_url.startswith("http://www.google.com/imgres?imgurl=") or \
            source_url.startswith("https://www.google.com/imgres?imgurl="):
            parsed_google_url = urlparse(source_url)
            if parsed_google_url.query:
                parsed_google_query = parse_qs(parsed_google_url.query)
                if parsed_google_query['imgrefurl']:
                    source_url = parsed_google_query['imgrefurl'][0]
                else:
                    source_url = ""
            else:
                source_url = ""

        #Clear out nasty reader cruft
        if source_url.find('utm_source=') > -1:
            source_url = source_url[:source_url.find('utm_source=')]
            if source_url[-1] == '?':
                source_url = source_url[:-1]

        parsed_url = urlparse(url)

        if not os.path.basename(parsed_url.path):
            raise tornado.web.HTTPError(404)

        if parsed_url.scheme.lower() not in ['http', 'https']:
            raise tornado.web.HTTPError(404)

        #need to determine if we can save it here. ERROR if you can't get a file name
        parsed_url_query = ''
        if parsed_url.query:
            parsed_url_query = "?" + parsed_url.query

        #determine if this is a vimeo or youtube URL
        is_video = False

        shakes = current_user.shakes(include_managed=True)
        can_upload_this_month = current_user.can_upload_this_month()

        #replace plus signs with %20's
        return self.render("tools/picker.html", file_name=file_name, width="", height="", \
            url=parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path + parsed_url_query, \
            source_url=source_url, description='', alt_text=alt_text, is_video=is_video, shakes=shakes,
            can_upload_this_month=can_upload_this_month)

    @tornado.web.authenticated
    @require_membership
    async def post(self):
        """
        TODO: better determination of correct file name, if it is indeed a file, plus type.
        """
        self.url = self.get_argument('url', None)
        self.content_type = None

        if not self.url:
            raise tornado.web.HTTPError(404)

        #TODO : check if it is a valid URL
        #       copy from above

        http = tornado.httpclient.AsyncHTTPClient()

        logger.debug("Fetching %s" % (self.url))
        request = HTTPRequest(self.url, header_callback=self.on_header)

        if self.get_argument('skip_s3', None):
            # This parameter is used specifically for unit testing, so mock the file being
            # served as well.
            self.content_type = 'image/png'
            dummy_buffer = io.BytesIO()
            with open(os.path.join(os.path.dirname(__file__), '../test/files/1.png'), 'rb') as f:
                dummy_buffer.write(f.read())
            dummy_response = tornado.httpclient.HTTPResponse(request, 200, buffer=dummy_buffer)
            self.on_response(dummy_response)
        else:
            fut = http.fetch(request)
            response = await fut
            logger.debug("Got response for %s" % (self.url))
            self.on_response(response)

    def on_response(self, response):
        logger.debug("Parsing response for %s" % (self.url))
        url_parts = urlparse(response.request.url)
        file_name = os.path.basename(url_parts.path)
        title = self.get_argument("title", None)
        source_url = self.get_argument('source_url', None)
        description = self.get_argument('description', None)
        alt_text = self.get_argument('alt_text', None)
        shake_id = self.get_argument('shake_id', None)
        skip_s3 = self.get_argument('skip_s3', None)

        if title == file_name:
            title = None

        if self.content_type not in self.approved_content_types:
            if response.body[0:50].find(b'JFIF') > -1:
                self.content_type = 'image/jpeg'
            else:
                return self.render("tools/picker-error.html", error="Invalid file type: %s" % self.content_type)

        if len(file_name) == 0:
            return self.render("tools/picker-error.html", error="file_name is empty")

        sha1_file_key = Sourcefile.get_sha1_file_key(file_data=response.body)
        user = self.get_current_user()
        try:
            logger.debug("Writing file %s/%s" % (options.uploaded_files, sha1_file_key))
            with open("%s/%s" % (options.uploaded_files, sha1_file_key), 'wb') as fh:
                fh.write(response.body)
        except Exception as e:
            logger.error("Error saving file %s/%s" % (options.uploaded_files, sha1_file_key))
            raise tornado.web.HTTPError(500)

        logger.debug("Creating sharedfile")
        sf = Sharedfile.create_from_file(
                file_path = "%s/%s" % (options.uploaded_files, sha1_file_key),
                file_name = file_name,
                sha1_value = sha1_file_key,
                content_type = self.content_type,
                user_id = user['id'],
                title = title,
                shake_id = shake_id,
                skip_s3 = skip_s3)
        sf.source_url = source_url
        sf.description = description
        sf.alt_text = alt_text
        logger.debug("Saving to database")
        sf.save()
        if not options.debug:
            # file cleanup
            try:
                os.remove("%s/%s" % (options.uploaded_files, sha1_file_key))
            except:
                pass
        logger.debug("Rendering picker-success.html")
        self.render("tools/picker-success.html", sf=sf)

    def on_header(self, header):
        if header.lower().startswith("content-length:"):
            content_length = re.search("content-length: (.*)", header, re.IGNORECASE)
            if int(content_length.group(1).rstrip()) > 10000000: #this is not the correct size to error on
                raise tornado.web.HTTPError(413)
        elif header.lower().startswith("content-type:"):
            ct = re.search("content-type: (.*)", header, re.IGNORECASE)
            self.content_type = ct.group(1).rstrip()


class PluginsHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self):
        return self.render("tools/plugins.html")


class ToolsTwitterHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self):
        return self.render("tools/twitter.html")


class ToolsTwitterHowToHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    def get(self):
        return self.render("tools/twitter-how-to.html")


class ToolsTwitterConnectHandler(BaseHandler, tornado.auth.TwitterMixin):
    @tornado.web.authenticated
    @require_membership
    async def get(self):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self._on_auth)
            return
        self.authorize_redirect(callback=self._on_redirect)

    def _on_redirect(self):
        pass

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Twitter auth failed")

        #is there an existing external account?
        current_user = self.get_current_user()
        authenticated_user = User.get("id=%s", current_user['id'])
        existing = Externalservice.by_user(authenticated_user, Externalservice.TWITTER)
        if existing:
            existing.service_id = user['access_token']['user_id']
            existing.service_secret = user['access_token']['secret']
            existing.service_key = user['access_token']['key']
            existing.screen_name = user['access_token']['screen_name']
            existing.save()
        else:
            external_service = Externalservice(
                                    user_id=authenticated_user.id,
                                    service_id=user['access_token']['user_id'],
                                    screen_name=user['access_token']['screen_name'],
                                    type=Externalservice.TWITTER,
                                    service_key=user['access_token']['key'],
                                    service_secret=user['access_token']['secret'])
            external_service.save()
        # if not, insert credentials for this user
        # if there is, update that account
        return self.render("tools/twitter-connected.html")

class BookmarkletPageHandler(BaseHandler):
    """Displays a page for a user to save the bookmarklet."""

    @tornado.web.authenticated
    @require_membership
    def get(self):
        return self.render("tools/bookmarklet.html", app_host=options.app_host)

class NewPostHandler(BaseHandler):
    """
    Renders a panel to kick off the new post process.
    """
    @tornado.web.authenticated
    @require_membership
    def get(self):
        user = self.get_current_user_object();
        shakes = user.shakes(include_managed=True)
        can_upload_this_month = user.can_upload_this_month()
        return self.render("tools/new-post.html", shakes=shakes, \
            can_upload_this_month=can_upload_this_month)


class SaveVideoHandler(BaseHandler):
    @tornado.web.authenticated
    @require_membership
    async def get(self):
        url = self.get_argument('url', None)
        shake_id = self.get_argument('shake_id', "")
        if not url:
            self.render("tools/save-video.html", url= url, shake_id=shake_id)
            return

        url = Sourcefile.make_oembed_url(url.strip())
        if url:
            await self.handle_oembed_url(url)
        else:
            self.render("tools/save-video-error.html", message="Invalid URL. We didn't recognize that URL")

    async def on_oembed_response(self, response):
        if response.code == 401:
            self.render("tools/save-video-error.html", message="Embedding disabled by request. The user who uploaded this file has requested it not be embedded on other web sites.")
            return
        await self.handle_oembed_data(response.body)

    async def handle_oembed_url(self, url):
        """Takes a sanitized URL (as created by models.sourcefile.make_oembed_url) and
        issues a request for it. If the URL is actually a data URI, strip off the well-known
        header, and handle the oembed JSON encoded into it instead.
        """
        if url.startswith('data:text/json;charset=utf-8,'):
            j_oembed = url.replace('data:text/json;charset=utf-8,', '', 1)
            await self.handle_oembed_data(j_oembed)
        else:
            request = HTTPRequest(url, 'GET')
            http = tornado.httpclient.AsyncHTTPClient()
            fut = http.fetch(request)
            response = await fut
            await self.on_oembed_response(response)

    async def handle_oembed_data(self, oembed):
        try:
            j_oembed = json_decode(oembed)
        except Exception as e:
            self.render("tools/save-video-error.html", message="We could not load the embed code for this file. Please contact support.")
            return

        if 'provider_name' not in j_oembed:
            self.render("tools/save-video-error.html", message="We could not load the embed code for this file. Please contact support.")
            return

        if 'type' in j_oembed and j_oembed['provider_name'] == 'Flickr' and j_oembed['type'] != 'video':
            self.render("tools/save-video-error.html", message="We could not load the embed code for this file. Please contact support.")
            return

        shake_id = self.get_argument('shake_id', "")
        url = self.get_argument('url', None)
        if j_oembed['provider_name'] == 'YouTube':
            m = re.search(r"src=\"(.*)v\/([A-Za-z0-9\-\_]+)", j_oembed['html']) or \
                re.search(r"src=\"(.*)embed\/([A-Za-z0-9\-\_]+)", j_oembed['html'])
            if m:
                url = "%swatch?v=%s" % (m.group(1), m.group(2))
                j_oembed['html'] = """<iframe class="youtube-player"
                type="text/html" width="%s" height="%s"
                src="https://www.youtube.com/embed/%s?fs=1&feature=oembed&rnd=%s"
                frameborder="0" id="ytframe" allowfullscreen></iframe>""" % (550, 339, m.group(2), str(random.random()))
            else:
                self.render("tools/save-video-error.html", message="We could not load the embed code for this file. Please contact support.")
                return
        elif j_oembed['provider_name'] == "Flickr":
            pass  # trust the thumbnail_url in the oembed

        if self.request.method == "POST":
            self.oembed_doc = j_oembed
            request = HTTPRequest(self.oembed_doc['thumbnail_url'], 'GET')
            http = tornado.httpclient.AsyncHTTPClient()
            fut = http.fetch(request)
            response = await fut
            self.on_thumbnail_response(response)
        else:
            self.render("tools/save-video.html", url=url, html=j_oembed['html'], shake_id=shake_id)

    def on_thumbnail_response(self, response):
        if response.code != 200:
            self.render("tools/save-video-error.html", message="We could not load the thumbnail for this file and therefore could not save this video. Please contact support.")
            return

        # save the response
        url = self.get_argument('url')
        current_user = self.get_current_user_object()

        sha1_key = Sourcefile.get_sha1_file_key(file_path=None, file_data=url)
        thumbnail_path = "%s/%s" % (options.uploaded_files, sha1_key)
        with open(thumbnail_path, 'wb') as fh:
            fh.write(response.body)
        source_file = Sourcefile.create_from_json_oembed(
            link=url, oembed_doc=self.oembed_doc, thumbnail_file_path=thumbnail_path,
            skip_s3=self.get_argument('skip_s3', None))
        #cleanup
        if not options.debug:
            try:
                os.remove(thumbnail_path)
            except:
                pass

        title = ''
        if 'title' in self.oembed_doc:
            title = self.oembed_doc['title']

        shared_file = Sharedfile(user_id=current_user.id, name=url, content_type='text/html', source_id=source_file.id, title=title, source_url=url)
        shared_file.save()

        share_key = base36encode(shared_file.id)
        shared_file.share_key = share_key
        shared_file.save()

        user_shake = Shake.get('user_id = %s and type=%s', current_user.id, 'user')
        shared_file.add_to_shake(self.destination_shake)

        if 'description' in self.oembed_doc:
            shared_file.description = self.oembed_doc['description']

        self.write({'path' : "/p/%s" % (share_key)})
        self.finish()

    @tornado.web.authenticated
    @require_membership
    async def post(self):
        url = self.get_argument('url', None)
        if not url:
            self.render("tools/save-video.html", url = url, title = None, description=None)
        url = Sourcefile.make_oembed_url(url.strip())
        if url:
            current_user = self.get_current_user_object();
            shake_id = self.get_argument('shake_id', None)
            if not shake_id:
                self.destination_shake = Shake.get('user_id=%s and type=%s', current_user.id, 'user')
            else:
                self.destination_shake = Shake.get('id=%s', shake_id)
                if not self.destination_shake:
                    return self.render("tools/save-video-error.html", message="We couldn't save the video to specified shake. Please contact support.")
                if not self.destination_shake.can_update(current_user.id):
                    return self.render("tools/save-video-error.html", message="We couldn't save the video to specified shake. Please contact support.")
                if current_user.email_confirmed != 1:
                    return self.render("tools/save-video-error.html", message="You must confirm your email address before you can post.")
            await self.handle_oembed_url(url)
        else:
            self.render("tools/save-video-error.html", message="We could not load the embed code. The video server may be down. Please contact support.")


class FindShakesGroups(BaseHandler):
    """
    path: /tools/find-shakes

    Returns a list of recommended group shakes.
    """
    @tornado.web.authenticated
    @require_membership
    def get(self):
        user = self.get_current_user_object()
        categories = ShakeCategory.all('ORDER BY name')
        users_sidebar = User.recommended_for_user(user)
        featured_shakes = Shake.featured_shakes(3)
        return self.render('tools/find-shakes.html', current_user_obj=user,
                            users_sidebar=users_sidebar, categories=categories,
                            featured_shakes=featured_shakes)


class FindShakesPeople(BaseHandler):
    """
    path: /tools/find-shakes/people

    Returns a list of recommended users.
    """
    @tornado.web.authenticated
    @require_membership
    def get(self):
        user = self.get_current_user_object()
        users = User.random_recommended(limit=30)
        users_sidebar = User.recommended_for_user(user)
        return self.render('tools/find-shakes-people.html', current_user_obj=user, users=users, users_sidebar=users_sidebar)


class FindShakesQuickFetchCategory(BaseHandler):

    @tornado.web.authenticated
    @require_membership
    def get(self, name):
        category = ShakeCategory.get("short_name = %s", name)
        if not category:
            raise tornado.web.HTTPError(404)

        user = self.get_current_user_object()
        shakes = Shake.for_category(category)
        return self.render("tools/find-shakes-quick-fetch-category.html",
                            shakes=shakes, current_user_obj=user)
