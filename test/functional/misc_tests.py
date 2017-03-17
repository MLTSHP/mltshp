import os
import test.base

class MiscTests(test.base.BaseAsyncTestCase):
    
    def test_terms_of_use_exists(self):
        """
        /terms-of-use should be accessible.
        """
        response = self.fetch('/terms-of-use')
        self.assertEqual(200, response.code)

    def test_faq_exists(self):
        """
        /faq should be accessible.
        """
        response = self.fetch('/faq')
        self.assertEqual(200, response.code)

    def test_coming_soon_exists(self):
        """
        /coming-soon should be accessible.
        """
        response = self.fetch('/coming-soon')
        self.assertEqual(200, response.code)
