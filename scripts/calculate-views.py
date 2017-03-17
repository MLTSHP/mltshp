#!/usr/bin/env python
"""
Create celery tasks for all the sharefiles that have views since
last time this script was run.

This script is run at a regular interval via cron.
"""
import json

import models

NAME = "calculate-views"

def main():
    script_log = models.ScriptLog.last_successful(NAME)
    if script_log and script_log.result:
        try:
            last_result = json.loads(script_log.result)
            return run_from(last_result['last_fileview_id'])
        except ValueError, AttributeError:
            pass
    return run_from()


def run_from(after_id=None):
    """
    Find all sharedfiles and calculate their likes starting
    at the fileview id supplied by after_id.
    """
    last_fileview = models.Fileview.last()
    updated_sharedfiles = 0
    for sharedfile_id in models.Fileview.sharedfile_ids(after_id=after_id):
        sharedfile = models.Sharedfile.get("id = %s and deleted = 0", sharedfile_id)
        if sharedfile:
            updated_sharedfiles += 1
            sharedfile.update_view_count()
    results = {
        'last_fileview_id': last_fileview.id,
        'updated_sharedfiles' : updated_sharedfiles
    }
    return json.dumps(results)