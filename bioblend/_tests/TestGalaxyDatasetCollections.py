import os
import tarfile
import tempfile
from inspect import signature
from zipfile import ZipFile

from bioblend.galaxy import dataset_collections
from . import (
    GalaxyTestBase,
    test_util
)


class TestGalaxyDatasetCollections(GalaxyTestBase.GalaxyTestBase):

    def test_create_list_in_history(self):
        history_id = self.gi.histories.create_history(name="TestDSListCreate")["id"]
        dataset1_id = self._test_dataset(history_id)
        dataset2_id = self._test_dataset(history_id)
        dataset3_id = self._test_dataset(history_id)
        collection_response = self.gi.histories.create_dataset_collection(
            history_id=history_id,
            collection_description=dataset_collections.CollectionDescription(
                name="MyDatasetList",
                elements=[
                    dataset_collections.HistoryDatasetElement(name="sample1", id=dataset1_id),
                    dataset_collections.HistoryDatasetElement(name="sample2", id=dataset2_id),
                    dataset_collections.HistoryDatasetElement(name="sample3", id=dataset3_id),
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
            collection_description=dataset_collections.CollectionDescription(
                name="MyListOfPairedDatasets",
                type="list:paired",
                elements=[
                    dataset_collections.CollectionElement(
                        name="sample1",
                        type="paired",
                        elements=[
                            dataset_collections.HistoryDatasetElement(name="forward", id=dataset1_id),
                            dataset_collections.HistoryDatasetElement(name="reverse", id=dataset2_id),
                        ]
                    ),
                    dataset_collections.CollectionElement(
                        name="sample2",
                        type="paired",
                        elements=[
                            dataset_collections.HistoryDatasetElement(name="forward", id=dataset3_id),
                            dataset_collections.HistoryDatasetElement(name="reverse", id=dataset4_id),
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

    def test_show_dataset_collection(self):
        history_id = self.gi.histories.create_history(name="TestDatasetCollectionShow")["id"]
        dataset_collection1 = self._create_pair_in_history(history_id)
        dataset_collection2 = self.gi.dataset_collections.show_dataset_collection(dataset_collection1['id'])
        self.assertEqual(dataset_collection1.keys(), dataset_collection2.keys())
        for element1, element2 in zip(dataset_collection1['elements'], dataset_collection2['elements']):
            self.assertEqual(element1['id'], element2['id'])
            self.assertEqual(element1.keys(), element2.keys())
            for key in element1['object'].keys():
                self.assertIn(key, element2['object'].keys())

    @test_util.skip_unless_galaxy('release_18.01')
    def test_download_dataset_collection(self):
        history_id = self.gi.histories.create_history(name="TestDatasetCollectionDownload")["id"]
        dataset_collection_id = self._create_pair_in_history(history_id)['id']
        self.gi.dataset_collections.wait_for_dataset_collection(dataset_collection_id)

        tempdir = tempfile.mkdtemp(prefix='bioblend_test_dataset_collection_download_')
        archive_path = os.path.join(tempdir, 'dataset_collection')
        archive_type = self.gi.dataset_collections.download_dataset_collection(dataset_collection_id, file_path=archive_path)['archive_type']
        expected_contents = signature(self._test_dataset).parameters['contents'].default + '\n'
        extract_dir_path = os.path.join(tempdir, 'extracted_files')
        os.mkdir(extract_dir_path)

        if archive_type == 'zip':
            archive = ZipFile(archive_path)
        elif archive_type == 'tgz':
            archive = tarfile.open(archive_path)

        archive.extractall(extract_dir_path)
        for fname in os.listdir(extract_dir_path):
            dataset_dir_path = os.path.join(extract_dir_path, fname)
            file_path = os.path.join(dataset_dir_path, os.listdir(dataset_dir_path)[0])
            with open(file_path) as f:
                self.assertEqual(expected_contents, f.read())
        archive.close()

    def test_wait_for_dataset_collection(self):
        history_id = self.gi.histories.create_history(name="TestDatasetCollectionWait")["id"]
        dataset_collection_id = self._create_pair_in_history(history_id)['id']
        dataset_collection = self.gi.dataset_collections.wait_for_dataset_collection(dataset_collection_id)
        for element in dataset_collection['elements']:
            self.assertEqual(element['object']['state'], 'ok')

    def _create_pair_in_history(self, history_id):
        dataset1_id = self._test_dataset(history_id)
        dataset2_id = self._test_dataset(history_id)
        collection_response = self.gi.histories.create_dataset_collection(
            history_id=history_id,
            collection_description=dataset_collections.CollectionDescription(
                name="MyTestPair",
                type="paired",
                elements=[
                    dataset_collections.HistoryDatasetElement(name="forward", id=dataset1_id),
                    dataset_collections.HistoryDatasetElement(name="reverse", id=dataset2_id),
                ]
            )
        )
        return collection_response
