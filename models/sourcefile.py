import hashlib
import io
from urllib.parse import parse_qs, urlencode, urlparse

from tornado.escape import url_escape, json_encode
from tornado.options import options
from PIL import Image
from lib.s3 import S3Bucket

from lib.flyingcow import Model, Property
from lib.flyingcow.cache import ModelQueryCache
from lib.utilities import utcnow

import logging
logger = logging.getLogger('mltshp')


class Sourcefile(ModelQueryCache, Model):
    width = Property()          # original width dimension of source file
    height = Property()         # original height dimension of source file
    data = Property()           # JSON representation of a non-binary "source file"
    type = Property()           # MIME type of file
    file_key = Property()       # S3 handle for original image
    thumb_key = Property()      # S3 handle for 100x100 thumbnail JPEG
    small_key = Property()      # S3 handle for 200x184 rectangle JPEG
    mp4_flag = Property()       # indicator when a H.264 MPEG video exists (specific to GIFs)
    webm_flag = Property()      # indicator when a WEBM video exists (specific to GIFs; VP9 codec)
    nsfw = Property(default=0)
    created_at = Property()
    updated_at = Property()

    def save(self, *args, **kwargs):
        """
        Sets the dates before saving.
        """
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        super(Sourcefile, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def width_constrained_dimensions(self, width_constraint):
        """
        This is used to figure out the size at which something will render on
        a page, which is constrained with a width of 550px. For photos, the
        image size will be scaled down if it's too big, and otherwise, it will
        be presented as is. Videos also get scaled down if too big, but they also
        get enlarged to fit the width if smaller than constraint.
        """
        if self.width <= width_constraint and self.type == 'image':
            return (self.width, self.height)
        rescale_ratio = float(width_constraint) / self.width
        return (int(self.width * rescale_ratio), int(self.height * rescale_ratio))

    def nsfw_bool(self):
        """
        NSFW flag cast to a boolean.
        """
        if not self.nsfw or self.nsfw == 0:
            return False
        return True

    @staticmethod
    def get_by_file_key(file_key):
        """
        Returns a Sourcefile by its file_key.
        """
        return Sourcefile.get("file_key = %s", file_key)

    @staticmethod
    def get_sha1_url_key(url=None):
        if not url:
            return None
        h = hashlib.sha1()
        h.update(url)
        return h.hexdigest()

    @staticmethod
    def get_sha1_file_key(file_path=None, file_data=None):
        h = hashlib.sha1()
        if not file_data:
            try:
                BUF_SIZE = 65536

                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(BUF_SIZE)
                        if not data:
                            break
                        h.update(data)
            except Exception as e:
                return None
        else:
            # test if file_data is a string
            if isinstance(file_data, str):
                h.update(file_data.encode("UTF-8"))
            elif isinstance(file_data, bytes):
                h.update(file_data)
            else:
                raise Exception("file_data must be a string or bytes")
        return h.hexdigest()

    @staticmethod
    def get_from_file(file_path, sha1_value, type='image', skip_s3=None, content_type=None):
        existing_source_file = Sourcefile.get("file_key = %s", sha1_value)
        thumb_cstr = io.BytesIO()
        small_cstr = io.BytesIO()
        if existing_source_file:
            return existing_source_file
        try:
            logger.debug("creating %s" % file_path)
            img = Image.open(file_path)
            original_width = img.size[0]
            original_height= img.size[1]
        except Exception as e:
            return None

        if img.mode != "RGB":
            logger.debug("converting to RGB")
            img2 = img.convert("RGB")
            img.close()
            img = img2

        #generate smaller versions
        thumb = img.copy()
        small = img.copy()

        thumb.thumbnail((100,100), Image.Resampling.LANCZOS)
        small.thumbnail((240,184), Image.Resampling.LANCZOS)

        thumb.save(thumb_cstr, format="JPEG")
        small.save(small_cstr, format="JPEG")

        thumbnail_file_key = Sourcefile.get_sha1_file_key(file_data=thumb_cstr.getvalue())
        small_file_key = Sourcefile.get_sha1_file_key(file_data=small_cstr.getvalue())

        bucket = None
        if not skip_s3:
            logger.debug("making S3 bucket")
            bucket = S3Bucket()

            # save original file
            if type != 'link':
                logger.debug("putting object originals/%s" % sha1_value)
                bucket.upload_file(
                    file_path,
                    "originals/%s" % sha1_value,
                    ExtraArgs={
                        "ContentType": content_type,
                    },
                )

            # save thumbnail
            thumb_bytes = thumb_cstr.getvalue()
            logger.debug("putting object thumbnails/%s (length %d)" % (thumbnail_file_key, len(thumb_bytes)))
            bucket.put_object(
                thumb_bytes,
                "thumbnails/%s" % thumbnail_file_key,
                ContentType="image/jpeg",
            )

            # save small
            small_bytes = small_cstr.getvalue()
            logger.debug("putting object smalls/%s (length %d)" % (small_file_key, len(small_bytes)))
            bucket.put_object(
                small_bytes,
                "smalls/%s" % small_file_key,
                ContentType="image/jpeg",
            )

        img.close()
        thumb.close()
        small.close()

        #save source file
        logger.debug("saving sourcefile")
        sf = Sourcefile(
            width=original_width, height=original_height, file_key=sha1_value,
            thumb_key=thumbnail_file_key, small_key=small_file_key, type=type)
        sf.save()
        return sf

    @staticmethod
    def make_oembed_url(url):
        url_parsed = None
        try:
            url_parsed = urlparse(url)
        except:
            return None

        if not url_parsed or not url_parsed.hostname:
            return None

        if url_parsed.hostname.lower() not in ['youtube.com', 'www.youtube.com', 'vimeo.com', 'www.vimeo.com', 'youtu.be', 'flic.kr', 'flickr.com', 'www.flickr.com']:
            return None

        oembed_url = None
        if url_parsed.hostname.lower() in ['youtube.com', 'www.youtube.com', 'youtu.be']:
            # We want to strip any `si` value from the query, as it can be used to track the original
            # YouTube user that shared the link.
            query_params = parse_qs(url_parsed.query)
            if "si" in query_params:
                del query_params["si"]
                url_parsed = url_parsed._replace(
                    query=urlencode(query_params, doseq=True)
                )
            to_url = 'https://%s%s?%s' % (url_parsed.hostname, url_parsed.path, url_parsed.query)
            oembed_url = 'https://www.youtube.com/oembed?url=%s&maxwidth=550&format=json' % (url_escape(to_url))
        elif url_parsed.hostname.lower() in ['vimeo.com', 'www.vimeo.com']:
            to_url = 'https://%s%s' % (url_parsed.hostname, url_parsed.path)
            oembed_url = 'https://vimeo.com/api/oembed.json?url=%s&maxwidth=550' % (url_escape(to_url))
        elif url_parsed.hostname.lower() in ['flic.kr', 'flickr.com', 'www.flickr.com']:
            to_url = 'https://%s%s' % (url_parsed.hostname, url_parsed.path)
            oembed_url = 'https://www.flickr.com/services/oembed/?url=%s&maxwidth=550&format=json' % (url_escape(to_url))
        return oembed_url

    @staticmethod
    def create_from_json_oembed(link=None, oembed_doc=None, thumbnail_file_path=None, skip_s3=False):
        """
        Ideally this is a link right now. Specificallly a video link.

        JSON object, thumbnail_path, and the actual url comes in, a sha1 should be created from the url and the
            file_key takes that sha1 value. Then call get_from_file with the type=link
            value set along with the thumbnail path in place.

            The resulting sourcefile should then have the data field set with the oembed doc.

            A source file should be created and returned.
        """
        sha1_key = Sourcefile.get_sha1_file_key(file_path=None, file_data=link)
        sf = Sourcefile.get_from_file(thumbnail_file_path, sha1_key, type='link', skip_s3=skip_s3)
        if sf:
            sf.data = json_encode(oembed_doc)
            sf.save()
        return sf


