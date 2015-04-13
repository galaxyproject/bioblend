"""
WARNING: only admins can operate on groups!
"""
import uuid

import GalaxyTestBase
import test_util


@test_util.skip_unless_galaxy()
class TestGalaxyGroups(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super(TestGalaxyGroups, self).setUp()
        self.name = 'test_%s' % uuid.uuid4().hex
        self.group = self.gi.groups.create_group(self.name)[0]

    def tearDown(self):
        # As of 2015/04/13, deleting a group is not possible through the API
        pass

    def test_create_group(self):
        self.assertEqual(self.group['name'], self.name)
        self.assertIsNotNone(self.group['id'])

    def test_get_groups(self):
        groups = self.gi.groups.get_groups()
        for group in groups:
            self.assertIsNotNone(group['id'])
            self.assertIsNotNone(group['name'])

    def test_show_group(self):
        group_data = self.gi.groups.show_group(self.group['id'])
        self.assertEqual(self.group['id'], group_data['id'])
        self.assertEqual(self.group['name'], group_data['name'])

    def test_get_group_users(self):
        group_users = self.gi.groups.get_group_users(self.group['id'])
        self.assertEqual(group_users, [])

    def test_get_group_roles(self):
        group_roles = self.gi.groups.get_group_roles(self.group['id'])
        self.assertEqual(group_roles, [])

    def test_update_group(self):
        new_name = 'test_%s' % uuid.uuid4().hex
        new_users = [self.gi.users.get_current_user()['id']]
        self.gi.groups.update_group(self.group['id'], new_name, user_ids=new_users)
        updated_group = self.gi.groups.show_group(self.group['id'])
        self.assertEqual(self.group['id'], updated_group['id'])
        self.assertEqual(updated_group['name'], new_name)
        updated_group_users = [_['id'] for _ in self.gi.groups.get_group_users(self.group['id'])]
        self.assertEqual(set(updated_group_users), set(new_users))
        updated_group_roles = [_['id'] for _ in self.gi.groups.get_group_roles(self.group['id'])]
        self.assertEqual(set(updated_group_roles), set())

    def test_add_delete_group_user(self):
        new_user = self.gi.users.get_current_user()['id']
        ret = self.gi.groups.add_group_user(self.group['id'], new_user)
        self.assertEqual(ret['id'], new_user)
        updated_group_users = [_['id'] for _ in self.gi.groups.get_group_users(self.group['id'])]
        self.assertIn(new_user, updated_group_users)
        self.gi.groups.delete_group_user(self.group['id'], new_user)
        updated_group_users = [_['id'] for _ in self.gi.groups.get_group_users(self.group['id'])]
        self.assertNotIn(new_user, updated_group_users)
