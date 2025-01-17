from .base import BaseTestCase
from models import User, Shake, Sourcefile, Sharedfile, Shakesharedfile, Post, Magicfile
from tasks.timeline import add_posts, delete_posts
from tornado.options import options

from mock import patch


class CeleryTaskTests(BaseTestCase):

    def setUp(self):
        super(CeleryTaskTests, self).setUp() # register connection.

        #create two users.
        self.user_a = User(name='user_a',email='user_a@example.com',verify_email_token='created', is_paid=1)
        self.user_a.save()
        self.user_b = User(name='user_b',email='user_b@example.com',verify_email_token='created', is_paid=1)
        self.user_b.save()

        #have the second user follow the first
        self.shake_a = Shake.get('user_id = %s and type=%s', self.user_a.id, 'user')
        self.user_b.subscribe(self.shake_a)

        #user one adds two files to their shake
        self.source = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        self.source.save()

        self.shared_1 = Sharedfile(source_id=self.source.id, name="my shared file",user_id=self.user_a.id, \
            content_type="image/png", share_key="oj")
        self.shared_1.save()

        self.shared_2 = Sharedfile(source_id=self.source.id, name="my shared file",user_id=self.user_a.id, \
            content_type="image/png", share_key="ok")
        self.shared_2.save()

    def test_task_timeline_add_posts(self):
        """
        this test calls the task directly to see if it inserts items into user b's timeline
        """
        add_posts(shake_id=self.shake_a.id, sharedfile_id=self.shared_1.id, sourcefile_id=self.source.id)
        timeline = Post.get('id = 1')
        self.assertFalse(timeline.seen)

        add_posts(shake_id=self.shake_a.id, sharedfile_id=self.shared_2.id, sourcefile_id=self.source.id)
        timeline = Post.get('id = 2')
        self.assertTrue(timeline.seen)

    def test_task_timeline_delete_posts(self):
        """
        this test calls delete_posts directly to ensure deleted files get marked as deleted
        """
        add_posts(shake_id=self.shake_a.id, sharedfile_id=self.shared_1.id, sourcefile_id=self.source.id)
        add_posts(shake_id=self.shake_a.id, sharedfile_id=self.shared_2.id, sourcefile_id=self.source.id)

        delete_posts(sharedfile_id=self.shared_1.id)
        delete_posts(sharedfile_id=self.shared_2.id)

        posts = Post.all()
        for post in posts:
            self.assertTrue(post.deleted)
