"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure.

Use ``nose`` to run these unit tests.
"""
from . import GalaxyTestBase, test_util


@test_util.skip_unless_galaxy()
class TestGalaxyRoles(GalaxyTestBase.GalaxyTestBase):

    def test_get_roles(self):
        roles = self.gi.roles.get_roles()
        for role in roles:
            self.assertIsNotNone(role['id'])
            self.assertIsNotNone(role['name'])
