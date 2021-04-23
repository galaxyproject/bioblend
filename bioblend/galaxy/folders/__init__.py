"""
Contains possible interactions with the Galaxy library folders
"""
from bioblend.galaxy.client import Client


class FoldersClient(Client):
    module = 'folders'

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def create_folder(self, parent_folder_id, name, description=None):
        """
        Create a folder.

        :type parent_folder_id: str
        :param parent_folder_id: Folder's description

        :type name: str
        :param name: name of the new folder

        :type description: str
        :param description: folder's description

        :rtype: dict
        :return: details of the updated folder
        """
        payload = {'name': name}
        if description:
            payload['description'] = description
        return self._post(payload=payload, id=parent_folder_id)

    def show_folder(self, folder_id, contents=False):
        """
        Display information about a folder.

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :type contents: bool
        :param contents: True to get the contents of the folder, rather
          than just the folder details.

        :rtype: dict
        :return: dictionary including details of the folder
        """

        return self._get(id=folder_id, contents=contents)

    def delete_folder(self, folder_id, undelete=False):
        """
        Marks the folder with the given ``id`` as `deleted` (or removes the
        `deleted` mark if the `undelete` param is True).

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :type undelete: bool
        :param undelete: If set to True, the folder will be undeleted
                         (i.e. the `deleted` mark will be removed)

        :return: detailed folder information
        :rtype: dict
        """
        payload = {'undelete': undelete}
        return self._delete(payload=payload, id=folder_id)

    def update_folder(self, folder_id, name, description=None):
        """
        Update folder information.

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :type name: str
        :param name: name of the new folder

        :type description: str
        :param description: folder's description

        :rtype: dict
        :return: details of the updated folder
        """
        payload = {'name': name}
        if description:
            payload['description'] = description
        return self._put(payload=payload, id=folder_id)

    def get_permissions(self, folder_id, scope):
        """
        Get the permissions of a folder.

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :type scope: str
        :param scope: scope of permissions, either 'current' or 'available'

        :rtype: dict
        :return: dictionary including details of the folder
        """
        url = self._make_url(folder_id) + '/permissions'
        return self._get(url=url)

    def set_permissions(self, folder_id, action='set_permissions', add_ids=None, manage_ids=None, modify_ids=None):
        """
        Set the permissions of a folder.

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :type action: str
        :param action: action to execute, only "set_permissions" is supported.

        :type add_ids: list of str
        :param add_ids: list of role IDs which can add datasets to the folder

        :type manage_ids: list of str
        :param manage_ids: list of role IDs which can manage datasets in the folder

        :type modify_ids: list of str
        :param modify_ids: list of role IDs which can modify datasets in the folder

        :rtype: dict
        :return: dictionary including details of the folder
        """
        url = self._make_url(folder_id) + '/permissions'
        payload = {'action': action}
        if add_ids:
            payload['add_ids[]'] = add_ids
        if manage_ids:
            payload['manage_ids[]'] = manage_ids
        if modify_ids:
            payload['modify_ids[]'] = modify_ids
        return self._post(url=url, payload=payload)
