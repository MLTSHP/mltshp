#!/usr/bin/env python

import os.path
import sys

import celery.bin.worker
from tornado.options import define, options

import mltshpoptions
import settings as app_settings


class TornadoWorkerCommand(celery.bin.worker.worker):

    def add_arguments(self, parser):
        super(TornadoWorkerCommand, self).add_arguments(parser)
        wopts = parser.add_argument_group('MLTSHP Worker Options')
        wopts.add_argument(
            '--settings', default='settings',
            action="store", dest="settings", type=str,
            help="Name of the set of settings to load"
        )

    def run(self, hostname=None, pool_cls=None, app=None, uid=None, gid=None,
            loglevel=None, logfile=None, pidfile=None, statedb=None,
            settings=None,
            **kwargs):
        # Set up the settings first.
        try:
            settings_data = getattr(app_settings, settings)
        except AttributeError:
            sys.stderr.write("\nCouldn't find set of settings %r in 'settings'?\n" % settings)
            sys.exit(1)

        mltshpoptions.parse_dictionary(settings_data)

        return super(TornadoWorkerCommand, self).run(hostname, pool_cls, app, uid, gid,
            loglevel, logfile, pidfile, statedb, **kwargs)


def main(app=None):
    if __name__ != '__main__':  # pragma: no cover
        sys.modules['__main__'] = sys.modules[__name__]
    from billiard import freeze_support
    freeze_support()
    TornadoWorkerCommand(app).execute_from_commandline()


if __name__ == '__main__':
    main()
