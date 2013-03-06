"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure. 

Use ``nose`` to run these unit tests.
"""
import unittest
import os
from bioblend import galaxy

class GalaxyTestBase(unittest.TestCase):

    def setUp(self):
        galaxy_key = os.environ['BIOBLEND_GALAXY_API_KEY']
        self.gi = galaxy.GalaxyInstance(url='https://galaxy-vic.genome.edu.au/', key=galaxy_key)
