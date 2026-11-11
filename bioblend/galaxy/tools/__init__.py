"""
Contains possible interaction dealing with Galaxy tools.
"""

from os.path import basename
from typing import (
    Any,
    Literal,
    TYPE_CHECKING,
)

from bioblend import (
    NotReady,
    wait_on,
)
from bioblend.galaxy.client import Client
from bioblend.galaxyclient import UPLOAD_CHUNK_SIZE
from bioblend.util import attach_file
from .inputs import InputsBuilder

if TYPE_CHECKING:
    from bioblend.galaxy import GalaxyInstance


class ToolRequestFailedException(RuntimeError):
    """
    Raised when Galaxy fails to process a tool request, see
    :meth:`ToolClient.run_tool_request`.
    """

    def __init__(self, tool_request: dict[str, Any]) -> None:
        self.tool_request = tool_request
        message = tool_request.get("state_message")
        if isinstance(message, dict):  # Galaxy 26.1 or later
            message = message.get("err_msg", message)
        super().__init__(f"Tool request {tool_request['id']} failed: {message}")


class ToolClient(Client["GalaxyInstance"]):
    module = "tools"

    def __init__(self, galaxy_instance: "GalaxyInstance") -> None:
        super().__init__(galaxy_instance)

    def get_tools(
        self, tool_id: str | None = None, name: str | None = None, trackster: bool | None = None
    ) -> list[dict[str, Any]]:
        """
        Get all tools, or select a subset by specifying optional arguments for
        filtering (e.g. a tool name).

        :type name: str
        :param name: Tool name to filter on.

        :type trackster: bool
        :param trackster: whether to return only tools that are compatible with
          Trackster

        :rtype: list
        :return: List of tool descriptions.

        .. seealso:: bioblend.galaxy.toolshed.get_repositories()

        .. versionchanged:: 1.1.1
           Using the deprecated ``tool_id`` parameter now raises a
           ``ValueError`` exception.
        """
        if tool_id is not None:
            raise ValueError(
                "The tool_id parameter has been removed, use the show_tool() method to view details of a tool for which you know the ID."
            )
        tools = self._raw_get_tool(in_panel=False, trackster=trackster)
        if name is not None:
            tools = [_ for _ in tools if _["name"] == name]
        return tools

    def get_tool_panel(self) -> list[dict[str, Any]]:
        """
        Get a list of available tool elements in Galaxy's configured toolbox.

        :rtype: list
        :return: List containing tools (if not in sections) or tool sections
                 with nested tool descriptions.

        .. seealso:: bioblend.galaxy.toolshed.get_repositories()
        """
        return self._raw_get_tool(in_panel=True)

    def _raw_get_tool(self, in_panel: bool | None = None, trackster: bool | None = None) -> list[dict[str, Any]]:
        params = {
            "in_panel": in_panel,
            "trackster": trackster,
        }
        return self._get(params=params)

    def requirements(self, tool_id: str) -> list[dict[str, Any]]:
        """
        Return the resolver status for a specific tool.

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

        .. note::
          This method works only if the user is a Galaxy admin.
        """
        url = self._make_url(tool_id) + "/requirements"
        return self._get(url=url)

    def reload(self, tool_id: str) -> dict:
        """
        Reload the specified tool in the toolbox.

        Any changes that have been made to the wrapper since the tool was last
        reloaded will take effect.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :rtype: dict
        :return: dict containing the id, name, and version of the reloaded tool.
          For example::

            {'message': {'id': 'toolshed.g2.bx.psu.edu/repos/lparsons/cutadapt/cutadapt/3.4+galaxy1',
                         'name': 'Cutadapt',
                         'version': '3.4+galaxy1'}}

        .. note::
          This method works only if the user is a Galaxy admin.
        """
        url = self._make_url(tool_id) + "/reload"
        return self._put(url=url)

    def get_citations(self, tool_id: str) -> list[dict]:
        """
        Get BibTeX citations for a given tool ID.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :rtype: list of dicts
        :return: list containing the citations
        """
        url = self._make_url(tool_id) + "/citations"
        return self._get(url=url)

    def install_dependencies(self, tool_id: str) -> list[dict[str, Any]]:
        """
        Install dependencies for a given tool via a resolver.
        This works only for Conda currently.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :rtype: list of dicts
        :return: List of tool requirement status dictionaries

        .. note::
          This method works only if the user is a Galaxy admin.
        """
        url = self._make_url(tool_id) + "/install_dependencies"
        return self._post(url=url)

    def uninstall_dependencies(self, tool_id: str) -> dict:
        """
        Uninstall dependencies for a given tool via a resolver.
        This works only for Conda currently.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :rtype: dict
        :return: Tool requirement status

        .. note::
          This method works only if the user is a Galaxy admin.
        """
        url = self._make_url(tool_id) + "/dependencies"
        return self._delete(url=url)

    def get_tool_source(self, tool_id: str) -> str:
        """
        Get the raw tool XML source for a given tool ID.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :rtype: str
        :return: Tool XML source as a string

        .. note::
          This method works only on Galaxy 22.01 or later and if the user is a
          Galaxy admin or the Galaxy instance has the
          ``enable_tool_source_display`` option set to ``true`` in the
          ``config/galaxy.yml`` configuration file.
        """
        raw_source_url = self._make_url(tool_id) + "/raw_tool_source"
        ht_response = self._get(url=raw_source_url, json=False)
        return ht_response.text

    def show_tool(self, tool_id: str, io_details: bool = False, link_details: bool = False) -> dict[str, Any]:
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
        params = {
            "io_details": io_details,
            "link_details": link_details,
        }
        return self._get(id=tool_id, params=params)

    def get_tool_tests(self, tool_id: str, tool_version: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch the test case definitions configured for a tool.

        :type tool_id: str
        :param tool_id: id of the requested tool

        :type tool_version: str
        :param tool_version: optional tool version selector. Use ``'*'`` to retrieve
          the tests for all available tool versions.

        :rtype: list
        :return: List of test case definitions.
          For example::

            [
                {
                    "name": "Test-1",
                    "tool_id": "random_lines1",
                    "tool_version": "2.0.2",
                    "inputs": {"num_lines": ["1"], "input": ["1.bed"]},
                    "outputs": [{"name": "out_file1", "value": "1.bed"}],
                    "required_files": [["1.bed", {"value": "1.bed"}]],
                },
                ...
            ]
        """
        params: dict[str, str] = {}
        if tool_version is not None:
            params["tool_version"] = tool_version
        url = self._make_url(tool_id) + "/test_data"
        return self._get(url=url, params=params)

    def build(
        self,
        tool_id: str,
        inputs: dict[str, Any] | None = None,
        tool_version: str | None = None,
        history_id: str | None = None,
    ) -> dict[str, Any]:
        """
        This method returns the tool model, which includes an updated input parameter array for the given tool,
        based on user-defined "inputs".

        :type inputs: dict
        :param inputs: (optional) inputs for the payload.
          For example::

            {
                "num_lines": "1",
                "input": {
                    "values": [
                        {
                            "src": "hda",
                            "id": "4d366c1196c36d18"
                        }
                    ]
                },
                "seed_source|seed_source_selector": "no_seed",
            }

        :type tool_id: str
        :param tool_id: id of the requested tool

        :type history_id: str
        :param history_id: id of the requested history

        :type tool_version: str
        :param tool_version: version of the requested tool

        :rtype: dict
        :return: Returns a tool model including dynamic parameters and updated values, repeats block etc.
          For example::

            {
                "model_class": "Tool",
                "id": "random_lines1",
                "name": "Select random lines",
                "version": "2.0.2",
                "description": "from a file",
                "labels": [],
                "edam_operations": [],
                "edam_topics": [],
                "hidden": "",
                "is_workflow_compatible": True,
                "xrefs": [],
                "config_file": "/Users/joshij/galaxy/tools/filters/randomlines.xml",
                "panel_section_id": "textutil",
                "panel_section_name": "Text Manipulation",
                "form_style": "regular",
                "inputs": [
                    {
                        "model_class": "IntegerToolParameter",
                        "name": "num_lines",
                        "argument": None,
                        "type": "integer",
                        "label": "Randomly select",
                        "help": "lines",
                        "refresh_on_change": False,
                        "min": None,
                        "max": None,
                        "optional": False,
                        "hidden": False,
                        "is_dynamic": False,
                        "value": "1",
                        "area": False,
                        "datalist": [],
                        "default_value": "1",
                        "text_value": "1",
                    },
                ],
                "help": 'This tool selects N random lines from a file, with no repeats, and preserving ordering.',
                "citations": False,
                "sharable_url": None,
                "message": "",
                "warnings": "",
                "versions": ["2.0.2"],
                "requirements": [],
                "errors": {},
                "tool_errors": None,
                "state_inputs": {
                    "num_lines": "1",
                    "input": {"values": [{"id": "4d366c1196c36d18", "src": "hda"}]},
                    "seed_source": {"seed_source_selector": "no_seed", "__current_case__": 0},
                },
                "job_id": None,
                "job_remap": None,
                "history_id": "c9468fdb6dc5c5f1",
                "display": True,
                "action": "/tool_runner/index",
                "license": None,
                "creator": None,
                "method": "post",
                "enctype": "application/x-www-form-urlencoded",
            }

        """
        params: dict[str, str | dict] = {}

        if inputs:
            params["inputs"] = inputs

        if tool_version:
            params["tool_version"] = tool_version

        if history_id:
            params["history_id"] = history_id

        url = f"{self.gi.url}/tools/{tool_id}/build"

        return self._post(payload=params, url=url)

    def run_tool(
        self,
        history_id: str,
        tool_id: str | None = None,
        tool_inputs: InputsBuilder | dict | None = None,
        input_format: Literal["21.01", "legacy"] = "legacy",
        data_manager_mode: Literal["populate", "dry_run", "bundle"] | None = None,
        credentials_context: list[dict[str, Any]] | None = None,
        tool_uuid: str | None = None,
        tool_version: str | None = None,
        *,
        strict: bool = False,
    ) -> dict[str, Any]:
        """
        Runs the tool specified by ``tool_id`` (or ``tool_uuid`` for an
        unprivileged user tool) in the history indicated by ``history_id``
        with inputs from ``dict`` ``tool_inputs``.

        :type history_id: str
        :param history_id: encoded ID of the history in which to run the tool

        :type tool_id: str
        :param tool_id: ID of the tool to be run. Mutually exclusive with
          ``tool_uuid``; one of the two must be provided.

        :type tool_uuid: str
        :param tool_uuid: UUID of an unprivileged user tool to run. Mutually
          exclusive with ``tool_id``.

        :type tool_version: str
        :param tool_version: Optional tool version to pin the run to.

        :type data_manager_mode: str
        :param data_manager_mode: Possible values are 'populate', 'dry_run' and 'bundle'.

          'populate' is the default behavior for data manager tools and results in tool data table
          files being updated after the data manager job completes.

          'dry_run' will skip any processing after the data manager job completes

          'bundle' will create a data manager bundle that can be imported on other Galaxy servers.

        :type credentials_context: list of dicts
        :param credentials_context: list of credential context dicts for tools
          that require credentials (e.g. API keys). Each dict should contain
          ``user_credentials_id``, ``name``, ``version``, and ``selected_group``
          (with ``id`` and ``name`` keys). Obtain credential IDs by storing
          credentials via the Galaxy credentials API first.

        :type tool_inputs: dict
        :param tool_inputs: dictionary of input datasets and parameters
          for the tool (see below)

        :type input_format:  string
        :param input_format: input format for the payload. Possible values are the
          default 'legacy' (where inputs nested inside conditionals
          or repeats are identified with e.g. '<conditional_name>|<input_name>')
          or '21.01' (where inputs inside conditionals or repeats are nested elements).

        :type strict: bool
        :param strict: if ``True``, run the tool through the Tool Request API
          (see :meth:`run_tool_request`), which rejects inputs that do not
          match the tool parameters or have a value of the wrong type with a
          HTTP 400 error, before any job is created. Requires Galaxy 26.0 or
          later and ``input_format='21.01'``. The jobs and outputs are then
          collected with :meth:`get_tool_request_outputs`.

        :rtype: dict
        :return: Information about outputs and job. With ``strict=True``, see
          :meth:`get_tool_request_outputs`.
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
        in the (largely undocumented) format used by the Galaxy API. If you are unsure
        how to construct this dict for the tool you want to run, you can obtain a
        template by executing the ``build()`` method and taking the value of
        ``state_inputs`` from its output, then modifying it as you require.
        You can also check the examples in `Galaxy's API test suite
        <https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy_test/api/test_tools.py>`_.

        .. note::
          By default, Galaxy ignores input names that do not match the tool
          parameters and uses the default values instead. Pass ``strict=True``
          to have such requests rejected. This is expected to become the
          default in a future major release of BioBlend.

        .. versionchanged:: 1.10.0
           Added the ``strict`` parameter.
        """
        if (tool_id is None) == (tool_uuid is None):
            raise ValueError("Exactly one of tool_id or tool_uuid must be provided.")
        if tool_inputs is None:
            raise ValueError("tool_inputs is required.")

        if strict:
            if input_format != "21.01":
                raise ValueError("strict=True requires input_format='21.01' (nested tool_inputs).")
            if self.gi.config.get_version()["version_major"] < "26.0":
                raise ValueError("strict=True requires Galaxy 26.0 or later.")
            tool_request = self.run_tool_request(
                history_id=history_id,
                tool_id=tool_id,
                tool_inputs=tool_inputs,
                tool_version=tool_version,
                tool_uuid=tool_uuid,
                data_manager_mode=data_manager_mode,
                credentials_context=credentials_context,
            )
            return self.get_tool_request_outputs(tool_request)

        payload: dict[str, Any] = {
            "history_id": history_id,
            "input_format": input_format,
        }
        if tool_id is not None:
            payload["tool_id"] = tool_id
        if tool_uuid is not None:
            payload["tool_uuid"] = tool_uuid
        if tool_version is not None:
            payload["tool_version"] = tool_version

        if isinstance(tool_inputs, InputsBuilder):
            payload["inputs"] = tool_inputs.to_dict()
        else:
            payload["inputs"] = tool_inputs

        if data_manager_mode:
            payload["data_manager_mode"] = data_manager_mode

        if credentials_context is not None:
            payload["credentials_context"] = credentials_context

        return self._post(payload)

    def run_tool_request(
        self,
        history_id: str,
        tool_id: str | None = None,
        tool_inputs: InputsBuilder | dict[str, Any] | None = None,
        tool_version: str | None = None,
        tool_uuid: str | None = None,
        strict: bool = True,
        wait: bool = True,
        maxwait: float = 12000,
        interval: float = 3,
        data_manager_mode: Literal["populate", "dry_run", "bundle"] | None = None,
        credentials_context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Run a tool through the Tool Request API (``POST /api/jobs``).

        Differently from the endpoint used by default by :meth:`run_tool`,
        Galaxy validates the request against the tool parameters and rejects
        inputs that do not match them, or have a value of the wrong type, with
        a HTTP 400 error before creating any job.

        :type history_id: str
        :param history_id: encoded ID of the history in which to run the tool

        :type tool_id: str
        :param tool_id: ID of the tool to be run. Mutually exclusive with
          ``tool_uuid``; one of the two must be provided.

        :type tool_inputs: dict
        :param tool_inputs: input datasets and parameters for the tool in the
          nested format (see ``input_format='21.01'`` in :meth:`run_tool`), or
          an :class:`~bioblend.galaxy.tools.inputs.InputsBuilder`. Values must
          have the proper type, e.g. an ``int`` for an integer parameter.

        :type tool_version: str
        :param tool_version: Optional tool version to pin the run to.

        :type tool_uuid: str
        :param tool_uuid: UUID of an unprivileged user tool to run. Mutually
          exclusive with ``tool_id``.

        :type strict: bool
        :param strict: whether Galaxy should validate the inputs strictly

        :type wait: bool
        :param wait: whether to wait for Galaxy to process the request, i.e.
          to create the jobs

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the request to be
          processed. After this time, a ``TimeoutException`` will be raised.

        :type interval: float
        :param interval: Time (in seconds) to wait between 2 consecutive checks.

        :type data_manager_mode: str
        :param data_manager_mode: see :meth:`run_tool`. Requires Galaxy 26.1
          or later.

        :type credentials_context: list of dicts
        :param credentials_context: see :meth:`run_tool`. Requires Galaxy 26.1
          or later.

        :rtype: dict
        :return: If ``wait`` is ``True``, the processed tool request (see
          :meth:`get_tool_request`), otherwise a dict with the
          ``tool_request_id``.

        :raises ToolRequestFailedException: if Galaxy fails to process the
          request

        .. note::
          This method works only on Galaxy 26.0 or later.
        """
        if (tool_id is None) == (tool_uuid is None):
            raise ValueError("Exactly one of tool_id or tool_uuid must be provided.")
        if tool_inputs is None:
            raise ValueError("tool_inputs is required.")
        # Galaxy 26.0 would silently ignore these options
        if (data_manager_mode or credentials_context is not None) and self.gi.config.get_version()[
            "version_major"
        ] < "26.1":
            raise ValueError("data_manager_mode and credentials_context require Galaxy 26.1 or later.")

        payload: dict[str, Any] = {
            "history_id": history_id,
            "strict": strict,
            "inputs": tool_inputs.to_nested_dict() if isinstance(tool_inputs, InputsBuilder) else tool_inputs,
        }
        if tool_id is not None:
            payload["tool_id"] = tool_id
        if tool_uuid is not None:
            payload["tool_uuid"] = tool_uuid
        if tool_version is not None:
            payload["tool_version"] = tool_version
        if data_manager_mode:
            payload["data_manager_mode"] = data_manager_mode
        if credentials_context is not None:
            payload["credentials_context"] = credentials_context

        response = self._post(payload, url=f"{self.gi.url}/jobs")
        if not wait:
            return response
        return self.wait_for_tool_request(response["tool_request_id"], maxwait=maxwait, interval=interval)

    def get_tool_request(self, tool_request_id: str) -> dict[str, Any]:
        """
        Get details of a tool request, see :meth:`run_tool_request`.

        :type tool_request_id: str
        :param tool_request_id: encoded ID of the tool request

        :rtype: dict
        :return: Details of the tool request. For example::

            {'id': 'f2db41e1fa331b3e',
             'implicit_collections': [],
             'jobs': [{'id': '7dd125b61b35d782', 'src': 'job'}],
             'request': {'input': {'id': '4d366c1196c36d18', 'src': 'hda'},
                         'num_lines': 1},
             'state': 'submitted',
             'state_message': None}

          ``state`` is ``new`` until Galaxy has processed the request, then
          ``submitted`` or ``failed``.

        .. note::
          This method works only on Galaxy 26.0 or later.
        """
        return self._get(url=f"{self.gi.url}/tool_requests/{tool_request_id}")

    def wait_for_tool_request(
        self, tool_request_id: str, maxwait: float = 12000, interval: float = 3
    ) -> dict[str, Any]:
        """
        Wait until Galaxy has processed a tool request, see
        :meth:`run_tool_request`.

        :type tool_request_id: str
        :param tool_request_id: encoded ID of the tool request

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the request to be
          processed. After this time, a ``TimeoutException`` will be raised.

        :type interval: float
        :param interval: Time (in seconds) to wait between 2 consecutive checks.

        :rtype: dict
        :return: Details of the tool request, see :meth:`get_tool_request`.

        :raises ToolRequestFailedException: if Galaxy fails to process the
          request

        .. note::
          This method works only on Galaxy 26.0 or later.
        """

        def check_and_get_tool_request() -> dict[str, Any]:
            tool_request = self.get_tool_request(tool_request_id)
            if tool_request["state"] == "new":
                raise NotReady(f"Tool request {tool_request_id} has not been processed yet")
            if tool_request["state"] == "failed":
                raise ToolRequestFailedException(tool_request)
            return tool_request

        return wait_on(check_and_get_tool_request, maxwait=maxwait, interval=interval)

    def get_tool_request_outputs(self, tool_request: dict[str, Any]) -> dict[str, Any]:
        """
        Get the jobs and outputs created by a processed tool request, with the
        same keys returned by :meth:`run_tool`.

        :type tool_request: dict
        :param tool_request: a tool request in state ``submitted``, as
          returned by :meth:`run_tool_request` or :meth:`get_tool_request`

        :rtype: dict
        :return: A dict with ``jobs``, ``outputs``, ``output_collections``,
          ``implicit_collections`` and ``tool_request_id`` keys. Jobs, datasets
          and collections are as returned by the respective ``show_*()``
          methods, with the ``output_name`` added to each output.

        .. note::
          This method works only on Galaxy 26.0 or later. It makes one request
          per job and one per output.
        """
        if tool_request["state"] != "submitted":
            raise ValueError(f"Tool request {tool_request['id']} is in state {tool_request['state']}")

        rval: dict[str, Any] = {
            "outputs": [],
            "output_collections": [],
            "jobs": [],
            "implicit_collections": [],
            "tool_request_id": tool_request["id"],
        }
        for job_ref in tool_request["jobs"]:
            job = self.gi.jobs.show_job(job_ref["id"])
            rval["jobs"].append(job)
            for output_name, dataset_ref in job.get("outputs", {}).items():
                dataset = self.gi.datasets.show_dataset(dataset_ref["id"], hda_ldda=dataset_ref.get("src", "hda"))
                dataset["output_name"] = output_name
                rval["outputs"].append(dataset)
            for output_name, collection_ref in job.get("output_collections", {}).items():
                collection = self.gi.dataset_collections.show_dataset_collection(collection_ref["id"])
                collection["output_name"] = output_name
                rval["output_collections"].append(collection)
        for collection_ref in tool_request["implicit_collections"]:
            collection = self.gi.dataset_collections.show_dataset_collection(collection_ref["id"])
            collection["output_name"] = collection_ref["output_name"]
            rval["implicit_collections"].append(collection)
        return rval

    def upload_file(
        self,
        path: str,
        history_id: str,
        storage: str | None = None,
        metadata: dict | None = None,
        chunk_size: int | None = UPLOAD_CHUNK_SIZE,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Upload the file specified by ``path`` to the history specified by
        ``history_id``.

        :type path: str
        :param path: path of the file to upload

        :type history_id: str
        :param history_id: id of the history where to upload the file

        :type storage: str
        :param storage: Local path to store URLs resuming uploads

        :type metadata: dict
        :param metadata: Metadata to send with upload request

        :type chunk_size: int
        :param chunk_size: Number of bytes to send in each chunk

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

        :type auto_decompress: bool
        :param auto_decompress: Automatically decompress files if the uploaded
          file is compressed and the file type is not one that supports
          compression (e.g. ``fastqsanger.gz``). Default is ``False``.

        :rtype: dict
        :return: Information about the created upload job

        .. note::
          The following parameters work only on Galaxy 22.01 or later:
          ``storage``, ``metadata``, ``chunk_size``, ``auto_decompress``.
        """
        if self.gi.config.get_version()["version_major"] >= "22.01":
            # Use the tus protocol
            uploader = self.gi.get_tus_uploader(path, storage=storage, metadata=metadata, chunk_size=chunk_size)
            uploader.upload()
            return self.post_to_fetch(path, history_id, uploader.session_id, **kwargs)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        else:
            if "file_name" not in kwargs:
                kwargs["file_name"] = basename(path)
            payload = self._upload_payload(history_id, **kwargs)
            payload["files_0|file_data"] = attach_file(path, name=kwargs["file_name"])
            try:
                return self._post(payload, files_attached=True)
            finally:
                payload["files_0|file_data"].close()

    def post_to_fetch(self, path: str, history_id: str, session_id: str, **kwargs: Any) -> dict[str, Any]:
        """
        Make a POST request to the Fetch API after performing a tus upload.

        This is called by :meth:`upload_file` after performing an upload. This
        method is useful if you want to control the tus uploader yourself (e.g.
        to report on progress)::

            uploader = gi.get_tus_uploader(path, storage=storage)
            while uploader.offset < uploader.file_size:
                uploader.upload_chunk()
                # perform other actions...
            gi.tools.post_to_fetch(path, history_id, uploader.session_id, **upload_kwargs)

        :type session_id: str
        :param session_id: Session ID returned by the tus service

        :rtype: dict
        :return: Information about the created upload job

        See :meth:`upload_file` for additional parameters.
        """
        payload = self._fetch_payload(path, history_id, session_id, **kwargs)
        url = f"{self.gi.url}/tools/fetch"
        return self._post(payload, url=url)

    def upload_from_ftp(self, path: str, history_id: str, **kwargs: Any) -> dict[str, Any]:
        """
        Upload the file specified by ``path`` from the user's FTP directory to
        the history specified by ``history_id``.

        :type path: str
        :param path: path of the file in the user's FTP directory

        :type history_id: str
        :param history_id: id of the history where to upload the file

        :rtype: dict
        :return: Information about the created upload job

        See :meth:`upload_file` for the optional parameters.
        """
        payload = self._upload_payload(history_id, **kwargs)
        payload["files_0|ftp_files"] = path
        return self._post(payload)

    def paste_content(self, content: str, history_id: str, **kwargs: Any) -> dict[str, Any]:
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
        payload = self._upload_payload(history_id, **kwargs)
        payload["files_0|url_paste"] = content
        return self._post(payload, files_attached=False)

    put_url = paste_content

    def _upload_payload(self, history_id: str, **kwargs: Any) -> dict[str, Any]:
        tool_input: dict[str, Any] = {
            "file_type": kwargs.get("file_type", "auto"),
            "dbkey": kwargs.get("dbkey", "?"),
            "files_0|type": "upload_dataset",
        }
        if not kwargs.get("to_posix_lines", True):
            tool_input["files_0|to_posix_lines"] = False
        elif kwargs.get("space_to_tab", False):
            tool_input["files_0|space_to_tab"] = "Yes"
        if "file_name" in kwargs:
            tool_input["files_0|NAME"] = kwargs["file_name"]
        return {
            "history_id": history_id,
            "tool_id": kwargs.get("tool_id", "upload1"),
            "inputs": tool_input,
        }

    def _fetch_payload(self, path: str, history_id: str, session_id: str, **kwargs: Any) -> dict:
        file_name = kwargs.get("file_name", basename(path))
        element = {
            "src": "files",
            "ext": kwargs.get("file_type", "auto"),
            "dbkey": kwargs.get("dbkey", "?"),
            "to_posix_lines": kwargs.get("to_posix_lines", True),
            "space_to_tab": kwargs.get("space_to_tab", False),
            "name": file_name,
        }
        payload = {
            "history_id": history_id,
            "targets": [
                {
                    "destination": {"type": "hdas"},
                    "elements": [element],
                }
            ],
            "files_0|file_data": {"session_id": session_id, "name": file_name},
            "auto_decompress": kwargs.get("auto_decompress", False),
        }
        return payload
