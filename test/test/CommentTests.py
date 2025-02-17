from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from tornado.escape import json_decode, url_escape

import time

from .base import BaseAsyncTestCase

from models import User, Sharedfile, Sourcefile, Conversation
import models

class CommentTests(BaseAsyncTestCase):
    def setUp(self):
        super(CommentTests, self).setUp()
        self.admin = User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()
        self.sid = self.sign_in('admin', 'asdfasdf')
        self.xsrf = self.get_xsrf().decode("ascii")
        self.flake=str(time.time())
        self.src = Sourcefile(width=1, height=1, file_key='asdf', thumb_key='qwer')
        self.src.save()
        self.shf = Sharedfile(source_id=self.src.id, user_id=self.admin.id, name='shared.jpg', title='shared', share_key='1', content_type='image/jpg')
        self.shf.save()

    def test_saving_a_comment_is_stored(self):
        #submit a comment to /share_key/save_comment
        body = """This is a comment.

        A multi-line comment.&amp;

        That is all.&_xsrf=asdf
        """
        response = self.fetch(self.shf.post_url(relative=True) + '/comment', method='POST', headers={'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, body="body=%s&_xsrf=%s" % (url_escape(body), self.xsrf))

        comments = self.shf.comments()
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].body, body.strip())

    def test_blank_comment_doesnt_save(self):
        body = ""
        response = self.fetch(self.shf.post_url(relative=True) + '/comment', method='POST', headers={'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, body="body=%s&_xsrf=%s" % (url_escape(body), self.xsrf))

        comments = self.shf.comments()
        self.assertEqual(len(comments), 0)

    def test_saving_an_empty_comment_not_stored(self):
        #submit a comment to /share_key/save_comment
        body = """
        """
        response = self.fetch(self.shf.post_url(relative=True) + '/comment', method='POST', headers={'Cookie':'_xsrf=%s;sid=%s' % (self.xsrf, self.sid)}, body="body=%s&_xsrf=%s" % (url_escape(body), self.xsrf))

        comments = self.shf.comments()
        self.assertEqual(len(comments), 0)

    def test_saving_not_signed_in_not_stored(self):
        #submit a comment to /share_key/save_comment
        body = """
        This is a comment.
        """
        response = self.fetch(self.shf.post_url(relative=True) + '/comment', method='POST', headers={'Cookie':'_xsrf=%s' % (self.xsrf)}, body="body=%s&_xsrf=%s" % (url_escape(body), self.xsrf))

        comments = self.shf.comments()
        self.assertEqual(len(comments), 0)
