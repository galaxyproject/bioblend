import shutil
import tempfile

from bioblend import ConnectionError, galaxy
from . import (
    GalaxyTestBase,
    test_util
)


class TestGalaxyDatasets(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super().setUp()
        self.history_id = self.gi.histories.create_history(name='TestDataset')['id']
        self.dataset_contents = "line 1\nline 2\rline 3\r\nline 4"
        self.dataset_id = self._test_dataset(self.history_id, contents=self.dataset_contents)
        self.gi.datasets.wait_for_dataset(self.dataset_id)

    def tearDown(self):
        self.gi.histories.delete_history(self.history_id, purge=True)

    @test_util.skip_unless_galaxy('release_19.05')
    def test_show_nonexistent_dataset(self):
        with self.assertRaises(ConnectionError):
            self.gi.datasets.show_dataset('nonexistent_id')

    def test_show_dataset(self):
        self.gi.datasets.show_dataset(self.dataset_id)

    def test_download_dataset(self):
        with self.assertRaises(Exception) as ctx:
            self.gi.datasets.download_dataset(None)
        self.assertIsInstance(ctx.exception, (TypeError, ConnectionError))
        expected_contents = ("\n".join(self.dataset_contents.splitlines()) + "\n").encode()
        # download_dataset() with file_path=None is already tested in TestGalaxyTools.test_paste_content()
        # self._wait_and_verify_dataset(self.dataset_id, expected_contents)
        tempdir = tempfile.mkdtemp(prefix='bioblend_test_')
        try:
            downloaded_dataset = self.gi.datasets.download_dataset(
                self.dataset_id, file_path=tempdir,
                maxwait=GalaxyTestBase.BIOBLEND_TEST_JOB_TIMEOUT * 2)
            self.assertTrue(downloaded_dataset.startswith(tempdir))
            with open(downloaded_dataset, 'rb') as f:
                self.assertEqual(f.read(), expected_contents)
        finally:
            shutil.rmtree(tempdir)
        with tempfile.NamedTemporaryFile(prefix='bioblend_test_') as f:
            download_filename = self.gi.datasets.download_dataset(
                self.dataset_id, file_path=f.name, use_default_filename=False,
                maxwait=GalaxyTestBase.BIOBLEND_TEST_JOB_TIMEOUT)
            self.assertEqual(download_filename, f.name)
            f.flush()
            self.assertEqual(f.read(), expected_contents)

    @test_util.skip_unless_galaxy('release_19.05')
    def test_get_datasets(self):
        datasets = self.gi.datasets.get_datasets()
        dataset_ids = [dataset['id'] for dataset in datasets]
        self.assertIn(self.dataset_id, dataset_ids)

    @test_util.skip_unless_galaxy('release_19.05')
    def test_get_datasets_history(self):
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id)
        self.assertEqual(len(datasets), 1)

    @test_util.skip_unless_galaxy('release_19.05')
    def test_get_datasets_limit_offset(self):
        datasets = self.gi.datasets.get_datasets(limit=0)
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, offset=1)
        self.assertEqual(datasets, [])

    @test_util.skip_unless_galaxy('release_19.05')
    def test_get_datasets_name(self):
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, name='Pasted Entry')
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, name='Wrong Name')
        self.assertEqual(datasets, [])

    @test_util.skip_unless_galaxy('release_20.05')
    def test_get_datasets_time(self):
        dataset = self.gi.datasets.show_dataset(self.dataset_id)
        ct = dataset['create_time']
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, create_time_min=ct)
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, create_time_max=ct)
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, create_time_min='2100-01-01T00:00:00')
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, create_time_max='2000-01-01T00:00:00')
        self.assertEqual(datasets, [])

        ut = dataset['update_time']
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, update_time_min=ut)
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, update_time_max=ut)
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, update_time_min='2100-01-01T00:00:00')
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, update_time_max='2000-01-01T00:00:00')
        self.assertEqual(datasets, [])

    @test_util.skip_unless_galaxy('release_20.05')
    def test_get_datasets_extension(self):
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, extension='txt')
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, extension='bam')
        self.assertEqual(datasets, [])

    @test_util.skip_unless_galaxy('release_20.05')
    def test_get_datasets_state(self):
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, state='ok')
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, state='queued')
        self.assertEqual(datasets, [])
        with self.assertRaises(ConnectionError):
            self.gi.datasets.get_datasets(history_id=self.history_id, state='nonexistent_state')
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, state=['ok', 'queued'])
        self.assertEqual(len(datasets), 1)

    @test_util.skip_unless_galaxy('release_20.05')
    def test_get_datasets_visible(self):
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, visible=True)
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, visible=False)
        self.assertEqual(len(datasets), 0)

    @test_util.skip_unless_galaxy('release_19.05')
    def test_get_datasets_ordering(self):
        self.dataset_id2 = self._test_dataset(self.history_id, contents=self.dataset_contents)
        self.gi.datasets.wait_for_dataset(self.dataset_id2)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, order='create_time-dsc')
        self.assertEqual(datasets[0]['id'], self.dataset_id2)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, order='create_time-asc')
        self.assertEqual(datasets[0]['id'], self.dataset_id)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, order='hid-dsc')
        self.assertEqual(datasets[0]['id'], self.dataset_id2)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, order='hid-asc')
        self.assertEqual(datasets[0]['id'], self.dataset_id)

    @test_util.skip_unless_galaxy('release_19.05')
    def test_get_datasets_deleted(self):
        deleted_datasets = self.gi.datasets.get_datasets(history_id=self.history_id, deleted=True)
        self.assertEqual(deleted_datasets, [])
        self.gi.histories.delete_dataset(self.history_id, self.dataset_id)
        deleted_datasets = self.gi.datasets.get_datasets(history_id=self.history_id, deleted=True)
        self.assertEqual(len(deleted_datasets), 1)
        purged_datasets = self.gi.datasets.get_datasets(history_id=self.history_id, purged=True)
        self.assertEqual(purged_datasets, [])
        self.gi.histories.delete_dataset(self.history_id, self.dataset_id, purge=True)
        purged_datasets = self.gi.datasets.get_datasets(history_id=self.history_id, purged=True)
        self.assertEqual(len(purged_datasets), 1)

    @test_util.skip_unless_galaxy('release_19.05')
    def test_get_datasets_tool_id_and_tag(self):
        cat1_datasets = self.gi.datasets.get_datasets(history_id=self.history_id, tool_id='cat1')
        self.assertEqual(cat1_datasets, [])
        upload1_datasets = self.gi.datasets.get_datasets(history_id=self.history_id, tool_id='upload1')
        self.assertEqual(len(upload1_datasets), 1)
        self.gi.histories.update_dataset(self.history_id, self.dataset_id, tags=['test'])
        tagged_datasets = self.gi.datasets.get_datasets(history_id=self.history_id, tag='test')
        self.assertEqual(len(tagged_datasets), 1)

    def test_wait_for_dataset(self):
        history_id = self.gi.histories.create_history(name='TestWaitForDataset')['id']
        dataset_contents = "line 1\nline 2\rline 3\r\nline 4"
        dataset_id = self._test_dataset(history_id, contents=dataset_contents)

        dataset = self.gi.datasets.wait_for_dataset(dataset_id)
        self.assertEqual(dataset['state'], 'ok')

        self.gi.histories.delete_history(history_id, purge=True)

    @test_util.skip_unless_galaxy('release_19.05')
    def test_dataset_permissions(self):
        admin_user_id = self.gi.users.get_current_user()['id']
        user_id = self.gi.users.create_local_user('newuser3', 'newuser3@example.com', 'secret')['id']
        user_api_key = self.gi.users.create_user_apikey(user_id)
        anonymous_gi = galaxy.GalaxyInstance(url=self.gi.base_url, key=None)
        user_gi = galaxy.GalaxyInstance(url=self.gi.base_url, key=user_api_key)
        sharing_role = self.gi.roles.create_role('sharing_role', 'sharing_role', [user_id, admin_user_id])['id']

        self.gi.datasets.publish_dataset(self.dataset_id, published=False)
        with self.assertRaises(ConnectionError):
            anonymous_gi.datasets.show_dataset(self.dataset_id)
        self.gi.datasets.publish_dataset(self.dataset_id, published=True)
        # now dataset is public, i.e. accessible to anonymous users
        self.assertEqual(anonymous_gi.datasets.show_dataset(self.dataset_id)['id'], self.dataset_id)
        self.gi.datasets.publish_dataset(self.dataset_id, published=False)

        with self.assertRaises(ConnectionError):
            user_gi.datasets.show_dataset(self.dataset_id)
        self.gi.datasets.update_permissions(self.dataset_id, access_ids=[sharing_role], manage_ids=[sharing_role])
        self.assertEqual(user_gi.datasets.show_dataset(self.dataset_id)['id'], self.dataset_id)
        # anonymous access now fails because sharing is only with the shared user role
        with self.assertRaises(ConnectionError):
            anonymous_gi.datasets.show_dataset(self.dataset_id)
