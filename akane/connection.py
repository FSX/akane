"""
    akane.connection
    ~~~~~~~~~~~~~~~~

    All functionality regarding sending and receiving data to redis.
"""


import socket

from tornado.ioloop import IOLoop
from tornado import iostream

import hiredis

from .exceptions import PoolError


class Connection(object):

    _busy = False
    _callback = None

    def __init__(self, host='localhost', port=6379,
                 encoding='utf-8', encoding_errors='strict'):
        self.host = host
        self.port = port
        self.encoding = encoding
        self.encoding_errors = encoding_errors

        self._reader = hiredis.Reader()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        s.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

        self._stream = iostream.IOStream(s)
        self._stream.connect((host, port))

    def busy(self):
        return self._busy

    def closed(self):
        self._stream.closed()

    def send_command(self, callback, *args):
        parts = []
        for arg in args:
            if isinstance(arg, unicode):
                arg = arg.encode('utf-8', 'strict')
            parts.append('$%s\r\n%s\r\n' % (len(arg), arg))

        command = '*%s\r\n%s' % (len(parts), ''.join(parts))

        self._busy = True
        self._callback = callback
        self._stream.write(command)
        self._stream.read_until('\r\n', self._handle_read)

    def _handle_read(self, data):
        self._reader.feed(data)

        response = self._reader.gets()
        if response is not False:
            self._busy = False
            cb = self._callback
            self._callback = None
            if cb is not None:
                cb(response)
            return

        self._stream.read_until('\r\n', self._handle_read)



class Pool(object):

    closed = True

    def __init__(self, connections=1, *args, **kwargs):
        self.closed = False
        self._pool = set()

        for i in range(connections):
            self._pool.add(Connection(*args, **kwargs))

    def get_free_conn(self):
        if self.closed:
            raise PoolError('connection pool is closed')
        for conn in self._pool:
            if not conn.busy():
                return conn
        raise PoolError('connection pool exhausted')

    def close(self):
        if self.closed:
            raise PoolError('connection pool is closed')
        for conn in self._pool:
            if not conn.closed():
                conn.close()
        self._pool = set()
        self.closed = True
