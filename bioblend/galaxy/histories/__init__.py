"""
Contains possible interactions with the Galaxy Histories
"""
import logging
import os
import re
import sys
import time

import six

import bioblend
from bioblend import ConnectionError
from bioblend.galaxy.client import Client

log = logging.getLogger(__name__)


class HistoryClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'histories'
        super(HistoryClient, self).__init__(galaxy_instance)

    def create_history(self, name=None):
        """
        Create a new history, optionally setting the ``name``.

        :type name: str
        :param name: Optional name for new history

        :rtype: dict
        :return: Dictionary containing information about newly created history
        """
        payload = {}
        if name is not None:
            payload['name'] = name
        return self._post(payload)

    def get_histories(self, history_id=None, name=None, deleted=False):
        """
        Get all histories or filter the specific one(s) via the provided
        ``name`` or ``history_id``. Provide only one argument, ``name`` or
        ``history_id``, but not both.

        If ``deleted`` is set to ``True``, return histories that have been
        deleted.

        :type history_id: str
        :param history_id: Encoded history ID to filter on

        :type name: str
        :param name: Name of history to filter on

        :type deleted: bool
        :param deleted: whether to filter for the deleted histories (``True``)
          or for the non-deleted ones (``False``)

        :rtype: list
        :return: Return a list of history element dicts. If more than one
                 history matches the given ``name``, return the list of all the
                 histories with the given name
        """
        if history_id is not None and name is not None:
            raise ValueError('Provide only one argument between name or history_id, but not both')
        histories = self._get(deleted=deleted)
        if history_id is not None:
            history = next((_ for _ in histories if _['id'] == history_id), None)
            histories = [history] if history is not None else []
        elif name is not None:
            histories = [_ for _ in histories if _['name'] == name]
        return histories

    def show_history(self, history_id, contents=False, deleted=None, visible=None, details=None, types=None):
        """
        Get details of a given history. By default, just get the history meta
        information.

        :type history_id: str
        :param history_id: Encoded history ID to filter on

        :type contents: bool
        :param contents: When ``True``, instead of the history details, return
          the list of datasets in the given history.

        :type deleted: bool or None
        :param deleted: When ``contents=True``, whether to filter for the
          deleted datasets (``True``) or for the non-deleted ones (``False``).
          If not set, no filtering is applied.

        :type visible: bool or None
        :param visible: When ``contents=True``, whether to filter for the
          visible datasets (``True``) or for the hidden ones (``False``). If not
          set, no filtering is applied.

        :type details: str
        :param details: When ``contents=True``, include dataset details. Set to
          'all' for the most information.

        :type types: list
        :param types: When ``contents=True``, filter for history content types.
          If set to ``['dataset']``, return only datasets. If set to
          ``['dataset_collection']``,  return only dataset collections. If not
          set, no filtering is applied.

        :rtype: dict
        :return: details of the given history
        """
        params = {}
        if contents:
            if details:
                params['details'] = details
            if deleted is not None:
                params['deleted'] = deleted
            if visible is not None:
                params['visible'] = visible
            if types is not None:
                params['types'] = types
        return self._get(id=history_id, contents=contents, params=params)

    def delete_dataset(self, history_id, dataset_id, purge=False):
        """
        Mark corresponding dataset as deleted.

        :type history_id: str
        :param history_id: Encoded history ID

        :type dataset_id: str
        :param dataset_id: Encoded dataset ID

        :type purge: bool
        :param purge: if ``True``, also purge (permanently delete) the dataset

        :rtype: None
        :return: None
        .. note::
            For the purge option to work, the Galaxy instance must have the
            ``allow_user_dataset_purge`` option set to ``true`` in the
            ``config/galaxy.yml`` configuration file.

        .. warning::
            If you purge a dataset which has not been previously deleted,
            Galaxy from release_15.03 to release_17.01 does not set the
            ``deleted`` attribute of the dataset to ``True``, see
            https://github.com/galaxyproject/galaxy/issues/3548
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        payload = {}
        if purge is True:
            payload['purge'] = purge
        self._delete(payload=payload, url=url)

    def delete_dataset_collection(self, history_id, dataset_collection_id):
        """
        Mark corresponding dataset collection as deleted.

        :type history_id: str
        :param history_id: Encoded history ID

        :type dataset_collection_id: str
        :param dataset_collection_id: Encoded dataset collection ID

        :rtype: None
        :return: None
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, "dataset_collections", dataset_collection_id])
        self._delete(url=url)

    def show_dataset(self, history_id, dataset_id):
        """
        Get details about a given history dataset.

        :type history_id: str
        :param history_id: Encoded history ID

        :type dataset_id: str
        :param dataset_id: Encoded dataset ID

        :rtype: dict
        :return: Information about the dataset
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        return self._get(url=url)

    def show_dataset_collection(self, history_id, dataset_collection_id):
        """
        Get details about a given history dataset collection.

        :type history_id: str
        :param history_id: Encoded history ID

        :type dataset_collection_id: str
        :param dataset_collection_id: Encoded dataset collection ID

        :rtype: dict
        :return: Information about the dataset collection
        """
        url = self.gi._make_url(self, history_id, contents=True)
        url = '/'.join([url, "dataset_collections", dataset_collection_id])
        return self._get(url=url)

    def show_matching_datasets(self, history_id, name_filter=None):
        """
        Get dataset details for matching datasets within a history.

        :type history_id: str
        :param history_id: Encoded history ID

        :type name_filter: str
        :param name_filter: Only datasets whose name matches the
                            ``name_filter`` regular expression will be
                            returned; use plain strings for exact matches and
                            None to match all datasets in the history

        :rtype: list
        :return: List of dictionaries
        """
        if isinstance(name_filter, six.string_types):
            name_filter = re.compile(name_filter + '$')
        return [self.show_dataset(history_id, h['id'])
                for h in self.show_history(history_id, contents=True)
                if name_filter is None or name_filter.match(h['name'])]

    def show_dataset_provenance(self, history_id, dataset_id, follow=False):
        """
        Get details related to how dataset was created (``id``, ``job_id``,
        ``tool_id``, ``stdout``, ``stderr``, ``parameters``, ``inputs``,
        etc...).

        :type history_id: str
        :param history_id: Encoded history ID

        :type dataset_id: str
        :param dataset_id: Encoded dataset ID

        :type follow: bool
        :param follow: If ``True``, recursively fetch dataset provenance
          information for all inputs and their inputs, etc.

        :rtype: dict
        :return: Dataset provenance information
          For example::

            {
                "tool_id": "toolshed.g2.bx.psu.edu/repos/ziru-zhou/macs2/modencode_peakcalling_macs2/2.0.10.2",
                "job_id": "5471ba76f274f929",
                "parameters": {
                    "input_chipseq_file1": {
                        "id": "6f0a311a444290f2",
                        "uuid": null
                    },
                    "dbkey": "\"mm9\"",
                    "experiment_name": "\"H3K4me3_TAC_MACS2\"",
                    "input_control_file1": {
                        "id": "c21816a91f5dc24e",
                        "uuid": null
                    },
                    "major_command": "{\"gsize\": \"2716965481.0\", \"bdg\": \"False\", \"__current_case__\": 0, \"advanced_options\": {\"advanced_options_selector\": \"off\", \"__current_case__\": 1}, \"input_chipseq_file1\": 104715, \"xls_to_interval\": \"False\", \"major_command_selector\": \"callpeak\", \"input_control_file1\": 104721, \"pq_options\":
            {\"pq_options_selector\": \"qvalue\", \"qvalue\": \"0.05\", \"__current_case__\": 1}, \"bw\": \"300\", \"nomodel_type\": {\"nomodel_type_selector\": \"create_model\", \"__current_case__\": 1}}",
                    "chromInfo": "\"/usr/local/galaxy/galaxy-dist/tool-data/shared/ucsc/chrom/mm9.len\""
                },
                "stdout": "",
                "stderr": "",
                "id": "6fbd9b2274c62ebe",
                "uuid": null
            }
        """
        url = self.gi._make_url(self, history_id, contents=True)
        url = '/'.join([url, dataset_id, "provenance"])
        return self._get(url=url)

    def update_history(self, history_id, **kwds):
        """
        Update history metadata information. Some of the attributes that can be
        modified are documented below.

        :type history_id: str
        :param history_id: Encoded history ID

        :type name: str
        :param name: Replace history name with the given string

        :type annotation: str
        :param annotation: Replace history annotation with given string

        :type deleted: bool
        :param deleted: Mark or unmark history as deleted

        :type purged: bool
        :param purged: If ``True``, mark history as purged (permanently deleted).
            Ignored on Galaxy release_15.01 and earlier

        :type published: bool
        :param published: Mark or unmark history as published

        :type importable: bool
        :param importable: Mark or unmark history as importable

        :type tags: list
        :param tags: Replace history tags with the given list

        :rtype: dict
        :return: details of the updated history (for Galaxy release_15.01 and
            earlier only the updated attributes)

        .. warning::
            The return value was changed in BioBlend v0.8.0, previously it was
            the status code (type int).
        """
        return self._put(payload=kwds, id=history_id)

    def update_dataset(self, history_id, dataset_id, **kwds):
        """
        Update history dataset metadata. Some of the attributes that can be
        modified are documented below.

        :type history_id: str
        :param history_id: Encoded history ID

        :type dataset_id: str
        :param dataset_id: Id of the dataset

        :type name: str
        :param name: Replace history dataset name with the given string

        :type genome_build: str
        :param genome_build: Replace history dataset genome build (dbkey)

        :type annotation: str
        :param annotation: Replace history dataset annotation with given string

        :type deleted: bool
        :param deleted: Mark or unmark history dataset as deleted

        :type visible: bool
        :param visible: Mark or unmark history dataset as visible

        :rtype: dict
        :return: details of the updated dataset (for Galaxy release_15.01 and
            earlier only the updated attributes)

        .. warning::
            The return value was changed in BioBlend v0.8.0, previously it was
            the status code (type int).
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        return self._put(payload=kwds, url=url)

    def update_dataset_collection(self, history_id, dataset_collection_id, **kwds):
        """
        Update history dataset collection metadata. Some of the attributes that
        can be modified are documented below.

        :type history_id: str
        :param history_id: Encoded history ID

        :type dataset_collection_id: str
        :param dataset_collection_id: Encoded dataset_collection ID

        :type name: str
        :param name: Replace history dataset collection name with the given
          string

        :type deleted: bool
        :param deleted: Mark or unmark history dataset collection as deleted

        :type visible: bool
        :param visible: Mark or unmark history dataset collection as visible

        :rtype: dict
        :return: the updated dataset collection attributes

        .. warning::
            The return value was changed in BioBlend v0.8.0, previously it was
            the status code (type int).
        """
        url = self.gi._make_url(self, history_id, contents=True)
        url = '/'.join([url, "dataset_collections", dataset_collection_id])
        return self._put(payload=kwds, url=url)

    def create_history_tag(self, history_id, tag):
        """
        Create history tag

        :type history_id: str
        :param history_id: Encoded history ID

        :type tag: str
        :param tag: Add tag to history

        :rtype: dict
        :return: A dictionary with information regarding the tag.
          For example::

            {'id': 'f792763bee8d277a',
             'model_class': 'HistoryTagAssociation',
             'user_tname': 'NGS_PE_RUN',
             'user_value': None}
        """

        # empty payload since we are adding the new tag using the url
        payload = {}

        # creating the url
        url = self.url
        url = '/'.join([url, history_id, 'tags', tag])

        return self._post(payload, url=url)

    def upload_dataset_from_library(self, history_id, lib_dataset_id):
        """
        Upload a dataset into the history from a library. Requires the
        library dataset ID, which can be obtained from the library
        contents.

        :type history_id: str
        :param history_id: Encoded history ID

        :type lib_dataset_id: str
        :param lib_dataset_id: Encoded library dataset ID

        :rtype: dict
        :return: Information about the newly created HDA
        """
        payload = {
            'content': lib_dataset_id,
            'source': 'library',
            'from_ld_id': lib_dataset_id,  # compatibility with old API
        }
        return self._post(payload, id=history_id, contents=True)

    def create_dataset_collection(self, history_id, collection_description):
        """
        Create a new dataset collection

        :type history_id: str
        :param history_id: Encoded history ID

        :type collection_description: bioblend.galaxy.dataset_collections.CollectionDescription
        :param collection_description: a description of the dataset collection
          For example::

            {'collection_type': 'list',
             'element_identifiers': [{'id': 'f792763bee8d277a',
                                      'name': 'element 1',
                                      'src': 'hda'},
                                     {'id': 'f792763bee8d277a',
                                      'name': 'element 2',
                                      'src': 'hda'}],
             'name': 'My collection list'}

        :rtype: dict
        :return: Information about the new HDCA
        """
        try:
            collection_description = collection_description.to_dict()
        except AttributeError:
            pass
        payload = dict(
            name=collection_description["name"],
            type="dataset_collection",
            collection_type=collection_description["collection_type"],
            element_identifiers=collection_description["element_identifiers"],
        )
        return self._post(payload, id=history_id, contents=True)

    def download_dataset(self, history_id, dataset_id, file_path,
                         use_default_filename=True):
        """
        .. deprecated:: 0.8.0
           Use :meth:`~bioblend.galaxy.datasets.DatasetClient.download_dataset`
           instead.
        """
        meta = self.show_dataset(history_id, dataset_id)
        if use_default_filename:
            file_local_path = os.path.join(file_path, meta['name'])
        else:
            file_local_path = file_path
        return self.gi.datasets.download_dataset(dataset_id,
                                                 file_path=file_local_path,
                                                 use_default_filename=False)

    def delete_history(self, history_id, purge=False):
        """
        Delete a history.

        :type history_id: str
        :param history_id: Encoded history ID

        :type purge: bool
        :param purge: if ``True``, also purge (permanently delete) the history

        :rtype: dict
        :return: An error object if an error occurred or a dictionary
                 containing: ``id`` (the encoded id of the history), ``deleted`` (if the
                 history was marked as deleted), ``purged`` (if the history was
                 purged).

        .. note::
          For the purge option to work, the Galaxy instance must have the
          ``allow_user_dataset_purge`` option set to ``true`` in the
          ``config/galaxy.yml`` configuration file.
        """
        payload = {}
        if purge is True:
            payload['purge'] = purge
        return self._delete(payload=payload, id=history_id)

    def undelete_history(self, history_id):
        """
        Undelete a history

        :type history_id: str
        :param history_id: Encoded history ID

        :rtype: str
        :return: 'OK' if it was deleted
        """
        url = self.gi._make_url(self, history_id, deleted=True)
        # Append the 'undelete' action to the history URL
        url = '/'.join([url, 'undelete'])
        return self._post(payload={}, url=url)

    def get_status(self, history_id):
        """
        Returns the state of this history

        :type history_id: str
        :param history_id: Encoded history ID

        :rtype: dict
        :return: A dict documenting the current state of the history. Has the following keys:
            'state' = This is the current state of the history, such as ok, error, new etc.
            'state_details' = Contains individual statistics for various dataset states.
            'percent_complete' = The overall number of datasets processed to completion.
        """
        state = {}
        history = self.show_history(history_id)
        state['state'] = history['state']
        if history.get('state_details') is not None:
            state['state_details'] = history['state_details']
            total_complete = sum(six.itervalues(history['state_details']))
            if total_complete > 0:
                state['percent_complete'] = 100 * history['state_details']['ok'] / total_complete
            else:
                state['percent_complete'] = 0
        return state

    def get_current_history(self):
        """
        .. deprecated:: 0.5.2
           Use :meth:`get_most_recently_used_history` instead.
        """
        return self.get_most_recently_used_history()

    def get_most_recently_used_history(self):
        """
        Returns the current user's most recently used history (not deleted).

        :rtype: dict
        :return: History representation
        """
        url = self.gi._make_url(self, None)
        url = '/'.join([url, 'most_recently_used'])
        return self._get(url=url)

    def export_history(self, history_id, gzip=True, include_hidden=False,
                       include_deleted=False, wait=False, maxwait=None):
        """
        Start a job to create an export archive for the given history.

        :type history_id: str
        :param history_id: history ID

        :type gzip: bool
        :param gzip: create .tar.gz archive if ``True``, else .tar

        :type include_hidden: bool
        :param include_hidden: whether to include hidden datasets
          in the export

        :type include_deleted: bool
        :param include_deleted: whether to include deleted datasets
          in the export

        :type wait: bool
        :param wait: if ``True``, block until the export is ready; else, return
          immediately

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the export to become
          ready. When set, implies that ``wait`` is ``True``.

        :rtype: str
        :return: ``jeha_id`` of the export, or empty if ``wait`` is ``False``
          and the export is not ready.
        """
        params = {
            'gzip': gzip,
            'include_hidden': include_hidden,
            'include_deleted': include_deleted,
        }
        url = '%s/exports' % self.gi._make_url(self, history_id)
        if wait and maxwait is None:
            maxwait = sys.maxsize
        time_left = maxwait
        while True:
            try:
                r = self._put(payload={}, url=url, params=params)
            except ConnectionError as e:
                if e.status_code == 202:  # export is not ready
                    if maxwait is not None:
                        time_left -= 1
                    if time_left > 0:
                        log.warning("Waiting for the export of history %s to complete. Will wait %i more s" % (history_id, time_left))
                        time.sleep(1)
                    else:
                        return ''
                else:
                    raise
            else:
                break
        jeha_id = r['download_url'].rsplit('/', 1)[-1]
        return jeha_id

    def download_history(self, history_id, jeha_id, outf,
                         chunk_size=bioblend.CHUNK_SIZE):
        """
        Download a history export archive.  Use :meth:`export_history`
        to create an export.

        :type history_id: str
        :param history_id: history ID

        :type jeha_id: str
        :param jeha_id: jeha ID (this should be obtained via
          :meth:`export_history`)

        :type outf: file
        :param outf: output file object, open for writing in binary mode

        :type chunk_size: int
        :param chunk_size: how many bytes at a time should be read into memory

        :rtype: None
        :return: None
        """
        url = '%s/exports/%s' % (
            self.gi._make_url(self, module_id=history_id), jeha_id)
        r = self.gi.make_get_request(url, stream=True)
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size):
            outf.write(chunk)
