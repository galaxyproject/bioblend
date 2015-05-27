"""
"""
import os
import shutil
import tarfile
import tempfile

import GalaxyTestBase
import test_util


@test_util.skip_unless_galaxy()
class TestGalaxyHistories(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super(TestGalaxyHistories, self).setUp()
        self.default_history_name = "buildbot - automated test"
        self.history = self.gi.histories.create_history(name=self.default_history_name)

    def test_create_history(self):
        history_name = "another buildbot - automated test"
        new_history = self.gi.histories.create_history(name=history_name)
        self.assertIsNotNone(new_history['id'])
        self.assertEqual(new_history['name'], history_name)
        self.assertIsNotNone(new_history['url'])

    def test_update_history(self):
        new_name = 'buildbot - automated test renamed'
        new_annotation = 'Annotation for %s' % new_name
        new_tags = ['tag1', 'tag2']
        self.gi.histories.update_history(self.history['id'], name=new_name, annotation=new_annotation, tags=new_tags)
        updated_hist = self.gi.histories.show_history(self.history['id'])
        self.assertEqual(self.history['id'], updated_hist['id'])
        self.assertEqual(updated_hist['name'], new_name)
        self.assertEqual(updated_hist['annotation'], new_annotation)
        self.assertEqual(updated_hist['tags'], new_tags)

    def test_get_histories(self):
        # Make sure there's at least one value - the one we created
        full_history = self.gi.histories.get_histories()
        self.assertIsNotNone(full_history)

        # Check whether name is correct, when searched by id
        new_history = self.gi.histories.get_histories(history_id=self.history['id'])
        self.assertTrue(any(d['name'] == self.default_history_name for d in new_history))

        # Check whether id is present, when searched by name
        new_history = self.gi.histories.get_histories(name=self.default_history_name)
        self.assertTrue(any(d['id'] == self.history['id'] for d in new_history))

        # TODO: check whether deleted history is returned correctly
        # At the moment, get_histories() returns only not-deleted histories
        # and get_histories(deleted=True) returns only deleted histories,
        # so they are not comparable.
        # In the future, according to https://trello.com/c/MoilsmVv/1673-api-incoherent-and-buggy-indexing-of-deleted-entities ,
        # get_histories() will return both not-deleted and deleted histories
        # and we can uncomment the following test.
        # deleted_history = self.gi.histories.get_histories(deleted=True)
        # self.assertGreaterEqual(len(full_history), len(deleted_history))

    def test_show_history(self):
        history_data = self.gi.histories.show_history(self.history['id'])
        self.assertEqual(self.history['id'], history_data['id'])
        self.assertEqual(self.history['name'], history_data['name'])
        self.assertEqual('new', history_data['state'])

    @test_util.skip_unless_galaxy('release_14.04')
    def test_create_history_tag(self):
        new_tag = 'tag1'
        self.gi.histories.create_history_tag(self.history['id'], new_tag)
        updated_hist = self.gi.histories.show_history(self.history['id'])
        self.assertEqual(self.history['id'], updated_hist['id'])
        self.assertIn(new_tag, updated_hist['tags'])

    def test_show_dataset(self):
        history_id = self.history["id"]
        dataset1_id = self._test_dataset(history_id)
        dataset = self.gi.histories.show_dataset(history_id, dataset1_id)
        for key in ["name", "hid", "id", "deleted", "history_id", "visible"]:
            self.assertIn(key, dataset)
        self.assertEqual(dataset["history_id"], history_id)
        self.assertEqual(dataset["hid"], 1)
        self.assertEqual(dataset["id"], dataset1_id)
        self.assertEqual(dataset["deleted"], False)
        self.assertEqual(dataset["visible"], True)

    def test_show_dataset_provenance(self):
        history_id = self.history["id"]
        dataset1_id = self._test_dataset(history_id)
        prov = self.gi.histories.show_dataset_provenance(history_id, dataset1_id)
        # 'job_id' key was added in Galaxy release_14.06
        for key in ["id", "stdout", "stderr", "parameters", "tool_id"]:
            self.assertIn(key, prov)

    def test_delete_dataset(self):
        history_id = self.history["id"]
        dataset1_id = self._test_dataset(history_id)
        self.gi.histories.delete_dataset(history_id, dataset1_id)
        dataset = self.gi.histories.show_dataset(history_id, dataset1_id)
        self.assertTrue(dataset["deleted"])

    def test_update_dataset(self):
        history_id = self.history["id"]
        dataset1_id = self._test_dataset(history_id)
        self.gi.histories.update_dataset(history_id, dataset1_id, visible=False)
        dataset = self.gi.histories.show_dataset(history_id, dataset1_id)
        self.assertFalse(dataset["visible"])

    def test_upload_dataset_from_library(self):
        pass

    def test_download_dataset(self):
        history_id = self.history["id"]
        dataset1_id = self._test_dataset(history_id)
        self._wait_and_verify_dataset(history_id, dataset1_id, b"1\t2\t3\n")

    def test_delete_history(self):
        result = self.gi.histories.delete_history(self.history['id'])
        self.assertTrue(result['deleted'])

        full_history = self.gi.histories.get_histories()
        self.assertTrue(not any(d['id'] == self.history['id'] for d in full_history))

    def test_undelete_history(self):
        self.gi.histories.delete_history(self.history['id'])
        self.gi.histories.undelete_history(self.history['id'])
        full_history = self.gi.histories.get_histories()
        self.assertTrue(any(d['id'] == self.history['id'] for d in full_history))

    def test_get_status(self):
        state = self.gi.histories.get_status(self.history['id'])
        self.assertEqual('new', state['state'])

    def test_get_most_recently_used_history(self):
        most_recently_used_history = self.gi.histories.get_most_recently_used_history()
        # if the user has been created via the API, it does not have
        # a session, therefore no history
        if most_recently_used_history is not None:
            self.assertIsNotNone(most_recently_used_history['id'])
            self.assertIsNotNone(most_recently_used_history['name'])
            self.assertIsNotNone(most_recently_used_history['state'])

    def test_download_history(self):
        jeha_id = self.gi.histories.export_history(
            self.history['id'], wait=True
        )
        self.assertTrue(jeha_id)
        tempdir = tempfile.mkdtemp(prefix='bioblend_test_')
        temp_fn = os.path.join(tempdir, 'export.tar.gz')
        try:
            with open(temp_fn, 'wb') as fo:
                self.gi.histories.download_history(self.history['id'], jeha_id,
                                                   fo)
            self.assertTrue(tarfile.is_tarfile(temp_fn))
        finally:
            shutil.rmtree(tempdir)

    def tearDown(self):
        self.gi.histories.delete_history(self.history['id'], purge=True)
