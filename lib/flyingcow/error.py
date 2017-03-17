
class Errors(dict):
    """
    A light wrapper for a dict, so we can test for existance of field errors in templates
    without getting AttributeErrors. We access keys as attributes.
    """
        
    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            return None
