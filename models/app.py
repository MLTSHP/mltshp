from datetime import datetime
import time
import uuid
import hashlib
from urlparse import urlparse
from tornado.options import options

from lib.flyingcow import Model, Property
from lib.utilities import base36encode, base36decode

import user
import accesstoken


class App(Model):
    user_id      = Property()
    title        = Property()
    description  = Property()
    secret       = Property()
    redirect_url = Property()
    deleted      = Property(default=0)
    created_at   = Property()
    updated_at   = Property()
    
    def save(self, *args, **kwargs):
        if options.readonly:
            self.add_error('_', 'Site is read-only.')
            return False

        self._set_dates()
        self._verify_title_and_description()
        self._verify_redirect_url()
            
        if self.errors:
            return False

        return super(App, self).save(*args, **kwargs)

    def _set_dates(self):
        """
        Sets the created_at and updated_at fields. This should be something
        a subclass of Property that takes care of this during the save cycle.
        """
        if self.id is None or self.created_at is None:
            self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
    def _verify_title_and_description(self):
        if self.title == '':
            self.add_error('title', 'Title cannot be blank.')
        
        if self.description == '':
            self.add_error('description', 'Description cannot be blank.')
        
        if self.errors:
            return False

    def _verify_redirect_url(self):
        if self.redirect_url == '' or self.redirect_url == None:
            return True

        the_url = urlparse(self.redirect_url)
        
        if the_url.netloc.find(options.app_host) > -1:
            return False
            
        if the_url.scheme != 'http' and the_url.scheme != 'https':
            self.add_error('redirect_url', 'Redirect URL must be valid.')
            return False
        
            
    def on_create(self):
        """Set the secret"""

        self.secret = hashlib.sha224("%s%s" % (str(uuid.uuid1()), time.time())).hexdigest()
        self.save()
        
    def key(self):
        return "%s-%s" % (base36encode(self.user_id), base36encode(self.id))
    
    def user(self):
        return user.User.get('id = %s', self.user_id)
    
    def get_title(self):
        return self.title or ''

    def get_description(self):
        return self.description or ''

    def disconnect_for_user(self, user):
        old_tokens = accesstoken.Accesstoken.where("user_id = %s and app_id = %s and deleted = 0", user.id, self.id)
        for old_token in old_tokens:
            old_token.delete()
    
    @classmethod
    def authorized_by_user(self, user):
        """
        Return list of apps authorized by user -- i.e. there is a non-deleted accesstoken.
        Takes instace of user object as argument.  We specify fields directly so we don't
        have a collision on user_id between the two joined tables (app & accesstoken).
        """
        sql = """select distinct app.id, app.user_id, app.title, app.description,
                 app.secret, app.redirect_url, app.deleted from app
                 left join accesstoken
                 on accesstoken.app_id = app.id
                 where accesstoken.user_id = %s
                 and accesstoken.deleted = 0
                 """ % user.id
        return self.object_query(sql)
    
    @staticmethod
    def by_key(key):
        if not key:
            return None        
        if len(key) < 3:
            return None
        if key.startswith('-') or key.endswith('-'):
            return None
            
        if key.find('-') == -1:
            return None
        
        (user_id, id) = key.split('-')
        return App.get('user_id = %s and id = %s', base36decode(user_id), base36decode(id))

