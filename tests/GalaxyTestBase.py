import unittest
import os
from bioblend import galaxy


class GalaxyTestBase(unittest.TestCase):

    def setUp(self):
        galaxy_key = os.environ['BIOBLEND_GALAXY_API_KEY']
        galaxy_url = os.environ['BIOBLEND_GALAXY_URL']
        self.gi = galaxy.GalaxyInstance(url=galaxy_url, key=galaxy_key)
