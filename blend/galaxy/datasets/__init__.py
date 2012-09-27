"""
Contains possible interactions with the Galaxy Datasets
"""
from blend.galaxy.client import Client
import shutil
import urllib2
import os

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
    
    def download_dataset(self, dataset_id, file_path=None):
        """
        Downloads the dataset identified by 'id'.
        If the file_path argument is provided, the dataset will be streamed to disk at that path, and the
        file name will be the dataset name.
        If the file_path argument is not provided, the dataset content is loaded into memory
        and returned by the method. Memory consumption may be heavy as the entire file will be in memory.
        
        If the dataset state is invalid, a DatasetStateException will be thrown.
        """
        dataset = self.show_dataset(dataset_id)
#        if not dataset['state'] == 'ok':
#            raise DatasetStateException(dataset)
        
        # Append the dataset_id to the base history contents URL
        url = '/'.join([self.gi.base_url, dataset['download_url']])
        if file_path is None:
            r = self.gi.make_get_request(url)        
            return r.content
        else:
            req = urllib2.urlopen(url)
            file = os.path.join(file_path, dataset['name'])
            with open(file, 'wb') as fp:
                shutil.copyfileobj(req, fp)

class DatasetStateException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)