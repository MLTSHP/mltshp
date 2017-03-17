class Property(object):
    """
    A way to denote a database property inside a model. Raw value of property is 
    stored in the instance of the Model w/ the property name prefixed with _.
    """
    def __init__(self, name=None, default=None):
        self.name = name
        self.default = default

    def __get__(self, model_instance, type):
        if model_instance is None:
            return self        
        try:
            return getattr(model_instance, self._raw_value_name())
        except AttributeError:
            return self.default

    def __set__(self, model_instance, value):
        setattr(model_instance, self._raw_value_name(), value)

    def _raw_value_name(self):
        return '_' + self.name
    
    def contribute_to_class(self, cls, name):
        """
        We use this hook when we're building the Model class to
        pass in the name of the attribute this Property is attached to.
        """
        if not self.name:
            self.name = name