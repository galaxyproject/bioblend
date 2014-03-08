"""
"""
import GalaxyTestBase
import test_util


@test_util.skip_unless_galaxy()
class TestGalaxyTools(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super(TestGalaxyTools, self).setUp()

    def test_paste_data(self):
        history = self.gi.histories.create_history(name="tool test history")

        tool_input = {}
        tool_input["file_type"] = "txt"
        tool_input["dbkey"] = "?"
        tool_input["files_0|NAME"] = "test1"
        tool_input["files_0|type"] = "upload_dataset"
        tool_input["files_0|url_paste"] = "test contents"
        tool_input["files_0|files_metadata"] = ""

        tool_output = self.gi.tools.run_tool(
            tool_id="upload1",
            history_id=history["id"],
            tool_inputs=tool_input
        )
        assert len(tool_output) == 1

    def test_upload_file(self):
        history = self.gi.histories.create_history(name="tool test history")

        tool_output = self.gi.tools.upload_file(
            "setup.py",
            # First param could be a regular path also of course...
            history_id=history["id"],
            file_name="test1",
            dbkey="?",
            file_type="txt",
        )
        assert len(tool_output) == 1
