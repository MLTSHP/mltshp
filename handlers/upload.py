from .base import BaseHandler, require_membership

import tornado.httpclient
from tornado.httpclient import HTTPRequest
import tornado.web
from tornado.options import options
import tornado.escape

from models import Sharedfile, Externalservice

class UploadHandler(BaseHandler):
    """
    We allow people posting without a user and with the correct OAUTH Echo header
    """
    def check_xsrf_cookie(self): 
        user = self.get_current_user()
        if 'X-Verify-Credentials-Authorization' in self.request.headers and not user:
            return
        else:
            super(UploadHandler, self).check_xsrf_cookie()
    
    @require_membership
    async def post(self):
        """
        {
            "file_name": ["before.png"], 
            "file_content_type": ["image/png"], 
            "file_sha1": ["31fb1023a1bc194a8e2df99b1d14125e3d084f0d"], 
            "_xsrf": ["bf61ab9cbbfb43bdb8b7746cb4862336"], 
            "file_size": ["33059"], 
            "file_path": ["/tmp/9/0004701669"]
        }
        """
        user = self.get_current_user_object()
        if user:
            if self.get_argument("file_name", None):
                content_type = self.get_argument("file_content_type")
                if user.email_confirmed != 1:
                    error_type = 'email_unconfirmed'
                    return self.render('upload/error.html', error_type=error_type)
                if not user.can_upload_this_month():
                    error_type = 'upload_limit'
                    return self.render('upload/error.html', error_type=error_type)

                if content_type not in self.approved_content_types:
                    error_type = 'content_type'
                    return self.render('upload/error.html', error_type=error_type)
                
                shake_id = self.get_argument('shake_id', None)

                sf = Sharedfile.create_from_file(
                    file_path = self.get_argument("file_path"), 
                    file_name = self.get_argument("file_name"), 
                    sha1_value = self.get_argument("file_sha1"),
                    content_type = self.get_argument("file_content_type"),
                    user_id = user.id,
                    shake_id=shake_id,
                    skip_s3=self.get_argument('skip_s3', None))
                if sf is not None:
                    return self.redirect("/p/%s" % (sf.share_key))
                else:
                    raise tornado.web.HTTPError(403)
            else:
                return self.redirect("/")
        elif 'X-Verify-Credentials-Authorization' in self.request.headers and 'X-Auth-Service-Provider' in self.request.headers:
            #pm = postmark.PMMail(api_key=options.postmark_api_key,
            #    sender="hello@mltshp.com", to="notifications@mltshp.com", 
            #    subject="TWITTER REQUEST",
            #    text_body=str(self.request.headers.__dict__)+ '\n' + str(self.request.body))
            #pm.send()

            if self.request.headers['X-Auth-Service-Provider'].startswith("https://api.twitter.com/1.1/account/verify_credentials.json") or self.request.headers['X-Auth-Service-Provider'].startswith("http://localhost:"):
                http = tornado.httpclient.AsyncHTTPClient()
                fut = http.fetch(
                    HTTPRequest(
                        url=self.request.headers['X-Auth-Service-Provider'], 
                        method='GET',
                        headers={'Authorization':self.request.headers['X-Verify-Credentials-Authorization']},
                        body=None #"asdf=asdf" -- GET requests can't have a body
                    ),
                )
                response = await fut
                self.on_response(response)
            else:
                raise tornado.web.HTTPError(403)
        else:
            raise tornado.web.HTTPError(403)

    def on_response(self, response):
        #pm = postmark.PMMail(api_key=options.postmark_api_key,
        #    sender="hello@mltshp.com", to="notifications@mltshp.com", 
        #    subject="TWITTER RESPONSE",
        #    text_body=str(response.__dict__))
        #pm.send()

        if response.code == 200:
            j_body = tornado.escape.json_decode(response.body)
            external_service = Externalservice.get("service_id = %s and screen_name = %s", j_body['id'], j_body['screen_name'])
            if not external_service:
                raise tornado.web.HTTPError(403)
            title = self.get_argument("message", None)
            if title:
                title = title.replace('\n', '')
                title = title.replace('\r', '')
                
            sf = Sharedfile.create_from_file(
                file_path = self.get_argument("media_path"), 
                file_name = self.get_argument("media_name"), 
                sha1_value = self.get_argument("media_sha1"),
                content_type = self.get_argument("media_content_type"),
                user_id = external_service.user_id,
                title = title
                )
            media_type = self.get_argument("media_content_type").split('/')[1]
            media_type = tornado.escape.xhtml_escape(media_type)
            self.write("<mediaurl>https://s.%s/r/%s.%s</mediaurl>" % (options.app_host, sf.share_key, media_type))
            return self.finish()
        raise tornado.web.HTTPError(403)

