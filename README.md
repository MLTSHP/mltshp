## MLTSHP

### Setup Development / Testing environment

Create settings.py from settings.example.py

* Update path for `uploaded_files`
* Add valid AWS bucket reference (`aws_bucket`)
* Add valid AWS key and secret (`aws_key`, `aws_secret`)
* Add valid Recaptcha key and secret (`recaptcha_private_key`,
  `recaptcha_public_key`)
* Add valid Twitter API keys (`twitter_consumer_key`,
  `twitter_consumer_secret`, `twitter_access_key`,
  `twitter_access_secret`)

#### Virtualenv

* Install virtualenv, pip, then run:

    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

You may need to tweak your library path for OpenSSL when
compiling the mysql module. This worked for me:

    export LDFLAGS="-L/usr/local/opt/openssl/lib"

#### Database

Install mysql and create an "mltshp\_testing" database
for unit tests to use. Create another empty "mltshp"
database and install an empty schema to it using
the setup/db-install.sql file.

#### RabbitMQ

The application relies on RabbitMQ and Celery for doing
background tasks. Install RabbitMQ and configure `celeryconfig.py`
appropriately (using `celeryconfig.example.py` as a basis).
A few rabbitmqctl commands need to be run to create the virtualhost,
user, etc. (customize these as you'd like):

    rabbitmqctl add_user mltshp_user password
    rabbitmqctl add_vhost kablam.local
    rabbitmqctl set_permissions -p kablam.local mltshp_user ".*" ".*" ".*"

Then, run the Celery worker using:

    python worker.py

Note: the celery worker and rabbitmq server are not necessary for running
unit tests.

#### Tests

Run unit tests using this command (assumes it is run with the
virtualenv activated):

    python test.py

#### Removing S3 test / development dependency

If you don't want to rely on S3 for tests or development, you can use the
fakes3 ruby gem.

* Make sure you have Ruby 1.9.3 installed (rvm is your easiest bet)
* Make sure you have bundle installed

    gem install bundler

* Install files in the Gemfile

    bundle install

* Update your settings.py and update `aws_host` to `localhost` and
  `aws_port` to whatever port you will run fakes3 on (default is `10050`).
* If your `aws_bucket` is called `mltshp_testing`, add appropriate entry
  in your /etc/hosts:

    127.0.0.1 mltshp_testing.localhost

* launch fakes3:

    bundle exec fakes3 -p 4000 --root /tmp
