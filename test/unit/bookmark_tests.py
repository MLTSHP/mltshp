import time
from datetime import datetime, timedelta

import models
from base import BaseTestCase

class BookmarkTests(BaseTestCase):
    def setUp(self):
        """
        We want a User, and a couple of sharedfiles.
        """
        super(BookmarkTests, self).setUp()
        self.user = models.User(name='admin', email='admin@example.com', email_confirmed=1, is_paid=1)
        self.user.set_password('asdfasdf')
        self.user.save()

        self.sourcefile = models.Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        self.sourcefile.save()
        self.sharedfile = models.Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="1", description="some\ndescription\nhere", source_url="http://www.mltshp.com/?hi")
        self.sharedfile.save()

    def test_start_reading_no_sharedfile(self):
        """
        Bookmark.start_reading should not set a bookmark if no sharedfile is passed in.
        """
        self.assertEqual(None, models.Bookmark.start_reading(self.user, None))
        self.assertEqual(0, len(models.Bookmark.all()))

    def test_start_reading(self):
        """
        Bookmark.start_reading should set a bookmark with a current timestamp
        if there are no bookmarks with newer timestamps than the sharedfile passed in.

        Only one newest bookmark should be created even if run twice.

        If a newer sharedfile is passed in, a brand new bookmark will be created.
        """
        first_bookmark = models.Bookmark.start_reading(self.user, self.sharedfile)
        self.assertTrue(first_bookmark.created_at >= self.sharedfile.created_at)

        first_bookmark = models.Bookmark.start_reading(self.user, self.sharedfile)
        self.assertEqual(1, len(models.Bookmark.all()))

        new_sharedfile = models.Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="1", description="some\ndescription\nhere", source_url="http://www.mltshp.com/?hi")
        # we need to make sure that sharedfile we pass in, is one second older than when original was set in setUp
        time.sleep(2)
        new_sharedfile.save()

        first_bookmark = models.Bookmark.start_reading(self.user, new_sharedfile)
        self.assertEqual(2, len(models.Bookmark.all()))

    def test_new_bookmark_stores_sharedfile_id(self):
        """
        Creating a new bookmark stores the sharedfile_id
        """
        first_bookmark = models.Bookmark.start_reading(self.user, self.sharedfile)
        self.assertEqual(first_bookmark.sharedfile_id, self.sharedfile.id)

    def test_new_bookmark_points_to_previous_bookmark(self):
        """
        Start reading then upload a file and start reading again. 
        The second bookmark should point to the first bookmark
        """
        first_bookmark = models.Bookmark.start_reading(self.user, self.sharedfile)

        new_sharedfile = models.Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="1", description="some\ndescription\nhere", source_url="http://www.mltshp.com/?hi")
        # we need to make sure that sharedfile we pass in, is one second older than when original was set in setUp
        time.sleep(2)
        new_sharedfile.save()

        second_bookmark = models.Bookmark.start_reading(self.user, new_sharedfile)
        self.assertEqual(second_bookmark.previous_sharedfile_id, self.sharedfile.id)
        self.assertEqual(second_bookmark.previous_sharedfile_id, first_bookmark.sharedfile_id)

    def test_for_user_between_sharedfiles(self):
        """
        Should return any bookmarks that are within the range of sharedfile dates passed in. 

        A bookmark that has the same timestamp as the latest file will not return as part of the result.  A bookmark
        that is equal to the oldest timestamp will return.
        """                
        latest_file = models.Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="1", description="some\ndescription\nhere", source_url="http://www.mltshp.com/?hi")
        latest_file.save()
        latest_file.created_at = datetime.utcnow() + timedelta(seconds=5)
        latest_file.save()

        middle_file = models.Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="1", description="some\ndescription\nhere", source_url="http://www.mltshp.com/?hi")
        middle_file.save()

        oldest_file = self.sharedfile
        oldest_file.created_at = datetime.utcnow() - timedelta(seconds=5)
        oldest_file.save()

        sharedfiles = [latest_file, middle_file, oldest_file]
        self.assertEqual(0, len(models.Bookmark.for_user_between_sharedfiles(self.user, sharedfiles)))

        bookmark_equal_to_latest = models.Bookmark(user_id=self.user.id, created_at=latest_file.created_at)
        bookmark_equal_to_latest.save()
        self.assertEqual(0, len(models.Bookmark.for_user_between_sharedfiles(self.user, sharedfiles)))

        between_latest_and_middle = models.Bookmark(user_id=self.user.id, created_at=middle_file.created_at + timedelta(seconds=1))
        between_latest_and_middle.save()
        self.assertEqual(1, len(models.Bookmark.for_user_between_sharedfiles(self.user, sharedfiles)))

        equal_oldest = models.Bookmark(user_id=self.user.id, created_at=oldest_file.created_at)
        equal_oldest.save()
        self.assertEqual(2, len(models.Bookmark.for_user_between_sharedfiles(self.user, sharedfiles)))

    def test_merge_with_sharedfiles(self):
        """
        When passed in two lists of bookmarks and sharedfiles, should return a combined list sorted
        by created_at.  Bookmarks come before sharedfiles when they have the same created_at.
        """
        latest_file = models.Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="1", description="some\ndescription\nhere", source_url="http://www.mltshp.com/?hi")
        latest_file.save()
        latest_file.created_at = datetime.utcnow() + timedelta(seconds=5)
        latest_file.save()
        middle_file = models.Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="1", description="some\ndescription\nhere", source_url="http://www.mltshp.com/?hi")
        middle_file.save()
        oldest_file = self.sharedfile
        oldest_file.created_at = datetime.utcnow() - timedelta(seconds=5)
        oldest_file.save()
        sharedfiles = [latest_file, middle_file, oldest_file]

        between_latest_and_middle = models.Bookmark(user_id=self.user.id, created_at=middle_file.created_at + timedelta(seconds=1))
        between_latest_and_middle.save()
        equal_oldest = models.Bookmark(user_id=self.user.id, created_at=oldest_file.created_at)
        equal_oldest.save()
        bookmarks = [between_latest_and_middle, equal_oldest]

        merged_bookmarks_sharedfiles = models.Bookmark.merge_with_sharedfiles(bookmarks, sharedfiles)
        self.assertEqual(latest_file, merged_bookmarks_sharedfiles[0])
        self.assertEqual(between_latest_and_middle, merged_bookmarks_sharedfiles[1])
        self.assertEqual(middle_file, merged_bookmarks_sharedfiles[2])
        self.assertEqual(equal_oldest, merged_bookmarks_sharedfiles[3])
        self.assertEqual(oldest_file, merged_bookmarks_sharedfiles[4])
