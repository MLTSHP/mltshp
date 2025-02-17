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
}
