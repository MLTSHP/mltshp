import hashlib
import logging
import time

from tornado import options

class QueryCache(object):
    _store = {}
    _initialized = False

    @classmethod
    def initialize(cls):
        cls._initialized = True
        cls.clear()
    
    @classmethod
    def finish(cls):
        cls._initialized = False
        cls.clear()
    
    @classmethod
    def clear(cls):
        cls._store = {}
    
    @classmethod
    def set(cls, query, *args, **kwargs):
        if not cls._initialized:
            return False

        key = cls.key(query, *args)
        cls._store[key] = kwargs['result']
        return cls._store[key]

    @classmethod
    def get(cls, query, *args):
        if not cls._initialized:
            return None

        key = cls.key(query, *args)
        if key in cls._store:
            return cls._store[key]
        else:
            return None
    
    @classmethod
    def key(cls, query, *args):
        return hashlib.md5(query % args).hexdigest()


class ModelQueryCache(object):
    """
    Mix in with flyingcow Models to use global QueryCache.
    
    When used, it's important that there is a process that invalidates
    the cache in a meaningful way.  QueryCache will not be used 
    unless it is first initialized.
    
    QueryCache gets automatically invalidated on write.
    """
    @classmethod
    def query(self, query, *args):
        if not use_query_cache:
            return super(ModelQueryCache, self).query(query, *args)
        
        cached_response = QueryCache.get(query, *args)
        if cached_response:
            logging.debug((query % args) + " [CACHED]")
            return cached_response
        
        response = super(ModelQueryCache, self).query(query, *args)
        QueryCache.set(query, *args, result=response)
        return response
    
    @classmethod
    def execute(self, query, *args):
        """
        Clear QueryCache on any writes.
        """
        if use_query_cache:
            QueryCache.clear()
        return super(ModelQueryCache, self).execute(query, *args)


class RequestHandlerQueryCache(object):
    """
    A tornado RequestHandler mixin that regulates the query cache by clearing
    it and starting / stopping it between requests.
    """
    def initialize(self, *args, **kwargs):
        if use_query_cache:
            QueryCache.initialize()
        return super(RequestHandlerQueryCache, self).initialize(*args, **kwargs)
    
    def finish(self, *args, **kwargs):
        QueryCache.finish()
        return super(RequestHandlerQueryCache, self).finish(*args, **kwargs)

use_query_cache = False
