import os
import time

from . import GalaxyTestBase, test_util


class TestGalaxyInvocations(GalaxyTestBase.GalaxyTestBase):
    @test_util.skip_unless_galaxy('release_19.09')
    def test_invocation(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        workflow = self.gi.workflows.import_workflow_from_local_path(path)
        history_id = self.gi.histories.create_history(name="TestWorkflowState")["id"]
        dataset1_id = self._test_dataset(history_id)
        dataset = {'src': 'hda', 'id': dataset1_id}

        invocation = self.gi.workflows.invoke_workflow(
            workflow['id'],
            inputs={'Input 1': dataset, 'Input 2': dataset},
            history_id=history_id,
            inputs_by='name',
        )

        invocation_id = invocation["id"]
        invocations = self.gi.invocations.get_invocations()
        self.assertEqual(len(invocations), 1)
        self.assertEqual(invocations[0]["id"], invocation_id)
        self.gi.invocations.cancel_invocation(invocation_id)
        invocation = self.gi.invocations.show_invocation(invocation_id)
        self.assertEqual(invocation['state'], 'cancelled')

        summary = self.gi.invocations.get_invocation_summary(invocation_id)
        report = self.gi.invocations.get_invocation_report(invocation_id)

        assert summary['states'] == {}
        assert report['workflows'] == {workflow['id']: {'name': 'paste_columns'}}

    @test_util.skip_unless_galaxy('release_19.09')
    @test_util.skip_unless_tool("cat1")
    @test_util.skip_unless_tool("cat")
    def test_workflow_scheduling(self):
        path = test_util.get_abspath(os.path.join('data', 'test_workflow_pause.ga'))
        workflow = self.gi.workflows.import_workflow_from_local_path(path)
        history_id = self.gi.histories.create_history(name="TestWorkflowState")["id"]
        dataset1_id = self._test_dataset(history_id)

        invocation = self.gi.workflows.invoke_workflow(
            workflow["id"],
            inputs={"0": {"src": "hda", "id": dataset1_id}},
        )
        invocation_id = invocation["id"]

        def invocation_steps_by_order_index():
            invocation = self.gi.invocations.show_invocation(invocation_id)
            return {s["order_index"]: s for s in invocation["steps"]}

        for _ in range(20):
            if 2 in invocation_steps_by_order_index():
                break
            time.sleep(.5)

        steps = invocation_steps_by_order_index()
        pause_step = steps[2]
        self.assertIsNone(
            self.gi.invocations.show_invocation_step(invocation_id, pause_step["id"])["action"])
        self.gi.invocations.run_invocation_step_action(invocation_id, pause_step["id"], action=True)
        self.assertTrue(self.gi.invocations.show_invocation_step(invocation_id, pause_step["id"])["action"])
        for _ in range(20):
            invocation = self.gi.invocations.show_invocation(invocation_id)
            if invocation["state"] == "scheduled":
                break

            time.sleep(.5)

        invocation = self.gi.invocations.show_invocation(invocation_id)
        self.assertEqual(invocation["state"], "scheduled")
