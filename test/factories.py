"""
Convenience functions for creating database-persisted mltshp objects to
test with.
"""
import models
import lib.utilities

def sharedfile(user, **kwargs):
    """
    Returns a sharedfile with a unique source file for the user.
    """
    sourcefile = models.Sourcefile(width=20,height=20,file_key="asdf",thumb_key="asdf_t")
    sourcefile.save()
    defaults = {
        'source_id' : sourcefile.id,
        'user_id' : user.id,
        'name' : "the name",
        'content_type' : "image/png",
        'description' : "description",
        'source_url' : 'http://www.mltshp.com/?hi',
    }    
    sharedfile = models.Sharedfile(**dict(defaults, **kwargs))
    sharedfile.save()
    sharedfile.share_key = lib.utilities.base36encode(sharedfile.id)
    sharedfile.save()
    return sharedfile

def user(**kwargs):
    defaults = {
        'name' : 'admin',
        'email' : 'admin@mltshp.com',
        'email_confirmed' : 1
    }    
    user = models.User(**dict(defaults, **kwargs))
    user.set_password('password')
    user.save()
    return user
