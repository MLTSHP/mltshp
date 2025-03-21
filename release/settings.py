# This is a collection of settings specifically for use with our automated
# build and test setup on buildkite.com

# dummy dict so main module loads okay
settings = {}

# Default settings for running tests; app host/cdn host are wired for
# expected values in tests.
test_settings = {
    "app_host": "my-mltshp.com",
    "cdn_host": "some-cdn.com",
    "cookie_secret": "secretz",
    "auth_secret" : "dummy-secret",
    "xsrf_cookies": True,
    "uploaded_files" : "/srv/mltshp.com/uploaded",
    "debug": True,
    # docker container's host ip address
    "database_user": "root",
    "database_name": "mltshp_testing",
    "database_password" : "",
    "database_host": "mysql",
    "aws_bucket": "mltshp-testing",
    "aws_key": "dummy-key",
    "aws_secret": "dummy-secret",
    "max_mb_per_month" : 300,
    "api_hits_per_hour" : 150,
    "use_workers": False,
    "debug_workers": True,
    "superuser_list": "admin",
    "tornado_logging": False,
    # these must be set for testing test/unit/externalservice_tests.py
    # "twitter_consumer_key" : "twitter_consumer_key_here",
    # "twitter_consumer_secret" : "twitter_consumer_secret_key_here",
    # "twitter_access_key" : "twitter_access_key_here",
    # "twitter_access_secret" : "twitter_access_secret_here",
}
