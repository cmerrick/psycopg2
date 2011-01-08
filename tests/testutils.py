# Utility module for psycopg2 testing.
# 
# Copyright (C) 2010 Daniele Varrazzo <daniele.varrazzo@gmail.com>

# Use unittest2 if available. Otherwise mock a skip facility with warnings.

import os
import sys

try:
    import unittest2
    unittest = unittest2
except ImportError:
    import unittest
    unittest2 = None

if hasattr(unittest, 'skipIf'):
    skip = unittest.skip
    skipIf = unittest.skipIf

else:
    import warnings

    def skipIf(cond, msg):
        def skipIf_(f):
            def skipIf__(self):
                if cond:
                    warnings.warn(msg)
                    return
                else:
                    return f(self)
            return skipIf__
        return skipIf_

    def skip(msg):
        return skipIf(True, msg)

    def skipTest(self, msg):
        warnings.warn(msg)
        return

    unittest.TestCase.skipTest = skipTest

# Silence warnings caused by the stubborness of the Python unittest maintainers
# http://bugs.python.org/issue9424
if not hasattr(unittest.TestCase, 'assert_') \
or unittest.TestCase.assert_ is not unittest.TestCase.assertTrue:
    # mavaff...
    unittest.TestCase.assert_ = unittest.TestCase.assertTrue
    unittest.TestCase.failUnless = unittest.TestCase.assertTrue
    unittest.TestCase.assertEquals = unittest.TestCase.assertEqual
    unittest.TestCase.failUnlessEqual = unittest.TestCase.assertEqual


def decorate_all_tests(cls, decorator):
    """Apply *decorator* to all the tests defined in the TestCase *cls*."""
    for n in dir(cls):
        if n.startswith('test'):
            setattr(cls, n, decorator(getattr(cls, n)))


def skip_if_no_pg_sleep(name):
    """Decorator to skip a test if pg_sleep is not supported by the server.

    Pass it the name of an attribute containing a connection or of a method
    returning a connection.
    """
    def skip_if_no_pg_sleep_(f):
        def skip_if_no_pg_sleep__(self):
            cnn = getattr(self, name)
            if callable(cnn):
                cnn = cnn()

            if cnn.server_version < 80100:
                return self.skipTest(
                    "server version %s doesn't support pg_sleep"
                    % cnn.server_version)

            return f(self)

        skip_if_no_pg_sleep__.__name__ = f.__name__
        return skip_if_no_pg_sleep__

    return skip_if_no_pg_sleep_

def skip_on_python2(f):
    """Skip a test on Python 3 and following."""
    def skip_on_python2_(self):
        if sys.version_info[0] < 3:
            return self.skipTest("skipped because Python 2")
        else:
            return f(self)

    return skip_on_python2_

def skip_on_python3(f):
    """Skip a test on Python 3 and following."""
    def skip_on_python3_(self):
        if sys.version_info[0] >= 3:
            return self.skipTest("skipped because Python 3")
        else:
            return f(self)

    return skip_on_python3_

def script_to_py3(script):
    """Convert a script to Python3 syntax if required."""
    if sys.version_info[0] < 3:
        return script

    import tempfile
    f = tempfile.NamedTemporaryFile(suffix=".py")
    f.write(script.encode())
    f.flush()

    # 2to3 is way too chatty
    import logging
    logging.basicConfig(filename=os.devnull)

    from lib2to3.main import main
    if main("lib2to3.fixes", ['--no-diffs', '-w', '-n', f.name]):
        raise Exception('py3 conversion failed')

    f2 = open(f.name)
    try:
        return f2.read()
    finally:
        f2.close()

