from . import GalaxyTestBase


class TestGalaxyConfig(GalaxyTestBase.GalaxyTestBase):
    def test_get_config(self):
        response = self.gi.config.get_config()
        self.assertTrue(isinstance(response, dict))
        self.assertTrue('brand' in response.keys())

    def test_get_version(self):
        response = self.gi.config.get_version()
        self.assertTrue(isinstance(response, dict))
        self.assertTrue('version_major' in response.keys())

    def test_whoami(self):
        response = self.gi.config.whoami()
        self.assertTrue(isinstance(response, dict))
        self.assertTrue('username' in response.keys())
