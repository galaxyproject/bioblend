"""
Contains possible interactions with the Galaxy Datasets
"""
from blend.galaxy.client import Client


class DatasetClient(Client):
    def __init__(self, galaxy_instance):
        self.module = 'datasets'
        super(DatasetClient, self).__init__(galaxy_instance)

    def show_dataset(self, dataset_id, deleted=False):
        """
        Display information about and/or content of a dataset. This can be a
        history or a library dataset.
        """
        return Client._get(self, id=dataset_id, deleted=deleted)
