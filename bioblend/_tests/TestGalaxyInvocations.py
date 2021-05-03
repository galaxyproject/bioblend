import os
import time

from . import GalaxyTestBase, test_util


class TestGalaxyInvocations(GalaxyTestBase.GalaxyTestBase):
    def setUp(self):
        super().setUp()
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        self.workflow_id = self.gi.workflows.import_workflow_from_local_path(path)['id']
        self.history_id = self.gi.histories.create_history(name="TestGalaxyInvocations")["id"]
        self.dataset_id = self._test_dataset(self.history_id)

    def tearDown(self):
        self.gi.histories.delete_history(self.history_id, purge=True)

    @test_util.skip_unless_galaxy('release_19.09')
    def test_cancel_invocation(self):
        invocation = self._invoke_workflow()

        invocation_id = invocation["id"]
        invocations = self.gi.invocations.get_invocations()
        self.assertEqual(len(invocations), 1)
        self.assertEqual(invocations[0]["id"], invocation_id)
        self.gi.invocations.cancel_invocation(invocation_id)
        invocation = self.gi.invocations.show_invocation(invocation_id)
        self.assertEqual(invocation['state'], 'cancelled')

    @test_util.skip_unless_galaxy('release_20.01')
    def test_get_invocations(self):
        invoc1 = self._invoke_workflow()

        # Run the first workflow on another history
        dataset = {'src': 'hda', 'id': self.dataset_id}
        hist2_id = self.gi.histories.create_history('hist2')['id']
        invoc2 = self.gi.workflows.invoke_workflow(
            self.workflow_id,
            history_id=hist2_id,
            inputs={'Input 1': dataset, 'Input 2': dataset},
            inputs_by='name'
        )

        # Run another workflow on the 2nd history
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        workflow2_id = self.gi.workflows.import_workflow_from_local_path(path)['id']
        invoc3 = self.gi.workflows.invoke_workflow(
            workflow2_id,
            history_id=hist2_id,
            inputs={'Input 1': dataset, 'Input 2': dataset},
            inputs_by='name'
        )

        for invoc in (invoc1, invoc2, invoc3):
            self.gi.invocations.wait_for_invocation(invoc['id'])

        # Test filtering by workflow ID
        for wf_id, expected_invoc_num in {self.workflow_id: 2, workflow2_id: 1}.items():
            invocs = self.gi.invocations.get_invocations(workflow_id=wf_id)
            self.assertEqual(len(invocs), expected_invoc_num)
            for invoc in invocs:
                self.assertEqual(invoc['workflow_id'], wf_id)

        # Test filtering by history ID
        for hist_id, expected_invoc_num in {self.history_id: 1, hist2_id: 2}.items():
            invocs = self.gi.invocations.get_invocations(history_id=hist_id)
            self.assertEqual(len(invocs), expected_invoc_num)
            for invoc in invocs:
                self.assertEqual(invoc['history_id'], hist_id)

        # Test limiting
        limit_invocs = self.gi.invocations.get_invocations(limit=2)
        self.assertEqual(len(limit_invocs), 2)

        self.gi.histories.delete_history(hist2_id, purge=True)

    @test_util.skip_unless_galaxy('release_19.09')
    def test_get_invocation_report(self):
        invocation = self._invoke_workflow()

        invocation_id = invocation['id']
        workflow_id = invocation['workflow_id']
        report = self.gi.invocations.get_invocation_report(invocation_id)
        assert report['workflows'] == {workflow_id: {'name': 'paste_columns'}}
        try:
            self.gi.invocations.get_invocation_report_pdf(invocation_id, 'report.pdf')
        except Exception:
            # This can fail if dependencies as weasyprint are not installed on the Galaxy server
            pass

    @test_util.skip_unless_galaxy('release_20.09')
    def test_get_invocation_biocompute_object(self):
        invocation = self._invoke_workflow()

        self.gi.invocations.wait_for_invocation(invocation['id'])
        biocompute_object = self.gi.invocations.get_invocation_biocompute_object(invocation['id'])
        self.assertEqual(len(biocompute_object['description_domain']['pipeline_steps']), 1)

    @test_util.skip_unless_galaxy('release_19.09')
    def test_get_invocation_jobs_summary(self):
        invocation = self._invoke_workflow()
        self.gi.invocations.wait_for_invocation(invocation['id'])
        jobs_summary = self.gi.invocations.get_invocation_summary(invocation['id'])
        self.assertEqual(jobs_summary['populated_state'], 'ok')
        step_jobs_summary = self.gi.invocations.get_invocation_step_jobs_summary(invocation['id'])
        self.assertEqual(len(step_jobs_summary), 1)
        self.assertEqual(step_jobs_summary[0]['populated_state'], 'ok')

    @test_util.skip_unless_galaxy('release_19.09')
    @test_util.skip_unless_tool("cat1")
    @test_util.skip_unless_tool("cat")
    def test_workflow_scheduling(self):
        path = test_util.get_abspath(os.path.join('data', 'test_workflow_pause.ga'))
        workflow = self.gi.workflows.import_workflow_from_local_path(path)

        invocation = self.gi.workflows.invoke_workflow(
            workflow["id"],
            inputs={"0": {"src": "hda", "id": self.dataset_id}},
            history_id=self.history_id,
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
        self.gi.invocations.wait_for_invocation(invocation['id'])

    @test_util.skip_unless_galaxy('release_21.01')
    def test_rerun_invocation(self):
        invocation = self._invoke_workflow()
        self.gi.invocations.wait_for_invocation(invocation['id'])
        rerun_invocation = self.gi.invocations.rerun_invocation(invocation['id'], import_inputs_to_history=True)
        self.gi.invocations.wait_for_invocation(rerun_invocation['id'])
        history = self.gi.histories.show_history(rerun_invocation['history_id'], contents=True)
        self.assertEqual(len(history), 3)

    def _invoke_workflow(self):
        dataset = {'src': 'hda', 'id': self.dataset_id}

        return self.gi.workflows.invoke_workflow(
            self.workflow_id,
            inputs={'Input 1': dataset, 'Input 2': dataset},
            history_id=self.history_id,
            inputs_by='name',
        )
