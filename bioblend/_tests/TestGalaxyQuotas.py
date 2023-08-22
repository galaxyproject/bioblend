import uuid

from . import GalaxyTestBase


class TestGalaxyQuotas(GalaxyTestBase.GalaxyTestBase):
    def setUp(self):
        super().setUp()
        # Quota names must be unique, and they're impossible to delete
        # without accessing the database.
        self.quota_name = f"BioBlend-Test-Quota-{uuid.uuid4().hex}"
        self.quota = self.gi.quotas.create_quota(self.quota_name, "testing", "100 GB", "=", default="registered")

    def tearDown(self):
        self.gi.quotas.update_quota(self.quota["id"], default="registered")
        self.gi.quotas.update_quota(self.quota["id"], default="no")
        self.gi.quotas.delete_quota(self.quota["id"])

    def test_create_quota(self):
        quota = self.gi.quotas.show_quota(self.quota["id"])
        assert quota["name"] == self.quota_name
        assert quota["bytes"] == 107374182400
        assert quota["operation"] == "="
        assert quota["description"] == "testing"

    def test_get_quotas(self):
        quotas = self.gi.quotas.get_quotas()
        assert self.quota["id"] in [quota["id"] for quota in quotas]

    def test_update_quota(self):
        response = self.gi.quotas.update_quota(
            self.quota["id"],
            name=self.quota_name + "-new",
            description="asdf",
            default="registered",
            operation="-",
            amount=".01 TB",
        )
        assert f"""Quota '{self.quota_name}' has been renamed to '{self.quota_name}-new'""" in response

        quota = self.gi.quotas.show_quota(self.quota["id"])
        assert quota["name"] == self.quota_name + "-new"
        assert quota["bytes"] == 10995116277
        assert quota["operation"] == "-"
        assert quota["description"] == "asdf"

    def test_update_quota_nondefault(self):
        """
        try to update a non-default quota (and leave it non-default)
        """
        # 1st make it non-default
        response = self.gi.quotas.update_quota(
            self.quota["id"],
            name=self.quota_name,
            description="testing",
            default="no",
            operation="=",
            amount="100 GB",
        )
        assert f"has been renamed to '{self.quota_name}'" in response
        assert f"Quota '{self.quota_name}' is no longer the default for registered users." in response

        # update it leaving it non-default
        response = self.gi.quotas.update_quota(
            self.quota["id"],
            name=self.quota_name + "-updated",
        )
        assert f"""Quota '{self.quota_name}' has been renamed to '{self.quota_name}-updated'""" in response
        quota = self.gi.quotas.show_quota(self.quota["id"])
        assert quota["default"] == "no"

    def test_delete_undelete_quota(self):
        self.gi.quotas.update_quota(self.quota["id"], default="no")
        response = self.gi.quotas.delete_quota(self.quota["id"])
        assert response == "Deleted 1 quotas: " + self.quota_name
        response = self.gi.quotas.undelete_quota(self.quota["id"])
        assert response == "Undeleted 1 quotas: " + self.quota_name
