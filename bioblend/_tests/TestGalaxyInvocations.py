import os

from . import GalaxyTestBase, test_util


class TestGalaxyInvocations(GalaxyTestBase.GalaxyTestBase):
    @test_util.skip_unless_galaxy('release_19.09')
    @test_util.skip_unless_tool("cat1")
    @test_util.skip_unless_tool("cat")
    def test_cancelling_workflow_scheduling(self):
        path = test_util.get_abspath(os.path.join('data', 'test_workflow_pause.ga'))
        workflow = self.gi.workflows.import_workflow_from_local_path(path)
        history_id = self.gi.histories.create_history(name="TestWorkflowState")["id"]
        dataset1_id = self._test_dataset(history_id)

        invocations = self.gi.invocations.get_invocations()
        self.assertEqual(len(invocations), 0)

        invocation = self.gi.workflows.invoke_workflow(
            workflow["id"],
            inputs={"0": {"src": "hda", "id": dataset1_id}},
        )
        invocation_id = invocation["id"]
        invocations = self.gi.invocations.get_invocations()
        self.assertEqual(len(invocations), 1)
        self.assertEqual(invocations[0]["id"], invocation_id)

        invocation = self.gi.invocations.show_invocation(invocation_id)
        self.assertIn(invocation['state'], ['new', 'ready'])

        self.gi.invocations.cancel_invocation(invocation_id)
        invocation = self.gi.invocations.show_invocation(invocation_id)
        self.assertEqual(invocation['state'], 'cancelled')

        step_id = invocation['steps'][0]['id']

        self.assertIsNone(
            self.gi.invocations.show_invocation_step(invocation_id, step_id)["action"])
        self.gi.invocations.run_invocation_step_action(invocation_id, step_id, action=True)
        self.assertTrue(self.gi.invocations.show_invocation_step(invocation_id, step_id)["action"])

        summary = self.gi.invocations.get_invocation_summary(invocation_id)
        report = self.gi.invocations.get_invocation_report(invocation_id)

        assert summary['states'] == {'ok': 1}
        assert report['workflows'] == {workflow['id']: {'name': 'paste_columns'}}
