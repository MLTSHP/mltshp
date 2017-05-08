# Default settings for running tests; app host/cdn host are wired for
# expected values in tests.
test_settings = {
    "app_host": "mltshp.com",
    "cdn_host": "mltshp-cdn.com",
    "cdn_ssl_host": "mltshp-cdn.com",
    "cookie_secret": "secretz",
    "auth_secret" : "ne4om9og3maw8orp2ot9quos5ed8aj3lam6up3ja",
    "xsrf_cookies": True,
    "uploaded_files" : "/srv/mltshp.com/uploaded",
    "debug": True,
    "database_user": "root",
    "database_name": "mltshp_testing",
    "database_password" : "",
    # docker container's host ip address
    "database_host": "dockerhost",
    "aws_bucket": "mltshp-testing",
    "aws_host": "fakes3",
    "aws_port": 8000,
    "aws_key": "dummy-key",
    "aws_secret": "dummy-secret",
    "max_mb_per_month" : 300,
    "api_hits_per_hour" : 150,
    "use_workers": True,
    "debug_workers": True,
    # these must be set for testing test/unit/externalservice_tests.py
    # "twitter_consumer_key" : "twitter_consumer_key_here",
    # "twitter_consumer_secret" : "twitter_consumer_secret_key_here",
    # "twitter_access_key" : "twitter_access_key_here",
    # "twitter_access_secret" : "twitter_access_secret_here",
}
