import os
import sys
import unittest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mediasync import backends
from mediasync import msettings
import mediasync

class BaseTestCase(unittest.TestCase):

    def testInvalidBackend(self):
        msettings.BACKEND = 'not.a.backend'

class DummyBackendTestCase(unittest.TestCase):

    def setUp(self):
        msettings.BACKEND = 'mediasync.backends.dummy'
        self.client = backends.client()

    def testPush(self):

        def callback(*args):
            pass

        self.client.put_callback = callback
        mediasync.sync(self.client)

    def testJoinedPush(self):
        pass

class S3BackendTestCase(unittest.TestCase):

    def setUp(self):
        msettings.BACKEND = 'mediasync.backends.s3'
        msettings.AWS_BUCKET = 'mediasync_test'
        msettings.AWS_KEY = os.environ['AWS_KEY']
        msettings.AWS_SECRET = os.environ['AWS_SECRET']
        self.client = backends.client()

    def testServeRemote(self):
        msettings.SERVE_REMOTE = False
        self.assertEqual(backends.client().media_url(), '/media')

        msettings.SERVE_REMOTE = True
        self.assertEqual(backends.client().media_url(), 'http://mediasync_test.s3.amazonaws.com')

    def testMissingBucket(self):
        msettings.AWS_BUCKET = None
        self.assertRaises(AssertionError, backends.client)

class ProcessorTestCase(unittest.TestCase):

    def setUp(self):
        msettings.PROCESSORS = (
            'mediasync.processors.js_minifier',
            lambda fd, ct, rp, r: fd.upper(),
        )
        self.client = backends.client()

    def testProcessor(self):
        content = """var foo = function() {
            alert(1);
        };"""
        ct = 'text/javascript'
        procd = self.client.process(content, ct, 'test.js')
        self.assertEqual(procd, "VAR FOO = FUNCTION(){ALERT(1)};")
