"""
Tests on the GalaxyInstance object itself.
"""
import time

from bioblend import ConnectionError
from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.client import Client
from .test_util import unittest


class TestGalaxyInstance(unittest.TestCase):

    def setUp(self):
        # "connect" to a galaxy instance that doesn't exist
        self.gi = GalaxyInstance("http://localhost:56789", key="whatever")

    def test_set_max_get_retries(self):
        self.gi.max_get_attempts = 3
        self.assertEqual(3, Client.max_get_retries())

    def test_set_retry_delay(self):
        self.gi.get_retry_delay = 5
        self.assertEqual(5, Client.get_retry_delay())

    def test_get_retry(self):
        # We set the client to try twice, with a delay of 5 seconds between
        # attempts. So, we expect the call to take at least 5 seconds before
        # failing.
        self.gi.max_get_attempts = 2
        self.gi.get_retry_delay = 5
        start = time.time()
        try:
            self.gi.libraries.get_libraries()
            self.fail("Call to show_libraries should have raised a ConnectionError")
        except ConnectionError:
            end = time.time()
        duration = end - start
        self.assertGreater(duration, self.gi.get_retry_delay, "Didn't seem to retry long enough")
