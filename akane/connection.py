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

from .exceptions import PoolError
from .utils import redis_request


if sys.version_info[0] < 3:
    string_type = unicode
    DELIMITER = '\r\n'
else:
    string_type = str
    DELIMITER = b'\r\n'



class ReplyParser(object):
    def __init__(self):
        self._mb_count = 0
        self._buffer = False # False means empty
        self._read_next = False
        self._continue_bulk = False

    def feed(self, data):
        t = data[0]

        if t == '*':
            d = int(data[1:-2])
            if d != '-1':
                self._read_next = True
                self._mb_count = d
            else:
                self._read_next = False
                self._buffer = None
        elif t in '+:':
            reply = data[1:-2]
            if t == ':':
                reply = int(reply)

            if self._mb_count > 0:
                self._buffer.append(reply)
                self._mb_count -= 1
                if self._mb_count == 0:
                    self._read_next = False
                else:
                    self._read_next = True
            else:
                self._buffer = reply
                self._read_next = False
        elif t == '$':
            d = int(data[1:-2])
            if d != '-1':
                self._read_next = d + 2
                self._continue_bulk = True
            else:
                reply = None

                if self._mb_count > 0:
                    self._buffer.append(reply)
                    self._mb_count -= 1
                    self._read_next = True
                else:
                    self._buffer = reply
                    self._read_next = False
        elif self._continue_bulk is True:
            reply = data[:-2]
            self._continue_bulk = False
            if self._mb_count > 0:
                self._buffer.append(reply)
                self._mb_count -= 1
                self._read_next = True
            else:
                self._buffer = reply
                self._read_next = False

    def read_next(self):
        return self._read_next

    def gets(self):
        if self._buffer is False:
            return False
        try:
            return self._buffer
        finally:
            self._buffer = False



class Connection(object):

    _busy = False
    _callback = None

    def __init__(self, host='localhost', port=6379,
                 encoding='utf-8', encoding_errors='strict'):
        self.host = host
        self.port = port
        self.encoding = encoding
        self.encoding_errors = encoding_errors

        # self._reader = hiredis.Reader()
        self._parser = ReplyParser()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        s.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

        self._stream = iostream.IOStream(s)
        self._stream.connect((host, port))

    def busy(self):
        return self._busy

    def closed(self):
        self._stream.closed()

    def send_request(self, callback, *args):
        # parts = []
        # for arg in args:
        #     if isinstance(arg, string_type):
        #         arg_b = arg.encode('utf-8', 'strict')
        #     else:
        #         arg_b = arg
        #     parts.append('$%s\r\n%s\r\n' % (len(arg_b), arg))

        # request = '*%s\r\n%s' % (len(parts), ''.join(parts))
        # if isinstance(request, string_type):
        #     request = request.encode('utf-8', 'strict')

        self._busy = True
        self._callback = callback
        self._stream.write(redis_request(args))
        self._stream.read_until(DELIMITER, self._handle_read)

    def _handle_read(self, data):
        # self._reader.feed(data)
        self._parser.feed(data)

        next = self._parser.read_next()
        if next is True:
            self._stream.read_until(DELIMITER, self._handle_read)
        elif next > 0:
            self._stream.read_bytes(next, self._handle_read)
        else: # if next is False
            data = self._parser.gets()
            self._busy = False
            cb = self._callback
            self._callback = None
            if cb is not None:
                cb(data)
            return

        # response = self._reader.gets()
        # if response is not False:
        #     self._busy = False
        #     cb = self._callback
        #     self._callback = None
        #     if cb is not None:
        #         cb(response)
        #     return

        # self._stream.read_until(DELIMITER, self._handle_read)



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
