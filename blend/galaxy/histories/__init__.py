"""
Contains possible interactions with the Galaxy Histories
"""
from blend.galaxy.client import Client


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

    def show_history(self, history_id, contents=False):
        """
        Get details of a given history. By default, just get the history meta
        information. If ``contents`` is set to ``True``, get the complete list of
        datasets in the given history.
        """
        return Client._get(self, id=history_id, contents=contents)

    def show_dataset(self, history_id, dataset_id):
        """
        Get details about a given history dataset. The required ``history_id``
        can be obtained from the datasets's history content details.
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        return Client._get(self, url=url)

    def upload_dataset_from_library(self, history_id, lib_dataset_id):
        """
        Upload a dataset into the history from a library. Requires the
        library dataset ID, which can be obtained from the library
        contents.
        """
        payload = {'from_ld_id': lib_dataset_id}
        return Client._post(self, payload, id=history_id, contents=True)

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
