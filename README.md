# MLTSHP

## Overview 

Want to get this set up and make sure it's all working right? Do these 
things as they're described in the below sections

1. Install mysql
2. Install fakes3 gems
3. Configure python environment / settings.py
4. Run the tests
5. Load it up in the browser

## Install mysql

Install mysql and start it:

    brew install mysql
    brew services start mysql

Now create an "mltshp_testing" database for unit tests to use. Create another 
empty "mltshp" database and install an empty schema to it using the 
`setup/db-install.sql` file:

    mysql -u root -e "CREATE DATABASE mltshp_testing"
    mysql -u root -e "CREATE DATABASE mltshp"
    mysql -u root -D mltshp < setup/db-install.sql
    mysql -u root -D mltshp < setup/db-fixtures.sql

## Install fakes3

If you don't want to rely on the real S3 for tests or development, you can 
use the fakes3 ruby gem.

Make sure you have a relatively recent Ruby installed (rvm method):

    gpg --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
    \curl -sSL https://get.rvm.io | bash -s stable --ruby

Make sure you have Bundler installed:

    gem install bundler
    bundle install

Ensure your settings.py has `aws_host` set to `localhost` and `aws_port` 
  to whatever port you will run fakes3 *in both settings and test_settings
  sections*

If your `aws_bucket` is called `mltshp_testing`, add appropriate entry in 
  your /etc/hosts:

    cp /etc/hosts /tmp/hosts
    echo "127.0.0.1 mltshp_testing.localhost" >> /tmp/hosts
    sudo cp /tmp/hosts /etc/hosts

Ensure that we have a safe place to store files:

    mkdir /tmp/mltshp

Launch fakes3 in the background:

    nohup bundle exec fakes3 -p 4000 --root /tmp/fakes3 &

## Configure python environment / settings.py

* Install virtualenv, pip, then run:

    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt # requires mysql install

(Unusual) You may need to tweak your library path for OpenSSL when compiling 
the mysql module. This worked for me:

    export LDFLAGS="-L/usr/local/opt/openssl/lib"

Create settings.py from settings.example.py:

    cp settings.example.py settings.py

    # Set new secret strings
    perl -pi -e "s/some_random_string/$(uuidgen)/g" settings.py
    perl -pi -e "s/secretz/$(uuidgen)/g" settings.py

(Unusual) If you want to work on real integrations, you'll need to change 
these things:

* Update path for `uploaded_files`
* Add valid AWS bucket reference (`aws_bucket`)
* Add valid AWS key and secret (`aws_key`, `aws_secret`)
* Add valid Recaptcha key and secret (`recaptcha_private_key`,
  `recaptcha_public_key`)
* Add valid Twitter API keys (`twitter_consumer_key`,
  `twitter_consumer_secret`, `twitter_access_key`,
  `twitter_access_secret`)

## Run the tests

At the beginning of your programming session, you'll need to activate 
virtualenv:

    virtualenv env
    source env/bin/activate

Each time you want to run unit tests, use this command:

    python test.py

## Load it up in the browser

At the beginning of your programming session, you'll need to activate 
virtualenv:

    virtualenv env
    source env/bin/activate

Each time you want to restart the server, use this command:

    python main.py

This will activate the website at `http://localhost:8000` by default:

    open http://localhost:8000

## (Optional) RabbitMQ

The live application relies on RabbitMQ and Celery for doing background tasks. 

Install RabbitMQ and configure `celeryconfig.py` appropriately (using 
`celeryconfig.example.py` as a basis):

    # Install and secure rabbit
    brew install rabbitmq
    brew services start rabbitmq
    rabbitmqctl change_password guest <new password>
 
    # Copy the example config
    cp celeryconfig.example.py celeryconfig.py

A few rabbitmqctl commands need to be run to create the virtualhost, user, etc.
(customize these as you'd like):

    rabbitmqctl add_user mltshp_user password
    rabbitmqctl add_vhost kablam.local
    rabbitmqctl set_permissions -p kablam.local mltshp_user ".*" ".*" ".*"

Then, run the Celery worker using:

    python worker.py

Note: the celery worker and rabbitmq server are not necessary for running
unit tests.
