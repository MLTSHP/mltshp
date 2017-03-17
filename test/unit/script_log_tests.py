import datetime

from models import ScriptLog
from base import BaseTestCase
import test.factories

class ScriptLogTests(BaseTestCase):

    def test_get_last_successful(self):
        """
        ScriptLog.get_last_successfull() should return the latest entry that
        matches passed in name with a success state of 1.
        """
        script_log = ScriptLog(name='test-script', success=0)
        script_log.save()
        self.assertEqual(None, ScriptLog.last_successful('test-script'))
        
        script_log2 = ScriptLog(name='test-script', success=1)
        script_log2.save()
        script_log3 = ScriptLog(name='test-script', success=1)
        script_log3.save()
        self.assertEqual(script_log3.id, ScriptLog.last_successful('test-script').id)
