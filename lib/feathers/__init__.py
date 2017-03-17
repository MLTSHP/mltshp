import sys
import urllib
import urlparse
import hmac
import hashlib
import binascii
import time
import uuid

import tornado.httpclient
import tornado.ioloop

class Feathers(object):
    """
    An experimental, minimalist twitter client to be used with Tornado.
    
    Translates an API method:
    
    (GET) statuses/public_timeline.format?include_entities=1
    
    Using chained property-access syntax:
    
    feather = Feathers(key='your app key', secret='your app secret')
    feather.statuses.public_timeline.get({'include_entitites' : 1})
    """
    __current_method = ''
    
    endpoint = "https://api.twitter.com/"
    api_version = '1'
    format = 'json'
    key = ''
    secret = ''
    
    def __init__(self, key='', secret=''):
        assert key
        assert secret
        self.key = key
        self.secret = secret
    
    def __getattr__(self, name):
        """
        Missing attributes get concatenated to  final api path.  Each 
        new attribute is seperated by a / Returns self so its chainable.  
        Gets reset when get() is called.
        """
        self.__current_method = self.__current_method + '/' + name
        return self
    
    def get(self, params={}, headers={}, callback=None, token_key=None, token_secret=None):
        """
        Send a GET request.
        
        If a user's token_key and token_secret are passed in, prepare an authenticated request
        on behalf of the user.
        """
        base_url = self._build_base_url(self.__current_method)
        if token_key and token_secret:
            params['oauth_consumer_key'] = self.key
            params['oauth_signature_method'] ="HMAC-SHA1"
            params['oauth_timestamp'] = str(int(time.time()))
            params['oauth_nonce'] = binascii.b2a_hex(uuid.uuid4().bytes)
            params['oauth_version'] = "1.0"
            params['oauth_token'] = token_key
            signature = self._oauth_signature(self.secret, "GET", base_url, params, token_secret)
            params['oauth_signature'] = signature
        url = self._build_url(base_url, params)
        self.__current_method = ''
        return self._fetch(url, headers, callback)
    
    def _build_base_url(self, method):
        return self.endpoint + self.api_version + method + '.' + self.format
    
    def _build_url(self, base_url, params):
        query = '' if not params else '?' + urllib.urlencode(params)
        return base_url + query
    
    def _fetch(self, url, headers={}, callback=None):
        """
        Make the request. If an IOloop is available make request asynchronous and use the
        passed in callback if it's provided.
        """
        request = tornado.httpclient.HTTPRequest(url=url, method="GET", headers=headers)
        if tornado.ioloop.IOLoop.initialized():
            http = tornado.httpclient.AsyncHTTPClient()
            http.fetch(request, callback)
        else:
            http = tornado.httpclient.HTTPClient()
            return http.fetch(request)

    @classmethod
    def _oauth_signature(self, consumer_secret, method, url, parameters={}, token_secret=None):
        """
        From tornado.auth
        
        Calculates the HMAC-SHA1 OAuth 1.0 signature for the given request.

        See http://oauth.net/core/1.0/#signing_process
        """
        parts = urlparse.urlparse(url)
        scheme, netloc, path = parts[:3]
        normalized_url = scheme.lower() + "://" + netloc.lower() + path

        base_elems = []
        base_elems.append(method.upper())
        base_elems.append(normalized_url)
        base_elems.append("&".join("%s=%s" % (k, self._oauth_escape(str(v)))
                                   for k, v in sorted(parameters.items())))
        base_string =  "&".join(self._oauth_escape(e) for e in base_elems)
        
        key_elems = [consumer_secret]
        key_elems.append(token_secret if token_secret else "")
        key = "&".join(key_elems)
        
        hash = hmac.new(key, base_string, hashlib.sha1)
        return binascii.b2a_base64(hash.digest())[:-1]
    
    @classmethod
    def _oauth_escape(self, val):
        """
        From tornado.auth
        """
        if isinstance(val, unicode):
            val = val.encode("utf-8")
        return urllib.quote(val, safe="~")
