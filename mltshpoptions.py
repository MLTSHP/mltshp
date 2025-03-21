from tornado.options import define, options


def parse_dictionary(settings):
    for key, value in settings.items():
        if key in options:
            setattr(options, key, value)


define('debug', type=bool, default=True, help="Run in debug/development mode")
define('dump_settings', type=bool, default=False, help="Dump evaluated settings and exit")
define('tornado_logging', type=bool, default=True, help="Controls Tornado logging")

# app settings
define('app_host', default='mltshp.com', metavar="HOST", help="Base hostname for web site")
define('cdn_host', default='mltshp-cdn.com', metavar="HOST", help="Hostname for CDN")
define('use_fastly', default=False, type=bool, help="Enable for Fastly CDN support")
define('disable_signups', type=bool, default=False, help="Are new user signups disabled")
define('readonly', type=bool, default=False, help="Switch to enable site-wide readonly mode (disables posts, signups, etc).")
define('show_promos', type=bool, default=True, help="Are we showing promos")
define('cookie_secret', metavar="SECRET", help="Secret to use for encoding secure cookies")
define('xsrf_cookies', type=bool, default=True, help="Use Tornado XSRF protection")
define('on_port', default=8000, help="Run on port")
define('auth_secret', metavar='SECRET', help="Secret to use when hashing passwords")
define('max_mb_per_month', type=int, metavar='MB', help="Maximum MB a free account can upload per month")
define('api_hits_per_hour', type=int, metavar='HITS', help='Number of API hits an access token can make in an hour before rate limiting')
define('likes_to_tweet', type=int, default=20, metavar='LIKES', help='Number of likes for a file to be tweeted to @best_of_mltshp')
define('likes_to_magic', type=int, default=10, metavar='LIKES', help='Number of likes for a file to be saved as a "magic" file')
define('use_query_cache', type=bool, default=True, help="Turn on flyingcow's QueryCache during request cycle.")
define('best_of_user_name', default='mltshp', help="User name where Best Of images are saved.")
define('superuser_list', default='', help='Comma separated list of users who are superuser accounts')
define('moderator_list', default='', help='Comma separated list of users who are moderator accounts')
define('host_banner', default='', help='Shown in header when present')

# infrastructure
define('database_host', metavar="HOST", help="Hostname for database connection")
define('database_name', metavar="DATABASE", help="Database name for database connection")
define('database_user', metavar="NAME", help="Username for database connection")
define('database_password', metavar="PASSWORD", help="Password for database connection")
define('uploaded_files', metavar='PATH', help="Path on disk where uploaded files go")
define('use_workers', type=bool, default=True, help="Use asynchronous Celery workers")
define('debug_workers', type=bool, default=False, help="Wait for asynchronous workers to complete (for testing)")
define('use_cdn', type=bool, default=False, help="Enable if s.mltshp.com should redirect to mltshp-cdn.com for images")
define('server_id', help='A name for this server instance (unique per server)')

# APIs
define('aws_key', metavar="KEY", help="Amazon API key for S3 & Payments")
define('aws_host', metavar="AWS_HOST", help="AWS Host", default="s3.amazonaws.com")
define('aws_port', metavar="AWS_PORT", type=int, help="AWS Port", default=None)
define('aws_secret', metavar="SECRET", help="Amazon API secret for S3 & Payments")
define('aws_bucket', metavar="NAME", help="Name of Amazon S3 bucket to use")
define('postmark_api_key', metavar='KEY', help="Postmark (postmarkapp.com) API key")
define('recaptcha_site_key', metavar="KEY", help="Site key for reCAPTCHA v3")
define('recaptcha_secret_key', metavar="SECRET", help="Secret key for reCAPTCHA v3")
define('slack_webhook_url', metavar="SECRET", help="URL for posting notifications to Slack")
define('repost_slack_webhook_url', metavar="SECRET", help="URL for posting best-of notifications to Slack")

# Stripe
define('stripe_secret_key', metavar='SECRET', help='Stripe.com secret key')
define('stripe_public_key', metavar='KEY', help='Stripe.com public key')
