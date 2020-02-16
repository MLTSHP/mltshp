from datetime import datetime
import time
from urllib import urlencode
from urlparse import urlparse, urlunparse, urljoin
from hashlib import sha1
import hmac
import base64
import functools

import tornado.web
from tornado.options import define, options

from base import BaseHandler
from lib.utilities import normalize_string, base36decode
from models import Accesstoken, Apihit, Apilog, App, Authorizationcode, \
    Favorite, Magicfile, Sharedfile, User, Shake, Comment


def oauth2authenticated(method):
    """Decorate methods with this to require that requests be hmac-sha-1 signed"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        #break up header and get access token, timestamp, nonce
        auth_items = {}
        if self.request.headers.get('Authorization'):
            try:
                h = self.request.headers.get('Authorization').replace('MAC ', '')
                auth_items = dict(item.split('=', 1) for item in h.replace('"', '').split(', '))
            except:
                self.set_status(401)
                self.set_header('WWW-Authenticate', 'MAC realm="mltshp" error="invalid_token", error_description="Cannot parse token."')
                self.finish()
                return

            try:
                access_token_str = auth_items['token']
            except KeyError:
                self.set_status(401)
                self.set_header('WWW-Authenticate', 'MAC realm="mltshp" error="invalid_token", error_description="Missing token."')
                self.finish()
                return
            access_token = Accesstoken.get('consumer_key = %s and deleted=0', access_token_str)

            if not access_token:
                self.set_status(401)
                self.set_header('WWW-Authenticate', 'MAC realm="mltshp" error="invalid_token", error_description="Invalid access token."')
                self.finish()
                return

            api_log = Apilog.get('accesstoken_id=%s and nonce=%s', access_token.id, auth_items['nonce'])
            if api_log:
                self.set_status(401)
                self.set_header('WWW-Authenticate', 'MAC realm="mltshp" error="invalid_token", error_description="Duplicate nonce."')
                self.finish()
                return
            else:
                api_log = Apilog(accesstoken_id=access_token.id, nonce=auth_items['nonce'])
                api_log.save()

            timestamp = int(auth_items['timestamp'])
            nowstamp =  int(time.mktime(datetime.utcnow().timetuple()))
            if (nowstamp - timestamp) > 30:
                self.set_status(401)
                self.set_header('WWW-Authenticate', 'MAC realm="mltshp" error="invalid_token", error_description="Token is expired."')
                self.finish()
                return

            hits_per_hour = options.api_hits_per_hour
            if hits_per_hour is not None:
                hits = Apihit.hit(access_token.id)
                #raise ValueError("YESSSS %d HITS PER HOUR AND %d HITS WHAT" % (hits_per_hour, hits))
                self.set_header('X-RateLimit-Limit', str(hits_per_hour))
                self.set_header('X-RateLimit-Reset', str(nowstamp % 3600 + 3600))
                if hits >= hits_per_hour:
                    self.set_status(400)
                    self.set_header('X-RateLimit-Remaining', '0')
                    self.finish()
                    return
                self.set_header('X-RateLimit-Remaining', hits_per_hour - hits)

            parsed_url = urlparse(self.request.full_url())
            query_array = []
            if parsed_url.query:
                query_array += parsed_url.query.split('&')
            for i in range(len(query_array)):
                if query_array[i].find('=') == -1:
                    query_array[i] += '='
            query_array.sort()
            port = 80
            if not parsed_url.port:
                if parsed_url.scheme == 'https':
                    port = 443
            elif parsed_url.port:
                port = parsed_url.port

            normalized_string = normalize_string(auth_items['token'],
                auth_items['timestamp'],
                auth_items['nonce'],
                self.request.method,
                parsed_url.hostname,
                port,
                parsed_url.path,
                query_array)

            digest = hmac.new(access_token.consumer_secret.encode('ascii'), normalized_string, sha1).digest()
            signature = base64.encodestring(digest).strip()

            if signature == auth_items['signature']:
                self.oauth2_user_id = access_token.user_id
                return method(self, *args, **kwargs)
            else:
                self.set_status(401)
                self.set_header('WWW-Authenticate', 'MAC realm="mltshp" error="invalid_token", error_description="Signature doesn\'t match."')
                self.write("NORMALIZED STRING: \n")
                self.write(normalized_string)
                self.write('-----\n')
                self.write('MY SIGNATURE\n')
                self.write(signature)
                self.write('\nYOUR SIGNATURE\n')
                self.write(auth_items['signature'])
                self.finish()
                return
        else:
            self.set_status(401)
            self.set_header('WWW-Authenticate','Basic realm="mltshp"')
            self.finish()
    return wrapper


class AuthorizeHandler(BaseHandler):

    def check_xsrf_cookie(self):
        return

    def redirect_with_params(self, redirect_url, **kwargs):
        urlparts = urlparse(redirect_url)
        if urlparts.query:
            query = '&'.join((urlparts.query, urlencode(kwargs)))
        else:
            query = urlencode(kwargs)
        full_url = urlunparse((urlparts.scheme, urlparts.netloc, urlparts.path, urlparts.params, query, urlparts.fragment))

        return self.redirect(full_url)

    @tornado.web.authenticated
    def get(self):
        response_type = self.get_argument('response_type', None)

        client_id = self.get_argument('client_id', None)
        app = App.by_key(client_id)

        if app:
            redirect_url = self.get_argument('redirect_uri', None)
            if redirect_url and app.redirect_url:
                # The specified redirect must match the app's existing redirect.
                redirect_parts = urlparse(redirect_url)
                app_parts = urlparse(app.redirect_url)
                if (redirect_parts.scheme != app_parts.scheme or redirect_parts.netloc != app_parts.netloc
                    or not redirect_parts.path.startswith(app_parts.path)):
                    raise tornado.web.HTTPError(400)
            elif not redirect_url and not app.redirect_url:
                # One or the other is required.
                raise tornado.web.HTTPError(400)
            elif not redirect_url:
                redirect_url = app.redirect_url

            if response_type == 'code': # VALID REQUEST
                return self.render('api/authorize.html', app=app, client_id=client_id, redirect_url=redirect_url)
            elif response_type == None or response_type == '': #INVALID REQUEST (Response type is blank)
                if redirect_url:
                    return self.redirect_with_params(redirect_url, error='invalid_request')
            else: # UNSUPPORTED RESPONSE TYPE (Not known)
                if redirect_url:
                    return self.redirect_with_params(redirect_url, error='unsupported_response_type')
        else: # APP DOES NOT EXIST
            redirect_url = self.get_argument('redirect_uri', None)
            if redirect_url:
                return self.redirect_with_params(redirect_url, error='invalid_client')

        #all else fails
        raise tornado.web.HTTPError(404)

    @tornado.web.authenticated
    def post(self):
        app = App.by_key(self.get_argument('client_id', '-'))
        current_user = self.get_current_user_object()

        redirect_url = self.get_argument('redirect_uri', app.redirect_url)
        agree_flag = self.get_argument('agree', None)
        if agree_flag == None or agree_flag == '0':
            return self.redirect_with_params(redirect_url, error='access_denied')
        else:
            auth_code = Authorizationcode.generate(app.id, redirect_url, current_user.id)
            return self.redirect_with_params(redirect_url, code=auth_code.code)


class TokenHandler(BaseHandler):

    def check_xsrf_cookie(self):
        return

    def post(self):
        grant_type = self.get_argument('grant_type', None)
        code = self.get_argument('code', None)
        redirect_url = self.get_argument('redirect_uri', None)
        client_secret = self.get_argument('client_secret', None)
        client_id = self.get_argument('client_id', None)
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)


        if not grant_type or not client_id or not client_secret:
            self.set_status(400)
            return self.write({'error':'invalid_request',
                'error_description': "The grant_type, client_id, and client_secret parameters are required."})

        if grant_type == 'password':
            pass
        elif grant_type == 'authorization_code':
            if not code or not redirect_url:
                self.set_status(400)
                return self.write({'error':'invalid_request',
                    'error_description': "The code and redirect_url parameters are required."})
        else:
            self.set_status(401)
            return self.write({'error':'invalid_grant'})


        app = App.by_key(client_id)
        if not app:
            self.set_status(401)
            return self.write({'error':'invalid_client'})

        if app.secret != client_secret:
            self.set_status(401)
            return self.write({'error':'access_denied'})

        auth_code = None
        if grant_type == 'password':
            #generating one in one fell swoop.
            #if user password match then make an auth_code
            check_user = User.authenticate(username, password)
            if check_user:
                auth_code = Authorizationcode.generate(app_id=app.id, redirect_url=app.redirect_url, user_id=check_user.id)
            else:
                self.set_status(401)
                return self.write({'error':'invalid_request'})
        else:
            auth_code = Authorizationcode.get("code = %s and redirect_url = %s  and expires_at > %s", code, redirect_url, datetime.utcnow())

        if auth_code:
            self.set_header("Cache-Control", "no-store")
            access_token = Accesstoken.generate(auth_code.id)
            if access_token:
                response =  {
                       "access_token":access_token.consumer_key,
                       "secret":access_token.consumer_secret,
                       "token_type":"mac",
                       "algorithm":"hmac-sha-1"
                       }
                return self.write(response)
            else:
                self.set_status(401)
                return self.write({'error':'invalid_grant'})
        else:
            self.set_status(401)
            return self.write({'error':'invalid_grant'})


class SharedfileHandler(BaseHandler):

    def check_xsrf_cookie(self):
        return

    @oauth2authenticated
    def post(self, share_key):
        user = User.get('id=%s', self.oauth2_user_id)
        sf = Sharedfile.get_by_share_key(share_key)

        if not sf:
            self.set_status(404)
            return self.write({'error': 'No such file.'})

        if not sf.can_edit(user):
            self.set_status(403)
            return self.write({'error' : "No permission to edit this file."})

        if self.get_argument('title', None):
            sf.title = self.get_argument('title', None)
            sf.save()
        if self.get_argument('description', None):
            sf.description = self.get_argument('description', None)
            sf.save()

        return self.write(sf.as_json(user_context=user))

    @oauth2authenticated
    def get(self, share_key):
        user = User.get('id=%s', self.oauth2_user_id)
        sf = Sharedfile.get_by_share_key(share_key)

        if not sf:
            self.set_status(404)
            return self.write({'error': 'No such file.'})
        return self.write(sf.as_json(user_context=user))


class SharedfileLikeHandler(BaseHandler):

    def check_xsrf_cookie(self):
        return

    @oauth2authenticated
    def post(self, sharedfile_key):
        user = User.get('id=%s', self.oauth2_user_id)

        sharedfile = Sharedfile.get_by_share_key(sharedfile_key)
        if not sharedfile:
            self.set_status(404)
            return self.write({'error': 'No such file.'})

        original_sf = sharedfile.original()
        parent_sf = sharedfile.parent()
        if original_sf and not original_sf.deleted:
            user.add_favorite(original_sf)
        if parent_sf and not parent_sf.deleted and parent_sf.user_id != original_sf.user_id:
            user.add_favorite(parent_sf)

        if not user.add_favorite(sharedfile):
            self.set_status(400)
            return self.write({'error': 'Could not like the image (probably already liked)'})

        return self.write(sharedfile.as_json(user_context=user))

class SharedfileSaveHandler(BaseHandler):

    def check_xsrf_cookie(self):
        return

    @oauth2authenticated
    def post(self, sharedfile_key):
        user = User.get('id=%s', self.oauth2_user_id)

        sharedfile = Sharedfile.get_by_share_key(sharedfile_key)
        if not sharedfile:
            self.set_status(404)
            return self.write({'error': 'No such file.'})

        if not sharedfile.can_save(user):
            self.set_status(400)
            return self.write({'error' : "Can't save own file."})

        shake = None
        count = sharedfile.save_count
        shake_id = self.get_argument('shake_id', None)
        if shake_id:
            shake = Shake.get("id = %s", shake_id)
            if not shake:
                self.set_status(404)
                return self.write({'error' : "No such shake."})

        if shake and not shake.can_update(user.id):
            self.set_status(403)
            return self.write({'error' : "No permission to save to shake."})

        already_saved = user.saved_sharedfile(sharedfile)
        if already_saved:
            return self.write(sharedfile.as_json(user_context=user))

        new_sharedfile = sharedfile.save_to_shake(user, shake)
        sharedfile_json = sharedfile.as_json(user_context=user)
        sharedfile_json['saves'] = count + 1
        return self.write(sharedfile_json)


class SharedfilesCommentsHandler(BaseHandler):

    def check_xsrf_cookie(self):
        return

    @oauth2authenticated
    def get(self, sharedfile_key):
        user = User.get('id = %s', int(self.oauth2_user_id))
        sharedfile = Sharedfile.get_by_share_key(sharedfile_key)
        if not sharedfile:
            self.set_status(404)
            return self.write({'error': 'No such file.'})

        comments = []
        for comment in sharedfile.comments():
            comments.append(comment.as_json())

        return self.write({'comments': comments})

    @oauth2authenticated
    def post(self, sharedfile_key):
        user = User.get('id = %s', int(self.oauth2_user_id))
        sharedfile = Sharedfile.get_by_share_key(sharedfile_key)
        if not sharedfile:
            self.set_status(404)
            return self.write({'error': 'No such file.'})

        body = self.get_argument('body', None)
        comment = Comment.add(user=user, sharedfile=sharedfile, body=body)
        if not comment:
            self.set_status(400)
            return self.write({'error': 'Could not save comment'})
        return self.write(comment.as_json())

class UserHandler(BaseHandler):

    @oauth2authenticated
    def get(self, type, resource=''):
        if type == 'user_name':
            u = User.get('name=%s', resource)
        elif type == 'user_id':
            u = User.get('id=%s', resource)
        elif type == 'user':
            u = User.get('id=%s', self.oauth2_user_id)
        return self.write(u.as_json(extended=True))


class UserShakesHandler(BaseHandler):

    def check_xsrf_cookie(self):
        return

    @oauth2authenticated
    def get(self):
        user = User.get('id=%s', self.oauth2_user_id)
        obj = { 'shakes' : [] }
        for shake in user.shakes(include_managed=True):
            obj['shakes'].append(shake.as_json(extended=True))
        return self.write(obj)


class ShakeHandler(BaseHandler):

    def check_xsrf_cookie(self):
        return

    @oauth2authenticated
    def get(self, type, resource=''):
        shake = None
        if type == 'shake_path':
            shake = Shake.get('path=%s and deleted=0', resource)
        elif type == 'shake_id':
            shake = Shake.get('id=%s and deleted=0', resource)

        if not shake:
            self.set_status(404)
            return self.write({'error' : "No such shake."})

        return self.write(shake.as_json(extended=True))


class FileUploadHandler(BaseHandler):

    def check_xsrf_cookie(self):
        return

    @oauth2authenticated
    def post(self):
        obj = {}
        user = User.get('id=%s', self.oauth2_user_id)
        if user is None:
            obj = {'error': 'Invalid user'}
        elif user.email_confirmed != 1:
            obj = {'error': 'User\'s email address is unconfirmed'}
        elif self.get_argument("file_name", None):
            try:
                sf = Sharedfile.create_from_file(
                    file_path = self.get_argument("file_path"),
                    file_name = self.get_argument("file_name"),
                    sha1_value = self.get_argument("file_sha1"),
                    content_type = self.get_argument("file_content_type"),
                    user_id = self.oauth2_user_id,
                    shake_id = self.get_argument('shake_id', None))
                obj['name'] = sf.name
                obj['share_key'] = sf.share_key
                if self.get_argument('title', None):
                    sf.title = self.get_argument('title', None)
                    sf.save()
                if self.get_argument('description', None):
                    sf.description = self.get_argument('description', None)
                    sf.save()
            except:
                obj = {'error':'Error processing file.'}
        else:
            obj = {'error':'No file received.'}
        return self.write(obj)


class FriendShakeHandler(BaseHandler):

    @oauth2authenticated
    def get(self, before_or_after=None, base36_id=None):
        sharedfile_id = None
        if base36_id:
            sharedfile_id = base36decode(base36_id)

        before_id, after_id = None, None
        if sharedfile_id and before_or_after == 'before':
            before_id = sharedfile_id
        elif sharedfile_id and before_or_after == 'after':
            after_id = sharedfile_id

        user = User.get('id=%s', int(self.oauth2_user_id))

        if before_id:
            shared_files = user.sharedfiles_from_subscriptions(before_id=before_id)
        elif after_id:
            shared_files = user.sharedfiles_from_subscriptions(after_id=after_id)
        else:
            shared_files = user.sharedfiles_from_subscriptions()

        obj = {'friend_shake':[]}
        for sf in shared_files:
            sharedfile_user = sf.user()
            fileobj = sf.as_json(user_context=user)
            obj['friend_shake'].append(fileobj)
        return self.write(obj)


class MagicfilesHandler(BaseHandler):

    @oauth2authenticated
    def get(self, before_or_after=None, magicfile_id=None):
        user = User.get('id = %s', int(self.oauth2_user_id))

        if before_or_after == 'before':
            magicfiles = Magicfile.sharedfiles_paginated(before_id=magicfile_id)
        elif before_or_after == 'after':
            magicfiles = Magicfile.sharedfiles_paginated(after_id=magicfile_id)
        else:
            magicfiles = Magicfile.sharedfiles_paginated()

        magical = []
        for sf in magicfiles:
            sf_dict = sf.as_json(user_context=user)
            sf_dict['pivot_id'] = str(sf.magicfile_id)
            magical.append(sf_dict)

        return self.write({'magicfiles': magical})


class FavoritesHandler(BaseHandler):

    @oauth2authenticated
    def get(self, before_or_after=None, favorite_id=None):
        user = User.get('id = %s', int(self.oauth2_user_id))

        # Make sure we don't error if an old client is still
        # trying to use sharekey (alphanumeric) to paginate.
        if favorite_id and not favorite_id.isdigit():
            favorite_id = None

        if before_or_after == 'before':
            sharedfiles = user.likes(before_id=favorite_id)
        elif before_or_after == 'after':
            sharedfiles = user.likes(after_id=favorite_id)
        else:
            sharedfiles = user.likes()

        favorites = []
        for sf in sharedfiles:
            sf_dict = sf.as_json(user_context=user)
            sf_dict['pivot_id'] = str(sf.favorite_id)
            favorites.append(sf_dict)

        return self.write({'favorites': favorites})


class IncomingHandler(BaseHandler):

    @oauth2authenticated
    def get(self, before_or_after=None, pivot_id=None):
        user = User.get('id = %s', int(self.oauth2_user_id))

        if before_or_after == 'before':
            sharedfiles = Sharedfile.incoming(before_id=pivot_id)
        elif before_or_after == 'after':
            sharedfiles = Sharedfile.incoming(after_id=pivot_id)
        else:
            sharedfiles = Sharedfile.incoming()

        incoming = []
        for sf in sharedfiles:
            sf_dict = sf.as_json(user_context=user)
            sf_dict['pivot_id'] = str(sf.id)
            incoming.append(sf_dict)

        return self.write({'incoming': incoming})

class ShakeStreamHandler(BaseHandler):

    @oauth2authenticated
    def get(self, id_, before_or_after=None, base36_id=None):
        user = User.get('id = %s', int(self.oauth2_user_id))
        shake = Shake.get('id = %s', id_)
        sharedfile_id = base36decode(base36_id) if base36_id else None

        if before_or_after == 'before':
            sharedfiles = shake.sharedfiles_paginated(max_id=sharedfile_id,per_page=10)
        elif before_or_after == 'after':
            sharedfiles = shake.sharedfiles_paginated(since_id=sharedfile_id,per_page=10)
        else:
            sharedfiles = shake.sharedfiles_paginated(per_page=10)

        sharedfiles_output = []
        for sf in sharedfiles:
            sf_dict = sf.as_json(user_context=user)
            sharedfiles_output.append(sf_dict)

        return self.write({'sharedfiles': sharedfiles_output})
