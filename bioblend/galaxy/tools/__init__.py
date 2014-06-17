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

    def get_tools(self, tool_id=None, name=None, trackster=None):
        """
        Get all tools or filter the specific one(s) via the provided ``name``
        or ``tool_id``. Provide only one argument, ``name`` or ``tool_id``,
        but not both.

        If ``name`` is set and multiple names match the given name, all the
        tools matching the argument will be returned.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :type name: str
        :param name: name of the requested tool(s)

        :type trackster: boolean
        :param trackster: if True, only tools that are compatible with
          Trackster are returned

        :rtype: list
        :return: List of tool descriptions.
        """
        if tool_id is not None and name is not None:
            raise ValueError('Provide only one argument between name or tool_id, but not both')
        tools = self._raw_get_tool(in_panel=False, trackster=trackster)
        if tool_id is not None:
            tool = next((_ for _ in tools if _['id'] == tool_id), None)
            tools = [tool] if tool is not None else []
        elif name is not None:
            tools = [_ for _ in tools if _['name'] == name]
        return tools

    def get_tool_panel(self):
        """
        Get a list of available tool elements in Galaxy's configured toolbox.

        :rtype: list
        :return: List containing tools (if not in sections) or tool sections
                 with nested tool descriptions.
        """
        return self._raw_get_tool(in_panel=True)

    def _raw_get_tool(self, in_panel=None, trackster=None):
        params = {}
        params['in_panel'] = in_panel
        params['trackster'] = trackster
        return Client._get(self, params=params)

    def show_tool(self, tool_id, io_details=False, link_details=False):
        """
        Get details of a given tool.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :type io_details: boolean
        :param io_details: if True, get also input and output details

        :type link_details: boolean
        :param link_details: if True, get also link details
        """
        params = {}
        params['io_details'] = io_details
        params['link_details'] = link_details
        return Client._get(self, id=tool_id, params=params)

    def run_tool(self, history_id, tool_id, tool_inputs):
        """
        Runs tool specified by ``tool_id`` in history indicated
        by ``history_id`` with inputs from ``dict`` ``tool_inputs``.

        :type tool_inputs: dict
        :param tool_inputs: dictionary of input datasets and parameters
          for the tool (see below)

        The ``tool_inputs`` dict should contain input datasets and parameters
        in the (largely undocumented) format used by the Galaxy API.
        Some examples can be found in https://bitbucket.org/galaxy/galaxy-central/src/tip/test/api/test_tools.py .
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
