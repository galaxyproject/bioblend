"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure. 

Use ``nose`` to run these unit tests.
"""
import GalaxyTestBase

class TestGalaxyDatasets(GalaxyTestBase.GalaxyTestBase):

    def test_show_dataset(self):
        dataset = self.gi.datasets.show_dataset(None)
        self.assertIsNone(dataset)

    def test_download_dataset(self):
        with self.assertRaises(Exception):
            dataset = self.gi.datasets.download_dataset(None)