"""
Contains possible interactions with the Galaxy Unprivileged Tools API.

Unprivileged tools let non-admin users register, list, fetch, and deactivate
their own tool definitions. To run one, use
:meth:`bioblend.galaxy.tools.ToolClient.run_tool` with ``tool_uuid``.
"""

from typing import (
    Any,
    TYPE_CHECKING,
)

from bioblend.galaxy.client import Client

if TYPE_CHECKING:
    from bioblend.galaxy import GalaxyInstance


class UnprivilegedToolsClient(Client):
    gi: "GalaxyInstance"
    module = "unprivileged_tools"

    def __init__(self, galaxy_instance: "GalaxyInstance") -> None:
        super().__init__(galaxy_instance)

    def get_user_tools(self, active: bool = True) -> list[dict[str, Any]]:
        """
        List the current user's unprivileged tools.

        :type active: bool
        :param active: If ``True`` (the default), return only active tools;
          if ``False``, return only deactivated tools.

        :rtype: list
        :return: A list of dicts describing the user's unprivileged tools.
        """
        return self._get(params={"active": active})

    def show_user_tool(self, uuid: str) -> dict[str, Any]:
        """
        Show information on a single unprivileged tool.

        :type uuid: str
        :param uuid: UUID of the unprivileged tool to fetch.

        :rtype: dict
        :return: Details of the given unprivileged tool.
        """
        return self._get(id=uuid)

    def create_user_tool(self, representation: dict[str, Any]) -> dict[str, Any]:
        """
        Register a new unprivileged tool from a tool ``representation``.

        :type representation: dict
        :param representation: The tool representation (the same structure
          accepted by Galaxy's unprivileged tools API). It will be wrapped
          as ``{"src": "representation", "representation": representation}``
          before being POSTed.

        :rtype: dict
        :return: Details of the newly created unprivileged tool, including
          its ``uuid``.
        """
        payload = {"src": "representation", "representation": representation}
        return self._post(payload)

    def delete_user_tool(self, uuid: str) -> None:
        """
        Deactivate an unprivileged tool.

        :type uuid: str
        :param uuid: UUID of the unprivileged tool to deactivate.
        """
        self._delete(id=uuid)
