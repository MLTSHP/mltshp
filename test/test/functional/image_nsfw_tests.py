import test.base
import test.factories
import models

class ImageNSFWTests(test.base.BaseAsyncTestCase):
    """
    Tests: /p/{share_key}/nsfw
    """
    def setUp(self):
        """
        Create users to test different liking situations.
        """
        super(ImageNSFWTests, self).setUp()
        # uploader
        self.admin = models.User(name='admin', email='admin@mltshp.com', email_confirmed=1, is_paid=1)
        self.admin.set_password('asdfasdf')
        self.admin.save()

        # another user
        self.bob = models.User(name='bob', email='bob@mltshp.com', email_confirmed=1, is_paid=1)
        self.bob.set_password('asdfasdf')
        self.bob.save()
    
    def test_non_logged_in_users_cant_set_nsfw(self):
        sharedfile = test.factories.sharedfile(self.admin)
        response = self.post_url(sharedfile.post_url(relative=True) + "/nsfw")
        self.assertEqual(403, response.code)
    
    def test_set_nsfw_on_anothers_file(self):
        """
        Another user setting NSFW for a file should result in an OK response,
        the nsfw set on the file and a log entry for the logged in user.
        """
        sharedfile = test.factories.sharedfile(self.admin)
        sourcefile = sharedfile.sourcefile()
        self.assertEqual(0, sourcefile.nsfw)
        self.sign_in('bob', 'asdfasdf')
        response = self.post_url(sharedfile.post_url(relative=True) + "/nsfw")
        self.assertEqual(200, response.code)
        sharedfile = models.Sharedfile.get("id = %s", sharedfile.id)
        sourcefile = sharedfile.sourcefile()
        self.assertEqual(1, sourcefile.nsfw)
        self.assertEqual(self.bob.id, models.NSFWLog.all()[0].user_id)
        self.assertEqual(sharedfile.id, models.NSFWLog.all()[0].sharedfile_id)
        self.assertEqual(sourcefile.id, models.NSFWLog.all()[0].sourcefile_id)

