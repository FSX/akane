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

    # Keys

    def delete(self, keys, callback=None):
        self.send_command(callback, 'DEL', *keys)

    def dump(self, key, callback=None):
        self.send_command(callback, 'DUMP', key)

    def exists(self, key, callback=None):
        self.send_command(callback, 'EXISTS', key)

    def expire(self, key, seconds, callback=None):
        self.send_command(callback, 'EXPIRE', key, seconds)

    def expire_at(self, key, timestamp, callback=None):
        self.send_command(callback, 'EXPIREAT', key, timestamp)

    def keys(self, pattern, callback=None):
        self.send_command(callback, 'KEYS', pattern)

    def migrate(self, host, port, key, destination_db, timeout, callback=None):
        self.send_command(callback, 'MIGRATE', host, port, key, destination_db, timeout)

    def move(self, key, db, callback=None):
        self.send_command(callback, 'MOVE', key, db)

    def object(self, subcommand, arguments=(), callback=None):
        self.send_command(callback, 'OBJECT', subcommand, *arguments)

    def persist(self, key, callback=None):
        self.send_command(callback, 'PERSIST', key)

    def pexpire(self, key, milliseconds, callback=None):
        self.send_command(callback, 'PEXPIRE', key, milliseconds)

    def pexpire_at(self, key, milliseconds_timestamp, callback=None):
        self.send_command(callback, 'PEXPIREAT', key, milliseconds_timestamp)

    def pttl(self, key, callback=None):
        self.send_command(callback, 'PTTL', key)

    def random_key(self, callback=None):
        self.send_command(callback, 'RANDOMKEY')

    def rename(self, key, newkey, callback=None):
        self.send_command(callback, 'RENAME', key, newkey)

    def rename_nx(self, key, newkey, callback=None):
        self.send_command(callback, 'RENAMENX', key, newkey)

    def restore(self, key, ttl, serialized_value, callback=None):
        self.send_command(callback, 'RESTORE', key, ttl, serialized_value)

    # TODO: SORT - http://redis.io/commands/sort

    def ttl(self, key, callback=None):
        self.send_command(callback, 'TTL', key)

    def type(self, key, callback=None):
        self.send_command(callback, 'TYPE', key)

    # Strings

    # TODO: APPEND - http://redis.io/commands/append

    # TODO: GETRANGE - http://redis.io/commands/getrange

    def mget(self, keys, callback=None):
        self.send_command(callback, 'MGET', *keys)

    # TODO: SETBIT - http://redis.io/commands/setbit

    def decr(self, key, callback=None):
        self.send_command(callback, 'DECR', key)

    def getset(self, key, value, callback=None):
        self.send_command(callback, 'GETSET', key, value)

    def mset(self, mapping, callback=None):
        items = []
        for pair in mapping.iteritems():
            items.extend(pair)
        self.send_command(callback, 'MSET', *items)

    # TODO: SETEX - http://redis.io/commands/setex

    def decrby(self, key, by, callback=None):
        self.send_command(callback, 'DECRBY', key, by)

    def incr(self, key, callback=None):
        self.send_command(callback, 'INCR', key)

    # TODO: MSETNX - http://redis.io/commands/msetnx

    # TODO: SETNX - http://redis.io/commands/setnx

    def get(self, key, callback=None):
        self.send_command(callback, 'GET', key)

    def incrby(self, key, by, callback=None):
        self.send_command(callback, 'INCRBY', key, by)

    # TODO: PSETNX - http://redis.io/commands/psetnx

    # TODO: SETRANGE - http://redis.io/commands/setrange

    # TODO: GETBIT - http://redis.io/commands/getbit

    # TODO: INCRBYFLOAT - http://redis.io/commands/incrbyfloat

    def set(self, key, value, callback=None):
        self.send_command(callback, 'SET', key, value)

    def strlen(self, key, callback=None):
        self.send_command(callback, 'STRLEN', key)

    # TODO: Hashes
    # TODO: Lists
    # TODO: Sets
    # TODO: Sorted Sets
    # TODO: Pub/Sub
    # TODO: Transactions
    # TODO: Scripting
    # TODO: Connection
    # TODO: Server
