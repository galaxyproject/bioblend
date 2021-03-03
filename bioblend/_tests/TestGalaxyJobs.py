import os
from operator import itemgetter

from bioblend import TimeoutException
from bioblend.galaxy.tools.inputs import (
    dataset,
    inputs,
)
from . import (
    GalaxyTestBase,
    test_util
)


class TestGalaxyJobs(GalaxyTestBase.GalaxyTestBase):
    def setUp(self):
        super().setUp()
        self.history_id = self.gi.histories.create_history(name='TestGalaxyJobs')['id']
        self.dataset_contents = "line 1\nline 2\rline 3\r\nline 4"
        self.dataset_id = self._test_dataset(self.history_id, contents=self.dataset_contents)

    def tearDown(self):
        pass
        self.gi.histories.delete_history(self.history_id, purge=True)

    @test_util.skip_unless_tool("cat1")
    def test_wait_for_job(self):
        tool_inputs = inputs().set(
            "input1", dataset(self.dataset_id)
        )
        tool_output = self.gi.tools.run_tool(
            history_id=self.history_id,
            tool_id="cat1",
            tool_inputs=tool_inputs
        )
        job_id = tool_output['jobs'][0]['id']
        job = self.gi.jobs.wait_for_job(job_id)
        self.assertEqual(job['state'], 'ok')

    @test_util.skip_unless_galaxy('release_21.01')
    @test_util.skip_unless_tool("random_lines1")
    def test_run_and_rerun_random_lines(self):
        tool_inputs = {
            'num_lines': '1',
            'input': {
                'src': 'hda',
                'id': self.dataset_id
            },
            'seed_source': {
                'seed_source_selector': 'set_seed',
                'seed': 'asdf'
            }
        }

        original_output = self.gi.tools.run_tool(
            history_id=self.history_id,
            tool_id="random_lines1",
            tool_inputs=tool_inputs,
            input_format='21.01'
        )
        original_job_id = original_output['jobs'][0]['id']

        rerun_output = self.gi.jobs.rerun_job(original_job_id)
        original_output_content = self.gi.datasets.download_dataset(original_output['outputs'][0]['id'])
        rerun_output_content = self.gi.datasets.download_dataset(rerun_output['outputs'][0]['id'])
        self.assertEqual(rerun_output_content, original_output_content)

    @test_util.skip_unless_galaxy('release_21.01')
    @test_util.skip_unless_tool("Show beginning1")
    def test_rerun_and_remap(self):
        path = test_util.get_abspath(os.path.join('data', 'select_first.ga'))
        wf = self.gi.workflows.import_workflow_from_local_path(path)
        wf_inputs = {
            "0": {'src': 'hda', 'id': self.dataset_id},
            "1": "-1",
        }
        invocation_id = self.gi.workflows.invoke_workflow(wf['id'], inputs=wf_inputs, history_id=self.history_id)['id']
        invocation = self.gi.invocations.wait_for_invocation(invocation_id)
        job_steps = [step for step in invocation['steps'] if step['job_id']]
        job_steps.sort(key=itemgetter('order_index'))
        for step in job_steps:
            try:
                self.gi.jobs.wait_for_job(step['job_id'], maxwait=30)
            except TimeoutException:
                # The first job should error, not time out
                raise
            except Exception:
                break
        else:
            raise Exception("The first job should have failed")

        history_contents = self.gi.histories.show_history(self.history_id, contents=True)
        self.assertEqual(len(history_contents), 3)
        self.assertEqual(history_contents[1]['state'], 'error')
        self.assertEqual(history_contents[2]['state'], 'paused')

        # now rerun and remap with correct input param
        job_id = self.gi.datasets.show_dataset(history_contents[1]['id'])['creating_job']
        tool_inputs_update = {
            'lineNum': '1'
        }
        self.gi.jobs.rerun_job(job_id, remap=True, tool_inputs_update=tool_inputs_update)

        # Wait for the last dataset in the history to be unpaused and complete
        last_dataset = self.gi.histories.show_history(self.history_id, contents=True)[-1]
        self.gi.datasets.wait_for_dataset(last_dataset['id'])
        self.assertEqual(last_dataset['hid'], 3)
        self.assertEqual(last_dataset['id'], history_contents[2]['id'])
        self._wait_and_verify_dataset(last_dataset['id'], b'line 1\tline 1\n')
