#!/usr/bin/env python

import sys
import json
import models
from tornado.options import options
import tornado.escape
import requests


"""
Delete a user from the system.
    - get the user id
"""

NAME = "delete-user"


def main():
    if len(sys.argv) > 2:

        #user = models.User.get("id=%s and name=%s", sys.argv[2], sys.argv[3])
        user = models.User.get("name=%s and nsfw=1 and is_paid=0", sys.argv[2])

        if not user:
            return json.dumps({'status': 'error', 'message': 'user not found or not eligible for deletion'})

        user.delete()

        if options.slack_webhook_url:
            try:
                msg = "User {0} was just deleted.".format(user.name)

                body = "{0}".format(
                    tornado.escape.json_encode(
                        {"text": msg,
                            "channel": "#moderation",
                            "username": "modbot",
                            "icon_emoji": ":ghost:"}))

                r = requests.post(options.slack_webhook_url, data=body)
            except Exception as e:
                pass

        return json.dumps({
            'user_id': user.id,
            'user_name': user.name
        })

    return json.dumps({'status': 'error',
                      'message': 'requires user name'})
