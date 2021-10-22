import uuid

from . import GalaxyTestBase


class TestGalaxyQuotas(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super().setUp()
        # Quota names must be unique, and they're impossible to delete
        # without accessing the database.
        self.quota_name = f"BioBlend-Test-Quota-{uuid.uuid4().hex}"
        self.quota = self.gi.quotas.create_quota(
            self.quota_name, 'testing', '100 GB', '=',
            default='registered'
        )

    def tearDown(self):
        self.gi.quotas.update_quota(self.quota['id'], default='registered')
        self.gi.quotas.update_quota(self.quota['id'], default='no')
        self.gi.quotas.delete_quota(self.quota['id'])

    def test_create_quota(self):
        quota = self.gi.quotas.show_quota(self.quota['id'])
        self.assertEqual(quota['name'], self.quota_name)
        self.assertEqual(quota['bytes'], 107374182400)
        self.assertEqual(quota['operation'], '=')
        self.assertEqual(quota['description'], 'testing')

    def test_get_quotas(self):
        quotas = self.gi.quotas.get_quotas()
        self.assertIn(self.quota['id'], [quota['id'] for quota in quotas])

    def test_update_quota(self):
        response = self.gi.quotas.update_quota(
            self.quota['id'], name=self.quota_name + '-new',
            description='asdf', default='registered', operation='-',
            amount='.01 TB'
        )
        self.assertIn(f"""Quota '{self.quota_name}' has been renamed to '{self.quota_name}-new'""", response)

        quota = self.gi.quotas.show_quota(self.quota['id'])
        self.assertEqual(quota['name'], self.quota_name + '-new')
        self.assertEqual(quota['bytes'], 10995116277)
        self.assertEqual(quota['operation'], '-')
        self.assertEqual(quota['description'], 'asdf')

    def test_delete_undelete_quota(self):
        self.gi.quotas.update_quota(
            self.quota['id'], default='no'
        )
        response = self.gi.quotas.delete_quota(self.quota['id'])
        self.assertEqual(response, 'Deleted 1 quotas: ' + self.quota_name)
        response = self.gi.quotas.undelete_quota(self.quota['id'])
        self.assertEqual(response, 'Undeleted 1 quotas: ' + self.quota_name)
