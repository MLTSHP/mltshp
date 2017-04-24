#!/usr/bin/env python
"""
Run a script that is located in a directory relative to the project root.

This allows us to keep one-off scripts out of the root dir namespace while
giving them access to bootstrap app components without sys.path acrobatics.

The convention is that each script's point of entry should be the main
function, which should return a JSON formatted string after the process
completes successfully.  The return value and other details are logged
using ScriptLog.

Example:

    ./runner.py scripts/calculate-views.py

"""
import sys
import optparse
import json

from tornado.options import options

import mltshpoptions
import settings
import models
import lib.flyingcow
import stripe


def run(script_path):
    module_path = script_path[:-3].replace('/', '.')
    script_name = module_path.split('.').pop()
    imported_module = __import__(module_path, None, None, [""])
    script_log = models.ScriptLog(name=script_name)
    script_log.start_running()
    try:
        result = imported_module.main()
        if result:
            script_log.result = result
        script_log.success = 1
    except Exception, e:
        script_log.success = 0
        script_log.result = json.dumps({'error': str(e)})
        sys.exit("Exception: %s" % e)
    finally:
        script_log.save()


def main(opts, args):
    if len(args) == 0:
        sys.exit("Need to specify a relative path to the script you want to run.")

    script_path = args[0]
    if not script_path.endswith('.py'):
        sys.exit("You can only reference python scripts that end with a .py extension.")

    mltshpoptions.parse_dictionary(getattr(settings, opts.settings))

    # if a server argument was specified and doesn't match with the
    # server_id configured for settings, then exit silently
    # without running
    if opts.server_id and opts.server_id != options.server_id:
        exit(0)

    lib.flyingcow.register_connection(host=options.database_host,
        name=options.database_name, user=options.database_user,
        password=options.database_password)    

    if options.stripe_secret_key:
        stripe.api_key = options.stripe_secret_key

    run(script_path)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-s", "--settings", dest="settings",
                    help="name of the settings dict inside the settings file used to bootstrap environment", 
                    metavar="PATH", default='settings')
    parser.add_option("--server_id", dest="server_id",
                    help="name of the server to scope for this script")
    main(*parser.parse_args())
