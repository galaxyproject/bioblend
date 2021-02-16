import os
import time

from . import (
    GalaxyTestBase,
    test_util
)


class TestGalaxyJobs(GalaxyTestBase.GalaxyTestBase):
    def setUp(self):
        super().setUp()
        self.history_id = self.gi.histories.create_history(name='TestJobRerun')['id']
        self.dataset_contents = "line 1\nline 2\rline 3\r\nline 4"
        self.dataset_id = self._test_dataset(self.history_id, contents=self.dataset_contents)

    def tearDown(self):
        pass
        self.gi.histories.delete_history(self.history_id, purge=True)

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
        self._wait_job(original_job_id)
        build_for_rerun = self.gi.jobs._build_for_rerun(original_job_id)
        self.assertEqual(build_for_rerun['state_inputs']['seed_source']['seed'], 'asdf')

        rerun_output = self.gi.jobs.rerun_job(original_job_id)
        rerun_output_content = self.gi.datasets.download_dataset(rerun_output['outputs'][0]['id'])
        original_output_content = self.gi.datasets.download_dataset(original_output['outputs'][0]['id'])
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
        inv = self.gi.workflows.invoke_workflow(wf['id'], wf_inputs)
        for _ in range(120):
            inv = self.gi.invocations.show_invocation(inv['id'])
            if inv['steps']:
                for step in inv['steps']:
                    if step['job_id']:
                        self._wait_job(step['job_id'])
                break
            time.sleep(.5)
        new_history_id = inv['history_id']
        history_contents = self.gi.histories.show_history(new_history_id, contents=True)
        self.assertEqual(len(history_contents), 2)
        self.assertEqual(history_contents[0]['state'], 'error')
        self.assertEqual(history_contents[1]['state'], 'paused')

        # now rerun and remap with correct input param
        job_id = self.gi.datasets.show_dataset(history_contents[0]['id'])['creating_job']
        tool_inputs_update = {
            'lineNum': '1'
        }
        self.gi.jobs.rerun_job(job_id, remap=True, tool_inputs_update=tool_inputs_update)
        jobs_to_complete = [job['id'] for job in self.gi.jobs.get_jobs() if job['history_id'] == new_history_id]
        for job_id in jobs_to_complete:
            self._wait_job(job_id)

        # check remapped outputs
        new_history_contents = self.gi.histories.show_history(new_history_id, contents=True)
        self.assertEqual(new_history_contents[0]['state'], 'error')  # from first run
        self.assertEqual(new_history_contents[0]['hid'], 1)
        self.assertEqual(new_history_contents[1]['state'], 'ok')  # from new run
        self.assertEqual(new_history_contents[1]['hid'], 1)
        self.assertEqual(new_history_contents[2]['state'], 'ok')  # child dataset
        self.assertEqual(new_history_contents[2]['hid'], 2)
        self.assertEqual(new_history_contents[2]['id'], history_contents[1]['id'])
        self.assertEqual(len(new_history_contents), 3)

    def _wait_job(self, job_id):
        for _ in range(120):
            job_state = self.gi.jobs.show_job(job_id)['state']
            if job_state in ['ok', 'error']:
                break
            time.sleep(.5)
