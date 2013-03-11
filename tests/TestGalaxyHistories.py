"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure. 

Use ``nose`` to run these unit tests.
"""
import GalaxyTestBase

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
        pass

    def test_upload_dataset_from_library(self):
        pass

    def test_download_dataset(self):
        pass

    def test_delete_history(self):
        result = self.gi.histories.delete_history(self.history['id'])
        self.assertEqual(result, 'OK')

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
