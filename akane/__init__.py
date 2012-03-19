# -*- coding: utf-8 -*-
"""
    akane
    ~~~~~

    An asynchronous Redis client for Tornado.

    :copyright: (c) 2012 by Frank Smit.
    :license: MIT, see LICENSE for more details.
"""


__authors__ = ('Frank Smit <frank@61924.nl>',)
__version__ = '0.1.0'
__license__ = 'MIT'


import socket

from tornado.ioloop import IOLoop
from tornado import iostream

import hiredis


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
            if self._callback is not None:
                self._busy = False
                cb = self._callback
                self._callback = None
                cb(response)
            return

        self._stream.read_until('\r\n', self._handle_read)



class Pool(object):

    closed = True

    def __init__(self, min_conn=1, max_conn=20, cleanup_timeout=10,
                 ioloop=None, *args, **kwargs):
        self.min_conn = min_conn
        self.max_conn = max_conn
        self.closed = False
        self._ioloop = ioloop or IOLoop.instance()
        self._args = args
        self._kwargs = kwargs

        self._pool = set()

        self.closed = False
        for i in range(self.min_conn):
            self._new_conn()

    def _new_conn(self):
        self._pool.add(Connection(*self._args, **self._kwargs))

    def _get_free_conn(self):
        if self.closed:
            raise PoolError('connection pool is closed')
        for conn in self._pool:
            if not conn.busy():
                return conn
        return None

    def close(self):
        if self.closed:
            raise PoolError('connection pool is closed')
        for conn in self._pool:
            if not conn.closed():
                conn.close()
        self._cleaner.stop()
        self._pool = set()
        self.closed = True


class Client(object):
    def __init__(self, settings={}):
        self._pool = Pool(**settings)

    def send_command(self, callback, *args):
        conn = self._pool._get_free_conn()
        if conn is not None:
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


class PoolError(Exception):
    pass
