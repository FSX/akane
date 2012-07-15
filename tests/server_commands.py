import tornado.ioloop
import tornado.testing
import akane

from minitest import TornadoTestCase, TestCase, ok, runner


class ServerCommandsTest(TornadoTestCase):
    name = 'Redis Server Commands'

    def setup(self):
        self.db = akane.Client({
            'connections': 1,
            'ioloop': self.io_loop
        })

    def test_get_and_set(self):
        self.db.get('test_get_and_set', callback=self.stop)
        ok(self.wait()) == None

        self.db.set('test_get_and_set', 'value', callback=self.stop)
        ok(self.wait()) == 'OK'

        self.db.get('test_get_and_set', callback=self.stop)
        ok(self.wait()) == 'value'

    def test_delete(self):
        self.db.set('test_delete', 'value', callback=self.stop)
        ok(self.wait()) == 'OK'

        self.db.delete(('test_delete',), callback=self.stop)
        ok(self.wait()) == 1

    # Command is not supported in Redis 2.4
    def test_dump(self):
        self.db.dump('test_dump', callback=self.stop)
        ok(self.wait()).instance_of(akane.ReplyError)

    def test_exists(self):
        self.db.set('test_exists', 'value', callback=self.stop)
        ok(self.wait()) == 'OK'

        self.db.exists('test_exists', callback=self.stop)
        ok(self.wait()) == 1

        self.db.exists('test_not_exists', callback=self.stop)
        ok(self.wait()) == 0

    def teardown(self):
        keys = (
            'test_get_and_set',
            'test_delete',
            'test_dump',
            'test_exists'
        )

        self.db.delete(keys, callback=self.stop)
        self.wait()


if __name__ == '__main__':
    runner([
        ServerCommandsTest
    ])
