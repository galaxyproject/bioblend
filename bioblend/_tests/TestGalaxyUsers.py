"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure.
"""
from . import GalaxyTestBase


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

    def test_create_remote_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be purged through the Galaxy API, so execute
        # this test only on a disposable Galaxy instance!
        if not self.gi.config.get_config()['use_remote_user']:
            self.skipTest('This Galaxy instance is not configured to use remote users')
        new_user_email = 'newuser@example.com'
        user = self.gi.users.create_remote_user(new_user_email)
        self.assertEqual(user['email'], new_user_email)
        if self.gi.config.get_config()['allow_user_deletion']:
            deleted_user = self.gi.users.delete_user(user['id'])
            self.assertEqual(deleted_user['email'], new_user_email)
            self.assertTrue(deleted_user['deleted'])

    def test_create_local_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be purged through the Galaxy API, so execute
        # this test only on a disposable Galaxy instance!
        if self.gi.config.get_config()['use_remote_user']:
            self.skipTest('This Galaxy instance is not configured to use local users')
        new_user_email = 'newuser@example.com'
        user = self.gi.users.create_local_user('newuser', new_user_email, 'secret')
        self.assertEqual(user['username'], 'newuser')
        self.assertEqual(user['email'], new_user_email)
        if self.gi.config.get_config()['allow_user_deletion']:
            deleted_user = self.gi.users.delete_user(user['id'])
            self.assertEqual(deleted_user['email'], new_user_email)
            self.assertTrue(deleted_user['deleted'])

    def test_get_current_user(self):
        user = self.gi.users.get_current_user()
        self.assertIsNotNone(user['id'])
        self.assertIsNotNone(user['username'])
        self.assertIsNotNone(user['email'])
        self.assertIsNotNone(user['nice_total_disk_usage'])
        self.assertIsNotNone(user['total_disk_usage'])

    def test_update_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be purged through the Galaxy API, so execute
        # this test only on a disposable Galaxy instance!
        if self.gi.config.get_config()['use_remote_user']:
            self.skipTest('This Galaxy instance is not configured to use local users')
        new_user_email = 'newuser2@example.com'
        user = self.gi.users.create_local_user('newuser2', new_user_email, 'secret')
        self.assertEqual(user['username'], 'newuser2')
        self.assertEqual(user['email'], new_user_email)

        updated_user_email = 'updateduser@example.com'
        updated_username = 'updateduser'
        user_id = user['id']
        self.gi.users.update_user(user_id, username=updated_username, email=updated_user_email)
        user = self.gi.users.show_user(user_id)
        self.assertEqual(user['username'], updated_username)
        self.assertEqual(user['email'], updated_user_email)

        if self.gi.config.get_config()['allow_user_deletion']:
            self.gi.users.delete_user(user['id'])
