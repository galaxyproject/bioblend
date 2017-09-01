"""
Contains possible interactions with the Galaxy Workflows
"""
import json
import os

from bioblend.galaxy.client import Client


class WorkflowClient(Client):
    def __init__(self, galaxy_instance):
        self.module = 'workflows'
        super(WorkflowClient, self).__init__(galaxy_instance)

    # the 'deleted' option is not available for workflows
    def get_workflows(self, workflow_id=None, name=None, published=False):
        """
        Get all workflows or filter the specific one(s) via the provided ``name``
        or ``workflow_id``. Provide only one argument, ``name`` or ``workflow_id``,
        but not both.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID (incompatible with ``name``)

        :type name: str
        :param name: Filter by name of workflow (incompatible with
          ``workflow_id``). If multiple names match the given name, all the
          workflows matching the argument will be returned.

        :type published: bool
        :param published: if ``True``, return also published workflows

        :rtype: list
        :return: A list of workflow dicts.
                 For example::

                   [{u'id': u'92c56938c2f9b315',
                     u'name': u'Simple',
                     u'url': u'/api/workflows/92c56938c2f9b315'}]

        """
        if workflow_id is not None and name is not None:
            raise ValueError('Provide only one argument between name or workflow_id, but not both')
        params = {}
        if published:
            params['show_published'] = 'True'
        workflows = self._get(params=params)
        if workflow_id is not None:
            workflow = next((_ for _ in workflows if _['id'] == workflow_id), None)
            workflows = [workflow] if workflow is not None else []
        elif name is not None:
            workflows = [_ for _ in workflows if _['name'] == name]
        return workflows

    def show_workflow(self, workflow_id):
        """
        Display information needed to run a workflow.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :rtype: dict
        :return: A description of the workflow and its inputs.
          For example::

            {u'id': u'92c56938c2f9b315',
             u'inputs': {u'23': {u'label': u'Input Dataset', u'value': u''}},
             u'name': u'Simple',
             u'url': u'/api/workflows/92c56938c2f9b315'}
        """
        return self._get(id=workflow_id)

    def get_workflow_inputs(self, workflow_id, label):
        """
        Get a list of workflow input IDs that match the given label.
        If no input matches the given label, an empty list is returned.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :type label: str
        :param label: label to filter workflow inputs on

        :rtype: list
        :return: list of workflow inputs matching the label query
        """
        wf = self._get(id=workflow_id)
        inputs = wf['inputs']
        return [id for id in inputs if inputs[id]['label'] == label]

    def import_workflow_dict(self, workflow_dict, publish=False):
        """
        Imports a new workflow given a dictionary representing a previously
        exported workflow.

        :type workflow_dict: dict
        :param workflow_dict: dictionary representing the workflow to be imported

        :type publish: bool
        :param publish:  if ``True`` the uploaded workflow will be published;
                         otherwise it will be visible only by the user which uploads it (default)
        """
        payload = {'workflow': workflow_dict, 'publish': publish}

        url = self.gi._make_url(self)
        url = _join(url, "upload")
        return self._post(url=url, payload=payload)

    def import_workflow_json(self, workflow_json):
        """
        .. deprecated:: 0.9.0
           Use :meth:`import_workflow_dict` instead.

        :type workflow_json: dict
        :param workflow_json: dictionary representing the workflow to be imported
        """
        return self.import_workflow_dict(workflow_json)

    def import_workflow_from_local_path(self, file_local_path, publish=False):
        """
        Imports a new workflow given the path to a file containing a previously
        exported workflow.

        :type file_local_path: str
        :param file_local_path: File to upload to the server for new workflow

        :type publish: bool
        :param publish:  if ``True`` the uploaded workflow will be published;
                         otherwise it will be visible only by the user which uploads it (default)

        """
        with open(file_local_path, 'r') as fp:
            workflow_json = json.load(fp)

        return self.import_workflow_dict(workflow_json, publish)

    def import_shared_workflow(self, workflow_id):
        """
        Imports a new workflow from the shared published workflows.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :rtype: dict
        :return: A description of the workflow.
          For example::

            {u'id': u'ee0e2b4b696d9092',
             u'model_class': u'StoredWorkflow',
             u'name': u'Super workflow that solves everything!',
             u'published': False,
             u'tags': [],
             u'url': u'/api/workflows/ee0e2b4b696d9092'}
        """
        payload = {'shared_workflow_id': workflow_id}
        url = self.gi._make_url(self)
        return self._post(url=url, payload=payload)

    def export_workflow_dict(self, workflow_id):
        """
        Exports a workflow.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :rtype: dict
        :return: Dictionary representing the requested workflow
        """
        url = self.gi._make_url(self)
        url = _join(url, "download", workflow_id)
        return self._get(url=url)

    def export_workflow_json(self, workflow_id):
        """
        .. deprecated:: 0.9.0
           Use :meth:`export_workflow_dict` instead.
        """
        return self.export_workflow_dict(workflow_id)

    def export_workflow_to_local_path(self, workflow_id, file_local_path, use_default_filename=True):
        """
        Exports a workflow in JSON format to a given local path.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :type file_local_path: str
        :param file_local_path: Local path to which the exported file will be saved.
                                (Should not contain filename if use_default_name=True)

        :type use_default_filename: bool
        :param use_default_filename: If the use_default_name parameter is True, the exported
          file will be saved as file_local_path/Galaxy-Workflow-%s.ga, where %s
          is the workflow name. If use_default_name is False, file_local_path
          is assumed to contain the full file path including filename.
        """
        workflow_dict = self.export_workflow_dict(workflow_id)

        if use_default_filename:
            filename = 'Galaxy-Workflow-%s.ga' % workflow_dict['name']
            file_local_path = os.path.join(file_local_path, filename)

        with open(file_local_path, 'w') as fp:
            json.dump(workflow_dict, fp)

    def run_workflow(self, workflow_id, dataset_map=None, params=None,
                     history_id=None, history_name=None,
                     import_inputs_to_history=False, replacement_params=None):
        """
        Run the workflow identified by ``workflow_id``.

        .. deprecated:: 0.7.0
           Use :meth:`invoke_workflow` instead.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :type dataset_map: dict
        :param dataset_map: A mapping of workflow inputs to datasets. The datasets
                            source can be a LibraryDatasetDatasetAssociation (``ldda``),
                            LibraryDataset (``ld``), or HistoryDatasetAssociation (``hda``).
                            The map must be in the following format:
                            ``{'<input>': {'id': <encoded dataset ID>, 'src': '[ldda, ld, hda]'}}``
                            (e.g. ``{'23': {'id': '29beef4fadeed09f', 'src': 'ld'}}``)

        :type params: dict
        :param params: A mapping of non-datasets tool parameters (see below)

        :type history_id: str
        :param history_id: The encoded history ID where to store the workflow
          output. Alternatively, ``history_name`` may be specified to create a
          new history.

        :type history_name: str
        :param history_name: Create a new history with the given name to store
          the workflow output. If both ``history_id`` and ``history_name`` are
          provided, ``history_name`` is ignored. If neither is specified, a new
          'Unnamed history' is created.

        :type import_inputs_to_history: bool
        :param import_inputs_to_history: If ``True``, used workflow inputs will be imported
                                         into the history. If ``False``, only workflow outputs
                                         will be visible in the given history.

        :type replacement_params: dict
        :param replacement_params: pattern-based replacements for post-job actions (see below)

        :rtype: dict
        :return: A dict containing the history ID where the outputs are placed
          as well as output dataset IDs. For example::

            {u'history': u'64177123325c9cfd',
             u'outputs': [u'aa4d3084af404259']}

        The ``params`` dict should be specified as follows::

          {STEP_ID: PARAM_DICT, ...}

        where PARAM_DICT is::

          {PARAM_NAME: VALUE, ...}

        For backwards compatibility, the following (deprecated) format is
        also supported for ``params``::

          {TOOL_ID: PARAM_DICT, ...}

        in which case PARAM_DICT affects all steps with the given tool id.
        If both by-tool-id and by-step-id specifications are used, the
        latter takes precedence.

        Finally (again, for backwards compatibility), PARAM_DICT can also
        be specified as::

          {'param': PARAM_NAME, 'value': VALUE}

        Note that this format allows only one parameter to be set per step.

        The ``replacement_params`` dict should map parameter names in
        post-job actions (PJAs) to their runtime values. For
        instance, if the final step has a PJA like the following::

          {u'RenameDatasetActionout_file1': {u'action_arguments': {u'newname': u'${output}'},
            u'action_type': u'RenameDatasetAction',
            u'output_name': u'out_file1'}}

        then the following renames the output dataset to 'foo'::

          replacement_params = {'output': 'foo'}

        see also `this email thread
        <http://lists.bx.psu.edu/pipermail/galaxy-dev/2011-September/006875.html>`_.

        .. warning::
            This method waits for the whole workflow to be scheduled before
            returning and does not scale to large workflows as a result. This
            method has therefore been deprecated in favor of
            :meth:`invoke_workflow`, which also features improved default
            behavior for dataset input handling.
        """
        payload = {'workflow_id': workflow_id}
        if dataset_map:
            payload['ds_map'] = dataset_map

        if params:
            payload['parameters'] = params

        if replacement_params:
            payload['replacement_params'] = replacement_params

        if history_id:
            payload['history'] = 'hist_id={0}'.format(history_id)
        elif history_name:
            payload['history'] = history_name
        if import_inputs_to_history is False:
            payload['no_add_to_history'] = True
        return self._post(payload)

    def invoke_workflow(self, workflow_id, inputs=None, params=None,
                        history_id=None, history_name=None,
                        import_inputs_to_history=False, replacement_params=None,
                        allow_tool_state_corrections=None):
        """
        Invoke the workflow identified by ``workflow_id``. This will
        cause a workflow to be scheduled and return an object describing
        the workflow invocation.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :type inputs: dict
        :param inputs: A mapping of workflow inputs to datasets and dataset collections.
                       The datasets source can be a LibraryDatasetDatasetAssociation (``ldda``),
                       LibraryDataset (``ld``), HistoryDatasetAssociation (``hda``), or
                       HistoryDatasetCollectionAssociation (``hdca``).

                       The map must be in the following format:
                       ``{'<input_index>': {'id': <encoded dataset ID>, 'src': '[ldda, ld, hda, hdca]'}}``
                       (e.g. ``{'2': {'id': '29beef4fadeed09f', 'src': 'hda'}}``)

                       This map may also be indexed by the UUIDs of the workflow steps,
                       as indicated by the ``uuid`` property of steps returned from the
                       Galaxy API.

        :type params: dict
        :param params: A mapping of non-datasets tool parameters (see below)

        :type history_id: str
        :param history_id: The encoded history ID where to store the workflow
          output. Alternatively, ``history_name`` may be specified to create a
          new history.

        :type history_name: str
        :param history_name: Create a new history with the given name to store
          the workflow output. If both ``history_id`` and ``history_name`` are
          provided, ``history_name`` is ignored. If neither is specified, a new
          'Unnamed history' is created.

        :type import_inputs_to_history: bool
        :param import_inputs_to_history: If ``True``, used workflow inputs will
          be imported into the history. If ``False``, only workflow outputs will
          be visible in the given history.

        :type allow_tool_state_corrections: bool
        :param allow_tool_state_corrections: If True, allow Galaxy to fill in
          missing tool state when running workflows. This may be useful for
          workflows using tools that have changed over time or for workflows
          built outside of Galaxy with only a subset of inputs defined.

        :type replacement_params: dict
        :param replacement_params: pattern-based replacements for post-job
          actions (see below)

        :rtype: dict
        :return: A dict containing the workflow invocation describing the
          scheduling of the workflow. For example::

            {u'history_id': u'2f94e8ae9edff68a',
             u'id': u'df7a1f0c02a5b08e',
             u'inputs': {u'0': {u'id': u'a7db2fac67043c7e',
               u'src': u'hda',
               u'uuid': u'7932ffe0-2340-4952-8857-dbaa50f1f46a'}},
             u'model_class': u'WorkflowInvocation',
             u'state': u'ready',
             u'steps': [{u'action': None,
               u'id': u'd413a19dec13d11e',
               u'job_id': None,
               u'model_class': u'WorkflowInvocationStep',
               u'order_index': 0,
               u'state': None,
               u'update_time': u'2015-10-31T22:00:26',
               u'workflow_step_id': u'cbbbf59e8f08c98c',
               u'workflow_step_label': None,
               u'workflow_step_uuid': u'b81250fd-3278-4e6a-b269-56a1f01ef485'},
              {u'action': None,
               u'id': u'2f94e8ae9edff68a',
               u'job_id': u'e89067bb68bee7a0',
               u'model_class': u'WorkflowInvocationStep',
               u'order_index': 1,
               u'state': u'new',
               u'update_time': u'2015-10-31T22:00:26',
               u'workflow_step_id': u'964b37715ec9bd22',
               u'workflow_step_label': None,
               u'workflow_step_uuid': u'e62440b8-e911-408b-b124-e05435d3125e'}],
             u'update_time': u'2015-10-31T22:00:26',
             u'uuid': u'c8aa2b1c-801a-11e5-a9e5-8ca98228593c',
             u'workflow_id': u'03501d7626bd192f'}

        The ``params`` dict should be specified as follows::

          {STEP_ID: PARAM_DICT, ...}

        where PARAM_DICT is::

          {PARAM_NAME: VALUE, ...}

        For backwards compatibility, the following (deprecated) format is
        also supported for ``params``::

          {TOOL_ID: PARAM_DICT, ...}

        in which case PARAM_DICT affects all steps with the given tool id.
        If both by-tool-id and by-step-id specifications are used, the
        latter takes precedence.

        Finally (again, for backwards compatibility), PARAM_DICT can also
        be specified as::

          {'param': PARAM_NAME, 'value': VALUE}

        Note that this format allows only one parameter to be set per step.

        The ``replacement_params`` dict should map parameter names in
        post-job actions (PJAs) to their runtime values. For
        instance, if the final step has a PJA like the following::

          {u'RenameDatasetActionout_file1': {u'action_arguments': {u'newname': u'${output}'},
            u'action_type': u'RenameDatasetAction',
            u'output_name': u'out_file1'}}

        then the following renames the output dataset to 'foo'::

          replacement_params = {'output': 'foo'}

        see also `this email thread
        <http://lists.bx.psu.edu/pipermail/galaxy-dev/2011-September/006875.html>`_.

        .. warning::
          Historically, the ``run_workflow`` method consumed a ``dataset_map``
          data structure that was indexed by unencoded workflow step IDs. These
          IDs would not be stable across Galaxy instances. The new ``inputs``
          property is instead indexed by either the ``order_index`` property
          (which is stable across workflow imports) or the step UUID which is
          also stable.
        """
        payload = {'workflow_id': workflow_id}
        if inputs:
            payload['inputs'] = inputs

        if params:
            payload['parameters'] = params

        if replacement_params:
            payload['replacement_params'] = replacement_params

        if history_id:
            payload['history'] = 'hist_id={0}'.format(history_id)
        elif history_name:
            payload['history'] = history_name
        if import_inputs_to_history is False:
            payload['no_add_to_history'] = True
        if allow_tool_state_corrections is not None:
            payload['allow_tool_state_corrections'] = allow_tool_state_corrections
        url = self.gi._make_url(self)
        url = _join(url, workflow_id, "invocations")
        return self._post(payload, url=url)

    def show_invocation(self, workflow_id, invocation_id):
        """
        Get a workflow invocation object representing the scheduling of a
        workflow. This object may be sparse at first (missing inputs and
        invocation steps) and will become more populated as the workflow is
        actually scheduled.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :rtype: dict
        :return: The workflow invocation.
          For example::

            {u'history_id': u'2f94e8ae9edff68a',
             u'id': u'df7a1f0c02a5b08e',
             u'inputs': {u'0': {u'id': u'a7db2fac67043c7e',
               u'src': u'hda',
               u'uuid': u'7932ffe0-2340-4952-8857-dbaa50f1f46a'}},
             u'model_class': u'WorkflowInvocation',
             u'state': u'ready',
             u'steps': [{u'action': None,
               u'id': u'd413a19dec13d11e',
               u'job_id': None,
               u'model_class': u'WorkflowInvocationStep',
               u'order_index': 0,
               u'state': None,
               u'update_time': u'2015-10-31T22:00:26',
               u'workflow_step_id': u'cbbbf59e8f08c98c',
               u'workflow_step_label': None,
               u'workflow_step_uuid': u'b81250fd-3278-4e6a-b269-56a1f01ef485'},
              {u'action': None,
               u'id': u'2f94e8ae9edff68a',
               u'job_id': u'e89067bb68bee7a0',
               u'model_class': u'WorkflowInvocationStep',
               u'order_index': 1,
               u'state': u'new',
               u'update_time': u'2015-10-31T22:00:26',
               u'workflow_step_id': u'964b37715ec9bd22',
               u'workflow_step_label': None,
               u'workflow_step_uuid': u'e62440b8-e911-408b-b124-e05435d3125e'}],
             u'update_time': u'2015-10-31T22:00:26',
             u'uuid': u'c8aa2b1c-801a-11e5-a9e5-8ca98228593c',
             u'workflow_id': u'03501d7626bd192f'}
        """
        url = self._invocation_url(workflow_id, invocation_id)
        return self._get(url=url)

    def get_invocations(self, workflow_id):
        """
        Get a list containing all the workflow invocations corresponding to the
        specified workflow.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :rtype: list
        :return: A list of workflow invocations.
          For example::

            [{u'history_id': u'2f94e8ae9edff68a',
              u'id': u'df7a1f0c02a5b08e',
              u'model_class': u'WorkflowInvocation',
              u'state': u'new',
              u'update_time': u'2015-10-31T22:00:22',
              u'uuid': u'c8aa2b1c-801a-11e5-a9e5-8ca98228593c',
              u'workflow_id': u'03501d7626bd192f'}]
        """
        url = self._invocations_url(workflow_id)
        return self._get(url=url)

    def cancel_invocation(self, workflow_id, invocation_id):
        """
        Cancel the scheduling of a workflow.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID
        """
        url = self._invocation_url(workflow_id, invocation_id)
        return self._delete(url=url)

    def show_invocation_step(self, workflow_id, invocation_id, step_id):
        """
        See the details of a particular workflow invocation step.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :type step_id: str
        :param step_id: Encoded workflow invocation step ID

        :rtype: dict
        :return: The workflow invocation step.
          For example::

            {u'action': None,
             u'id': u'63cd3858d057a6d1',
             u'job_id': None,
             u'model_class': u'WorkflowInvocationStep',
             u'order_index': 2,
             u'state': None,
             u'update_time': u'2015-10-31T22:11:14',
             u'workflow_step_id': u'52e496b945151ee8',
             u'workflow_step_label': None,
             u'workflow_step_uuid': u'4060554c-1dd5-4287-9040-8b4f281cf9dc'}
        """
        url = self._invocation_step_url(workflow_id, invocation_id, step_id)
        return self._get(url=url)

    def run_invocation_step_action(self, workflow_id, invocation_id, step_id, action):
        """ Execute an action for an active workflow invocation step. The
        nature of this action and what is expected will vary based on the
        the type of workflow step (the only currently valid action is True/False
        for pause steps).

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :type step_id: str
        :param step_id: Encoded workflow invocation step ID

        :type action: object
        :param action: Action to use when updating state, semantics depends on
           step type.

        """
        url = self._invocation_step_url(workflow_id, invocation_id, step_id)
        payload = {"action": action}
        return self._put(payload=payload, url=url)

    def delete_workflow(self, workflow_id):
        """
        Delete a workflow identified by `workflow_id`.

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID

        .. warning::
            Deleting a workflow is irreversible - all workflow data
            will be permanently deleted.
        """
        return self._delete(id=workflow_id)

    def _invocation_step_url(self, workflow_id, invocation_id, step_id):
        return _join(self._invocation_url(workflow_id, invocation_id), "steps", step_id)

    def _invocation_url(self, workflow_id, invocation_id):
        return _join(self._invocations_url(workflow_id), invocation_id)

    def _invocations_url(self, workflow_id):
        return _join(self._workflow_url(workflow_id), "invocations")

    def _workflow_url(self, workflow_id):
        url = self.gi._make_url(self)
        url = _join(url, workflow_id)
        return url


def _join(*args):
    return "/".join(args)


__all__ = ('WorkflowClient',)
