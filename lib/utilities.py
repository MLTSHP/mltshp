import hashlib
import re
import hmac
import time
import base64
import urllib.request, urllib.parse, urllib.error
from datetime import datetime, UTC
import urllib.request, urllib.parse, urllib.error

from PIL import Image
from tornado.options import options
import tornado.httpclient
import tornado.escape
from tornado.httpclient import HTTPRequest

from xml.dom import minidom


PLANS = {
    "mltshp-single": "Single Scoop",
    "mltshp-double": "Double Scoop",
}


def utcnow():
    return datetime.now(UTC)


def plan_name(plan_id):
    return PLANS.get(plan_id) or "None"


def undom(dom):
    children = dom.childNodes
    if len(children) == 0:
        return None
    elif len(children) == 1 and children[0].localName == None:
        return children[0].nodeValue
    else:
        node = {}
        for child in dom.childNodes:
            name = child.localName
            if name != None:
                value = undom(child)
                #node.setdefault(name, []).append(value)
                node[name] = value
    return node


def parse_xml(xml_string):
    return undom(minidom.parseString(xml_string))


def s3_authenticated_url(s3_key, s3_secret, bucket_name=None, file_path=None,
                             seconds=3600):
    """
    Return S3 authenticated URL sans network access or phatty dependencies like boto.
    """
    assert bucket_name
    assert file_path

    seconds = int(time.time()) + seconds
    to_sign = "GET\n\n\n%s\n/%s/%s" % (seconds, bucket_name, file_path)
    digest = hmac.new(s3_secret.encode("ascii"), to_sign.encode("ascii"), hashlib.sha1).digest()
    signature = urllib.parse.quote(base64.b64encode(digest).strip())
    signature = "?AWSAccessKeyId=%s&Expires=%s&Signature=%s" % (s3_key, seconds, signature)

    if options.aws_host == "s3.amazonaws.com":
        url_prefix = "https://"
        port = ""
    else:
        url_prefix = "http://"
        port = options.aws_port and (":%d" % options.aws_port) or ""

    return "%s%s.%s%s/%s%s" % (
        url_prefix, bucket_name, options.aws_host, port,
        file_path, signature)


def s3_url(file_path):
    """
    Return S3 authenticated URL sans network access or phatty dependencies like boto.
    """
    assert file_path

    port = ""
    if options.aws_host == "s3.amazonaws.com":
        url_prefix = 'https://'
    else:
        url_prefix = 'http://'
        if options.aws_port:
            port = ":%d" % options.aws_port

    return "%s%s.%s%s/%s" % (
        url_prefix, options.aws_bucket, options.aws_host, port, file_path)


def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    if not isinstance(number, int):
        raise TypeError('number must be an integer')

    # Special case for zero
    if number == 0:
        return '0'

    base36 = ''

    if number < 0:
        base36='-'
        number=-number

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return base36


def base36decode(number):
    return int(number,36)


def generate_digest_from_dictionary(values):
    h = hashlib.sha1()
    for value in values:
        h.update(("%s" % value).encode("ascii"))
    return h.hexdigest()


# Adapted from http://stackoverflow.com/questions/1551382/python-user-friendly-time-format
def pretty_date(time=False):
    """
    Expects a datetime in utc.
    """
    now = utcnow()
    diff = now - time
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( int(second_diff / 60) ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( int(second_diff / 3600) ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        diff = int(day_diff/7)
        diff_string = "week"
        if diff > 1:
            diff_string = "weeks"
        return  "%s %s ago" % (str(diff), diff_string)
    if day_diff < 365:
        diff = int(day_diff/30)
        diff_string = "month"
        if diff > 1:
            diff_string = "months"
        return "%s %s ago" % (str(diff), diff_string)

    diff_string = "year"
    diff = int(day_diff/365)
    if diff > 1:
        diff_string = "years"
    return "%s %s ago" % (str(diff), diff_string)


def normalize_string(token, timestamp, nonce, request_method, host, port, path, query_array):
    normalized_string = "%s\n" % (token)
    normalized_string += "%s\n" % (timestamp)
    normalized_string += "%s\n" % (nonce)
    normalized_string += "%s\n" % (request_method)
    normalized_string += "%s\n" % (host)
    normalized_string += "%s\n" % (port)
    normalized_string += "%s\n" % (path)
    if len(query_array) > 0:
        normalized_string += "%s\n" % ("\n".join(query_array))
    return normalized_string


def send_slack_notification(message, channel=None, username=None, icon_emoji=None):
    if options.slack_webhook_url is None:
        return

    try:
        payload = {"text": message}
        if channel is not None:
            payload['channel'] = channel
        if username is not None:
            payload['username'] = username
        if icon_emoji is not None:
            payload['icon_emoji'] = icon_emoji

        body = "payload=%s" % tornado.escape.url_escape(
            tornado.escape.json_encode(payload))
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch(
            HTTPRequest(
                url=options.slack_webhook_url,
                method='POST',
                body=body
            )
        )
    except Exception as e:
        # eh, wasn't that important anyway
        pass


def payment_notifications(user, action, amount=None):
    msg = None
    if action == "subscription":
        msg = """<https://%s/user/%s|%s> just gave us some cold hard cash: %s! :smile:""" % (
            options.app_host, user.name, user.name, amount
        )
    elif action == "cancellation":
        msg = """<https://%s/user/%s|%s> has canceled their subscription. :frowning:""" % (
            options.app_host, user.name, user.name
        )
    elif action == "redeemed":
        msg = """<https://%s/user/%s|%s> has redeemed a voucher for %s. :smile:""" % (
            options.app_host, user.name, user.name, amount
        )

    if msg is not None:
        send_slack_notification(msg)


def transform_to_square_thumbnail(file_path, size_constraint, destination):
    """
    Takes a local path with a file, and writes the thumbntail to the destination
    which is a io.BytesIO instance. Used by User.set_profile_image()
    """
    img = Image.open(file_path)
    # convert to RGB, probably for proper resizing of gifs.
    if img.mode != "RGB":
        img2 = img.convert("RGB")
        img.close()
        img = img2
    width, height = img.size

    # if image is below size constraint, we just paste it on
    # and let any pieces that are above constraint just get clipped off.
    if width < size_constraint or height < size_constraint:
        canvas = Image.new("RGB", (size_constraint, size_constraint,), (255, 255, 255,))
        canvas.paste(img, (0,0,))
        canvas.save(destination, format="JPEG", quality=95)
    # Otherwise, we crop the image to a square and then create thumbnail
    # out of it. Since Image.thumbnail method doesn't create good
    # looking thumbs otherwise.
    else:
        if width > height:
            max_dimension = height
        else:
            max_dimension = width
        cropped = img.crop((0,0,max_dimension,max_dimension,))
        cropped.load()
        cropped.thumbnail((size_constraint,size_constraint), Image.Resampling.LANCZOS)
        cropped.save(destination, format="JPEG", quality=95)
    img.close()
    return True

email_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
    r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain


def is_valid_voucher_key(key_value):
    from models import Voucher

    clean_key_value = key_value.replace(' ', '').upper()
    voucher = Voucher.by_voucher_key(clean_key_value)

    # validate key... right now, we support
    # thinkup promotional claim codes, which are in the form:
    # [A-Za-z0-9]{12} (whitespace is stripped)
    #if voucher is None:
    #    if re.match(r"^[A-Z0-9]{12}$", clean_key_value):
    #        # verify this is a valid code using ThinkUP API
    #        http = tornado.httpclient.HTTPClient()
    #        try:
    #            url = 'https://www.thinkup.com/join/api/bundle/?code=%s' % \
    #                 clean_key_value
    #            response = http.fetch(url)
    #            data = {}
    #            if response.code == 200:
    #                data = json.loads(response.body)
    #            if 'is_valid' in data and data['is_valid'] == True:
    #                return Voucher(voucher_key=data['code'],
    #                    promotion_id=options.thinkup_promotion_id)
    #        except tornado.httpclient.HTTPError as e:
    #            pass
    #        finally:
    #            http.close()

    if voucher and voucher.claimed_by_user_id > 0:
        return None

    return voucher


def uses_a_banned_phrase(s):
    """
    Dumb routine to test input string `s` for words or combinations
    of words. Used in conjunction with saving post title, description
    as a stop-gap mechanism to prevent spammers from self-promotion.
    """
    return False

def clean_search_term(s):
    """
    Routine to centralize search term character input cleaning rules.
    Replacing unicode left/right double quotation with standard quote
    """
    if s is None:
        return None

    return s.replace("\u201C", '"').replace("\u201D", '"')
