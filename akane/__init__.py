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


from .client import Client
from .connection import Pool
from .exceptions import PoolError, ReplyError
