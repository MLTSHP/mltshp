from tornado.options import define, options
import mltshpoptions
from settings import settings
mltshpoptions.parse_dictionary(settings)

from yoyo import read_migrations, get_backend
import logging

logging.basicConfig(level=logging.INFO)

backend = get_backend(
    "mysql+mysqldb://%s:%s@%s/%s" %
    (options.database_user, options.database_password,
     options.database_host, options.database_name))
migrations = read_migrations("migrations")
print "Applying migrations..."
backend.apply_migrations(backend.to_apply(migrations))
print "...complete!"
