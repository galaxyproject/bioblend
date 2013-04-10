"""
Contains possible interaction dealing with Galaxy tools.

"""
from bioblend.galaxy.client import Client
from os.path import basename
from simplejson import dumps


class ToolClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'tools'
        super(ToolClient, self).__init__(galaxy_instance)

    def run_tool(self, history_id, tool_id, tool_inputs):
        """
        Runs tool specified by ``tool_id`` in history indicated
        by ``history_id`` with inputs from ``dict`` ``tool_inputs``.
        """
        payload = {}
        payload["history_id"] = history_id
        payload["tool_id"] = tool_id
        payload["inputs"] = dumps(tool_inputs)
        return Client._post(self, payload)

    def upload_file(self, path, history_id, **keywords):
        """
        Upload specified file specified by ``path`` to history specified by
        ``history_id``.
        """
        payload = {}
        payload["history_id"] = history_id
        payload["tool_id"] = keywords.get("tool_id", "upload1")
        file_type = keywords.get("file_type", "auto")
        file_name = keywords.get("file_name", basename(path))
        tool_input = {}
        tool_input["file_type"] = file_type
        tool_input["dbkey"] = keywords.get("dbkey", "?")
        tool_input["files_0|NAME"] = file_name
        tool_input["files_0|type"] = "upload_dataset"
        payload["inputs"] = dumps(tool_input)
        payload["files_0|file_data"] = open(path, 'rb')
        return Client._post(self, payload, files_attached=True)
