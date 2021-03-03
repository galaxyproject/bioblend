from datetime import datetime, timedelta

from . import (
    GalaxyTestBase,
    test_util
)


class TestGalaxyJobs(GalaxyTestBase.GalaxyTestBase):
    @test_util.skip_unless_tool("random_lines1")
    def test_get_jobs(self):
        history_id = self.gi.histories.create_history(name="test_get_jobs history1")["id"]
        dataset_id = self.gi.tools.paste_content("line 1\nline 2\rline 3\r\nline 4", history_id)["outputs"][0]["id"]
        tool_inputs = {
            'num_lines': '1',
            'input': {
                'src': 'hda',
                'id': dataset_id
            },
            'seed_source': {
                'seed_source_selector': 'set_seed',
                'seed': 'asdf'
            }
        }
        self.gi.tools.run_tool(
            history_id=history_id,
            tool_id="random_lines1",
            tool_inputs=tool_inputs,
            input_format='21.01'
        )
        self.gi.tools.run_tool(
            history_id=history_id,
            tool_id="random_lines1",
            tool_inputs=tool_inputs,
            input_format='21.01'
        )

        jobs = self.gi.jobs.get_jobs(tool_id='random_lines1', history_id=history_id, state='new')
        self.assertEqual(len(jobs), 2)
        jobs = self.gi.jobs.get_jobs(tool_id='random_lines1', history_id=history_id, state='failed')
        self.assertEqual(len(jobs), 0)
        yesterday = datetime.today() - timedelta(days=1)
        jobs = self.gi.jobs.get_jobs(date_range_max=yesterday.strftime('%Y-%m-%d'))
        self.assertEqual(len(jobs), 0)
        tomorrow = datetime.today() + timedelta(days=1)
        jobs = self.gi.jobs.get_jobs(date_range_min=tomorrow.strftime('%Y-%m-%d'))
        self.assertEqual(len(jobs), 0)
        jobs = self.gi.jobs.get_jobs(date_range_min=datetime.today().strftime('%Y-%m-%d'), history_id=history_id)
        self.assertEqual(len(jobs), 3)

    @test_util.skip_unless_galaxy('release_21.01')
    @test_util.skip_unless_tool("random_lines1")
    def test_run_and_rerun_random_lines(self):
        history_id = self.gi.histories.create_history(name="test_run_random_lines history")["id"]
        dataset_id = self._test_dataset(history_id, contents="line 1\nline 2\rline 3\r\nline 4")
        tool_inputs = {
            'num_lines': '1',
            'input': {
                'src': 'hda',
                'id': dataset_id
            },
            'seed_source': {
                'seed_source_selector': 'set_seed',
                'seed': 'asdf'
            }
        }

        original_output = self.gi.tools.run_tool(
            history_id=history_id,
            tool_id="random_lines1",
            tool_inputs=tool_inputs,
            input_format='21.01'
        )
        original_job_id = original_output['jobs'][0]['id']
        build_for_rerun = self.gi.jobs._build_for_rerun(original_job_id)
        self.assertEqual(build_for_rerun['state_inputs']['seed_source']['seed'], 'asdf')

        rerun_output = self.gi.jobs.rerun_job(original_job_id)
        rerun_output_content = self.gi.datasets.download_dataset(rerun_output['outputs'][0]['id'])
        original_output_content = self.gi.datasets.download_dataset(original_output['outputs'][0]['id'])
        self.assertEqual(rerun_output_content, original_output_content)
