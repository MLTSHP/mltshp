from models import Sharedfile, Sourcefile, User
from .base import BaseTestCase
import os
from tornado.escape import json_decode
import re


class SourcefileModelTests(BaseTestCase):

    def setUp(self):
        """
        Create a user sourcefile and sharedfile to work with.
        """
        super(SourcefileModelTests, self).setUp() # register connection.
        self.user = User(name='thename',email='theemail@gmail.com',verify_email_token='created',email_confirmed=0, is_paid=1)
        self.user.save()
        self.sourcefile = Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
        self.sourcefile.save()
        self.sharedfile = Sharedfile(source_id=self.sourcefile.id, name="my shared file",user_id=self.user.id, \
            content_type="image/png", share_key="ok")
        self.sharedfile.save()

    def testGetByShareKey(self):
        existing_source_file = Sourcefile.get_by_file_key('asdf')
        self.assertEqual(self.sourcefile.id, existing_source_file.id)

    def test_sha1_file_encoding(self):
        sha1_key = Sourcefile.get_sha1_file_key(os.path.join(os.path.dirname(os.path.dirname(__file__)), "files/love.gif"))
        self.assertEqual("ac7180f6b038d5ae4f2297989e39a900995bb8fc", sha1_key)

    def test_make_oembed_url(self):
        v_urls = [
            'https://vimeo.com/7100569',
            'https://www.youtube.com/watch?v=bDOYN-6gdRE',
            'https://www.youtube.com/watch?si=123&v=bDOYN-6gdRE',
            'https://www.youtube.com/watch?v=cE0wfjsybIQ&si=123&feature=youtu.be',
        ]
        o_encoded = [
            'https://vimeo.com/api/oembed.json?url=https%3A%2F%2Fvimeo.com%2F7100569&maxwidth=550',
            'https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DbDOYN-6gdRE&maxwidth=550&format=json',
            'https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DbDOYN-6gdRE&maxwidth=550&format=json',
            'https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DcE0wfjsybIQ%26feature%3Dyoutu.be&maxwidth=550&format=json',
        ]
        for (i, v_url) in enumerate(v_urls):
            oembed_url = Sourcefile.make_oembed_url(v_url)
            self.assertEqual(oembed_url, o_encoded[i])

    def test_fail_to_make_oembed_url(self):
        bad_urls = ['http://cnn.com/7100569', 'http://www.waxy.org/watch?v=bDOYN-6gdRE']
        for url in bad_urls:
            self.assertEqual(Sourcefile.make_oembed_url(url), None)

    def test_create_from_json_oembed(self):
        o_encoded = ['https://vimeo.com/api/oembed.json?url=https%3A%2F%2Fvimeo.com%2F7100569', 'https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DbDOYN-6gdRE&format=json&maxwidth=550']
        #get each url
        #and
        #
        test_responses = [
        r'{"provider_url": "https:\/\/www.youtube.com\/", "title": "Auto-Tune the News #8: dragons. geese. Michael Vick. (ft. T-Pain)", "html": "<object width=\"425\" height=\"344\"><param name=\"movie\" value=\"https:\/\/www.youtube.com\/e\/bDOYN-6gdRE\"><\/param><param name=\"allowFullScreen\" value=\"true\"><\/param><param name=\"allowscriptaccess\" value=\"always\"><\/param><embed src=\"https:\/\/www.youtube.com\/e\/bDOYN-6gdRE\" type=\"application\/x-shockwave-flash\" width=\"425\" height=\"344\" allowscriptaccess=\"always\" allowfullscreen=\"true\"><\/embed><\/object>", "author_name": "schmoyoho", "height": 344, "thumbnail_width": 480, "width": 425, "version": "1.0", "author_url": "https:\/\/www.youtube.com\/user\/schmoyoho", "provider_name": "YouTube", "thumbnail_url": "http:\/\/i3.ytimg.com\/vi\/bDOYN-6gdRE\/hqdefault.jpg", "type": "video", "thumbnail_height": 360}',
        r'{"type":"video","version":"1.0","provider_name":"Vimeo","provider_url":"https:\/\/vimeo.com\/","title":"Brad!","author_name":"Casey Donahue","author_url":"https:\/\/vimeo.com\/caseydonahue","is_plus":"1","html":"<iframe src=\"https:\/\/player.vimeo.com\/video\/7100569\" width=\"1280\" height=\"720\" frameborder=\"0\"><\/iframe>","width":"1280","height":"720","duration":"118","description":"Brad finally gets the attention he deserves.","thumbnail_url":"http:\/\/b.vimeocdn.com\/ts\/294\/128\/29412830_1280.jpg","thumbnail_width":1280,"thumbnail_height":720,"video_id":"7100569"}',
        ]
        for response in test_responses:
            Sourcefile.create_from_json_oembed(response)





            #print sf.__dict__
            #self.assertTrue(sf.id > 0)
            #self.assertTrue(sf.width > 0)
            #self.assertTrue(sf.width <= 240)
            #self.assertTrue(sf.height > 0)
            #self.assertTrue(sf.height <= 184)
            #self.assertTrue(sf.thumb_key != '')
            #self.assertTrue(sf.small_key != '')


    #def test_fail_to_create_from_url(self):
    #    bad_urls = ['http://www.cnn.com/asdf', 'http://mltshp.com/?lksdjf=123']
    #    for url in bad_urls:
    #        response = Sourcefile.create_from_url(url)
    ##        self.assertFalse(response)
