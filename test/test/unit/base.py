import unittest
from lib.flyingcow import register_connection
from tornado.options import options
import string
import random
import re

import logging

logger = logging.getLogger('mltshp.test')
logger.setLevel(logging.INFO)

class BaseTestCase(unittest.TestCase):   
    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
        self.db = register_connection(
            host=options.database_host,
            name="mysql",
            user=options.database_user,
            password=options.database_password,
            charset="utf8mb4")

    def setUp(self):
        super(BaseTestCase, self).setUp()
        if options.database_name != "mltshp_testing":
            raise Exception("Invalid database name for unit tests")
        self.reset_database()

    def reset_database(self):
        self.db.execute("USE %s" % (options.database_name))
        with open("setup/database/db-truncate.sql") as f:
            query = f.read()
        self.db.execute(query)

    def generate_string_of_len(self, length):
        return ''.join(random.choice(string.ascii_letters) for i in range(length))
    
