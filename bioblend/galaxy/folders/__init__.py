"""
Contains possible interactions with the Galaxy library folders
"""

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
    Union,
)

from bioblend.galaxy.client import Client

if TYPE_CHECKING:
    from bioblend.galaxy import GalaxyInstance


class FoldersClient(Client):
    module = "folders"

    def __init__(self, galaxy_instance: "GalaxyInstance") -> None:
        super().__init__(galaxy_instance)

    def create_folder(self, parent_folder_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
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
        payload: Dict[str, str] = {"name": name}
        if description:
            payload["description"] = description
        return self._post(payload=payload, id=parent_folder_id)

    def show_folder(
        self,
        folder_id: str,
        contents: bool = False,
        limit: int = 10,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """
        Display information about a folder.

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :type contents: bool
        :param contents: True to get the contents of the folder, rather
          than just the folder details.

        :type limit: int
        :param limit: Maximum number of contents to return (default: 10).
          Only considered for contents=True.

        :type offset: int
        :param contents: Return contents from this specified position (default: 0).
          Only considered for contents=True.

        :type include_deleted: bool
        :param include_deleted: Returns also deleted contents.
          Only considered for contents=True.

        :rtype: dict
        :return: dictionary including details of the folder
        """
        params = {
            "limit": limit,
            "offset": offset,
            "include_deleted": include_deleted,
        }
        return self._get(id=folder_id, contents=contents, params=params)

    def contents(
        self,
        folder_id: str,
        limit: int = 10,
        include_deleted: bool = False,
    ) -> Iterable[Dict[str, Any]]:
        """
        Iterate over folder contents.

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :type limit: int
        :param limit: Batch size to be used internally (default: 10).

        :type include_deleted: bool
        :param include_deleted: Include also deleted contents.

        :rtype: dict
        :return: A generator for the folder contents
        """
        total_rows: Optional[int] = None
        params = {
            "limit": limit,
            "offset": 0,
            "include_deleted": include_deleted,
        }

        while total_rows is None or params["offset"] <= total_rows:
            chunk = self._get(id=folder_id, contents=True, params=params)
            total_rows = chunk["metadata"]["total_rows"]
            yield from chunk["folder_contents"]
            params["offset"] += limit

    def delete_folder(self, folder_id: str, undelete: bool = False) -> Dict[str, Any]:
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
        payload = {"undelete": undelete}
        return self._delete(payload=payload, id=folder_id)

    def update_folder(self, folder_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
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
        payload = {"name": name}
        if description:
            payload["description"] = description
        return self._put(payload=payload, id=folder_id)

    def get_permissions(self, folder_id: str, scope: Literal["current", "available"] = "current") -> Dict[str, Any]:
        """
        Get the permissions of a folder.

        :type folder_id: str
        :param folder_id: the folder's encoded id, prefixed by 'F'

        :type scope: str
        :param scope: scope of permissions, either 'current' or 'available'

        :rtype: dict
        :return: dictionary including details of the folder permissions
        """
        url = self._make_url(folder_id) + "/permissions"
        return self._get(url=url)

    def set_permissions(
        self,
        folder_id: str,
        action: Literal["set_permissions"] = "set_permissions",
        add_ids: Optional[List[str]] = None,
        manage_ids: Optional[List[str]] = None,
        modify_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
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
        url = self._make_url(folder_id) + "/permissions"
        payload: Dict[str, Union[str, List[str]]] = {"action": action}
        if add_ids:
            payload["add_ids[]"] = add_ids
        if manage_ids:
            payload["manage_ids[]"] = manage_ids
        if modify_ids:
            payload["modify_ids[]"] = modify_ids
        return self._post(url=url, payload=payload)
