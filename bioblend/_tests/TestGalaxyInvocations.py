import os
import time

from bioblend import galaxy
from . import GalaxyTestBase, test_util


class TestGalaxyInvocations(GalaxyTestBase.GalaxyTestBase):
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
        user1 = self.gi.users.create_local_user('user1', 'email1@email.test', 'password1')
        user2 = self.gi.users.create_local_user('user2', 'email2@email.test', 'password2')
        key1 = self.gi.users.create_user_apikey(user1['id'])
        key2 = self.gi.users.create_user_apikey(user2['id'])
        user1_gi = galaxy.GalaxyInstance(url=self.gi.base_url, key=key1)
        user2_gi = galaxy.GalaxyInstance(url=self.gi.base_url, key=key2)

        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        workflow = self.gi.workflows.import_workflow_from_local_path(path, publish=True)
        dataset = {'src': 'hda', 'id': None}

        hist1 = user1_gi.histories.create_history('hist1')
        hist2 = user1_gi.histories.create_history('hist2')
        dataset_id = self._test_dataset(hist1['id'])
        dataset['id'] = dataset_id
        invoc1 = user1_gi.workflows.invoke_workflow(workflow['id'], history_id=hist1['id'],
                                                    inputs={'Input 1': dataset, 'Input 2': dataset},
                                                    inputs_by='name')
        dataset_id = self._test_dataset(hist2['id'])
        dataset['id'] = dataset_id
        invoc2 = user1_gi.workflows.invoke_workflow(workflow['id'], history_id=hist2['id'],
                                                    inputs={'Input 1': dataset, 'Input 2': dataset},
                                                    inputs_by='name')

        hist3 = user2_gi.histories.create_history('hist3')
        dataset_id = self._test_dataset(hist3['id'])
        dataset['id'] = dataset_id
        invoc3 = user2_gi.workflows.invoke_workflow(workflow['id'], history_id=hist3['id'],
                                                    inputs={'Input 1': dataset, 'Input 2': dataset},
                                                    inputs_by='name')

        self.gi.invocations.wait_for_invocation(invoc1['id'])
        self.gi.invocations.wait_for_invocation(invoc2['id'])
        self.gi.invocations.wait_for_invocation(invoc3['id'])

        self.assertEqual(invoc1['workflow_id'], invoc2['workflow_id'])
        self.assertEqual(invoc2['workflow_id'], invoc3['workflow_id'])

        all_invocs = self.gi.invocations.get_invocations(workflow['id'])
        user1_invocs = self.gi.invocations.get_invocations(workflow['id'], user_id=user1['id'])
        user2_invocs = self.gi.invocations.get_invocations(workflow['id'], user_id=user2['id'])
        self.assertEqual(len(all_invocs), 3)
        self.assertEqual(len(user1_invocs), 2)
        self.assertEqual(len(user2_invocs), 1)
        self.assertEqual(set(invoc['id'] for invoc in user1_invocs),
                         set([invoc1['id'], invoc2['id']]))

        hist1_invocs = self.gi.invocations.get_invocations(workflow['id'], history_id=hist1['id'])
        hist1_user1_invocs = self.gi.invocations.get_invocations(workflow['id'], history_id=hist1['id'],
                                                                 user_id=user1['id'])
        hist1_user2_invocs = self.gi.invocations.get_invocations(workflow['id'], history_id=hist1['id'],
                                                                 user_id=user2['id'])
        self.assertEqual(len(hist1_invocs), 1)
        self.assertEqual(len(hist1_user1_invocs), 1)
        self.assertEqual(len(hist1_user2_invocs), 0)

        limit_invocs = self.gi.invocations.get_invocations(workflow['id'], limit=2)
        self.assertEqual(len(limit_invocs), 2)

        self.gi.users.delete_user(user1['id'])
        self.gi.users.delete_user(user2['id'])

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
        self.gi.invocations.wait_for_invocation(invocation['id'])

    def _invoke_workflow(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        workflow = self.gi.workflows.import_workflow_from_local_path(path)
        history_id = self.gi.histories.create_history(name="TestWorkflowState")["id"]
        dataset1_id = self._test_dataset(history_id)
        dataset = {'src': 'hda', 'id': dataset1_id}

        return self.gi.workflows.invoke_workflow(
            workflow['id'],
            inputs={'Input 1': dataset, 'Input 2': dataset},
            history_id=history_id,
            inputs_by='name',
        )
