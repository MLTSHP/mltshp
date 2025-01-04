import datetime

from models import Fileview
from .base import BaseTestCase
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
        self.assertEqual(2, len(Fileview.sharedfile_ids(last_id+1)))

        sharedfile3.add_view()
        # still just "2", since we're selecting sharedfile ids
        # that are less than last_id+1
        self.assertEqual(2, len(Fileview.sharedfile_ids(last_id+1)))

        # last sharedfile id returned before last_id should be sharedfile2
        last_id = Fileview.last().id
        self.assertEqual(sharedfile2.id, Fileview.sharedfile_ids(last_id)[-1])


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
