import torndb

class NoConnectionRegistered(Exception):
    """
    Raised when a connection is attempted to be used without
    having one registered to begin with.
    """


class ConnectionManager(object):
    """
    Helps manage a connection between modules.
    """
    def __init__(self):
        self._connection = None
    
    def register(self, host='localhost', name=None, user=None, password=None, charset="utf8mb4"):
        self._connection = self._connection or torndb.Connection(host, name, user, password, charset=charset)
        return self._connection
    
    def connection(self):
        if not self._connection:
            raise NoConnectionRegistered
        return self._connection

IntegrityError = torndb.IntegrityError
OperationalError = torndb.OperationalError

_connection_manager = ConnectionManager()
register_connection = _connection_manager.register
connection = _connection_manager.connection
