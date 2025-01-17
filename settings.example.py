# Development settings; suitable for running against our Docker
# image.
settings = {
    # Exclude any port number from the host name here; also used for setting cookies
    "app_host": "mltshp.localhost",
    # Include any port number for the host name here
    "cdn_host": "s.mltshp.localhost:8000",
    "api_hits_per_hour" : 150,
    "auth_secret" : "dummy-secret",
    "aws_bucket": "mltshp-dev",
    "aws_host": "fakes3",
    "aws_port": 4567,
    "aws_key": "dummy-key",
    "aws_secret": "dummy-secret",
    "cookie_secret": "some secret string",
    "database_host": "mysql",
    "database_name": "mltshp",
    "database_user": "root",
    "database_password" : "",
    "debug": True,
    "debug_workers": False,
    "max_mb_per_month" : 300,
    "uploaded_files" : "/srv/mltshp.com/uploaded",
    "use_workers": False,
    "xsrf_cookies": True,
    "server_id": "mltshp-web-1",
}

# Default settings for running tests; app host/cdn host are wired for
# expected values in tests.
test_settings = {
    "app_host": "mltshp.com",
    "cdn_host": "mltshp-cdn.com",
    "cdn_ssl_host": "mltshp-cdn.com",
    "cookie_secret": "secretz",
    "auth_secret" : "dummy-secret",
    "xsrf_cookies": True,
    "uploaded_files" : "/srv/mltshp.com/uploaded",
    "debug": True,
    "database_user": "root",
    "database_name": "mltshp_testing",
    "database_password" : "",
    "database_host": "mysql",
    "aws_bucket": "mltshp-testing",
    "aws_host": "fakes3",
    "aws_port": 4567,
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
