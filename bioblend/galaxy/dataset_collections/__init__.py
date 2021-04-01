import logging
import os
import time
from typing import Optional

from bioblend import TimeoutException
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


__all__ = (
    "CollectionDescription",
    "CollectionElement",
    "HistoryDatasetElement",
    "HistoryDatasetCollectionElement",
    "LibraryDatasetElement",
)


class DatasetCollectionClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'dataset_collections'
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
        url: str = self._make_url(module_id=dataset_collection_id)
        return self._get(url=url, params=params)

    def download_dataset_collection(self, dataset_collection_id: str, dir_path: Optional[str] = None,
                                    use_default_dirname: bool = True, require_ok_state: bool = True,
                                    maxwait: float = 12000) -> Optional[list]:
        """
        Download a dataset collection to memory or to disk.

        When saving to memory, a list of dicts with be returned.
        When saving to disk, a directory will be created containing the dataset collection.

        If any dataset inside the collection does not have 'ok' states, a
        ``DatasetStateException`` will be raised, unless ``require_ok_state=False``.

        :type dataset_collection_id: str
        :param dataset_collection_id: Encoded dataset collection ID

        :type dir_path: str
        :param dir_path: If this argument is no empty, the dataset will be streamed to disk
          at that path (should be a directory if ``use_default_filename=True``).
          If the file_path argument is not provided, the dataset content is loaded into memory
          and returned by the method (Memory consumption may be heavy as the entire file
          will be in memory).

        :type use_default_dirname: bool
        :param use_default_dirname: If ``True``, the export
          directory will be named ``file_path/%s``,
          where ``%s`` is the dataset collection name.
          If ``False``, ``dir_path`` is assumed to
          contain the full directory path including the directory name.

        :type require_ok_state: bool
        :param require_ok_state: If ``False``, datasets will be downloaded even if not in an 'ok' state,
          issuing a ``DatasetStateWarning`` rather than raising a ``DatasetStateException``.

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the dataset state to
          become terminal. If the dataset state is not terminal within this
          time, a ``DatasetTimeoutException`` will be thrown.

        :rtype: list of str
        :return: If a ``dir_path`` argument is not provided, returns a list containing the dataset collection contents.
          Otherwise returns nothing.
        """
        dataset_collection: dict = self.gi.dataset_collections.show_dataset_collection(dataset_collection_id)

        if dir_path:
            dir_path: str = os.path.join(dir_path, dataset_collection['name'] if use_default_dirname else '')
            try:
                os.mkdir(dir_path)
            except OSError:
                log.error(f'OSError: failed to create directory ``{dir_path}``')
            else:
                log.debug(f'Successfully created dataset collection download directory at ``{dir_path}``.')

        collection_contents: list = []
        for element in dataset_collection['elements']:
            dataset: dict = element['object']
            dataset_contents: Optional[bytes] = self.gi.datasets.download_dataset(
                dataset_id=dataset['id'],
                file_path=dir_path,
                require_ok_state=require_ok_state,
                maxwait=maxwait
            )
            collection_contents.append(dataset_contents)

        if not dir_path:
            return [contents.decode('utf-8') for contents in collection_contents]

    def wait_for_dataset_collection(self, dataset_collection_id: str, maxwait: float = 12000,
                                    interval: float = 3, proportion_complete: float = 1.0,
                                    check: bool = True) -> dict:
        """
        Wait until a dataset is in a terminal state.

        :type dataset_id: str
        :param dataset_id: dataset ID

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the dataset state to
          become terminal. If the dataset state is not terminal within this
          time, a ``DatasetTimeoutException`` will be raised.

        :type interval: float
        :param interval: Time (in seconds) to wait between 2 consecutive checks.

        :type check: bool
        :param check: Whether to check if all datasets terminal states are 'ok'.

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
            count = 0
            for i, state in enumerate(states):
                if state in TERMINAL_STATES:
                    if check and state != 'ok':
                        raise Exception(f"Dataset {dataset_collection['elements']['object'][i]['id']} is in terminal state {state}")
                    count += 1
            proportion = count / len(states)
            if proportion >= proportion_complete:
                return dataset_collection
            if time_left > 0:
                log.info(f"The dataset collection {dataset_collection_id} has {count} out of {len(states)} datasets in a terminal state. Will wait {time_left} more s")
                time.sleep(min(time_left, interval))
                time_left -= interval
            else:
                raise DatasetCollectionTimeoutException(f"Less than {proportion_complete * 100}% of datasets in the dataset collection is in a terminal state after {maxwait} s")


class DatasetCollectionTimeoutException(TimeoutException):
    pass
