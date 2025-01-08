import tempfile
import os

from torndb import Connection
from tornado.options import options
from celery import chain
from celery.utils.log import get_task_logger

from tasks import mltshp_task

from ffmpy import FFmpeg
from PIL import Image
from lib.s3 import S3Bucket


logger = get_task_logger(__name__)


def db_connect():
    return Connection(
        options.database_host, options.database_name,
        options.database_user, options.database_password)


@mltshp_task()
def gif_to_video(sourcefile_id, file_key, input_file, format):
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
        options = "-c:v libvpx -auto-alt-ref 0 -crf 23 -b:v 2M -acodec none"

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

        # upload transcoded file to S3, then flag the sourcefile
        bucket = S3Bucket()
        logger.info("uploading transcoded video: %s" % file_key)
        bucket.upload_file(
            output_file,
            "%s/%s" % (format, file_key),
        )
        logger.info("-- upload complete")
        db = db_connect()
        db.execute(
            "UPDATE sourcefile SET %s_flag=1 WHERE id=%%s" % format,
            sourcefile_id)
        db.close()
    except Exception as ex:
        logger.exception("error transcoding %s - %s" % (sourcefile_id, input_file))
        raise ex
    finally:
        os.unlink(output_file)


@mltshp_task()
def remove_temp_file(temp_file):
    os.unlink(temp_file)


@mltshp_task()
def transcode_sharedfile(sharedfile_id):
    db = db_connect()

    sharedfile = db.get(
        "SELECT source_id FROM sharedfile WHERE id=%s AND content_type='image/gif' AND deleted=0",
        sharedfile_id)
    if not sharedfile:
        db.close()
        return

    # download sharedfile from S3
    sourcefile = db.get("SELECT id, file_key, webm_flag, mp4_flag FROM sourcefile WHERE id=%s", sharedfile["source_id"])
    db.close()

    if not sourcefile:
        return

    if sourcefile["webm_flag"] == 1 and sourcefile["mp4_flag"] == 1:
        return

    input_temp = tempfile.NamedTemporaryFile(
        mode="w+b",
        suffix=".gif",
        delete=False)
    input_file = input_temp.name

    bucket = S3Bucket()
    key = "originals/%s" % sourcefile["file_key"]
    logger.info("Downloading original GIF from S3 for sourcefile %s..." % sharedfile["source_id"])
    bucket.download_file(input_file, key)

    # Test to see if GIF is animated or not
    animated = False
    im = Image.open(input_file)
    try:
        im.seek(1) # skip to the second frame
        animated = True
    except EOFError:
        pass
    im.close()

    if not animated:
        os.unlink(input_file)
        db = db_connect()
        db.execute("UPDATE sourcefile SET mp4_flag=0, webm_flag=0 WHERE id=%s", sharedfile["source_id"])
        db.close()
        return

    if options.use_workers:
        tasks = []
        if sourcefile["webm_flag"] != 1:
            tasks.append(gif_to_video.si(sourcefile["id"], sourcefile["file_key"], input_file, "webm"))
        if sourcefile["mp4_flag"] != 1:
            tasks.append(gif_to_video.si(sourcefile["id"], sourcefile["file_key"], input_file, "mp4"))
        tasks.append(remove_temp_file.si(input_file))
        chain(*tasks).apply_async(expires=86400)  # expire in 1 day
    else:
        if sourcefile["webm_flag"] != 1:
            gif_to_video.delay_or_run(sourcefile["id"], sourcefile["file_key"], input_file, "webm")
        if sourcefile["mp4_flag"] != 1:
            gif_to_video.delay_or_run(sourcefile["id"], sourcefile["file_key"], input_file, "mp4")
        remove_temp_file.delay_or_run(input_file)
