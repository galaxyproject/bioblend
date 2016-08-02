"""
Use ``nose`` to run these unit tests.
"""
import json
import os
import shutil
import tempfile
import time

from six.moves import range

from . import GalaxyTestBase, test_util


def get_abspath(path):
    return os.path.join(os.path.dirname(__file__), path)


@test_util.skip_unless_galaxy()
class TestGalaxyWorkflows(GalaxyTestBase.GalaxyTestBase):

    @test_util.skip_unless_galaxy('release_15.03')
    @test_util.skip_unless_tool("cat1")
    @test_util.skip_unless_tool("cat")
    def test_workflow_scheduling(self):
        path = get_abspath(os.path.join('data', 'test_workflow_pause.ga'))
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

        def invocation_steps_by_order_index():
            invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
            return dict([(s["order_index"], s) for s in invocation["steps"]])

        for i in range(20):
            if 2 in invocation_steps_by_order_index():
                break
            time.sleep(.5)

        invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
        self.assertEqual(invocation['state'], "ready")

        steps = invocation_steps_by_order_index()
        pause_step = steps[2]
        self.assertIsNone(self.gi.workflows.show_invocation_step(workflow_id, invocation_id, pause_step["id"])["action"])
        self.gi.workflows.run_invocation_step_action(workflow_id, invocation_id, pause_step["id"], action=True)
        self.assertTrue(self.gi.workflows.show_invocation_step(workflow_id, invocation_id, pause_step["id"])["action"])
        for i in range(20):
            invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
            if invocation["state"] == "scheduled":
                break

            time.sleep(.5)

        invocation = self.gi.workflows.show_invocation(workflow_id, invocation_id)
        self.assertEqual(invocation["state"], "scheduled")

    @test_util.skip_unless_galaxy('release_15.03')
    @test_util.skip_unless_tool("cat1")
    @test_util.skip_unless_tool("cat")
    def test_cancelling_workflow_scheduling(self):
        path = get_abspath(os.path.join('data', 'test_workflow_pause.ga'))
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

    def test_import_workflow_from_local_path(self):
        with self.assertRaises(Exception):
            self.gi.workflows.import_workflow_from_local_path(None)
        path = get_abspath(os.path.join('data', 'paste_columns.ga'))
        wk = self.gi.workflows.import_workflow_from_local_path(path)
        self.assertIsNotNone(wk['id'])

    def test_export_workflow_to_local_path(self):
        export_dir = tempfile.mkdtemp(prefix='bioblend_test_')
        with self.assertRaises(Exception):
            self.gi.workflows.export_workflow_to_local_path(None, None, None)
        path = get_abspath(os.path.join('data', 'paste_columns.ga'))
        wk = self.gi.workflows.import_workflow_from_local_path(path)
        self.gi.workflows.export_workflow_to_local_path(wk['id'], export_dir)
        dir_contents = os.listdir(export_dir)
        self.assertEqual(len(dir_contents), 1)
        export_path = os.path.join(export_dir, dir_contents[0])
        with open(export_path, 'r') as f:
            workflow_json = json.load(f)
        self.assertIsInstance(workflow_json, dict)
        shutil.rmtree(export_dir)

    def test_get_workflows(self):
        wk = self.gi.workflows.get_workflows()[0]
        self.assertIsNotNone(wk['id'])
        self.assertIsNotNone(wk['name'])
        self.assertIsNotNone(wk['url'])

    def test_show_workflow(self):
        wk = self.gi.workflows.get_workflows()[0]
        # TODO: This test is problematic, because it relies on the get_workflow method!
        # This test is not self-contained.
        wk = self.gi.workflows.show_workflow(wk['id'])
        self.assertIsNotNone(wk['id'])
        self.assertIsNotNone(wk['name'])
        self.assertIsNotNone(wk['inputs'])
        self.assertIsNotNone(wk['url'])

    def test_run_workflow(self):
        wk = self.gi.workflows.get_workflows()[0]
        # Try invalid run of workflow
        with self.assertRaises(Exception):
            self.gi.workflows.run_workflow(wk['id'], None)

        # TODO: Hard coded workflow ID. We need to either import, or have a fixed workflow id for testing
#        workflowID = wk['id']
#        sourcehist = '177346507b04acbf'
#
#        # Do a run of a workflow over fastq files from a history
#        print "Finding workflow"
#        wk = self.gi.workflows.show_workflow(workflowID)
#        print wk
#        input = wk['inputs'].keys()[0]
#
#        print "Finding fastqsanger input files"
#        sourcecontents = self.gi.histories.show_history(sourcehist, contents=True)
#        sourcedata = [self.gi.histories.show_dataset(sourcehist, content['id']) for content in sourcecontents]
#
#        fastqdata = [data['id'] for data in sourcedata if data['data_type']=='fastqsanger']
#
#        fastqID = fastqdata[0]
#        datamap = dict()
#        datamap[input] = dict()
#        datamap[input]['src'] = 'hda'
#        datamap[input]['id'] = fastqID
#        data_name = self.gi.histories.show_dataset(sourcehist, fastqID)['name']
#        print "Running workflow on "+data_name
#        self.gi.workflows.run_workflow(workflowID, datamap, history_name="automated_test", import_inputs_to_history=True)
