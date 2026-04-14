"""
Contains possible interactions with the Galaxy Unprivileged Tools API.

Unprivileged tools let non-admin users register, list, fetch, and deactivate
their own tool definitions, then run them via the jobs API using the tool's
UUID.
"""

from typing import (
    Any,
    Literal,
    TYPE_CHECKING,
)

from bioblend.galaxy.client import Client
from bioblend.galaxy.tools.inputs import InputsBuilder

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

    def run_user_tool(
        self,
        history_id: str,
        tool_uuid: str,
        tool_inputs: InputsBuilder | dict[str, Any],
        tool_version: str | None = None,
        input_format: Literal["21.01", "legacy"] = "legacy",
    ) -> dict[str, Any]:
        """
        Run an unprivileged tool by its ``tool_uuid``.

        Unprivileged tool runs are submitted to the jobs API rather than the
        regular tools API; the returned shape mirrors
        :meth:`bioblend.galaxy.tools.ToolClient.run_tool`.

        :type history_id: str
        :param history_id: encoded ID of the history in which to run the tool

        :type tool_uuid: str
        :param tool_uuid: UUID of the unprivileged tool to be run

        :type tool_inputs: dict
        :param tool_inputs: dictionary of input datasets and parameters
          for the tool (see :meth:`ToolClient.run_tool` for the expected
          format)

        :type tool_version: str
        :param tool_version: Optional version of the unprivileged tool to run.

        :type input_format: str
        :param input_format: input format for the payload. Possible values are
          the default ``'legacy'`` or ``'21.01'`` (see
          :meth:`ToolClient.run_tool` for details).

        :rtype: dict
        :return: Information about outputs and the submitted job.
        """
        payload: dict[str, Any] = {
            "history_id": history_id,
            "tool_uuid": tool_uuid,
            "input_format": input_format,
        }

        if isinstance(tool_inputs, InputsBuilder):
            payload["inputs"] = tool_inputs.to_dict()
        else:
            payload["inputs"] = tool_inputs

        if tool_version is not None:
            payload["tool_version"] = tool_version

        url = "/".join((self.gi.url, "jobs"))
        return self._post(payload, url=url)
