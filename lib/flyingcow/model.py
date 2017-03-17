import re
import logging
import time

import error
import db
import properties

class MultipleRows(Exception):
    def __str__(self):
        return "Multiple rows returned for get() query"

class BaseModel(type):
    """
    Used to create the class for our Model definitions.  Allows us to
    cache the properties before they are used as well as have nicer
    Property definition syntax.
    """
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return super(BaseModel, cls).__new__(cls, name, bases, attrs)
                
        new_class = type.__new__(cls, name, bases, attrs)
        for key, value in attrs.items():
            if isinstance(value, properties.Property):
                value.contribute_to_class(new_class, key)
        new_class.properties()
        return new_class

class Model(object):
    """
    The Model class that gets inherited to create table-specific Models.
    """
    __metaclass__ = BaseModel
    
    def __init__(self, *args, **kwargs):
        self._id = None
        self.connection = db.connection()
        self.errors = error.Errors()
        
        # populate existing Properties from any keyword arguments
        self._populate_properties(False, **kwargs)
        
        # hook for subclasses.
        self.initialize(*args, **kwargs)

    @property
    def id(self):
        """
        A special property that is never set directly.  Its presence denotes
        that an instance is tied to a DB record.
        """
        return self._id
    
    def saved(self):
        """
        A way to check if object has been saved.
        """
        if self._id:
            return True
        else:
            return False

    def initialize(self, *args, **kwargs):
        """
        A hook for subclasses to override model initialization.
        """
    
    def add_error(self, property_name, error_message):
        """
        Used to add any errors while validating an object.
        """
        self.errors[property_name] = error_message
    
    def on_create(self):
        pass
        
    def on_update(self):
        pass
        
    def save(self):
        """
        Builds the query to save all of the object's db attributes.
        """
        if not self.saved():
            sql_snippet = []
            values = []
            for property_name in self.properties():
                sql_snippet.append('%s')
                values.append(getattr(self, property_name))
            sql_snippet = ','.join(sql_snippet)

            sql = "INSERT INTO %s (%s) VALUES (%s)" % (self._table_name(), ','.join(self.properties()), sql_snippet)
            self._id = self.execute(sql, *values)
            self.on_create()
        else:
            sql_set_snippets = []
            values = []
            for property_name in self.properties():
                sql_set_snippets.append(property_name + " = %s")
                values.append(getattr(self, property_name))
            sql_set_snippets = ','.join(sql_set_snippets)
            sql = "UPDATE %s SET %s where id = %s" % (self._table_name(), sql_set_snippets, self._id)
            self.execute(sql, *values)
            self.on_update()
        return True

    def update_attribute(self, name, value):
        """
        Updates only one field, without impacting the rest.
        """
        if name not in self.properties():
            return False
        setattr(self, name, value)
        sql = "UPDATE %s SET %s = %s where id = %s" % (self._table_name(), name, "%s", "%s")
        self.execute(sql, value, self.id)
        return True
    
    def _populate_properties(self, include_id, **kwargs):
        """
        Populates the properties with values, if include_id is passed in,
        means we are populating data from the database, so allow populating the
        id field.
        """
        if include_id:
            if 'id' in kwargs:
                self._id = kwargs['id']
                kwargs.pop('id')
        if not kwargs:
            return
        for property_name in self.properties():
            if property_name in kwargs:
                setattr(self, property_name, kwargs[property_name])
                kwargs.pop(property_name)
        for remaining_field in kwargs:
            setattr(self, remaining_field, kwargs[remaining_field])

    @classmethod
    def get(cls, get_query, *args):
        """
        Runs a select query and returns one instance of the Model's objects or None.
        
        Raises a MultipleRows exception if more than one row is returned.
        """
        select = "SELECT * FROM %s WHERE %s" % (cls._table_name(), get_query)
        rows = cls.query(select, *args)
        if not rows:
            return None
        elif len(rows) > 1:
            raise MultipleRows
        else:
            return cls._make_instance(rows[0])

    @classmethod
    def where(cls, where_query, *args):
        """
        Runs a select query and returns a list of Model objects or an empty list.
        """
        select = "SELECT * FROM %s WHERE %s" % (cls._table_name(), where_query)
        results = []
        for result in cls.query(select, *args):
            results.append(cls._make_instance(result))
        return results
    
    @classmethod
    def where_count(cls, where_query, *args):
        """
        Runs a select query and returns a list of Model objects or an empty list.
        """
        select = "SELECT count(id) FROM %s WHERE %s" % (cls._table_name(), where_query)
        result = cls.query(select, *args)
        return result[0]['count(id)']

    @classmethod
    def object_query(cls, query, *args):
        """
        Returns Model objects for any full SQL query.  It is the query's 
        responsibility to include all the fields a model needs.
        """
        results = []
        for result in cls.query(query, *args):
            results.append(cls._make_instance(result))
        return results
    
    @classmethod
    def query(cls, query, *args):
        """
        A raw query that doesn't try to coerce the results into
        Model objects.
        """
        start_time = time.time()
        result = db.connection().query(query, *args)
        query_run_time = (time.time() - start_time) * 1000      
        logging.debug((query % args) + " [%s ms]" % query_run_time)
        return result
     
    @classmethod
    def execute(cls, query, *args):
        """
        Used for writes and updates, returns row id of last insert.
        """
        start_time = time.time()
        result = db.connection().execute(query, *args)
        query_run_time = (time.time() - start_time) * 1000      
        logging.debug((query % args) + " [%s ms]" % query_run_time)
        return result
    
    @classmethod
    def all(cls, conditions='', *args):
        """
        Runs a select query and returns a list of Model objects or an empty list.
        """
        select = "SELECT * FROM %s %s" % (cls._table_name(), conditions)
        results = []
        for result in cls.query(select, *args):
            results.append(cls._make_instance(result))
        return results
        
    _properties_cache = None
    @classmethod
    def properties(cls):
        """Returns a dictionary of all the Properties defined for this model. Caches
        the result in an class variable."""
        if cls._properties_cache is not None:
            return cls._properties_cache

        cls._properties_cache = []
        for key in cls.__dict__.keys():
            if isinstance(cls.__dict__[key], properties.Property):
                cls._properties_cache.append(key)
        return cls._properties_cache

    @classmethod
    def _make_instance(cls, result):
        """
        Constructs an instance from a dictionary returned by a query result.
        """
        new_instance = cls()
        new_instance._populate_properties(True, **result)
        return new_instance
    
    @classmethod
    def _table_name(cls):
        return re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__).lower()
