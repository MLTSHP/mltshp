#!/usr/bin/env python
"""
For a specific user, we get the last 10 files and collect the sharedfile ids
the file was saved from.  We then go through last 10 magic files and save 
them to user until we reach a sharedifile that has already been saved.
"""
import json
import models
from tornado.options import options


def main():
    user = models.User.get("name = %s", options.best_of_user_name)
    if not user:
        raise Exception("Username not found.")

    user_shake = user.shake()
    sharedfile_ids = set([sharedfile.parent_id for sharedfile in user_shake.sharedfiles()])

    to_add = []
    magicfiles = models.Magicfile.object_query("select * from magicfile order by id desc limit 10")
    for magicfile in magicfiles:
        if magicfile.sharedfile_id in sharedfile_ids:
            break
        sf = magicfile.sharedfile()
        if sf and sf.deleted == 0:
            to_add.insert(0, magicfile.sharedfile())

    for sharedfile in to_add:
        sharedfile.save_to_shake(user)

    results = {
        'files_saved': len(to_add)
    }
    return json.dumps(results)
