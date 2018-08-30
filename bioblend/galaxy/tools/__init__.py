"""
Contains possible interaction dealing with Galaxy tools.
"""
from json import dumps
from os.path import basename

from bioblend.galaxy.client import Client
from bioblend.util import attach_file


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

        :type trackster: bool
        :param trackster: if True, only tools that are compatible with
          Trackster are returned

        :rtype: list
        :return: List of tool descriptions.

        .. seealso:: bioblend.galaxy.toolshed.get_repositories()
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

        .. seealso:: bioblend.galaxy.toolshed.get_repositories()
        """
        return self._raw_get_tool(in_panel=True)

    def _raw_get_tool(self, in_panel=None, trackster=None):
        params = {}
        params['in_panel'] = in_panel
        params['trackster'] = trackster
        return self._get(params=params)

    def install_dependencies(self, tool_id):
        """
        Install dependencies for a given tool via a resolver.
        This works only for Conda currently.
        This functionality is available since Galaxy release_16.10
        and is available only to Galaxy admins.

        :type tool_id: str
        :param tool_id: id of the requested tool
        """
        url = "%s/tools/%s/install_dependencies" % (self.gi.url, tool_id)
        return self._post(payload={}, url=url)

    def show_tool(self, tool_id, io_details=False, link_details=False):
        """
        Get details of a given tool.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :type io_details: bool
        :param io_details: if True, get also input and output details

        :type link_details: bool
        :param link_details: if True, get also link details
        """
        params = {}
        params['io_details'] = io_details
        params['link_details'] = link_details
        return self._get(id=tool_id, params=params)

    def run_tool(self, history_id, tool_id, tool_inputs):
        """
        Runs tool specified by ``tool_id`` in history indicated
        by ``history_id`` with inputs from ``dict`` ``tool_inputs``.

        :type history_id: str
        :param history_id: encoded ID of the history in which to run the tool

        :type tool_id: str
        :param tool_id: ID of the tool to be run

        :type tool_inputs: dict
        :param tool_inputs: dictionary of input datasets and parameters
          for the tool (see below)

        The ``tool_inputs`` dict should contain input datasets and parameters
        in the (largely undocumented) format used by the Galaxy API.
        Some examples can be found in `Galaxy's API test suite
        <https://github.com/galaxyproject/galaxy/blob/dev/test/api/test_tools.py>`_.
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
        Upload the file specified by ``path`` to the history specified by
        ``history_id``.

        :type path: str
        :param path: path of the file to upload

        :type history_id: str
        :param history_id: id of the history where to upload the file

        :type file_name: str
        :param file_name: (optional) name of the new history dataset

        :type file_type: str
        :param file_type: Galaxy datatype for the new dataset, default is auto

        :type dbkey: str
        :param dbkey: (optional) genome dbkey

        :type to_posix_lines: bool
        :param to_posix_lines: if True, convert universal line endings to POSIX
          line endings. Default is True. Set to False if you upload a gzip, bz2
          or zip archive containing a binary file

        :type space_to_tab: bool
        :param space_to_tab: whether to convert spaces to tabs. Default is
          False. Applicable only if to_posix_lines is True
        """
        if "file_name" not in keywords:
            keywords["file_name"] = basename(path)
        payload = self._upload_payload(history_id, **keywords)
        payload["files_0|file_data"] = attach_file(path, name=keywords["file_name"])
        try:
            return self._tool_post(payload, files_attached=True)
        finally:
            payload["files_0|file_data"].close()

    def upload_from_ftp(self, path, history_id, **keywords):
        """
        Upload the file specified by ``path`` from the user's FTP directory to
        the history specified by ``history_id``.

        :type path: str
        :param path: path of the file in the user's FTP directory

        :type history_id: str
        :param history_id: id of the history where to upload the file

        See :meth:`upload_file` for the optional parameters.
        """
        payload = self._upload_payload(history_id, **keywords)
        payload['files_0|ftp_files'] = path
        return self._tool_post(payload)

    def paste_content(self, content, history_id, **kwds):
        """
        Upload a string to a new dataset in the history specified by
        ``history_id``.

        :type content: str
        :param content: content of the new dataset to upload or a list of URLs
          (one per line) to upload

        :type history_id: str
        :param history_id: id of the history where to upload the content

        See :meth:`upload_file` for the optional parameters.
        """
        payload = self._upload_payload(history_id, **kwds)
        payload["files_0|url_paste"] = content
        return self._tool_post(payload, files_attached=False)

    put_url = paste_content

    def _upload_payload(self, history_id, **keywords):
        payload = {}
        payload["history_id"] = history_id
        payload["tool_id"] = keywords.get("tool_id", "upload1")
        tool_input = {}
        tool_input["file_type"] = keywords.get('file_type', 'auto')
        tool_input["dbkey"] = keywords.get("dbkey", "?")
        if not keywords.get('to_posix_lines', True):
            tool_input['files_0|to_posix_lines'] = False
        elif keywords.get('space_to_tab', False):
            tool_input['files_0|space_to_tab'] = 'Yes'
        if 'file_name' in keywords:
            tool_input["files_0|NAME"] = keywords['file_name']
        tool_input["files_0|type"] = "upload_dataset"
        payload["inputs"] = tool_input
        return payload

    def _tool_post(self, payload, files_attached=False):
        if files_attached:
            # If files_attached - this will be posted as multi-part form data
            # and so each individual parameter needs to be encoded so can be
            # decoded as JSON by Galaxy (hence dumping complex parameters).
            # If no files are attached, the whole thing is posted as
            # application/json and dumped/loaded all at once by requests and
            # Galaxy.
            complex_payload_params = ["inputs"]
            for key in complex_payload_params:
                if key in payload:
                    payload[key] = dumps(payload[key])
        return self._post(payload, files_attached=files_attached)
