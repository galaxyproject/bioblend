"""
Contains possible interaction dealing with Galaxy tools.

"""
from bioblend.galaxy.client import Client
from os.path import basename
from json import dumps


class ToolClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'tools'
        super(ToolClient, self).__init__(galaxy_instance)

    def get_tools(self):
        """
        Get a list of available tool elements in Galaxy's configured toolbox.

        :rtype: list
        :return: List of tool descriptions.
        """
        return self._raw_get_tool(in_panel=False)

    def get_tool_panel(self):
        """
        Get a list of available tool elements in Galaxy's configured toolbox.

        :rtype: list
        :return: List containing tools (if not in sections) or tool sections
                 with nested tool descriptions.
        """
        return self._raw_get_tool(in_panel=True)

    def _raw_get_tool(self, in_panel=None):
        params = {}
        params['in_panel'] = in_panel
        return Client._get(self, params=params)

    def run_tool(self, history_id, tool_id, tool_inputs):
        """
        Runs tool specified by ``tool_id`` in history indicated
        by ``history_id`` with inputs from ``dict`` ``tool_inputs``.
        """
        payload = {}
        payload["history_id"] = history_id
        payload["tool_id"] = tool_id
        try:
            payload["inputs"] = tool_inputs.to_dict()
        except AttributeError:
            payload["inputs"] = tool_inputs
        return self._tool_post(payload)

    def upload_file(self, path, history_id, **keywords):
        """
        Upload specified file specified by ``path`` to history specified by
        ``history_id``.
        """
        default_file_name = basename(path)
        if "file_name" not in keywords:
            keywords["file_name"] = default_file_name
        payload = self.upload_payload(history_id, **keywords)
        payload["files_0|file_data"] = open(path, "rb")
        return self._tool_post(payload, files_attached=True)

    def paste_content(self, content, history_id, **kwds):
        payload = self.upload_payload(history_id, **kwds)
        payload["files_0|url_paste"] = content
        return self._tool_post(payload, files_attached=False)

    put_url = paste_content

    def upload_payload(self, history_id, **keywords):
        payload = {}
        payload["history_id"] = history_id
        payload["tool_id"] = keywords.get("tool_id", "upload1")
        file_type = keywords.get("file_type", "auto")
        file_name = keywords.get("file_name", None)
        tool_input = {}
        tool_input["file_type"] = file_type
        tool_input["dbkey"] = keywords.get("dbkey", "?")
        if file_name:
            tool_input["files_0|NAME"] = file_name
        tool_input["files_0|type"] = "upload_dataset"
        payload["inputs"] = tool_input
        return payload

    def _tool_post(self, payload, files_attached=False):
        if files_attached:
            # If files_attached - this will be posted as multi-part form data
            # and so each individual parameter needs to be encoded so can be
            # decoded as JSON by Galaxy (hence dumping complex parameters).
            # If not files are attached the whole thing is posted a
            # application/json and dumped/loaded all at once by requests and
            # Galaxy.
            complex_payload_params = ["inputs"]
            for key in complex_payload_params:
                if key in payload:
                    payload[key] = dumps(payload[key])
        return Client._post(self, payload, files_attached=files_attached)
