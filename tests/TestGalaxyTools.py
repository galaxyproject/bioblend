"""
"""
import os
import GalaxyTestBase
import test_util
from bioblend.galaxy.tools.inputs import (
    inputs,
    dataset,
    repeat,
    conditional,
)


def get_abspath(path):
    return os.path.join(os.path.dirname(__file__), path)


@test_util.skip_unless_galaxy()
class TestGalaxyTools(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super(TestGalaxyTools, self).setUp()

    def test_get_tools(self):
        # Test requires target Galaxy is configured with at least one tool.
        tools = self.gi.tools.get_tools()
        assert len(tools) > 0
        assert all(map(self._assert_is_tool_rep, tools))

    def test_get_tool_panel(self):
        # Test requires target Galaxy is configured with at least one tool
        # section.
        tool_panel = self.gi.tools.get_tool_panel()
        sections = [s for s in tool_panel if "elems" in s]
        assert len(sections) > 0
        assert all(map(self._assert_is_tool_rep, sections[0]["elems"]))

    def _assert_is_tool_rep(self, data):
        assert data["model_class"].endswith("Tool")
        # Special tools like SetMetadataTool may have different model_class
        # than Tool - but they all seem to end in tool.

        for key in ["name", "id", "version"]:
            assert key in data, "key %s not in %s" % (key, data)
        return True

    def test_paste_data(self):
        history = self.gi.histories.create_history(name="test_paste_data history")

        tool_output = self.gi.tools.paste_content("test contents", history["id"])
        assert len(tool_output["outputs"]) == 1

    def test_upload_file(self):
        history = self.gi.histories.create_history(name="test_upload_file history")

        fn = get_abspath(os.path.join(os.pardir, "setup.py"))
        tool_output = self.gi.tools.upload_file(
            fn,
            # First param could be a regular path also of course...
            history_id=history["id"],
            file_name="test1",
            dbkey="?",
            file_type="txt",
        )
        assert len(tool_output["outputs"]) == 1

    @test_util.skip_unless_tool("random_lines1")
    def test_run_random_lines(self):
        # Run second test case from randomlines.xml
        history_id = self.gi.histories.create_history(name="test_run_random_lines history")["id"]
        with open(get_abspath(os.path.join("data", "1.bed"))) as f:
            contents = f.read()
        dataset_id = self._test_dataset(history_id, contents=contents)
        tool_inputs = inputs().set(
            "num_lines", "1"
        ).set(
            "input", dataset(dataset_id)
        ).set(
            "seed_source", conditional().set(
                "seed_source_selector", "set_seed"
            ).set(
                "seed", "asdf"
            )
        )
        tool_output = self.gi.tools.run_tool(
            history_id=history_id,
            tool_id="random_lines1",
            tool_inputs=tool_inputs
        )
        assert len(tool_output["outputs"]) == 1
        # TODO: Wait for results and verify has 1 line and is
        # chr5  131424298   131424460   CCDS4149.1_cds_0_0_chr5_131424299_f 0   +

    @test_util.skip_unless_tool("cat1")
    def test_run_cat1(self):
        history_id = self.gi.histories.create_history(name="test_run_cat1 history")["id"]
        dataset1_id = self._test_dataset(history_id, contents="1 2 3")
        dataset2_id = self._test_dataset(history_id, contents="4 5 6")
        dataset3_id = self._test_dataset(history_id, contents="7 8 9")
        tool_inputs = inputs().set(
            "input1", dataset(dataset1_id)
        ).set(
            "queries", repeat().instance(
                inputs().set("input2", dataset(dataset2_id))
            ).instance(
                inputs().set("input2", dataset(dataset3_id))
            )
        )
        tool_output = self.gi.tools.run_tool(
            history_id=history_id,
            tool_id="cat1",
            tool_inputs=tool_inputs
        )
        assert len(tool_output["outputs"]) == 1
        # TODO: Wait for results and verify it has 3 lines - 1 2 3, 4 5 6,
        # and 7 8 9.
