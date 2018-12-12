import shutil
import tempfile

import six

from . import GalaxyTestBase


class TestGalaxyDatasets(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super(TestGalaxyDatasets, self).setUp()
        self.history_id = self.gi.histories.create_history(name='TestShowDataset')['id']
        self.dataset_contents = "line 1\nline 2\rline 3\r\nline 4"
        self.dataset_id = self._test_dataset(self.history_id, contents=self.dataset_contents)

    def tearDown(self):
        self.gi.histories.delete_history(self.history_id, purge=True)

    def test_show_dataset(self):
        with self.assertRaises(Exception):
            self.gi.datasets.show_dataset(None)
        self.gi.datasets.show_dataset(self.dataset_id)

    def test_download_dataset(self):
        with self.assertRaises(Exception):
            self.gi.datasets.download_dataset(None)
        expected_contents = six.b("\n".join(self.dataset_contents.splitlines()) + "\n")
        # download_dataset() with file_path=None is already tested in TestGalaxyTools.test_paste_content()
        # self._wait_and_verify_dataset(self.dataset_id, expected_contents)
        tempdir = tempfile.mkdtemp(prefix='bioblend_test_')
        try:
            downloaded_dataset = self.gi.datasets.download_dataset(
                self.dataset_id, file_path=tempdir,
                maxwait=GalaxyTestBase.BIOBLEND_TEST_JOB_TIMEOUT)
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

    def test_show_stderr(self):
        stderr = self.gi.datasets.show_stderr(self.dataset_id)
        self.assertIsNotNone(stderr)

    def test_show_stdout(self):
        stdout = self.gi.datasets.show_stdout(self.dataset_id)
        self.assertIsNotNone(stdout)
