import os
from datetime import datetime, timedelta
from bioblend import galaxy

from . import (
    GalaxyTestBase,
    test_util
)


class TestGalaxyJobs(GalaxyTestBase.GalaxyTestBase):
    @test_util.skip_unless_tool("random_lines1")
    def test_get_jobs(self):
        user1 = self.gi.users.create_local_user('user1', 'email1@email.test', 'password1')
        user2 = self.gi.users.create_local_user('user2', 'email2@email.test', 'password2')
        key1 = self.gi.users.create_user_apikey(user1['id'])
        key2 = self.gi.users.create_user_apikey(user2['id'])
        user1_gi = galaxy.GalaxyInstance(url=self.gi.base_url, key=key1)
        user2_gi = galaxy.GalaxyInstance(url=self.gi.base_url, key=key2)

        history_id1 = user1_gi.histories.create_history(name="test_run_random_lines history1")["id"]
        dataset_id1 = user1_gi.tools.paste_content("line 1\nline 2\rline 3\r\nline 4", history_id1)["outputs"][0]["id"]
        tool_inputs = {
            'num_lines': '1',
            'input': {
                'src': 'hda',
                'id': dataset_id1
            },
            'seed_source': {
                'seed_source_selector': 'set_seed',
                'seed': 'asdf'
            }
        }
        user1_gi.tools.run_tool(
            history_id=history_id1,
            tool_id="random_lines1",
            tool_inputs=tool_inputs,
            input_format='21.01'
        )
        user1_gi.tools.run_tool(
            history_id=history_id1,
            tool_id="random_lines1",
            tool_inputs=tool_inputs,
            input_format='21.01'
        )

        path = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
        wf = user2_gi.workflows.import_workflow_from_local_path(path)
        history_id2 = user2_gi.histories.create_history(name="test_wf_invocation")['id']
        dataset_id2 = user2_gi.tools.paste_content("line 1\nline 2\rline 3\r\nline 4", history_id2)["outputs"][0]["id"]
        dataset = {'src': 'hda', 'id': dataset_id2}
        user2_gi.workflows.invoke_workflow(
            wf['id'],
            inputs={'Input 1': dataset, 'Input 2': dataset},
            history_id=history_id2,
            inputs_by='name',
        )

        jobs = user1_gi.jobs.get_jobs(tool_id='random_lines1')
        self.assertEqual(len(jobs), 2)
        yesterday = datetime.today() - timedelta(days=1)
        jobs = user1_gi.jobs.get_jobs(date_range_max=yesterday.strftime('%Y-%m-%d'))
        self.assertEqual(len(jobs), 0)
        tomorrow = datetime.today() + timedelta(days=1)
        jobs = user1_gi.jobs.get_jobs(date_range_min=tomorrow.strftime('%Y-%m-%d'))
        self.assertEqual(len(jobs), 0)
        jobs = user1_gi.jobs.get_jobs(date_range_min=datetime.today().strftime('%Y-%m-%d'))
        self.assertEqual(len(jobs), 3)
        jobs = user2_gi.jobs.get_jobs(history_id=history_id2)
        self.assertEqual(len(jobs), 1)
        jobs = self.gi.jobs.get_jobs(user_details=True)
        self.assertEqual(len(jobs), 4)
        self.assertEqual(len([x for x in jobs if x['history_id'] == history_id1]), 3)
        self.assertEqual(len([x for x in jobs if x['history_id'] == history_id2]), 1)

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
