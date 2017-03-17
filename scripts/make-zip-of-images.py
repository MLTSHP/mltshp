# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Create a zip file of all the images posted or shared from 
an account, zip into a file on S3, and email notification to them.
"""
import models
import sys
from lib.s3 import S3Bucket
from boto.s3.key import Key
from tornado.options import options
import json
import os
import subprocess
import postmark

NAME = "make-zip-of-images"

def main():
    names = sys.argv[2:]
    for name in names:
        make_zip_file(name)
    
    results = {
        'last_name': name,    
        'command' : 'make-zip-of-images'
    }
    return json.dumps(results)

def percent_cb(complete, total):
    sys.stdout.write('.')
    sys.stdout.flush()

def make_zip_file(for_user=None):
    """
    get all shared files, pull to /mnt, zip them into a file and then email the
    user in their user account.
    """
    if not for_user:
        sys.exit()

    s3_bucket = S3Bucket()

    user = models.User.get("name='{0}'".format(for_user))
    if not user:
        return json.dumps({'status':'error', 'message':'user not found'})

    os.mkdir("/mnt/backups/users/{0}".format(user.name))

    
    sfs = models.Sharedfile.where("user_id = %s and deleted=0 order by id", user.id)

    if sfs:
        print(len(sfs))
        for sf in sfs:
            source = sf.sourcefile()
            if source.type == 'link':
                sys.stdout.write('x')
                sys.stdout.flush()
                continue
            else:
                sys.stdout.write('.')
                sys.stdout.flush()
            file_object = s3_bucket.get_key("originals/{0}".format(source.file_key))
            extension = ""
            if sf.content_type == 'image/gif':
                extension = "gif"
            elif sf.content_type == 'image/jpg' or sf.content_type == 'image/jpeg':
                extension = "jpg"
            elif sf.content_type == 'image/png':
                extension = "png"

            if extension == "":
                print(sf.content_type)
                print("extension blank")
                sys.exit()

            file_object.get_contents_to_filename("/mnt/backups/users/{0}/{1}.{2}".format(user.name, sf.share_key, extension))

        #zip contents of directory and save to /users/id-name.zip
        subprocess.call(["zip", "-r", "/mnt/backups/users/{0}.zip".format(user.name), "/mnt/backups/users/{0}/".format(user.name)])

        #upload to s3 as /bucket-name/account/id/images.zip
        k = Key(s3_bucket)
        k.key = "account/{0}/images.zip".format(user.id)
        k.set_contents_from_filename("/mnt/backups/users/{0}.zip".format(user.name), cb=percent_cb, num_cb=10)

        happy_url = k.generate_url(expires_in=72000)
        #email link to user email 8 hours
        pm = postmark.PMMail(api_key=options.postmark_api_key,
            sender="hello@mltshp.com", to=user.email,
            subject="[mltshp] Your Images Are Ready!",
            text_body="Hi, you requested to receive all of your images in a .zip file.\n" + \
            "Here they are! This link is good for the next TWENTY hours starting…now.\n\n" + \
            "{0}\n\n".format(happy_url) + \
            "Thanks for making MLTSHP so much fun. :D\n" + \
            "- MLTSHP")
        pm.send()

