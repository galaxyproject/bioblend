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
        # The 2 following tests randomly fail
#        self.assertEqual(user['nice_total_disk_usage'], current_user['nice_total_disk_usage'])
#        self.assertEqual(user['total_disk_usage'], current_user['total_disk_usage'])

    @test_util.skip_unless_galaxy('release_14.06')
    def test_create_remote_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be deleted in Galaxy, so execute this test only
        #          on a disposable Galaxy instance!
        if self.gi.config.get_config()['use_remote_user']:
            user = self.gi.users.create_remote_user('newuser@example.com')
            self.assertEqual(user['email'], 'newuser@example.com')

    @test_util.skip_unless_galaxy('release_14.06')
    def test_create_local_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be deleted in Galaxy, so execute this test only
        #          on a disposable Galaxy instance!
        if not self.gi.config.get_config()['use_remote_user']:
            user = self.gi.users.create_local_user('newuser', 'newuser@example.com', 'secret')
            self.assertEqual(user['username'], 'newuser')
            self.assertEqual(user['email'], 'newuser@example.com')

    def test_get_current_user(self):
        user = self.gi.users.get_current_user()
        self.assertIsNotNone(user['id'])
        self.assertIsNotNone(user['username'])
        self.assertIsNotNone(user['email'])
        self.assertIsNotNone(user['nice_total_disk_usage'])
        self.assertIsNotNone(user['total_disk_usage'])
