""" """

import unittest

import bioblend
from . import GalaxyTestBase

# Minimal user-tool representation (mirrors TOOL_WITH_SHELL_COMMAND from
# galaxy_test.base.populators). Galaxy must allow the test user to run
# unprivileged tools for these tests to succeed; otherwise create returns
# a payload with ``err_msg`` and we skip.
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


class TestGalaxyUnprivilegedTools(GalaxyTestBase.GalaxyTestBase):
    def setUp(self):
        super().setUp()
        created = self.gi.unprivileged_tools.create_user_tool(USER_TOOL_REPRESENTATION)
        if "err_msg" in created:
            raise unittest.SkipTest(f"Galaxy did not accept the unprivileged tool: {created['err_msg']}")
        self.tool_uuid = created["uuid"]

    def tearDown(self):
        if self.tool_uuid is None:
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
        uuid = self.tool_uuid
        self.gi.unprivileged_tools.delete_user_tool(uuid)
        self.tool_uuid = None
        active = self.gi.unprivileged_tools.get_user_tools(active=True)
        assert not any(t["uuid"] == uuid for t in active)

    def test_run_user_tool(self):
        history = self.gi.histories.create_history(name="test_run_user_tool history")
        dataset_id = self._test_dataset(history["id"], contents="abc\n")
        result = self.gi.unprivileged_tools.run_user_tool(
            history_id=history["id"],
            tool_uuid=self.tool_uuid,
            tool_inputs={"input": {"src": "hda", "id": dataset_id}},
        )
        assert "jobs" in result
        assert len(result["jobs"]) > 0
