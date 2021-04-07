import json
import os
import shutil
import tempfile
import time

from bioblend import ConnectionError
from . import GalaxyTestBase, test_util


class TestGalaxyWorkflows(GalaxyTestBase.GalaxyTestBase):

    @test_util.skip_unless_tool("cat1")
    @test_util.skip_unless_tool("cat")
    def test_workflow_scheduling(self):
        path = test_util.get_abspath(os.path.join('data', 'test_workflow_pause.ga'))
        workflow = self.gi.workflows.import_workflow_from_local_path(path)
        workflow_id = workflow["id"]
        history_id = self.gi.histories.create_history(name="TestWorkflowState")["id"]

        invocations = self.gi.workflows.get_invocations(workflow_id)
        self.assertEqual(len(invocations), 0)

        # Try invalid invocation (no input)
        with self.assertRaises(ConnectionError):
            self.gi.workflows.invoke_workflow(workflow['id'])

        dataset1_id = self._test_dataset(history_id)
        invocation = self.gi.workflows.invoke_workflow(
            workflow["id"],
            inputs={"0": {"src": "hda", "id": dataset1_id}},
        )
        self.assertEqual(invocation['state'], 'new')
        invocation_id = invocation["id"]
        invocations = self.gi.workflows.get_invocations(workflow_id)
        self.assertEqual(len(invocations), 1)
        self.assertEqual(invocations[0]["id"], invocation_id)

        def invocation_steps_by_order_index():
            invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
            return {s["order_index"]: s for s in invocation["steps"]}

        for _ in range(20):
            if 2 in invocation_steps_by_order_index():
                break
            time.sleep(.5)

        invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
        self.assertEqual(invocation['state'], "ready")

        steps = invocation_steps_by_order_index()
        pause_step = steps[2]
        self.assertIsNone(
            self.gi.workflows.show_invocation_step(workflow_id, invocation_id, pause_step["id"])["action"])
        self.gi.workflows.run_invocation_step_action(workflow_id, invocation_id, pause_step["id"], action=True)
        self.assertTrue(self.gi.workflows.show_invocation_step(workflow_id, invocation_id, pause_step["id"])["action"])
        for _ in range(20):
            invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
            if invocation["state"] == "scheduled":
                break

            time.sleep(.5)

        invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
        self.assertEqual(invocation["state"], "scheduled")

    @test_util.skip_unless_galaxy('release_19.01')
    def test_invoke_workflow_parameters_normalized(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns_subworkflow.ga'))
        workflow_id = self.gi.workflows.import_workflow_from_local_path(path)["id"]
        history_id = self.gi.histories.create_history(name="TestWorkflowInvokeParametersNormalized")["id"]
        dataset_id = self._test_dataset(history_id)
        with self.assertRaises(ConnectionError):
            self.gi.workflows.invoke_workflow(
                workflow_id,
                inputs={'0': {'src': 'hda', 'id': dataset_id}},
                params={'1': {'1|2': 'comma'}}
            )
        self.gi.workflows.invoke_workflow(
            workflow_id,
            inputs={'0': {'src': 'hda', 'id': dataset_id}},
            params={'1': {'1|2': 'comma'}},
            parameters_normalized=True
        )

    @test_util.skip_unless_tool("cat1")
    @test_util.skip_unless_tool("cat")
    def test_cancelling_workflow_scheduling(self):
        path = test_util.get_abspath(os.path.join('data', 'test_workflow_pause.ga'))
        workflow = self.gi.workflows.import_workflow_from_local_path(path)
        workflow_id = workflow["id"]
        history_id = self.gi.histories.create_history(name="TestWorkflowState")["id"]
        dataset1_id = self._test_dataset(history_id)

        invocations = self.gi.workflows.get_invocations(workflow_id)
        self.assertEqual(len(invocations), 0)

        invocation = self.gi.workflows.invoke_workflow(
            workflow["id"],
            inputs={"0": {"src": "hda", "id": dataset1_id}},
        )
        invocation_id = invocation["id"]
        invocations = self.gi.workflows.get_invocations(workflow_id)
        self.assertEqual(len(invocations), 1)
        self.assertEqual(invocations[0]["id"], invocation_id)

        invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
        self.assertIn(invocation['state'], ['new', 'ready'])

        self.gi.workflows.cancel_invocation(workflow_id, invocation_id)
        invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
        self.assertEqual(invocation['state'], 'cancelled')

    def test_import_export_workflow_from_local_path(self):
        with self.assertRaises(TypeError):
            self.gi.workflows.import_workflow_from_local_path(None)
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        imported_wf = self.gi.workflows.import_workflow_from_local_path(path)
        self.assertIsInstance(imported_wf, dict)
        self.assertEqual(imported_wf['name'], 'paste_columns')
        self.assertTrue(imported_wf['url'].startswith('/api/workflows/'))
        self.assertFalse(imported_wf['deleted'])
        self.assertFalse(imported_wf['published'])
        with self.assertRaises(TypeError):
            self.gi.workflows.export_workflow_to_local_path(None, None, None)
        export_dir = tempfile.mkdtemp(prefix='bioblend_test_')
        try:
            self.gi.workflows.export_workflow_to_local_path(imported_wf['id'], export_dir)
            dir_contents = os.listdir(export_dir)
            self.assertEqual(len(dir_contents), 1)
            export_path = os.path.join(export_dir, dir_contents[0])
            with open(export_path) as f:
                exported_wf_dict = json.load(f)
        finally:
            shutil.rmtree(export_dir)
        self.assertIsInstance(exported_wf_dict, dict)

    def test_import_publish_workflow_from_local_path(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        imported_wf = self.gi.workflows.import_workflow_from_local_path(path, publish=True)
        self.assertIsInstance(imported_wf, dict)
        self.assertFalse(imported_wf['deleted'])
        self.assertTrue(imported_wf['published'])

    def test_import_export_workflow_dict(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        with open(path) as f:
            wf_dict = json.load(f)
        imported_wf = self.gi.workflows.import_workflow_dict(wf_dict)
        self.assertIsInstance(imported_wf, dict)
        self.assertEqual(imported_wf['name'], 'paste_columns')
        self.assertTrue(imported_wf['url'].startswith('/api/workflows/'))
        self.assertFalse(imported_wf['deleted'])
        self.assertFalse(imported_wf['published'])
        exported_wf_dict = self.gi.workflows.export_workflow_dict(imported_wf['id'])
        self.assertIsInstance(exported_wf_dict, dict)

    def test_import_publish_workflow_dict(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        with open(path) as f:
            wf_dict = json.load(f)
        imported_wf = self.gi.workflows.import_workflow_dict(wf_dict, publish=True)
        self.assertIsInstance(imported_wf, dict)
        self.assertFalse(imported_wf['deleted'])
        self.assertTrue(imported_wf['published'])

    def test_get_workflows(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        workflow = self.gi.workflows.import_workflow_from_local_path(path)
        all_wfs = self.gi.workflows.get_workflows()
        self.assertGreater(len(all_wfs), 0)
        wfs_with_name = self.gi.workflows.get_workflows(name=workflow['name'])
        wf_list = [w for w in wfs_with_name if w['id'] == workflow['id']]
        self.assertEqual(len(wf_list), 1)
        wf_data = wf_list[0]
        self.assertEqual(wf_data['url'], workflow['url'])

    def test_show_workflow(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        wf = self.gi.workflows.import_workflow_from_local_path(path)
        wf_data = self.gi.workflows.show_workflow(wf['id'])
        self.assertEqual(wf_data['id'], wf['id'])
        self.assertEqual(wf_data['name'], wf['name'])
        self.assertEqual(wf_data['url'], wf['url'])
        self.assertEqual(len(wf_data['steps']), 3)
        self.assertIsNotNone(wf_data['inputs'])

    @test_util.skip_unless_galaxy('release_18.05')
    def test_update_workflow_name(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        wf = self.gi.workflows.import_workflow_from_local_path(path)
        new_name = 'new name'
        updated_wf = self.gi.workflows.update_workflow(wf['id'], name=new_name)
        self.assertEqual(updated_wf['name'], new_name)

    @test_util.skip_unless_galaxy('release_21.01')
    def test_update_workflow_published(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        wf = self.gi.workflows.import_workflow_from_local_path(path)
        self.assertFalse(wf['published'])
        updated_wf = self.gi.workflows.update_workflow(wf['id'], published=True)
        self.assertTrue(updated_wf['published'])
        updated_wf = self.gi.workflows.update_workflow(wf['id'], published=False)
        self.assertFalse(updated_wf['published'])

    @test_util.skip_unless_galaxy('release_19.09')  # due to Galaxy bug fixed in https://github.com/galaxyproject/galaxy/pull/9014
    def test_show_workflow_versions(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        wf = self.gi.workflows.import_workflow_from_local_path(path)
        wf_data = self.gi.workflows.show_workflow(wf['id'])
        self.assertEqual(wf_data['version'], 0)
        new_name = 'new name'
        self.gi.workflows.update_workflow(wf['id'], name=new_name)
        updated_wf = self.gi.workflows.show_workflow(wf['id'])
        self.assertEqual(updated_wf['name'], new_name)
        self.assertEqual(updated_wf['version'], 1)
        updated_wf = self.gi.workflows.show_workflow(wf['id'], version=0)
        self.assertEqual(updated_wf['name'], 'paste_columns')
        self.assertEqual(updated_wf['version'], 0)
        updated_wf = self.gi.workflows.show_workflow(wf['id'], version=1)
        self.assertEqual(updated_wf['name'], new_name)
        self.assertEqual(updated_wf['version'], 1)

    @test_util.skip_unless_galaxy('release_19.09')
    def test_extract_workflow_from_history(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        wf = self.gi.workflows.import_workflow_from_local_path(path)
        history_id = self.gi.histories.create_history(name="test_wf_invocation")['id']
        dataset1_id = self._test_dataset(history_id)
        dataset = {'src': 'hda', 'id': dataset1_id}
        invocation_id = self.gi.workflows.invoke_workflow(
            wf['id'],
            inputs={'Input 1': dataset, 'Input 2': dataset},
            history_id=history_id,
            inputs_by='name',
        )['id']
        invocation = self.gi.invocations.wait_for_invocation(invocation_id)
        wf1 = self.gi.workflows.show_workflow(invocation['workflow_id'])
        datasets = self.gi.histories.show_history(invocation['history_id'], contents=True)
        dataset_hids = [dataset['hid'] for dataset in datasets]
        job_ids = [step['job_id'] for step in invocation['steps'] if step['job_id']]

        for job_id in job_ids:
            self.gi.jobs.wait_for_job(job_id)

        new_workflow_name = 'My new workflow!'
        wf2 = self.gi.workflows.extract_workflow_from_history(
            history_id=invocation['history_id'],
            workflow_name=new_workflow_name,
            job_ids=job_ids,
            dataset_hids=dataset_hids,
        )
        wf2 = self.gi.workflows.show_workflow(wf2['id'])
        self.assertEqual(wf2['name'], new_workflow_name)
        self.assertEqual(len(wf1['steps']), len(wf2['steps']))
        for i in range(len(wf1['steps'])):
            self.assertEqual(wf1['steps'][str(i)]['type'], wf2['steps'][str(i)]['type'])
            self.assertEqual(wf1['steps'][str(i)]['tool_id'], wf2['steps'][str(i)]['tool_id'])

    @test_util.skip_unless_galaxy('release_18.09')
    def test_show_versions(self):
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        wf = self.gi.workflows.import_workflow_from_local_path(path)
        versions = self.gi.workflows.show_versions(wf['id'])
        self.assertEqual(len(versions), 1)
        version = versions[0]
        self.assertEqual(version['version'], 0)
        self.assertTrue('update_time' in version)
        self.assertTrue('steps' in version)

    @test_util.skip_unless_galaxy('release_21.01')
    def test_refactor_workflow(self):
        actions = [
            {"action_type": "add_input", "type": "data", "label": "foo"},
            {"action_type": "update_step_label", "label": "bar", "step": {"label": "foo"}},
        ]
        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        wf = self.gi.workflows.import_workflow_from_local_path(path)
        response = self.gi.workflows.refactor_workflow(wf['id'], actions, dry_run=True)
        self.assertEqual(len(response), 3)
        self.assertTrue('action_executions' in response)
        self.assertTrue('workflow' in response)
        self.assertTrue('dry_run' in response)
        self.assertEqual(len(response['action_executions']), 2)
        self.assertEqual(response['workflow']['steps']['0']['label'], 'bar')
        self.assertEqual(response['dry_run'], True)
