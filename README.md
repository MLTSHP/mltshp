# MLTSHP

## Overview 

Want to get this set up and make sure it's all working right? Run the following script:

    bin/setup

## Run the tests

Each time you want to run unit tests, use this command:

    bin/test

## Load it up in the browser

Each time you want to restart the server, use this command:

    bin/start_dev

This will activate the website at `http://localhost:8000` by default:

    open http://localhost:8000

## Live integrations

(Unusual) If you want to work on real integrations, you'll need to change 
these things in your settings.py:

* Update path for `uploaded_files`
* Add valid AWS bucket reference (`aws_bucket`)
* Add valid AWS key and secret (`aws_key`, `aws_secret`)
* Add valid Recaptcha key and secret (`recaptcha_private_key`,
  `recaptcha_public_key`)
* Add valid Twitter API keys (`twitter_consumer_key`,
  `twitter_consumer_secret`, `twitter_access_key`,
  `twitter_access_secret`)
