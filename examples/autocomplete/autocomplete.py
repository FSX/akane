#!/usr/bin/env python

import json
import uuid
from os import path

import tornado.httpserver
import tornado.ioloop
import tornado.options
from tornado import gen, web

from akane import Client


KEY = 'compl'


class BaseHandler(web.RequestHandler):
    @property
    def db(self):
        return self.application.db


class IndexHandler(BaseHandler):
    @web.asynchronous
    @gen.engine
    def get(self):
        key_exists = yield gen.Task(self.db.exists, KEY)
        if key_exists == 0:
            with open('female-names.txt', 'r') as fd:
                for line in fd.xreadlines():
                    if line.startswith('#'):
                        continue
                    line = line.strip()
                    for end_index in range(1, len(line)):
                        prefix = line[0:end_index]
                        yield gen.Task(self.db.zadd, KEY, (0, prefix))
                    yield gen.Task(self.db.zadd, KEY, (0, line + '*'))

        self.render('autocomplete.html')


class AutoCompleteHandler(BaseHandler):
    @web.asynchronous
    @gen.engine
    def post(self):
        prefix = self.get_argument('input')
        count = 50

        results = []
        rangelen = 50
        start = yield gen.Task(self.db.zrank, KEY, prefix)
        if start is not None:
            while len(results) != count:
                r = yield gen.Task(self.db.zrange, KEY, str(start), str(start + rangelen - 1))
                start += rangelen
                if not r or len(r) == 0:
                    break
                for entry in r:
                    minlen = min((len(entry), len(prefix)))
                    if entry[0:minlen] != prefix[0:minlen]:
                        count = len(results)
                        break
                    if entry[-1] == '*' and len(results) != count:
                        results.append(entry[0:-1])

        self.write(json.dumps(results))
        self.finish()


if __name__ == '__main__':
    try:
        tornado.options.parse_command_line()

        application = web.Application((
            (r'/', IndexHandler),
            (r'/autocomplete', AutoCompleteHandler)
        ),
        template_path=path.join(path.dirname(__file__), 'templates'),
        static_path=path.join(path.dirname(__file__), 'static'),
        debug=True)

        application.db = Client({
            'connections': 10
        })

        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8888)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print('Exit')
