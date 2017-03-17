#!/usr/bin/env python

import os.path
import sys

from celery.bin.base import Option
import celery.bin.celeryd
from tornado.options import define, options

import mltshpoptions
import settings


class TornadoWorkerCommand(celery.bin.celeryd.WorkerCommand):

    def get_options(self):
        opts = super(TornadoWorkerCommand, self).get_options()
        return opts + (
            Option('--settings', default='settings',
                action="store", dest="settings", type="str",
                help="Name of the set of settings to load"),
        )

    def run(self, *args, **opts):
        # Set up the settings first.
        settings_name = opts.pop('settings')
        try:
            settings_data = getattr(settings, settings_name)
        except AttributeError:
            sys.stderr.write("\nCouldn't find set of settings %r in 'settings'?\n" % settings_name)
            sys.exit(1)

        mltshpoptions.parse_dictionary(settings_data)

        return super(TornadoWorkerCommand, self).run(*args, **opts)


def main():
    # Act like the celeryd.main().
    celery.bin.celeryd.freeze_support()
    worker = TornadoWorkerCommand()
    worker.execute_from_commandline()


if __name__ == '__main__':
    main()
