import datetime
import json

from models import Fileview, ScriptLog
from test.unit.base import BaseTestCase
import test.factories

import runner

class CalculateViewsTests(BaseTestCase):

    def test_main(self):
        """
        When the script runs for the first time, it should calculate
        the view_count for all sharedfiles, store the results in the
        script_log results table.
        
        The second time it run, it should use the previous run to only
        calculate views for files that have had views since last time
        the script ran.
        """
        user = test.factories.user()
        sharedfile = test.factories.sharedfile(user)
        sharedfile2 = test.factories.sharedfile(user)
        sharedfile3 = test.factories.sharedfile(user)
        
        sharedfile.add_view()
        sharedfile.add_view()
        sharedfile2.add_view()
        sharedfile2.add_view()
        sharedfile2.add_view()
        self.assertEqual(0, sharedfile.get("id = %s", sharedfile.id).view_count)
        self.assertEqual(0, sharedfile2.get("id = %s", sharedfile2.id).view_count)
        runner.run('scripts/calculate-views.py')
        self.assertEqual(2, sharedfile.get("id = %s", sharedfile.id).view_count)
        self.assertEqual(3, sharedfile2.get("id = %s", sharedfile2.id).view_count)
        
        script_log = ScriptLog.last_successful('calculate-views')
        results = json.loads(script_log.result)
        self.assertEqual(2, results['updated_sharedfiles'])
        self.assertEqual(Fileview.last().id, results['last_fileview_id'])
        
        sharedfile3.add_view()
        runner.run('scripts/calculate-views.py')
        script_log = ScriptLog.last_successful('calculate-views')
        results = json.loads(script_log.result)        
        self.assertEqual(1, results['updated_sharedfiles'])
        self.assertEqual(Fileview.last().id, results['last_fileview_id'])
