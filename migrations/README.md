## About this folder

This folder will contain all the database migration scripts required
to bring a schema forward in case it is behind. We're using "yoyo"
for handling the migration work. See https://bitbucket.org/ollyc/yoyo
for more information. Note: the `setup/db-install.sql` file should always
have the latest schema. So please keep that file up to date, since it
is used by tests to create a fresh database with the schema the
application expects.
