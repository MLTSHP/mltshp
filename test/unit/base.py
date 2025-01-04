import unittest
from lib.flyingcow import register_connection
from tornado.options import options
import string
import random

import logging

logger = logging.getLogger('mltshp.test')
logger.setLevel(logging.INFO)

class BaseTestCase(unittest.TestCase):   
    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
        self.db = register_connection(
            host=options.database_host,
            name=options.database_name,
            user=options.database_user,
            password=options.database_password,
            charset="utf8mb4")

    def setUp(self):
        super(BaseTestCase, self).setUp()
        if options.database_name != "mltshp_testing":
            raise Exception("Invalid database name for unit tests")
        self.create_database()

    def create_database(self):
        # logger.info("Creating database from BaseTestCase...")
        self.db.execute("DROP database IF EXISTS %s" % (options.database_name))
        self.db.execute("CREATE database %s" % (options.database_name))
        self.db.execute("USE %s" % (options.database_name))
        f = open("setup/db-install.sql")
        load_query = f.read()
        f.close()
        statements = load_query.split(";")
        for statement in statements:
            if statement.strip() != "":
                self.db.execute(statement.strip())
        
    def generate_string_of_len(self, length):
        return ''.join(random.choice(string.ascii_letters) for i in range(length))
    
