"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure. 

Use ``nose`` to run these unit tests.
"""
import unittest
from bioblend import galaxy

class GalaxyTestBase(unittest.TestCase):
    
    def setUp(self):        
        self.gi = galaxy.GalaxyInstance(url='https://galaxy-vic.genome.edu.au/', key='90dd6a93c3085dbf192439bfcc0c63f0')
