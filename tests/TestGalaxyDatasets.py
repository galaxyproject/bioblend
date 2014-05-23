"""
Use ``nose`` to run these unit tests.
"""
import GalaxyTestBase
import test_util


@test_util.skip_unless_galaxy()
class TestGalaxyDatasets(GalaxyTestBase.GalaxyTestBase):

    def test_show_dataset(self):
        with self.assertRaises(Exception):
            dataset = self.gi.datasets.show_dataset(None)

    def test_download_dataset(self):
        with self.assertRaises(Exception):
            dataset = self.gi.datasets.download_dataset(None)
