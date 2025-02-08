from tornado.escape import url_escape, json_decode
from tornado.options import options
from tornado.httpclient import HTTPRequest

import time
import json
import os
from urllib.parse import urlparse
from contextlib import contextmanager

from .base import BaseAsyncTestCase

from models import Sharedfile, Sourcefile, User, Shakesharedfile, Post
from lib.utilities import base36encode


@contextmanager
def test_option(optname, value):
    old_value = getattr(options, optname)
    setattr(options, optname, value)
    yield
    setattr(options, optname, old_value)


class FileDeleteTests(BaseAsyncTestCase):
    def setUp(self):
        super(FileDeleteTests, self).setUp()

        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()

        self.sid = self.sign_in("admin", "asdfasdf")
        self.xsrf = self.get_xsrf().decode("ascii")

        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path)
        self.test_file1_content_type = "image/png"

        self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)

    def test_deleting_file_sets_to_true(self):
        response = self.post_url("/p/1/delete")

        sf = Sharedfile.get("id=1")
        self.assertEqual(sf.deleted, 1)

    def test_delete_button_only_shows_for_owner(self):
        bill = User(name='bill', email='bill@mltshp.com', email_confirmed=1, is_paid=1)
        bill.set_password('asdfasdf')
        bill.save()

        self.sign_in("bill", "asdfasdf")
        response = self.fetch("/p/1", method='GET', headers={'Cookie':'sid=%s' % self.sid})
        self.assertEqual(response.body.find('/p/1/delete'.encode("ascii")), -1)

        self.sign_in("admin", "asdfasdf")
        response = self.fetch("/p/1", method='GET', headers={'Cookie':'sid=%s' % self.sid})
        self.assertIn('/p/1/delete', response.body)

    def test_delete_button_only_works_for_owner(self):
        bill = User(name='bill', email='bill@mltshp.com', email_confirmed=1, is_paid=1)
        bill.set_password('asdfasdf')
        bill.save()
        sid = self.sign_in("bill", "asdfasdf")

        response = self.post_url("/p/1/delete")

        sf = Sharedfile.get("id=1")
        self.assertEqual(sf.deleted, 0)


class FileViewTests(BaseAsyncTestCase):
    def setUp(self):
        super(FileViewTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()

        self.user2 = User(name='user', email='user@mltshp.com', email_confirmed=1, is_paid=1)
        self.user2.set_password('asdfasdf')
        self.user2.save()

        self.sid2 = self.sign_in('user', 'asdfasdf')

        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf().decode("ascii")

        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path)
        self.test_file1_content_type = "image/png"

        self.test_file2_path = os.path.abspath("test/files/love.gif")
        self.test_file2_sha1 = Sourcefile.get_sha1_file_key(self.test_file2_path)
        self.test_file2_content_type = "image/gif"

    def test_raw_image_view_counts(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
        response = self.fetch('/user/admin', method='GET', headers={"Cookie":"sid=%s" % self.sid2})
        self.assertIn("1.png", response.body)

        for i in range(0,10):
            if i % 2 == 0:
                response = self.fetch('/r/1', method='GET', headers={"Cookie":"sid=%s" % self.sid2})
            else:
                response = self.fetch('/r/1', method='GET')

        imageviews = self.db.query("SELECT id, user_id, sharedfile_id, created_at from fileview")
        self.assertEqual(len(imageviews), 10)

        imageviews = self.db.query("SELECT id, user_id, sharedfile_id, created_at from fileview WHERE user_id = 0")
        self.assertEqual(len(imageviews), 5)

    def test_raw_load_with_extension(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
        response = self.fetch('/user/admin', method='GET', headers={"Cookie":"sid=%s" % self.sid2})
        self.assertIn("1.png", response.body)

        for i in range(0,10):
            if i % 2 == 0:
                response = self.fetch('/r/1.jpg', method='GET', headers={"Cookie":"sid=%s" % self.sid2})
            else:
                response = self.fetch('/r/1.jpg', method='GET')

        imageviews = self.db.query("SELECT id, user_id, sharedfile_id, created_at from fileview")
        self.assertEqual(len(imageviews), 10)

        imageviews = self.db.query("SELECT id, user_id, sharedfile_id, created_at from fileview WHERE user_id = 0")
        self.assertEqual(len(imageviews), 5)

    def test_delete_image_raw_404s(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)

        sf = Sharedfile.get("id=1")
        self.assertEqual("1.png", sf.name)
        sf.delete()

        response = self.fetch('/r/%s' % sf.share_key)
        self.assertEqual(response.error.code, 404)

    def test_raw_head_handler(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)

        sf = Sharedfile.get("id=1")
        self.assertEqual("1.png", sf.name)

        response = self.fetch('/r/%s' % sf.share_key, method='HEAD')
        self.assertEqual(response.headers['Content-Type'], 'image/png')
        self.assertEqual(response.body, b'')

    def test_delete_image_permalink_404s(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
        sf = Sharedfile.get("id=1")
        self.assertEqual("1.png", sf.name)
        sf.delete()

        response = self.fetch(sf.post_url(relative=True), follow_redirects=False)
        self.assertEqual(response.error.code, 404)


class SharedFileTests(BaseAsyncTestCase):
    def setUp(self):
        super(SharedFileTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf().decode("ascii")

        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path)
        self.test_file1_content_type = "image/png"

        self.test_file2_path = os.path.abspath("test/files/love.gif")
        self.test_file2_sha1 = Sourcefile.get_sha1_file_key(self.test_file2_path)
        self.test_file2_content_type = "image/gif"

    def test_oembed_response_json(self):
        with test_option("cdn_host", "cdn-service.com"), test_option("app_host", "my-mltshp.com"):
            response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
            response = self.fetch("/services/oembed?url=http%3A//my-mltshp.com/p/1")
            j = json.loads(response.body)
            self.assertEqual(j['width'], 1)
            self.assertEqual(j['height'], 1)
            self.assertEqual(j['title'], '1.png')
            # pattern from oembed.json is...
            #    https://{{ cdn_host }}/r/{{sharedfile.share_key}}
            self.assertEqual(j['url'], 'https://cdn-service.com/r/1')

        #test jsonp callback works
        sharedfile = Sharedfile.get('id = %s', 1)
        file_time_stamp = int(time.mktime(sharedfile.created_at.timetuple()))
        callback = "jsonp" + str(file_time_stamp)
        with test_option("app_host", "my-mltshp.com"):
            response = self.fetch("/services/oembed?url=http%3A//my-mltshp.com/p/1&jsoncallback=" + callback)

        j = json.loads(response.body.strip()[len(callback)+1:-1])
        self.assertEqual(j['callback'], callback)
        self.assertTrue(response.body.startswith(callback.encode("ascii")))

    def test_oembed_response_json_for_link(self):
        url = 'https://vimeo.com/20379529'
        sourcefile = Sourcefile(width=100, height=100, data="{'junk':'here'}", type='link', file_key="asdfasdfasdfasdfasdf")
        sourcefile.save()

        sharedfile = Sharedfile(source_id=sourcefile.id, user_id=self.user.id, name=url, title="Some Title", source_url=url, content_type='text/html')
        sharedfile.save()
        sharedfile.share_key = base36encode(sharedfile.id)
        sharedfile.save()
        sharedfile = Sharedfile.get('id = %s', 1)
        file_time_stamp = int(time.mktime(sharedfile.created_at.timetuple()))
        with test_option("app_host", "my-mltshp.com"):
            response = self.fetch("/services/oembed?url=http%3A//my-mltshp.com/p/1")
        j_response = json_decode(response.body)
        self.assertEqual(j_response['type'], "link")
        self.assertEqual(j_response['url'], url)

    def test_oembed_malformed_requests(self):
        malformed_requests = ['http%3A//mltshp.com/p', 'http%3A//mltshp.com/p/', 'http%3A//mltshp.com/', 'http%3A//mltshp.com/r/1', 'NaN', 'http%3A//cnn.com/p/1']
        for request in malformed_requests:
            response = self.fetch("/services/oembed?url=%s" % request)
            self.assertEqual(response.code, 404)

    def test_title_pulls_from_name_if_blank_or_null(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
        sf = Sharedfile.get("id = %s", 1)
        self.assertEqual(sf.get_title(), "1.png")

    def test_quick_edit_title(self):
        self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
        response = self.post_url('/p/1/quick-edit-title', arguments={"title": "Monkey Business"})
        j = json_decode(response.body)
        self.assertEqual(j['title'], 'Monkey Business')

    def test_quick_edit_description(self):
        self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
        response = self.post_url('/p/1/quick-edit-description', arguments={"description": "Bilbo\nbaggins"})
        j = json_decode(response.body)
        self.assertEqual(j['description_raw'], 'Bilbo\nbaggins')

    def test_quick_edit_alt_text(self):
        self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
        response = self.post_url('/p/1/quick-edit-alt-text', arguments={"alt_text": 'A small person carrying a ring'})
        j = json_decode(response.body)
        self.assertEqual(j['alt_text_raw'], 'A small person carrying a ring')

    def test_quick_edit_source_url(self):
        self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
        response = self.post_url('/p/1/quick-edit-source-url', arguments={"source_url": 'http://www.example.com/'})
        j = json_decode(response.body)
        self.assertEqual(j['source_url'], 'http://www.example.com/')


class VideoPickerTests(BaseAsyncTestCase):
    def setUp(self):
        super(VideoPickerTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.user_shake = self.user.shake()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf().decode("ascii")

    def test_save_video_allows_link_to_vimeo_youtube(self):
        video_sites = {'vimeo':'https://vimeo.com/20379529', 'youtube':'https://www.youtube.com/watch?v=EmcMG4uxiHk', 'flickr':'https://www.flickr.com/photos/dahliablack/5497635343/'}
        for site in list(video_sites.keys()):
            response = self.fetch('/tools/save-video?url=%s' % (url_escape(video_sites[site])), method='GET', headers={"Cookie":"sid=%s" % self.sid})
            if site == 'vimeo':
                self.assertIn('value="https://vimeo.com/20379529">', response.body)
            elif site == 'youtube':
                self.assertIn('value="https://www.youtube.com/watch?v=EmcMG4uxiHk">', response.body)
            elif site == 'flickr':
                self.assertIn('value="https://www.flickr.com/photos/dahliablack/5497635343/">', response.body)

    def test_save_video_correctly_processes_various_youtube_urls(self):
        urls = ['https://www.youtube.com/watch?v=EmcMG4uxiHk&recommended=0', 'https://youtu.be/EmcMG4uxiHk', 'https://www.youtube.com/watch?v=EmcMG4uxiHk&feature=rec-LGOUT-real_rev-rn-1r-11-HM']
        for url in urls:
            response = self.fetch('/tools/save-video?url=%s' % url_escape(url), method='GET', headers={"Cookie":"sid=%s" % self.sid})
            self.assertIn('value="https://www.youtube.com/watch?v=EmcMG4uxiHk">', response.body)

    def test_adding_video_makes_it_show_up_in_friends_shake(self):
        user2 = User(name='user2', email='user2@mltshp.com', email_confirmed=1, is_paid=1)
        user2.set_password('asdfasdf')
        user2.save()
        user2.subscribe(self.user.shake())

        url = 'https://vimeo.com/20379529'
        response = self.post_url('/tools/save-video', arguments={"url": url, "skip_s3": "1"})
        sfs = Sharedfile.from_subscriptions(user2.id)
        self.assertTrue(len(sfs) > 0)
        self.assertEqual(sfs[0].name , url)


class FilePickerTests(BaseAsyncTestCase):
    def setUp(self):
        super(FilePickerTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.user_shake = self.user.shake()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf().decode("ascii")

        self.url = 'https://example.com/images/television.png?x=1'
        self.source_url = 'https://example.com/'
        self.description = "This is a multi-\nline\ndescription"
        self.alt_text = "This is some alt text\nit spans two lines."

    def test_picker_not_authed_displays_sign_in(self):
        response = self.fetch('/tools/p?url=%s' % self.url)
        self.assertIn('action="/sign-in/"', response.body)

    def test_picker_get_displays_image_passed_in(self):
        response = self.fetch('/tools/p?url=%s' % self.url, method='GET', headers={"Cookie":"sid=%s" % self.sid})
        self.assertIn('hidden" name="url" value="%s"' % self.url, response.body)

    def test_picker_authenticated_stores_image(self):
        response = self.post_url('/tools/p', arguments={"url": self.url, "title": "boatmoatgoat", "skip_s3": "1"}, raise_error=True)
        self.assertNotIn("ERROR", response.body)
        sf = Sharedfile.get("id=1")
        self.assertEqual(sf.name, "television.png")
        self.assertEqual(sf.title, "boatmoatgoat")
        self.assertEqual(sf.id, 1)

    def test_picker_url_parsing(self):
        good_urls = [('http://3.bp.blogspot.com/_dG2__iWuqsM/TNLfbQodu4I/AAAAAAAAFPE/BSUd6o2G5xU/s1600/1288708901.jpg', '1288708901.jpg')]
        for url in good_urls:
            parsed = urlparse(url[0])
            self.assertEqual(url[1], os.path.basename(parsed.path))

    def test_picker_errors(self):
        """
        This is not done.
        """
        host = "http://localhost:%s/tools/p?url=" % (self.get_http_port())
        bad_urls = ["http://", "hps://sdlfkj.com/asdlkfj", "something.com/file.jpg"]
        for url in bad_urls:
            response = self.fetch('/tools/p?url=%s' % url, method='GET', headers={"Cookie":"sid=%s" % self.sid})
            self.assertTrue(response.error)

    def test_picker_stores_image_and_shakesharedfile(self):
        response = self.post_url('/tools/p', arguments={"url": self.url, "title": "boatmoatgoat", "skip_s3": "1"})
        ssf = Shakesharedfile.get("sharedfile_id=1 and shake_id=%s", self.user_shake.id)
        self.assertTrue(ssf)

    def test_picker_stores_source_url(self):
        response = self.post_url('/tools/p', arguments={"url": self.url, "title": "boatmoatgoat", "source_url": self.source_url, "skip_s3": "1"})
        sf = Sharedfile.get("id=1")
        self.assertEqual(sf.source_url, 'https://example.com/')

    def test_picker_stores_description(self):
        response = self.post_url('/tools/p', arguments={"url": self.url, "title": "boatmoatgoat", "description": self.description, "skip_s3": "1"})
        self.assertNotIn("ERROR", response.body)
        sf = Sharedfile.get("id=1")
        self.assertEqual(sf.description, self.description)

    def test_picker_stores_alt_text(self):
        response = self.post_url('/tools/p', arguments={"url": self.url, "title": "boatmoatgoat", "description": self.description, "alt_text": self.alt_text, "skip_s3": "1"})
        self.assertNotIn("ERROR", response.body)
        sf = Sharedfile.get("id=1")
        self.assertEqual(sf.alt_text, self.alt_text)

    def test_picker_doesnt_see_filepile(self):
        response = self.fetch('/tools/p?url=%s' % url_escape("http://www.filepile.org/something/something"), method='GET', headers={"Cookie":"sid=%s" % self.sid})
        self.assertEqual(response.body.find('source: http://www.filepile.org'.encode("ascii")),  -1)

    def test_picker_strips_google_reader_url(self):
        response = self.fetch('/tools/p?url=%s&source_url=%s' % (self.url, url_escape("http://laughingsquid.com/skeleton-light-painting/?utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A laughingsquid %28Laughing Squid%29")), method='GET', headers={"Cookie":"sid=%s" % self.sid})
        self.assertIn("source: http://laughingsquid.com/skeleton-light-painting/</textarea>", response.body)

    def test_picker_strips_google_img_url(self):
        """
        https://www.google.com/imgres?imgurl=http://cragganmorefarm.com/user/gimage/Baby-Ground-hogs_480_320.jpg&imgrefurl=http://cragganmorefarm.com/&usg=__kpRJbm_WBlbEnqDvfi3A2JuJ9Wg=&h=320&w=480&sz=33&hl=en&start=24&sig2=SyR_NSDovcsOYu5tJYtlig&zoom=1&tbnid=TT5jIOrb76kqbM:&tbnh=130&tbnw=173&ei=f5lJTdjbHoL6lweT2cU3&prev=/images%3Fq%3Dbaby%2Bgroundhogs%26um%3D1%26hl%3Den%26client%3Dfirefox-a%26sa%3DX%26rls%3Dorg.mozilla:en-US:official%26biw%3D1152%26bih%3D709%26tbs%3Disch:10%2C540&um=1&itbs=1&iact=rc&dur=326&oei=YZlJTYuYJsH78AaQh6msDg&esq=2&page=2&ndsp=24&ved=1t:429,r:8,s:24&tx=103&ty=85&biw=1152&bih=709
        """
        response = self.fetch('/tools/p?url=%s&source_url=%s' % (self.url, url_escape("https://www.google.com/imgres?imgurl=http://cragganmorefarm.com/user/gimage/Baby-Ground-hogs_480_320.jpg&imgrefurl=http://cragganmorefarm.com/&usg=__kpRJbm_WBlbEnqDvfi3A2JuJ9Wg=&h=320&w=480&sz=33&hl=en&start=24&sig2=SyR_NSDovcsOYu5tJYtlig&zoom=1&tbnid=TT5jIOrb76kqbM:&tbnh=130&tbnw=173&ei=f5lJTdjbHoL6lweT2cU3&prev=/images%3Fq%3Dbaby%2Bgroundhogs%26um%3D1%26hl%3Den%26client%3Dfirefox-a%26sa%3DX%26rls%3Dorg.mozilla:en-US:official%26biw%3D1152%26bih%3D709%26tbs%3Disch:10%2C540&um=1&itbs=1&iact=rc&dur=326&oei=YZlJTYuYJsH78AaQh6msDg&esq=2&page=2&ndsp=24&ved=1t:429,r:8,s:24&tx=103&ty=85&biw=1152&bih=709")), method='GET', headers={"Cookie":"sid=%s" % self.sid})
        self.assertIn("source: http://cragganmorefarm.com/</textarea>", response.body)

class FileUploadTests(BaseAsyncTestCase):
    def setUp(self):
        super(FileUploadTests, self).setUp()
        self.user = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()
        self.user_shake = self.user.shake()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf().decode("ascii")

        self.test_file1_path = os.path.abspath("test/files/1.png")
        self.test_file1_sha1 = Sourcefile.get_sha1_file_key(self.test_file1_path)
        self.test_file1_content_type = "image/png"

        self.test_file2_path = os.path.abspath("test/files/love.gif")
        self.test_file2_sha1 = Sourcefile.get_sha1_file_key(self.test_file2_path)
        self.test_file2_content_type = "image/gif"

    def test_file_upload_size_check(self):
        response = self.upload_test_file()
        sharedfile = Sharedfile.get('id=1')
        self.assertIsNotNone(sharedfile)
        sourcefile = sharedfile.sourcefile()
        self.assertEqual(sourcefile.width, 640)
        self.assertEqual(sourcefile.height, 643)

    def test_file_upload_with_user(self):
        response = self.upload_test_file()
        shared_file = Sharedfile.get('id=1')
        self.assertIsNotNone(shared_file)
        self.assertEqual(shared_file.name, "love.gif")
        self.assertEqual(shared_file.source_id, 1)
        self.assertEqual(shared_file.user_id, 1)

    def test_file_upload_user_missing(self):
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, "", self.xsrf)
        self.assertEqual(response.code, 403)

    def test_file_upload_fastly(self):
        options.use_fastly = True
        response = self.upload_test_file()
        response = self.fetch('/r/1', follow_redirects=False)
        options.use_fastly = False
        self.assertTrue(response.headers['Location'].startswith("/s3/originals/ac7180f6b038d5ae4f2297989e39a900995bb8fc"))

    def test_file_upload_contents(self):
        response = self.upload_test_file()
        response = self.fetch('/r/1')
        self.assertTrue(response.headers['X-Accel-Redirect'].startswith("/s3/originals/ac7180f6b038d5ae4f2297989e39a900995bb8fc"))

    def test_uploading_file_creates_shared_shake_file(self):
        response = self.upload_test_file()
        ssf = Shakesharedfile.get("shake_id=%s and sharedfile_id=1", self.user_shake.id)
        self.assertTrue(ssf)

    def test_uploading_to_a_shake_saves_shake_id_in_post(self):
        response = self.upload_test_file()
        all_posts = Post.all()
        self.assertTrue(len(all_posts) > 0)
        self.assertEqual(1, all_posts[0].shake_id)

    def test_uploading_when_over_limit(self):
        """
        When an unpaid user uploads and they are over their limit, they should be
        presented with error. We override the max_mb_per_month setting to emulate
        going over limit.
        """
        # First we upload something
        response = self.upload_test_file()

        with test_option('max_mb_per_month', -1):
            # now we overeride the max_mb_ and try to upload, should fail.
            self.user.stripe_plan_id = "mltshp-single"
            self.user.save()
            response = self.upload_test_file()
            self.assertEqual(True, response.body.find('Single Scoop Account Limit'.encode("ascii")) > -1)

            # but if they paid, we're good.
            self.user.stripe_plan_id = "mltshp-double"
            self.user.save()

            response = self.upload_test_file()
            self.assertEqual(True, response.body.find('Single Scoop Account Limit'.encode("ascii")) == -1)

    def test_uploading_file_creates_post_record_for_user(self):
        response = self.upload_test_file()
        posts = Post.all()

        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post.user_id, self.user.id)
        self.assertEqual(post.sharedfile_id, 1)
        self.assertEqual(post.sourcefile_id, 1)
        self.assertEqual(post.seen, 1)

    def test_uploading_file_with_unsupported_content_type(self):
        """
        Uploading file with an unsupported content type should return a 200 page
        with a message explaining file type is not supported.
        """
        response = self.upload_file(self.test_file1_path, self.test_file1_sha1, "image/tiff", 1, self.sid, self.xsrf)
        self.assertEqual(200, response.code)
        self.assertIn("We don't support that file type.", response.body)
        posts = Post.all()
        self.assertEqual(len(posts), 0)

    # TODO: FINISH THIS
    #def test_pagination_above_one_digit_or_more(self):
    #    response = self.upload_file(self.test_file1_path, self.test_file1_sha1, self.test_file1_content_type, 1, self.sid, self.xsrf)
    #    shared_file = self.db.get("SELECT user_id, source_id, name FROM sharedfile where id = 1")
    #    self.assertEqual(shared_file['name'], "1.png")
    #    self.assertEqual(shared_file['source_id'], 1)
    #    self.assertEqual(shared_file['user_id'], 1)
