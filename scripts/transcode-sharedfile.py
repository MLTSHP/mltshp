import sys
from tornado.options import options

from models import Sharedfile
from tasks.transcode import transcode_sharedfile


def main():
    keys = sys.argv[2:]

    if len(keys) == 0:
        print "Selecting untranscoded sharedfiles..."
        select = """SELECT share_key
                    FROM sharedfile
                    JOIN sourcefile ON sourcefile.id = sharedfile.source_id
                    WHERE sharedfile.deleted = 0
                    AND sharedfile.content_type = 'image/gif'
                    AND sharedfile.parent_id = 0
                    AND (sourcefile.webm_flag != 1 OR sourcefile.mp4_flag != 1)
                    ORDER BY sharedfile.created_at DESC"""
        results = Sharedfile.query(select)
        for result in results:
            keys.append(result["share_key"])
        print "Found %d sharedfiles to transcode" % len(keys)

    for key in keys:
        sf = Sharedfile.get("share_key=%s AND content_type='image/gif' AND deleted=0", key)
        if sf is not None:
            print "Transcoding %s..." % sf.share_key
            transcode_sharedfile.delay_or_run(sf.id)
        else:
            print "Could not find sharedfile with key: %s" % key
