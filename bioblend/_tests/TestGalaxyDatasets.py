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
        self.history_id = self.gi.histories.create_history(name='TestShowDataset')['id']
        self.dataset_contents = "line 1\nline 2\rline 3\r\nline 4"
        self.dataset_id = self._test_dataset(self.history_id, contents=self.dataset_contents)

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
        datasets = self.gi.datasets.get_datasets(limit=0)
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id)
        self.assertEqual(len(datasets), 1)

    def test_wait_for_dataset(self):
        dataset = self.gi.datasets.wait_for_dataset(self.dataset_id)
        self.assertEqual(dataset['state'], 'ok')

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
