import sys
import unittest

import tornado.ioloop
import tornado.testing
import akane


class AsyncClientTest(tornado.testing.AsyncTestCase):
    """``AsyncClient`` tests.
    """
    def setUp(self):
        super(AsyncClientTest, self).setUp()
        self.db = akane.Client({
            'connections': 1,
            'ioloop': self.io_loop
        })

    def tearDown(self):
        super(AsyncClientTest, self).tearDown()

    def test_get_and_set(self):
        self.db.get('a', callback=self.stop)
        result = self.wait()
        self.assertEqual(result, None)


if __name__ == '__main__':
    unittest.main()
