import datetime
from functools import wraps

from models import Apihit
from .base import BaseTestCase


class ApihitModelTests(BaseTestCase):

    def test_hit_counts(self):
        testtime = datetime.datetime(2011, 6, 2, 7, 33, 45)
        testtime_eight = datetime.datetime(2011, 6, 2, 8, 0, 1)

        ret = Apihit.hit(7, testtime)
        self.assertEqual(ret, 1)

        apih = Apihit.where("accesstoken_id=%s and hour_start=%s", 7, '2011-06-02 07:00:00')
        self.assertEqual(len(apih), 1)
        self.assertEqual(apih[0].hits, 1)

        ret = Apihit.hit(7, testtime)

        apih = Apihit.where("accesstoken_id=%s and hour_start=%s", 7, '2011-06-02 07:00:00')
        self.assertEqual(len(apih), 1)
        self.assertEqual(apih[0].hits, 2)

        self.assertEqual(ret, 2)

        ret = Apihit.hit(7, testtime_eight)
        self.assertEqual(ret, 1)

        apih = Apihit.where("accesstoken_id=%s and hour_start=%s", 7, '2011-06-02 08:00:00')
        self.assertEqual(len(apih), 1)
        self.assertEqual(apih[0].hits, 1)
