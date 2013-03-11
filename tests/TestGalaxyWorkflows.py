"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure. 

Use ``nose`` to run these unit tests.
"""
import os
import simplejson
import GalaxyTestBase

class TestGalaxyWorkflows(GalaxyTestBase.GalaxyTestBase):

    def test_import_workflow_from_local_path(self):
        with self.assertRaises(Exception):
            self.gi.workflows.import_workflow_from_local_path(None)
        wk = self.gi.workflows.import_workflow_from_local_path('tests/data/SampleWorkflow.ga')
        self.assertNotEqual(wk['id'], None)

    def test_export_workflow_to_local_path(self):
        with self.assertRaises(Exception):
            self.gi.workflows.export_workflow_to_local_path(None, None, None)
        wk = self.gi.workflows.get_workflows()[0]
        file_local_path = "."
        filename = 'Galaxy-Workflow-%s.ga' % wk['name']
        self.gi.workflows.export_workflow_to_local_path(wk['id'], file_local_path)
        file_local_path = os.path.join(file_local_path, filename)

        with open(file_local_path, 'rb') as fp:
            workflow_json = simplejson.load(fp)

    def test_get_workflows(self):
        wk = self.gi.workflows.get_workflows()[0]
        self.assertNotEqual(wk['id'], None)
        self.assertNotEqual(wk['name'], None)
        self.assertNotEqual(wk['url'], None)

    def test_show_workflow(self):
        wk = self.gi.workflows.get_workflows()[0]
        # TODO: This test is problematic, because it relies on the get_workflow method!
        # This test is not self-contained.
        wk = self.gi.workflows.show_workflow(wk['id'])
        self.assertNotEqual(wk['id'], None)
        self.assertNotEqual(wk['name'], None)
        self.assertNotEqual(wk['inputs'], None)
        self.assertNotEqual(wk['url'], None)

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
