"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure. 

Use ``nose`` to run these unit tests.
"""
import GalaxyTestBase
import test_util


@test_util.skip_unless_galaxy()
class TestGalaxyUsers(GalaxyTestBase.GalaxyTestBase):

    def test_get_users(self):
        users = self.gi.users.get_users()
        for user in users:
            self.assertIsNotNone(user['id'])
            self.assertIsNotNone(user['email'])

    def test_show_user(self):
        current_user = self.gi.users.get_current_user()
        user = self.gi.users.show_user(current_user['id'])
        self.assertEqual(user['id'], current_user['id'])
        self.assertEqual(user['username'], current_user['username'])
        self.assertEqual(user['email'], current_user['email'])
        self.assertEqual(user['nice_total_disk_usage'], current_user['nice_total_disk_usage'])
        self.assertEqual(user['total_disk_usage'], current_user['total_disk_usage'])

    def test_create_user(self):
        # TODO: Need to have permissions to create user!
        # users = self.gi.users.create_user('buildbot@galaxy-vic.genome.edu.au')
        pass

    def test_get_current_user(self):
        user = self.gi.users.get_current_user()
        self.assertIsNotNone(user['id'])
        self.assertIsNotNone(user['username'])
        self.assertIsNotNone(user['email'])
        self.assertIsNotNone(user['nice_total_disk_usage'])
        self.assertIsNotNone(user['total_disk_usage'])
