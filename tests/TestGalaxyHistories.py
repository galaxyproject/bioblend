"""
"""
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

        # check whether deleted history is returned correctly
        deleted_history = self.gi.histories.get_histories(deleted=True)
        self.assertGreaterEqual(len(deleted_history), len(full_history))

    def test_show_history(self):
        history_data = self.gi.histories.show_history(self.history['id'])
        self.assertEqual(self.history['id'], history_data['id'])
        self.assertEqual(self.history['name'], history_data['name'])
        self.assertEqual('new', history_data['state'])

    def test_show_dataset(self):
        history_id = self.history["id"]
        dataset1_id = self._test_dataset(history_id)
        dataset = self.gi.histories.show_dataset(history_id, dataset1_id)
        for key in ["name", "hid", "id", "deleted", "history_id", "visible"]:
            assert key in dataset
        self.assertEqual(dataset["history_id"], history_id)
        self.assertEqual(dataset["hid"], 1)
        self.assertEqual(dataset["id"], dataset1_id)
        self.assertEqual(dataset["deleted"], False)
        self.assertEqual(dataset["visible"], True)

    def test_show_dataset_provenance(self):
        history_id = self.history["id"]
        dataset1_id = self._test_dataset(history_id)
        prov = self.gi.histories.show_dataset_provenance(history_id, dataset1_id)
        for key in ["job_id", "id", "stdout", "stderr", "parameters", "tool_id"]:
            assert key in prov

    def test_delete_dataset(self):
        history_id = self.history["id"]
        dataset1_id = self._test_dataset(history_id)
        self.gi.histories.delete_dataset(history_id, dataset1_id)
        dataset = self.gi.histories.show_dataset(history_id, dataset1_id)
        self.assertEqual(dataset["deleted"], True)

    def test_update_dataset(self):
        history_id = self.history["id"]
        dataset1_id = self._test_dataset(history_id)
        self.gi.histories.update_dataset(history_id, dataset1_id, visible=False)
        dataset = self.gi.histories.show_dataset(history_id, dataset1_id)
        self.assertEqual(dataset["visible"], False)

    def test_upload_dataset_from_library(self):
        pass

    def test_download_dataset(self):
        pass

    def test_delete_history(self):
        result = self.gi.histories.delete_history(self.history['id'])
        self.assertTrue(result['deleted'])

        full_history = self.gi.histories.get_histories()
        self.assertTrue(not any(d['id'] == self.history['id'] for d in full_history))

    def test_undelete_history(self):
        result = self.gi.histories.delete_history(self.history['id'])
        result = self.gi.histories.undelete_history(self.history['id'])
        full_history = self.gi.histories.get_histories()
        self.assertTrue(any(d['id'] == self.history['id'] for d in full_history))

    def test_get_status(self):
        state = self.gi.histories.get_status(self.history['id'])
        self.assertEqual('new', state['state'])

    def test_get_current_history(self):
        current_history = self.gi.histories.get_current_history()
        self.assertIsNotNone(current_history['id'])
        self.assertIsNotNone(current_history['name'])
        self.assertIsNotNone(current_history['state'])

    def tearDown(self):
        self.history = self.gi.histories.delete_history(self.history['id'], purge=True)
