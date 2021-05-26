"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure.
"""
import uuid

from . import GalaxyTestBase


class TestGalaxyRoles(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super().setUp()
        self.name = f"test_{uuid.uuid4().hex}"
        self.description = 'automated test role'
        self.role = self.gi.roles.create_role(self.name, self.description)

    def tearDown(self):
        # As of 2017/07/26, deleting a role is not possible through the API
        pass

    def test_get_roles(self):
        roles = self.gi.roles.get_roles()
        for role in roles:
            self.assertIsNotNone(role['id'])
            self.assertIsNotNone(role['name'])

    def test_create_role(self):
        self.assertEqual(self.role['name'], self.name)
        self.assertEqual(self.role['description'], self.description)
        self.assertIsNotNone(self.role['id'])
