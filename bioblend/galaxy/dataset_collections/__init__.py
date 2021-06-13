import logging
import time

from bioblend import (
    CHUNK_SIZE,
    TimeoutException,
)
from bioblend.galaxy.client import Client
from bioblend.galaxy.datasets import TERMINAL_STATES

log = logging.getLogger(__name__)


class HasElements:

    def __init__(self, name, type="list", elements=None):
        self.name = name
        self.type = type
        if isinstance(elements, dict):
            self.elements = [dict(name=key, id=value, src="hda") for key, value in elements.values()]
        elif elements:
            self.elements = elements

    def add(self, element):
        self.elements.append(element)
        return self


class CollectionDescription(HasElements):

    def to_dict(self):
        return dict(
            name=self.name,
            collection_type=self.type,
            element_identifiers=[e.to_dict() for e in self.elements]
        )


class CollectionElement(HasElements):

    def to_dict(self):
        return dict(
            src="new_collection",
            name=self.name,
            collection_type=self.type,
            element_identifiers=[e.to_dict() for e in self.elements]
        )


class SimpleElement:

    def __init__(self, value):
        self.value = value

    def to_dict(self):
        return self.value


class HistoryDatasetElement(SimpleElement):

    def __init__(self, name, id):
        super().__init__(dict(
            name=name,
            src="hda",
            id=id,
        ))


class HistoryDatasetCollectionElement(SimpleElement):

    def __init__(self, name, id):
        super().__init__(dict(
            name=name,
            src="hdca",
            id=id,
        ))


class LibraryDatasetElement(SimpleElement):

    def __init__(self, name, id):
        super().__init__(dict(
            name=name,
            src="ldda",
            id=id,
        ))


class DatasetCollectionClient(Client):
    module = 'dataset_collections'

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def show_dataset_collection(self, dataset_collection_id: str,
                                instance_type: str = 'history') -> dict:
        """
        Get details of a given dataset collection of the current user

        :type dataset_collection_id: str
        :param dataset_collection_id: dataset collection ID

        :type instance_type: str
        :param instance_type: instance type of the collection - 'history' or 'library'

        :rtype: dict
        :return: element view of the dataset collection
        """
        params = {
            'id': dataset_collection_id,
            'instance_type': instance_type,
        }
        url = self._make_url(module_id=dataset_collection_id)
        return self._get(url=url, params=params)

    def download_dataset_collection(self, dataset_collection_id: str, file_path: str) -> dict:
        """
        Download a history dataset collection as an archive.

        :type dataset_collection_id: str
        :param dataset_collection_id: Encoded dataset collection ID

        :type file_path: str
        :param file_path: The path to which the archive will be downloaded

        :rtype: dict
        :return: Information about the downloaded archive.

        .. note::
          This method downloads a ``zip`` archive for Galaxy 21.01 and later.
          For earlier versions of Galaxy this method downloads a ``tgz`` archive.
          This method is only supported by Galaxy 18.01 or later.
        """
        url = self._make_url(module_id=dataset_collection_id) + '/download'
        r = self.gi.make_get_request(url, stream=True)
        r.raise_for_status()

        archive_type = 'zip' if self.gi.config.get_version()['version_major'] >= '21.01' else 'tgz'

        with open(file_path, 'wb') as fp:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    fp.write(chunk)

        return {
            'file_path': file_path,
            'archive_type': archive_type
        }

    def wait_for_dataset_collection(self, dataset_collection_id: str, maxwait: float = 12000,
                                    interval: float = 3, proportion_complete: float = 1.0,
                                    check: bool = True) -> dict:
        """
        Wait until all or a specified proportion of elements of a dataset
        collection are in a terminal state.

        :type dataset_collection_id: str
        :param dataset_id: dataset collection ID

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the dataset
          states in the dataset collection to become terminal. If not
          all datasets are in a terminal state within this time, a
          ``DatasetCollectionTimeoutException`` will be raised.

        :type interval: float
        :param interval: Time (in seconds) to wait between two consecutive checks.

        :type proportion_complete: float
        :param proportion_complete: Proportion of elements in this collection
          that have to be in a terminal state for this method to return. Must
          be a number between 0 and 1. For example: if the dataset collection
          contains 2 elements, and proportion_complete=0.5 is specified, then
          wait_for_dataset_collection will return as soon as 1 of the 2
          datasets is in a terminal state. Default is 1, i.e. all elements must
          complete.

        :type check: bool
        :param check: Whether to check if all the terminal states of datasets
          in the dataset collection are 'ok'. This will raise an Exception if
          a dataset is in a terminal state other than 'ok'.

        :rtype: dict
        :return: Details of the given dataset collection.
        """
        assert maxwait >= 0
        assert interval > 0
        assert 0 <= proportion_complete <= 1

        time_left = maxwait
        while True:
            dataset_collection = self.gi.dataset_collections.show_dataset_collection(dataset_collection_id)
            states = [elem['object']['state'] for elem in dataset_collection['elements']]
            terminal_states = [state for state in states if state in TERMINAL_STATES]
            if set(terminal_states) not in [{'ok'}, set()]:
                raise Exception(f"Dataset collection {dataset_collection_id} contains elements in the "
                                f"following non-ok terminal states: {', '.join(set(terminal_states) - {'ok'})}")
            proportion = len(terminal_states) / len(states)
            if proportion >= proportion_complete:
                return dataset_collection
            if time_left > 0:
                log.info(f"The dataset collection {dataset_collection_id} has {len(terminal_states)} out of {len(states)} datasets in a terminal state. Will wait {time_left} more s")
                time.sleep(min(time_left, interval))
                time_left -= interval
            else:
                raise DatasetCollectionTimeoutException(f"Less than {proportion_complete * 100}% of datasets in the dataset collection is in a terminal state after {maxwait} s")


class DatasetCollectionTimeoutException(TimeoutException):
    pass


__all__ = (
    "CollectionDescription",
    "CollectionElement",
    "DatasetCollectionClient",
    "HistoryDatasetElement",
    "HistoryDatasetCollectionElement",
    "LibraryDatasetElement",
)
