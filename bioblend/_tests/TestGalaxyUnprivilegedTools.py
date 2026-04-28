""" """

import os
import unittest

import bioblend
from bioblend.galaxy import GalaxyInstance
from . import (
    GalaxyTestBase,
    test_util,
)

# Minimal user-tool representation (mirrors TOOL_WITH_SHELL_COMMAND from
# galaxy_test.base.populators). Running the tool requires a container
# runtime (busybox); the run test is gated on that.
USER_TOOL_REPRESENTATION = {
    "id": "bioblend_test_basecommand",
    "name": "BioBlend test base command tool",
    "class": "GalaxyUserTool",
    "container": "busybox",
    "version": "1.0.0",
    "shell_command": "cat '$(inputs.input.path)' > output.txt",
    "inputs": [
        {
            "type": "data",
            "name": "input",
            "format": "txt",
        }
    ],
    "outputs": [
        {
            "type": "data",
            "from_work_dir": "output.txt",
            "name": "output",
        }
    ],
}


@test_util.skip_unless_galaxy("release_25.0")
class TestGalaxyUnprivilegedTools(GalaxyTestBase.GalaxyTestBase):
    admin_gi: GalaxyInstance
    role_id: str

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        master_key = os.environ.get("BIOBLEND_GALAXY_MASTER_API_KEY")
        if not master_key:
            raise unittest.SkipTest(
                "BIOBLEND_GALAXY_MASTER_API_KEY is required to grant the test user the user_tool_execute role."
            )
        cls.admin_gi = GalaxyInstance(url=os.environ["BIOBLEND_GALAXY_URL"], key=master_key)
        user_id = cls.gi.users.get_current_user()["id"]
        payload = {
            "name": f"bioblend_user_tool_execute_{user_id}",
            "description": "BioBlend test role granting user_tool_execute",
            "role_type": "user_tool_execute",
            "user_ids": [user_id],
            "group_ids": [],
        }
        role = cls.admin_gi.make_post_request(f"{cls.admin_gi.url}/roles", payload=payload)
        cls.role_id = role[0]["id"] if isinstance(role, list) else role["id"]

    @classmethod
    def tearDownClass(cls):
        role_id = getattr(cls, "role_id", None)
        if role_id:
            try:
                cls.admin_gi.make_delete_request(f"{cls.admin_gi.url}/roles/{role_id}")
                cls.admin_gi.make_post_request(f"{cls.admin_gi.url}/roles/{role_id}/purge", payload={})
            except bioblend.ConnectionError:
                pass

    def setUp(self):
        super().setUp()
        created = self.gi.unprivileged_tools.create_user_tool(USER_TOOL_REPRESENTATION)
        self.tool_uuid: str = created["uuid"]
        self._tool_deleted = False

    def tearDown(self):
        if self._tool_deleted:
            return
        try:
            self.gi.unprivileged_tools.delete_user_tool(self.tool_uuid)
        except bioblend.ConnectionError:
            pass

    def test_create_user_tool(self):
        tool = self.gi.unprivileged_tools.show_user_tool(self.tool_uuid)
        assert tool["uuid"] == self.tool_uuid
        assert tool["representation"]["name"] == USER_TOOL_REPRESENTATION["name"]

    def test_get_user_tools(self):
        active = self.gi.unprivileged_tools.get_user_tools(active=True)
        assert any(t["uuid"] == self.tool_uuid for t in active)

    def test_delete_user_tool(self):
        self.gi.unprivileged_tools.delete_user_tool(self.tool_uuid)
        self._tool_deleted = True
        active = self.gi.unprivileged_tools.get_user_tools(active=True)
        assert not any(t["uuid"] == self.tool_uuid for t in active)

    @unittest.skipUnless(
        os.environ.get("BIOBLEND_TEST_CONTAINER_RUNTIME"),
        "Set BIOBLEND_TEST_CONTAINER_RUNTIME=1 when docker/singularity is available",
    )
    def test_run_user_tool(self):
        history = self.gi.histories.create_history(name="test_run_user_tool history")
        dataset_id = self._test_dataset(history["id"], contents="abc\n")
        result = self.gi.tools.run_tool(
            history_id=history["id"],
            tool_uuid=self.tool_uuid,
            tool_inputs={"input": {"src": "hda", "id": dataset_id}},
        )
        assert "jobs" in result
        assert len(result["jobs"]) > 0
