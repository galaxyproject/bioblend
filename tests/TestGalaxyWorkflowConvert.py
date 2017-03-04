"""
Tests on the GalaxyInstance object itself.

Use ``nose`` to run these unit tests.
"""
from test_util import unittest

from bioblend.galaxy.workflows.convert import workflow_to_simple, simple_to_workflow

import os
import yaml
import json
import uuid

def get_abspath(path):
    return os.path.join(os.path.dirname(__file__), path)


class TestGalaxyWorkflowConvert(unittest.TestCase):

    def setUp(self):
        pass

    def validate_workflow(self, workflow):
        self.assertIn('a_galaxy_workflow', workflow)
        self.assertIn('uuid', workflow)
        uuid.UUID(workflow['uuid'])
        for step_id, step in workflow['steps'].items():
            self.assertIn(step['type'], ['data_input', 'tool', 'pause'])
            if step['type'] == 'data_input':
                self.assertEqual(len(step['inputs']), 1)
                self.assertIn('name', step['inputs'][0])
                self.assertIn('description', step['inputs'][0])

            for name, connections in step['input_connections'].items():
                for connection in connections:
                    self.assertIn(str(connection['id']), workflow['steps'])

    def compare_workflow(self, workflow_a, workflow_b):
        self.assertEqual(workflow_a['uuid'], workflow_b['uuid'])

        for step_id, step in workflow_a['steps'].items():
            self.assertIn(step_id, workflow_b['steps'])
            if step['type'] == 'tool':
                for connection_name, connection in step['input_connections'].items():
                    self.assertIn( connection_name,
                        workflow_b['steps'][step_id]['input_connections'] )
                    #add check to make sure connections are equivilant


    def test_simple_convert(self):
        with open(get_abspath(os.path.join("data", "simple_workflow.yaml"))) as f:
            data_str = f.read()
        data = yaml.load(data_str)
        workflow = simple_to_workflow(data)
        #make sure it will serialize
        workflow_json = json.dumps(workflow)
        new_workflow = json.loads(workflow_json)
        self.validate_workflow(new_workflow)

    def test_workflow_convert(self):
        with open(get_abspath(os.path.join("data", "paste_columns.ga"))) as f:
            data_str = f.read()
        data = json.loads(data_str)
        simple = workflow_to_simple(data)

        print yaml.safe_dump(simple, default_flow_style = False)
        workflow = simple_to_workflow(simple)
        print json.dumps(workflow, indent=4)

        self.validate_workflow(workflow)
        self.compare_workflow(workflow, data)
