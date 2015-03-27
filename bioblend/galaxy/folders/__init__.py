"""
Contains possible interactions with the Galaxy library folders
"""
from bioblend.galaxy.client import Client


class FoldersClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'folders'
        super(FoldersClient, self).__init__(galaxy_instance)

    def show_folder(self, folder_id):
        """
        Display information about a folder.

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :rtype: dict
        :return: dictionary including details of the folder
        """

        return Client._get(self, id=folder_id)

    def delete_folder(self, folder_id, undelete=False):
        """
        Marks the folder with the given ``id`` as `deleted` (or removes the
        `deleted` mark if the `undelete` param is True).

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :type undelete: bool
        :param undelete: If set to True, the folder will be undeleted
                         (i.e. the `deleted` mark will be removed)

        :returns:   detailed folder information
        :rtype:     dict
        """
        payload = {'undelete': undelete}
        return Client._delete(self, payload, id=folder_id)
