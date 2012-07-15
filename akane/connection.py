"""
    akane.connection
    ~~~~~~~~~~~~~~~~

    All functionality regarding sending and receiving data to redis.
"""

import sys
import socket

from tornado.ioloop import IOLoop
from tornado import iostream

import hiredis

from .exceptions import PoolError, ReplyError
from .utils import redis_request


if sys.version_info[0] < 3:
    DELIMITER = '\r\n'
else:
    DELIMITER = b'\r\n'


class Connection(object):

    _busy = False
    _callback = None

    def __init__(self, host='localhost', port=6379, ioloop=None):
        self.host = host
        self.port = port
        self._ioloop = ioloop or IOLoop.instance()
        self._parser = hiredis.Reader(encoding="utf-8")

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        s.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        s.settimeout(None)

        self._stream = iostream.IOStream(s, self._ioloop)
        self._stream.connect((host, port))

    def busy(self):
        return self._busy

    def closed(self):
        self._stream.closed()

    def send_request(self, callback, *args):
        self._busy = True
        self._callback = callback
        self._stream.write(redis_request(args))
        self._stream.read_until(DELIMITER, self._handle_read)

    def _handle_read(self, data):
        self._parser.feed(data)

        parsed_data = self._parser.gets()
        if parsed_data is False:
            next  = True
            if data[0] == '$':
                next = int(data[1:-2])
        else:
            next = False

        if next is True:
            self._stream.read_until(DELIMITER, self._handle_read)
        elif next > 0:
            self._stream.read_bytes(next, self._handle_read)
        else: # if next is False
            self._busy = False
            cb = self._callback
            self._callback = None
            if cb is not None:
                cb(parsed_data)
            return


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
