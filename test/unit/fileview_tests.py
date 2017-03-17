import datetime

from models import Fileview
from base import BaseTestCase
import test.factories

class FileviewTests(BaseTestCase):

    def test_sharedfile_ids(self):
        """
        Fileview.sharedfile_ids should return a list of distinct sharedfile_ids.
        """
        user = test.factories.user()
        sharedfile = test.factories.sharedfile(user)
        sharedfile2 = test.factories.sharedfile(user)
        sharedfile3 = test.factories.sharedfile(user)
        
        sharedfile.add_view()
        sharedfile.add_view()
        sharedfile.add_view()
        self.assertEqual(1, len(Fileview.sharedfile_ids()))
        self.assertEqual(sharedfile.id, Fileview.sharedfile_ids()[0])
        
        sharedfile2.add_view()
        sharedfile2.add_view()
        sharedfile2.add_view()
        self.assertEqual(2, len(Fileview.sharedfile_ids()))
        
        last_id = Fileview.last().id
        self.assertEqual(0, len(Fileview.sharedfile_ids(last_id)))
        sharedfile3.add_view()
        self.assertEqual(1, len(Fileview.sharedfile_ids(last_id)))
        self.assertEqual(sharedfile3.id, Fileview.sharedfile_ids(last_id)[0])


    def test_last(self):
        """
        Fileview.last() should return the last entry entered into fileview
        table.
        """
        user = test.factories.user()
        sharedfile = test.factories.sharedfile(user)

        self.assertEqual(None, Fileview.last())
        sharedfile.add_view()
        sharedfile.add_view()
        sharedfile.add_view()
        sharedfile.add_view()
        self.assertEqual(4, Fileview.last().id)
