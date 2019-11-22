import os

from . import GalaxyTestBase, test_util


class TestGalaxyInvocations(GalaxyTestBase.GalaxyTestBase):
    @test_util.skip_unless_galaxy('release_19.09')
    def test_cancelling_workflow_scheduling(self):
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
