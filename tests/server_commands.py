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

    def test_delete(self):
        self.db.delete('a', callback=self.stop)
        r = self.wait()

        ok(r).instance_of(int)
        ok(r) >= 0

    def test_get_and_set(self):
        self.db.get('a', callback=self.stop)
        ok(self.wait()) == None

        self.db.set('a', 'value', callback=self.stop)
        ok(self.wait()) == 'OK'

        self.db.get('a', callback=self.stop)
        ok(self.wait()) == 'value'


if __name__ == '__main__':
    runner([
        ServerCommandsTest
    ])
