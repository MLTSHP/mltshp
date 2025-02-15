#!/usr/bin/env python3
"""
For a specific user, we get the last 10 files and collect the sharedfile ids
the file was saved from.  We then go through last 10 magic files and save 
them to user until we reach a sharedifile that has already been saved.
"""
import json
import models
from tornado.options import options

from lib.utilities import send_slack_notification


def post_to_slack(sharedfile):
    cdn_host = options.cdn_host
    app_host = options.app_host
    scheme = cdn_host and "https" or "http"

    title = sharedfile.get_title()
    sourcefile = sharedfile.sourcefile()
    alt_text = sharedfile.get_alt_text(raw=True)
    description = sharedfile.get_description(raw=True)
    username = sharedfile.user.name
    postlink = f"{scheme}://{app_host}/p/{sharedfile.share_key}"

    payload = {
        "blocks": []
    }

    if title != "":
        payload["blocks"].append(
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": sharedfile.get_title(),
                    "emoji": False,
                },
            },
        )

    if sourcefile.type == "image":
        payload["blocks"].append(
            {
                "type": "image",
                "image_url": f"{scheme}://{cdn_host or app_host}/r/{sharedfile.share_key}",
                "alt_text": alt_text,
            },
        )
    elif sourcefile.type == "link":
        if sharedfile.source_url.contains("youtube.com") or sharedfile.source_url.contains("youtu.be"):
            try:
                data = json.loads(sourcefile.data)
            except Exception as e:
                return
            payload["blocks"].append(
                {
                    "type": "video",
                    "video_url": sharedfile.source_url,
                    "author_name": data["author_name"],
                    "alt_text": alt_text,
                    "thumbnail_url": data["thumbnail_url"],
                    "title": {
                        "type": "plain_text",
                        "text": data["title"],
                        "emoji": False,
                    },
                },
            )
        else:
            return

    payload["blocks"].append(
        {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [
                        {
                            "type": "link",
                            "text": f"@{username}",
                            "url": f"{scheme}://{cdn_host or app_host}/user/{username}",
                        },
                        {
                            "type": "link",
                            "text": postlink,
                            "url": postlink,
                        },
                        {
                            "type": "date",
                            "timestamp": sharedfile.created_at.timestamp(),
                            "format": "posted {ago}",
                        },
                    ],
                },
            ],
        }
    )

    if description != "":
        payload["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": description,
                    "emoji": False,
                }
            }
        )

    send_slack_notification(payload=payload, channel="#popular", username="mltshp", icon_emoji=":popular:")


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
        try:
            post_to_slack(sharedfile)
        except Exception as e:
            print(f"Error posting to slack: {e}")
            pass

    results = {
        'files_saved': len(to_add)
    }
    return json.dumps(results)
