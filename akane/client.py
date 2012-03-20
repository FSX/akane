"""
    akane.client
    ~~~~~~~~~~~~

    The client is a wrapper for the connection pool and also implements the
    supported commands.
"""

from .connection import Pool


class Client(object):
    def __init__(self, settings={}):
        self._pool = Pool(**settings)

    def send_command(self, callback, *args):
        conn = self._pool.get_free_conn()
        conn.send_command(callback, *args)

    def set(self, key, value, callback=None):
        self.send_command(callback, 'SET', key, value)

    def get(self, key, callback=None):
        self.send_command(callback, 'GET', key)

    def getset(self, key, value, callback=None):
        self.send_command(callback, 'GETSET', key, value)

    def mset(self, mapping, callback=None):
        items = []
        for pair in mapping.iteritems():
            items.extend(pair)
        self.send_command(callback, 'MSET', *items)

    def mget(self, keys, callback=None):
        self.send_command(callback, 'MGET', *keys)
