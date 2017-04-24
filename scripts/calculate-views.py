#!/usr/bin/env python
"""
Create celery tasks for all the sharefiles that have views since
last time this script was run.

This script is run at a regular interval via cron.
"""
import json

import models
from lib.flyingcow.db import connection


NAME = "calculate-views"


def main():
    """
    Find all sharedfiles and calculate their likes from fileview.
    """
    updated_sharedfiles = 0
    last_fileview = models.Fileview.last()
    if last_fileview:
        sharedfile_ids = models.Fileview.sharedfile_ids(before_id=last_fileview.id+1)

        conn = connection()
        cursor = conn._cursor()
        try:
            for sharedfile_id in sharedfile_ids:
                sharedfile = models.Sharedfile.get("id = %s", sharedfile_id)
                if sharedfile:
                    conn._execute(
                        cursor,
                        "DELETE FROM fileview WHERE sharedfile_id=%s AND user_id != %s AND id <= %s",
                        [sharedfile_id, sharedfile.user_id, last_fileview.id], {})
                    count = cursor.rowcount
                    if count > 0:
                        sharedfile.increment_view_count(count)
                        updated_sharedfiles += 1

            # delete the remaining rows; will only be cases where the image was
            # viewed by the owner of the sharedfile; we shouldn't actually have
            # these for new fileview records, just legacy ones...
            conn._execute(
               cursor,
               "DELETE FROM fileview WHERE id <= %s",
               [last_fileview.id], {})
        finally:
            cursor.close()

    results = {
        'updated_sharedfiles' : updated_sharedfiles
    }
    return json.dumps(results)