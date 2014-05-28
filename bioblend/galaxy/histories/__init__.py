"""
Contains possible interactions with the Galaxy Histories
"""
from bioblend.galaxy.client import Client

import os
import re
import shutil
import urllib2


class HistoryClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'histories'
        super(HistoryClient, self).__init__(galaxy_instance)

    def create_history(self, name=None):
        """
        Create a new history, optionally setting the ``name``.
        """
        payload = {}
        if name is not None:
            payload['name'] = name
        return Client._post(self, payload)

    def get_histories(self, history_id=None, name=None, deleted=False):
        """
        Get all histories or filter the specific one(s) via the provided ``name``
        or ``history_id``. Provide only one argument, ``name`` or ``history_id``,
        but not both.

        If ``deleted`` is set to ``True``, return histories that have been deleted.

        Return a list of history element dicts. If more than one history
        matches the given ``name``, return the list of all the histories with the
        given name.
        """
        histories = Client._get(self, deleted=deleted)
        if name is not None or history_id is not None:
            filtered_hists = []
            for history in histories:
                if name == history['name'] or history_id == history['id']:
                    filtered_hists.append(history)
                    # History ID's are unique so break now that the hist was found
                    if history_id is not None:
                        break
            histories = filtered_hists
        return histories

    def show_history(self, history_id, contents=False, deleted=None, visible=None, details=None, types=None):
        """
        Get details of a given history. By default, just get the history meta
        information. If ``contents`` is set to ``True``, get the complete list of
        datasets in the given history. ``deleted``, ``visible``, and ``details`` are
        used only if ``contents`` is ``True`` and are used to modify the datasets returned
        and their contents. Set ``details`` to 'all' to get more information
        about each dataset.
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
                params['types'] = types.join(",")
        return Client._get(self, id=history_id, contents=contents, params=params)

    def delete_dataset(self, history_id, dataset_id):
        """
        Mark corresponding datset as deleted.
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        Client._delete(self, payload={}, url=url)

    def delete_dataset_collection(self, history_id, dataset_collection_id):
        """
        Mark corresponding datset as deleted.
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, "dataset_collections", dataset_collection_id])
        Client._delete(self, payload={}, url=url)

    def show_dataset(self, history_id, dataset_id):
        """
        Get details about a given history dataset. The required ``history_id``
        can be obtained from the datasets's history content details.
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        return Client._get(self, url=url)

    def show_dataset_collection(self, history_id, dataset_collection_id):
        """
        Get details about a given history dataset collection.
        """
        url = self.gi._make_url(self, history_id, contents=True)
        url = '/'.join([url, "dataset_collections", dataset_collection_id])
        return Client._get(self, url=url)

    def show_matching_datasets(self, history_id, name_filter=None):
        """
        Get dataset details for matching datasets within a history.

        Only datasets whose name matches the ``name_filter`` regular
        expression will be returned; use plain strings for exact
        matches and None to match all datasets in the history.
        """
        if isinstance(name_filter, basestring):
            name_filter = re.compile(name_filter + '$')
        return [self.show_dataset(history_id, h['id'])
                for h in self.show_history(history_id, contents=True)
                if name_filter is None or name_filter.match(h['name'])]

    def show_dataset_provenance(self, history_id, dataset_id, follow=False):
        """
        Get details related to how dataset was created (``id``, ``job_id``,
        ``tool_id``, ``stdout``, ``stderr``, ``parameters``, ``inputs``,
        etc...).

        If ``follow`` is ``True``, recursively fetch dataset provenance
        information for all inputs and their inputs, etc....
        """
        url = self.gi._make_url(self, history_id, contents=True)
        url = '/'.join([url, dataset_id, "provenance"])
        return Client._get(self, url=url)

    def update_history(self, history_id, name=None, annotation=None):
        """
        Update history metadata information. Current attributes that can be modified
        for a history 'name' and 'annotation'.

        :type history_id: string
        :param history_id: Encoded history ID
        :type name: string
        :param name: Replace history with the given string
        :type annotation: string
        :param annotation: Replace history annotation with given string

        :rtype: status_code (int)

        """

        payload = {}
        if name:
            payload['name'] = name
        if annotation:
            payload['annotation'] = annotation

        return Client._put(self, payload, id=history_id)

    def update_dataset(self, history_id, dataset_id, **kwds):
        """
        Update history dataset metadata. Only a subset of the available
        metadata parameters for modification are documented below currently.

        :type history_id: string
        :param history_id: Encoded history ID
        :type name: string
        :param name: Replace history dataset name with the given string
        :type annotation: string
        :param annotation: Replace history dataset annotation with given string
        :type deleted: boolean
        :param deleted: Mark or unmark history dataset as deleted.
        :type visible: boolean
        :param visible: Mark or unmark history dataset as visible.

        :rtype: status_code (int)
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        return Client._put(self, payload=kwds, url=url)

    def update_dataset_collection(self, history_id, dataset_collection_id, **kwds):
        """
        Update history dataset metadata. Only a subset of the available
        metadata parameters for modification are documented below currently.

        :type history_id: string
        :param history_id: Encoded history ID
        :type name: string
        :param name: Replace history dataset collection name with the given string
        :type deleted: boolean
        :param deleted: Mark or unmark history dataset collection as deleted.
        :type visible: boolean
        :param visible: Mark or unmark history dataset collection as visible.

        :rtype: status_code (int)
        """
        url = self.gi._make_url(self, history_id, contents=True)
        url = '/'.join([url, "dataset_collections", dataset_collection_id])
        return Client._put(self, payload=kwds, url=url)

    def create_history_tag(self, history_id, tag):
        """
        Create history tag

        :type history_id: string
        :param history_id: Encoded history ID
        :type tag: string
        :param tag: Add tag to history

        :rtype: json object
        :return: Return json object
                 For example::

                 {'model_class':'HistoryTagAssociation', 'user_tname': 'NGS_PE_RUN', 'id': 'f792763bee8d277a', 'user_value': None}

        """

        # empty payload since we are adding the new tag using the url
        payload = {}

        # creating the url
        url = self.url
        url = '/'.join([url, history_id, 'tags', tag])

        return Client._post(self, payload, url=url)

    def upload_dataset_from_library(self, history_id, lib_dataset_id):
        """
        Upload a dataset into the history from a library. Requires the
        library dataset ID, which can be obtained from the library
        contents.
        """
        payload = {
            'content': lib_dataset_id,
            'source': 'library',
            'from_ld_id': lib_dataset_id,  # compatibility with old API
        }
        return Client._post(self, payload, id=history_id, contents=True)

    def create_dataset_collection(self, history_id, collection_description):
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
        return Client._post(self, payload, id=history_id, contents=True)

    def download_dataset(self, history_id, dataset_id, file_path,
                         use_default_filename=True, to_ext=None):
        """
        Download a ``dataset_id`` from history with ``history_id`` to a
        file on the local file system, saving it to ``file_path``.
        """
        meta = self.show_dataset(history_id, dataset_id)
        d_type = to_ext
        if d_type is None and 'data_type' in meta:
            d_type = meta['data_type']
        url = '/'.join([self.gi.base_url, 'datasets', meta['id'], "display"]) + "?to_ext=" + d_type
        req = urllib2.urlopen(url)
        if use_default_filename:
            file_local_path = os.path.join(file_path, meta['name'])
        else:
            file_local_path = file_path

        with open(file_local_path, 'wb') as fp:
            shutil.copyfileobj(req, fp)

    def delete_history(self, history_id, purge=False):
        """
        Delete a history.

        If ``purge`` is set to ``True``, also purge the history. Note that for
        the purge option to work, ``allow_user_dataset_purge`` option must be
        set in the Galaxy's configuration file ``universe_wsgi.ini``
        """
        payload = {}
        if purge is True:
            payload['purge'] = purge
        return Client._delete(self, payload, id=history_id)

    def undelete_history(self, history_id):
        """
        Undelete a history
        """
        url = self.gi._make_url(self, history_id, deleted=True)
        # Append the 'undelete' action to the history URL
        url = '/'.join([url, 'undelete'])
        return Client._post(self, payload={}, url=url)

    def get_status(self, history_id):
        """
        Returns the state of this history as a dictionary, with the following keys.
        'state' = This is the current state of the history, such as ok, error, new etc.
        'state_details' = Contains individual statistics for various dataset states.
        'percent_complete' = The overall number of datasets processed to completion.
        """
        state = {}
        history = self.show_history(history_id)
        state['state'] = history['state']
        if history.get('state_details') is not None:
            state['state_details'] = history['state_details']
            total_complete = sum(history['state_details'].itervalues())
            if total_complete > 0:
                state['percent_complete'] = 100 * history['state_details']['ok'] / total_complete
            else:
                state['percent_complete'] = 0
        return state

    def get_current_history(self):
        """
        Returns the current user's most recently used history object (not deleted)
        """
        url = self.gi._make_url(self, None)
        url = '/'.join([url, 'most_recently_used'])
        return Client._get(self, url=url)
