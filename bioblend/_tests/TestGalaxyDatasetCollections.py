from bioblend.galaxy import dataset_collections as collections
from . import GalaxyTestBase


class TestGalaxyDatasetCollections(GalaxyTestBase.GalaxyTestBase):

    def test_create_list_in_history(self):
        history_id = self.gi.histories.create_history(name="TestDSListCreate")["id"]
        dataset1_id = self._test_dataset(history_id)
        dataset2_id = self._test_dataset(history_id)
        dataset3_id = self._test_dataset(history_id)
        collection_response = self.gi.histories.create_dataset_collection(
            history_id=history_id,
            collection_description=collections.CollectionDescription(
                name="MyDatasetList",
                elements=[
                    collections.HistoryDatasetElement(name="sample1", id=dataset1_id),
                    collections.HistoryDatasetElement(name="sample2", id=dataset2_id),
                    collections.HistoryDatasetElement(name="sample3", id=dataset3_id),
                ]
            )
        )
        self.assertEqual(collection_response["name"], "MyDatasetList")
        self.assertEqual(collection_response["collection_type"], "list")
        elements = collection_response["elements"]
        self.assertEqual(len(elements), 3)
        self.assertEqual(elements[0]["element_index"], 0)
        self.assertEqual(elements[0]["object"]["id"], dataset1_id)
        self.assertEqual(elements[1]["object"]["id"], dataset2_id)
        self.assertEqual(elements[2]["object"]["id"], dataset3_id)
        self.assertEqual(elements[2]["element_identifier"], "sample3")

    def test_create_list_of_paired_datasets_in_history(self):
        history_id = self.gi.histories.create_history(name="TestDSListCreate")["id"]
        dataset1_id = self._test_dataset(history_id)
        dataset2_id = self._test_dataset(history_id)
        dataset3_id = self._test_dataset(history_id)
        dataset4_id = self._test_dataset(history_id)
        collection_response = self.gi.histories.create_dataset_collection(
            history_id=history_id,
            collection_description=collections.CollectionDescription(
                name="MyListOfPairedDatasets",
                type="list:paired",
                elements=[
                    collections.CollectionElement(
                        name="sample1",
                        type="paired",
                        elements=[
                            collections.HistoryDatasetElement(name="forward", id=dataset1_id),
                            collections.HistoryDatasetElement(name="reverse", id=dataset2_id),
                        ]
                    ),
                    collections.CollectionElement(
                        name="sample2",
                        type="paired",
                        elements=[
                            collections.HistoryDatasetElement(name="forward", id=dataset3_id),
                            collections.HistoryDatasetElement(name="reverse", id=dataset4_id),
                        ]
                    ),
                ]
            )
        )
        self.assertEqual(collection_response["name"], "MyListOfPairedDatasets")
        self.assertEqual(collection_response["collection_type"], "list:paired")
        elements = collection_response["elements"]
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0]["element_index"], 0)
        created_pair1 = elements[0]["object"]
        self.assertEqual(created_pair1["collection_type"], "paired")
        self.assertEqual(len(created_pair1["elements"]), 2)
        forward_element1 = created_pair1["elements"][0]
        self.assertEqual(forward_element1["element_identifier"], "forward")
        self.assertEqual(forward_element1["element_index"], 0)
        forward_dataset1 = forward_element1["object"]
        self.assertEqual(forward_dataset1["id"], dataset1_id)

        self.assertEqual(elements[1]["element_index"], 1)
        created_pair2 = elements[1]["object"]
        self.assertEqual(created_pair2["collection_type"], "paired")
        self.assertEqual(len(created_pair2["elements"]), 2)
        reverse_element2 = created_pair2["elements"][1]
        reverse_dataset2 = reverse_element2["object"]

        self.assertEqual(reverse_element2["element_identifier"], "reverse")
        self.assertEqual(reverse_element2["element_index"], 1)
        self.assertEqual(reverse_dataset2["id"], dataset4_id)

    def test_collections_in_history_index(self):
        history_id = self.gi.histories.create_history(name="TestHistoryDSIndex")["id"]
        history_dataset_collection = self._create_pair_in_history(history_id)
        contents = self.gi.histories.show_history(history_id, contents=True)
        self.assertEqual(len(contents), 3)
        self.assertEqual(contents[2]["id"], history_dataset_collection["id"])
        self.assertEqual(contents[2]["name"], "MyTestPair")
        self.assertEqual(contents[2]["collection_type"], "paired")

    def test_show_history_dataset_collection(self):
        history_id = self.gi.histories.create_history(name="TestHistoryDSIndexShow")["id"]
        history_dataset_collection = self._create_pair_in_history(history_id)
        show_response = self.gi.histories.show_dataset_collection(history_id, history_dataset_collection["id"])
        for key in ["collection_type", "elements", "name", "deleted", "visible"]:
            self.assertIn(key, show_response)
        self.assertFalse(show_response["deleted"])
        self.assertTrue(show_response["visible"])

    def test_delete_history_dataset_collection(self):
        history_id = self.gi.histories.create_history(name="TestHistoryDSDelete")["id"]
        history_dataset_collection = self._create_pair_in_history(history_id)
        self.gi.histories.delete_dataset_collection(history_id, history_dataset_collection["id"])
        show_response = self.gi.histories.show_dataset_collection(history_id, history_dataset_collection["id"])
        self.assertTrue(show_response["deleted"])

    def test_update_history_dataset_collection(self):
        history_id = self.gi.histories.create_history(name="TestHistoryDSDelete")["id"]
        history_dataset_collection = self._create_pair_in_history(history_id)
        self.gi.histories.update_dataset_collection(history_id, history_dataset_collection["id"], visible=False)
        show_response = self.gi.histories.show_dataset_collection(history_id, history_dataset_collection["id"])
        self.assertFalse(show_response["visible"])

    def _create_pair_in_history(self, history_id):
        dataset1_id = self._test_dataset(history_id)
        dataset2_id = self._test_dataset(history_id)
        collection_response = self.gi.histories.create_dataset_collection(
            history_id=history_id,
            collection_description=collections.CollectionDescription(
                name="MyTestPair",
                type="paired",
                elements=[
                    collections.HistoryDatasetElement(name="forward", id=dataset1_id),
                    collections.HistoryDatasetElement(name="reverse", id=dataset2_id),
                ]
            )
        )
        return collection_response
