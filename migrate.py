from tornado.options import define, options
import mltshpoptions
from settings import settings
mltshpoptions.parse_dictionary(settings)

from yoyo import read_migrations, get_backend

backend = get_backend(
    "mysql+mysqldb://%s:%s@%s/%s" %
    (options.database_user, options.database_password,
     options.database_host, options.database_name))
migrations = read_migrations("migrations")
backend.apply_migrations(backend.to_apply(migrations))
