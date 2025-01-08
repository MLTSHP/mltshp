#!/usr/bin/env python3

import sys

import mltshpoptions
import settings as app_settings


def load_settings():
    # Hardcode for now
    settings = "settings"

    try:
        settings_data = getattr(app_settings, settings)
    except AttributeError:
        sys.stderr.write("\nCouldn't find set of settings %r in 'settings'?\n" % settings)
        sys.exit(1)

    mltshpoptions.parse_dictionary(settings_data)


if __name__ == '__main__':
    load_settings()
    from celery.bin.celery import main
    main()
