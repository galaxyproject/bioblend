"""
Test functions in bioblend.galaxy.tool_dependencies
"""
from . import GalaxyTestBase, test_util


class TestGalaxyToolDependencies(GalaxyTestBase.GalaxyTestBase):

    @test_util.skip_unless_galaxy('release_20.01')
    def test_summarize_toolbox(self):
        toolbox_summary = self.gi.tool_dependencies.summarize_toolbox()
        self.assertTrue(isinstance(toolbox_summary, list))
        self.assertGreater(len(toolbox_summary), 0)

        toolbox_summary_by_tool = self.gi.tool_dependencies.summarize_toolbox(index_by='tools')
        self.assertTrue(isinstance(toolbox_summary_by_tool, list))
        self.assertGreater(len(toolbox_summary_by_tool), 0)
        self.assertTrue(isinstance(toolbox_summary_by_tool[0], dict))
        self.assertTrue('tool_ids' in toolbox_summary_by_tool[0])
        self.assertTrue(isinstance(toolbox_summary_by_tool[0]['tool_ids'], list))
        tool_id = toolbox_summary_by_tool[0]['tool_ids'][0]

        toolbox_summary_select_tool_ids = self.gi.tool_dependencies.summarize_toolbox(index_by='tools', tool_ids=[tool_id])
        self.assertTrue(isinstance(toolbox_summary_select_tool_ids, list))
        self.assertEqual(len(toolbox_summary_select_tool_ids), 1)
        self.assertEqual(toolbox_summary_select_tool_ids[0]['tool_ids'][0], tool_id)
