import shutil
import tempfile

from bioblend import ConnectionError, galaxy
from . import (
    GalaxyTestBase,
    test_util
)


class TestGalaxyDatasets(GalaxyTestBase.GalaxyTestBase):

    @classmethod
    def setUpClass(cls):
        super().setUp(cls)
        cls.history_id = cls.gi.histories.create_history(name='TestDataset')['id']
        cls.dataset_contents = "line 1\nline 2\rline 3\r\nline 4"
        cls.dataset_id = super()._test_dataset(cls, cls.history_id, contents=cls.dataset_contents)
        cls.gi.datasets.wait_for_dataset(cls.dataset_id)

    @classmethod
    def tearDownClass(cls):
        cls.gi.histories.delete_history(cls.history_id, purge=True)

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

        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, name='Pasted Entry')
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, name='Wrong Name')
        self.assertEqual(datasets, [])

    @test_util.skip_unless_galaxy('release_20.05')
    def test_get_datasets_time(self):
        dataset = self.gi.datasets.show_dataset(self.dataset_id)
        ct = dataset['create_time']
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, create_time={'gt': ct})
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, create_time={'ge': ct})
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, create_time={'lt': ct})
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, create_time={'le': ct})
        self.assertEqual(len(datasets), 1)

        ut = dataset['update_time']
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, update_time={'gt': ut})
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, update_time={'ge': ut})
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, update_time={'lt': ut})
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, update_time={'le': ut})
        self.assertEqual(len(datasets), 1)

    @test_util.skip_unless_galaxy('release_20.05')
    def test_get_datasets_extension(self):
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id)
        print(datasets)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, extension='txt')
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, extension='auto')
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
        self.gi.histories.update_dataset(history_id=self.history_id, dataset_id=self.dataset_id, visible=False)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id)
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, visible=False)
        self.assertEqual(len(datasets), 1)
        self.gi.histories.update_dataset(history_id=self.history_id, dataset_id=self.dataset_id, visible=True)

    @test_util.skip_unless_galaxy('release_20.05')
    def test_get_datasets_id(self):
        datasets = self.gi.datasets.get_datasets(id=[self.dataset_id])
        self.assertGreaterEqual(len(datasets), 1)
        with self.assertRaises(ConnectionError):
            self.gi.datasets.get_datasets(id=['nonexistent_id'])
        # This does not seem to work, returns []
        # datasets = self.gi.datasets.get_datasets(history_id=self.history_id, id=[self.dataset_id])
        # self.assertEqual(len(datasets), 1)

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
