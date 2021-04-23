"""
Contains possible interaction dealing with Galaxy tools.
"""
import warnings
from os.path import basename
from typing import List

from bioblend.galaxy.client import Client
from bioblend.util import attach_file


class ToolClient(Client):
    module = 'tools'

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def get_tools(self, tool_id=None, name=None, trackster=None):
        """
        Get all tools, or select a subset by specifying optional arguments for
        filtering (e.g. a tool name).

        :type tool_id: str
        :param tool_id: id of the requested tool

          .. deprecated:: 0.16.0
             To get details of a tool for which you know the ID, use the much
             more efficient :meth:`show_tool` instead.

        :type name: str
        :param name: Tool name to filter on.

        :type trackster: bool
        :param trackster: whether to return only tools that are compatible with
          Trackster

        :rtype: list
        :return: List of tool descriptions.

        .. seealso:: bioblend.galaxy.toolshed.get_repositories()
        """
        if tool_id is not None:
            warnings.warn(
                'The tool_id parameter is deprecated, use the show_tool() method to view details of a tool for which you know the ID.',
                category=FutureWarning
            )
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

    def requirements(self, tool_id):
        """
        Return the resolver status for a specific tool.
        This functionality is available only to Galaxy admins.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :rtype: list
        :return: List containing a resolver status dict for each tool
          requirement. For example::

            [{'cacheable': False,
              'dependency_resolver': {'auto_init': True,
                                      'auto_install': False,
                                      'can_uninstall_dependencies': True,
                                      'ensure_channels': 'iuc,conda-forge,bioconda,defaults',
                                      'model_class': 'CondaDependencyResolver',
                                      'prefix': '/mnt/galaxy/tool_dependencies/_conda',
                                      'resolver_type': 'conda',
                                      'resolves_simple_dependencies': True,
                                      'use_local': False,
                                      'versionless': False},
              'dependency_type': 'conda',
              'environment_path': '/mnt/galaxy/tool_dependencies/_conda/envs/__blast@2.10.1',
              'exact': True,
              'model_class': 'MergedCondaDependency',
              'name': 'blast',
              'version': '2.10.1'}]
        """
        url = self._make_url(tool_id) + '/requirements'
        return self._get(url=url)

    def get_citations(self, tool_id: str) -> List[dict]:
        """
        Get BibTeX citations for a given tool ID.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :rtype: list of dicts
        :param: list containing the citations
        """
        url = self._make_url(tool_id) + '/citations'
        return self._get(url=url)

    def install_dependencies(self, tool_id):
        """
        Install dependencies for a given tool via a resolver.
        This works only for Conda currently.
        This functionality is available only to Galaxy admins.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :rtype: dict
        :return: Tool requirement status
        """
        url = self._make_url(tool_id) + '/install_dependencies'
        return self._post(payload={}, url=url)

    def uninstall_dependencies(self, tool_id: str) -> dict:
        """
        Uninstall dependencies for a given tool via a resolver.
        This works only for Conda currently.
        This functionality is available only to Galaxy admins.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :rtype: dict
        :return: Tool requirement status
        """
        url = self._make_url(tool_id) + '/dependencies'
        return self._delete(payload={}, url=url)

    def show_tool(self, tool_id, io_details=False, link_details=False):
        """
        Get details of a given tool.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :type io_details: bool
        :param io_details: whether to get also input and output details

        :type link_details: bool
        :param link_details: whether to get also link details

        :rtype: dict
        :return: Information about the tool's interface
        """
        params = {}
        params['io_details'] = io_details
        params['link_details'] = link_details
        return self._get(id=tool_id, params=params)

    def run_tool(self, history_id, tool_id, tool_inputs, input_format='legacy'):
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

        :type input_format:  string
        :param input_format: input format for the payload. Possible values are the
          default 'legacy' (where inputs nested inside conditionals
          or repeats are identified with e.g. '<conditional_name>|<input_name>')
          or '21.01' (where inputs inside conditionals or repeats are nested elements).

        :rtype: dict
        :return: Information about outputs and job
          For example::

            {'implicit_collections': [],
             'jobs': [{'create_time': '2019-05-08T12:26:16.067372',
                       'exit_code': None,
                       'id': '7dd125b61b35d782',
                       'model_class': 'Job',
                       'state': 'new',
                       'tool_id': 'cut1',
                       'update_time': '2019-05-08T12:26:16.067389'}],
             'output_collections': [],
             'outputs': [{'create_time': '2019-05-08T12:26:15.997739',
                          'data_type': 'galaxy.datatypes.tabular.Tabular',
                          'deleted': False,
                          'file_ext': 'tabular',
                          'file_size': 0,
                          'genome_build': '?',
                          'hda_ldda': 'hda',
                          'hid': 42,
                          'history_content_type': 'dataset',
                          'history_id': 'df8fe5ddadbf3ab1',
                          'id': 'aeb65580396167f3',
                          'metadata_column_names': None,
                          'metadata_column_types': None,
                          'metadata_columns': None,
                          'metadata_comment_lines': None,
                          'metadata_data_lines': None,
                          'metadata_dbkey': '?',
                          'metadata_delimiter': '\t',
                          'misc_blurb': 'queued',
                          'misc_info': None,
                          'model_class': 'HistoryDatasetAssociation',
                          'name': 'Cut on data 1',
                          'output_name': 'out_file1',
                          'peek': None,
                          'purged': False,
                          'state': 'new',
                          'tags': [],
                          'update_time': '2019-05-08T12:26:16.069798',
                          'uuid': 'd91d10af-7546-45be-baa9-902010661466',
                          'visible': True}]}

        The ``tool_inputs`` dict should contain input datasets and parameters
        in the (largely undocumented) format used by the Galaxy API.
        Some examples can be found in `Galaxy's API test suite
        <https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy_test/api/test_tools.py>`_.
        """
        payload = {}
        payload["history_id"] = history_id
        payload["tool_id"] = tool_id
        payload["input_format"] = input_format
        try:
            payload["inputs"] = tool_inputs.to_dict()
        except AttributeError:
            payload["inputs"] = tool_inputs
        return self._post(payload)

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
        :param file_type: (optional) Galaxy datatype for the new dataset, default is auto

        :type dbkey: str
        :param dbkey: (optional) genome dbkey

        :type to_posix_lines: bool
        :param to_posix_lines: if ``True`` (the default), convert universal line
          endings to POSIX line endings. Set to ``False`` when uploading a gzip,
          bz2 or zip archive containing a binary file

        :type space_to_tab: bool
        :param space_to_tab: whether to convert spaces to tabs. Default is
          ``False``. Applicable only if to_posix_lines is ``True``

        :rtype: dict
        :return: Information about the created upload job
        """
        if "file_name" not in keywords:
            keywords["file_name"] = basename(path)
        payload = self._upload_payload(history_id, **keywords)
        payload["files_0|file_data"] = attach_file(path, name=keywords["file_name"])
        try:
            return self._post(payload, files_attached=True)
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

        :rtype: dict
        :return: Information about the created upload job
        """
        payload = self._upload_payload(history_id, **keywords)
        payload['files_0|ftp_files'] = path
        return self._post(payload)

    def paste_content(self, content, history_id, **kwds):
        """
        Upload a string to a new dataset in the history specified by
        ``history_id``.

        :type content: str
        :param content: content of the new dataset to upload or a list of URLs
          (one per line) to upload

        :type history_id: str
        :param history_id: id of the history where to upload the content

        :rtype: dict
        :return: Information about the created upload job

        See :meth:`upload_file` for the optional parameters.
        """
        payload = self._upload_payload(history_id, **kwds)
        payload["files_0|url_paste"] = content
        return self._post(payload, files_attached=False)

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
