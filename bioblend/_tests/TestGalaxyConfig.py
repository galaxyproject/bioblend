from . import GalaxyTestBase


class TestGalaxyConfig(GalaxyTestBase.GalaxyTestBase):
    def test_get_config(self):
        response = self.gi.config.get_config()
        assert isinstance(response, dict)
        assert "brand" in response.keys()

    def test_get_version(self):
        response = self.gi.config.get_version()
        assert isinstance(response, dict)
        assert "version_major" in response.keys()

    def test_whoami(self):
        response = self.gi.config.whoami()
        assert isinstance(response, dict)
        assert "username" in response.keys()
