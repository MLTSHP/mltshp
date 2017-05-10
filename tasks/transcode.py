import tempfile
import os
from datetime import timedelta

from torndb import Connection
from tornado.options import options
from celery import chain
from celery.utils.log import get_task_logger

from tasks import mltshp_task
from models import Sourcefile

from ffmpy import FFmpeg
from lib.s3 import S3Bucket
from boto.s3.key import Key


logger = get_task_logger(__name__)


def db_connect():
    return Connection(
        options.database_host, options.database_name,
        options.database_user, options.database_password)


@mltshp_task()
def gif_to_video(sourcefile_id, input_file, format):
    from models import Sourcefile

    result = None

    options = None
    if format == "mp4":
        options = "-c:v libx264 -acodec none -crf 23 -profile:v baseline -level 3.0 -pix_fmt yuv420p"
        db = db_connect()
        sourcefile = db.get("SELECT width, height FROM sourcefile WHERE id=%s", sourcefile_id)
        db.close()
        if not sourcefile:
            return

        width = int(float(sourcefile["width"]))
        height = int(float(sourcefile["height"]))

        # scale if necessary
        if width % 2 == 1:
            if height % 2 == 1:
                options += " -vf scale=%s:%s" % (str(width-1), str(height-1))
            else:
                options += " -vf scale=-2:ih"
        else:
            if height % 2 == 1:
                options += " -vf scale=iw:-2"

    elif format == "webm":
        options = "-vcodec libvpx-vp9 -lossless 1"

    output_file = input_file.replace(".gif", ".%s" % format)

    # now, transcode...

    try:
        ff = FFmpeg(
            inputs={input_file: None},
            outputs={output_file: options}
        )
        logger.info("invoking transcode operation: %s" % ff.cmd)
        result = ff.run()
        logger.info("-- transcode completed")
    except Exception as ex:
        logger.exception("error transcoding %s - %s" % (sourcefile_id, input_file))
    finally:
        if result:
            # check for output file
            # upload transcoded file to S3, then save the key
            upload_key = Sourcefile.get_sha1_file_key(output_file)
            if upload_key:
                bucket = S3Bucket()
                key = Key(bucket)
                key.key = "%s/%s" % (format, upload_key)

                logger.info("uploading transcoded video: %s" % upload_key)
                key.set_contents_from_filename(output_file)
                logger.info("-- upload complete")
                db = db_connect()
                db.execute(
                    "UPDATE sourcefile SET %s_key=%%s WHERE id=%%s" % format,
                    upload_key, sourcefile_id)
                db.close()

            os.unlink(output_file)


@mltshp_task()
def remove_temp_file(temp_file):
    os.unlink(temp_file)


@mltshp_task()
def transcode_sharedfile(sharedfile_id):
    db = db_connect()

    sharedfile = db.get(
        "SELECT source_id, parent_id, size FROM sharedfile WHERE id=%s AND content_type='image/gif' AND deleted=0",
        sharedfile_id)
    if not sharedfile:
        db.close()
        return

    # download sharedfile from S3
    sourcefile = db.get("SELECT id, file_key, webm_key, mp4_key FROM sourcefile WHERE id=%s", sharedfile["source_id"])
    db.close()

    if not sourcefile:
        return

    if sourcefile["webm_key"] and sourcefile["mp4_key"]:
        return

    input_temp = tempfile.NamedTemporaryFile(
        mode="w+b",
        bufsize=int(float(sharedfile["size"])),
        suffix=".gif",
        delete=False)
    input_file = input_temp.name

    bucket = S3Bucket()
    key = Key(bucket)
    key.key = "originals/%s" % sourcefile["file_key"]
    logger.info("Downloading original GIF from S3 for sourcefile %s..." % sharedfile["source_id"])
    key.get_contents_to_filename(input_file)

    if options.use_workers:
        tasks = []
        if not sourcefile["webm_key"]:
            tasks.append(gif_to_video.s(sourcefile["id"], input_file, "webm"))
        if not sourcefile["mp4_key"]:
            tasks.append(gif_to_video.s(sourcefile["id"], input_file, "mp4"))
        tasks.append(remove_temp_file.s(input_file))
        chain(*tasks).apply_async(expires=timedelta(days=1))
    else:
        if not sourcefile["webm_key"]:
            gif_to_video.delay_or_run(sourcefile["id"], input_file, "webm")
        if not sourcefile["mp4_key"]:
            gif_to_video.delay_or_run(sourcefile["id"], input_file, "mp4"),
        remove_temp_file.delay_or_run(input_file)
