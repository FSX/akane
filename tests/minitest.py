"""
    minitest
    ~~~~~~~~

    minitest is a really simple unit testing module. Inspired by
    Oktest, http://www.kuwata-lab.com/oktest/

    The code in ``TornadoTestCase`` is taken from ``AsyncTestCase`` in
    https://github.com/facebook/tornado/blob/master/tornado/testing.py

    Changelog:

     * 0.3:
        - Handle unexpected exceptions.

     * 0.2:
        - Use exit code '1' when there are failed tests.
        - Added ``pre_setup`` and ``post_teardown`` for ``TestCase`` subclasses.
        - Added a test case class for Tornado, ``TornadoTestCase``.

     * 0.1: Initial version.
"""

VERSION = (0, 2, 0)

import sys
import time
import traceback
import contextlib
from difflib import unified_diff
from collections import namedtuple

from tornado.ioloop import IOLoop
from tornado.stack_context import StackContext, NullContext


Result = namedtuple('Result', ('func', 'name', 'failure'))


def msg(message):
    return '{0}\n{1}\n{0}'.format('-' * 80, message)


class TimeOutException(Exception):
    pass


class ExtendedDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            return None

    def __setattr__(self, name, value):
        self[name] = value


class AssertionObject(object):
    def __init__(self, target):
        self._target = target

    def __lt__(self, other):
        if not self._target < other:
            raise AssertionError(msg('%r < %r' % (self._target, other)))

    def __le__(self, other):
        if not self._target <= other:
            raise AssertionError(msg('%r <= %r' % (self._target, other)))


    def __eq__(self, other):
        if not self._target == other:
            raise AssertionError(msg('%r == %r' % (self._target, other)))

    def __ne__(self, other):
        if not self._target != other:
            raise AssertionError(msg('%r != % ' % (self._target, other)))

    def __gt__(self, other):
        if not self._target > other:
            raise AssertionError(msg('%r > %r' % (self._target, other)))

    def __ge__(self, other):
        if not self._target >= other:
            raise AssertionError(msg('%r >= %r' % (self._target, other)))

    def diff(self, other):
        if self._target != other:
            difference = unified_diff(
                other.splitlines(True),
                self._target.splitlines(True))
            raise AssertionError(msg(''.join(difference)))

    def instance_of(self, other):
        if not isinstance(self._target, other):
            raise AssertionError(msg('%r instance of %r' % (self._target, other)))

    def contains(self, other):
        if other not in self._target:
            raise AssertionError(msg('%r in %r' % (other, self._target)))

    def not_contains(self, other):
        if other in self._target:
            raise AssertionError(msg('%r not in %r' % (other, self._target)))


def ok(target):
    return AssertionObject(target)


class TestCase(object):
    def __init__(self, config):
        self.config = config
        self._tests = []
        for t in dir(self):
            if t.startswith('test_'):
                self.add_test(getattr(self, t))

    def add_test(self, func):
        def catch_exception():
            try:
                func()
                failure = None
            except AssertionError as e:
                failure = str(e)
            except Exception as e:
                failure = msg(''.join(
                    traceback.format_exception(*sys.exc_info())).strip())
            return Result(func.__name__, func.__doc__, failure)

        self._tests.append(catch_exception)
        return catch_exception

    def pre_setup(self):
        pass

    def setup(self):
        pass

    def teardown(self):
        pass

    def post_teardown(self):
        pass

    def run(self):
        self.pre_setup()
        self.setup()
        for test in self._tests:
            yield test()
        self.teardown()
        self.post_teardown()


class TornadoTestCase(TestCase):
    def __init__(self, config):
        super(TornadoTestCase, self).__init__(config)
        self._stopped = False
        self._running = False
        self._failure = None
        self._stop_args = None

    def get_new_ioloop(self):
        """Creates a new IOLoop for this test.  May be overridden in
        subclasses for tests that require a specific IOLoop (usually
        the singleton).
        """
        return IOLoop()

    def pre_setup(self):
        self.io_loop = self.get_new_ioloop()

    def post_teardown(self):
        if (not IOLoop.initialized() or self.io_loop is not IOLoop.instance()):
            # Try to clean up any file descriptors left open in the ioloop.
            # This avoids leaks, especially when tests are run repeatedly
            # in the same process with autoreload (because curl does not
            # set FD_CLOEXEC on its file descriptors)
            self.io_loop.close(all_fds=True)

    @contextlib.contextmanager
    def _stack_context(self):
        try:
            yield
        except Exception:
            self._failure = sys.exc_info()
            self.stop()

    def run(self):
        with StackContext(self._stack_context):
            self.pre_setup()
            self.setup()
            for test in self._tests:
                yield test()
            self.teardown()
            self.post_teardown()

    def stop(self, _arg=None, **kwargs):
        """Stops the ioloop, causing one pending (or future) call to wait()
        to return.

        Keyword arguments or a single positional argument passed to stop() are
        saved and will be returned by wait().
        """
        assert _arg is None or not kwargs
        self._stop_args = kwargs or _arg
        if self._running:
            self.io_loop.stop()
            self._running = False
        self._stopped = True

    def wait(self, condition=None, timeout=5):
        """Runs the IOLoop until stop is called or timeout has passed.

        In the event of a timeout, an exception will be thrown.

        If condition is not None, the IOLoop will be restarted after stop()
        until condition() returns true.
        """
        if not self._stopped:
            if timeout:
                def timeout_func():
                    try:
                        raise TimeOutException('Async operation timed out after %d seconds' % timeout)
                    except Exception:
                        self._failure = sys.exc_info()
                    self.stop()
                self.io_loop.add_timeout(time.time() + timeout, timeout_func)
            while True:
                self._running = True
                with NullContext():
                    # Wipe out the StackContext that was established in
                    # self.run() so that all callbacks executed inside the
                    # IOLoop will re-run it.
                    self.io_loop.start()
                if (self._failure is not None or condition is None or condition()):
                    break
        assert self._stopped
        self._stopped = False
        if self._failure is not None:
            # 2to3 isn't smart enough to convert three-argument raise
            # statements correctly in some cases.
            if isinstance(self._failure[1], self._failure[0]):
                raise self._failure[1], None, self._failure[2]
            else:
                raise self._failure[0], self._failure[1], self._failure[2]
        result = self._stop_args
        self._stop_args = None
        return result


def runner(testcases, config={}):
    passed = failed = 0
    config = ExtendedDict(config)

    for testcase in testcases:
        tests = testcase(config)

        if hasattr(tests, 'name'):
            print('\n>> %s' % tests.name)

        for result in tests.run():
            name = result.name or result.func
            if result.failure is not None:
                failed += 1
                print('%s ... FAILED\n\n%s\n' % (name, result.failure))
            else:
                passed += 1
                print('%s ... PASSED' % name)

    print('\n\n%s passed; %s failed.' % (passed, failed))
    if failed > 0:
        sys.exit(1)
