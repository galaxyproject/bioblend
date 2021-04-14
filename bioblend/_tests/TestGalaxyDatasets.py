import shutil
import tempfile

from bioblend import ConnectionError
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
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, offset=1)
        self.assertEqual(datasets, [])

        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, name='Pasted Entry')
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, name='Wrong Name')
        self.assertEqual(datasets, [])

        dataset = self.gi.datasets.wait_for_dataset(self.dataset_id)
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

        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, extension='txt')
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, extension='auto')
        self.assertEqual(datasets, [])

        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, state='ok')
        self.assertEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, state='queued')
        self.assertEqual(datasets, [])
        with self.assertRaises(ConnectionError):
            datasets = self.gi.datasets.get_datasets(history_id=self.history_id, state='invalid state name')
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, state=['ok', 'queued'])
        self.assertEqual(len(datasets), 1)

        self.gi.histories.update_dataset(history_id=self.history_id, dataset_id=self.dataset_id, visible=False)
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id)
        self.assertEqual(datasets, [])
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, visible=False)
        self.assertEqual(len(datasets), 1)
        self.gi.histories.update_dataset(history_id=self.history_id, dataset_id=self.dataset_id, visible=True)

        datasets = self.gi.datasets.get_datasets(id=[self.dataset_id])
        self.assertGreaterEqual(len(datasets), 1)
        datasets = self.gi.datasets.get_datasets(id=['invalid dataset id'])
        self.assertEqual(datasets, [])
        # This does not seem to work, returns []
        # datasets = self.gi.datasets.get_datasets(history_id=self.history_id, id=[self.dataset_id])
        # self.assertEqual(len(datasets), 1)

    def test_wait_for_dataset(self):
        dataset = self.gi.datasets.wait_for_dataset(self.dataset_id)
        self.assertEqual(dataset['state'], 'ok')
