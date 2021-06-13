"""
Contains possible interactions with the Galaxy workflow invocations
"""
import logging
import time
from typing import (
    Optional,
)

from bioblend import (
    CHUNK_SIZE,
    TimeoutException,
)
from bioblend.galaxy.client import Client

log = logging.getLogger(__name__)

INVOCATION_TERMINAL_STATES = {'cancelled', 'failed', 'scheduled'}
# Invocation non-terminal states are: 'new', 'ready'


class InvocationClient(Client):
    module = 'invocations'

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def get_invocations(self, workflow_id=None, history_id=None, user_id=None,
                        include_terminal=True, limit=None, view='collection',
                        step_details=False):
        """
        Get all workflow invocations, or select a subset by specifying optional
        arguments for filtering (e.g. a workflow ID).

        :type workflow_id: str
        :param workflow_id: Encoded workflow ID to filter on

        :type history_id: str
        :param history_id: Encoded history ID to filter on

        :type user_id: str
        :param user_id: Encoded user ID to filter on. This must be
                        your own user ID if your are not an admin user.

        :type include_terminal: bool
        :param include_terminal: Whether to include terminal states.

        :type limit: int
        :param limit: Maximum number of invocations to return - if specified,
                      the most recent invocations will be returned.

        :type view: str
        :param view: Level of detail to return per invocation, either
                     'element' or 'collection'.

        :type step_details: bool
        :param step_details: If 'view' is 'element', also include details
                             on individual steps.

        :rtype: list
        :return: A list of workflow invocations.
          For example::

            [{'history_id': '2f94e8ae9edff68a',
              'id': 'df7a1f0c02a5b08e',
              'model_class': 'WorkflowInvocation',
              'state': 'new',
              'update_time': '2015-10-31T22:00:22',
              'uuid': 'c8aa2b1c-801a-11e5-a9e5-8ca98228593c',
              'workflow_id': '03501d7626bd192f'}]
        """
        params = {
            'include_terminal': include_terminal,
            'view': view,
            'step_details': step_details
        }
        if workflow_id:
            params['workflow_id'] = workflow_id
        if history_id:
            params['history_id'] = history_id
        if user_id:
            params['user_id'] = user_id
        if limit is not None:
            params['limit'] = limit
        return self._get(params=params)

    def show_invocation(self, invocation_id):
        """
        Get a workflow invocation dictionary representing the scheduling of a
        workflow. This dictionary may be sparse at first (missing inputs and
        invocation steps) and will become more populated as the workflow is
        actually scheduled.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :rtype: dict
        :return: The workflow invocation.
          For example::

            {'history_id': '2f94e8ae9edff68a',
             'id': 'df7a1f0c02a5b08e',
             'inputs': {'0': {'id': 'a7db2fac67043c7e',
               'src': 'hda',
               'uuid': '7932ffe0-2340-4952-8857-dbaa50f1f46a'}},
             'model_class': 'WorkflowInvocation',
             'state': 'ready',
             'steps': [{'action': None,
               'id': 'd413a19dec13d11e',
               'job_id': None,
               'model_class': 'WorkflowInvocationStep',
               'order_index': 0,
               'state': None,
               'update_time': '2015-10-31T22:00:26',
               'workflow_step_id': 'cbbbf59e8f08c98c',
               'workflow_step_label': None,
               'workflow_step_uuid': 'b81250fd-3278-4e6a-b269-56a1f01ef485'},
              {'action': None,
               'id': '2f94e8ae9edff68a',
               'job_id': 'e89067bb68bee7a0',
               'model_class': 'WorkflowInvocationStep',
               'order_index': 1,
               'state': 'new',
               'update_time': '2015-10-31T22:00:26',
               'workflow_step_id': '964b37715ec9bd22',
               'workflow_step_label': None,
               'workflow_step_uuid': 'e62440b8-e911-408b-b124-e05435d3125e'}],
             'update_time': '2015-10-31T22:00:26',
             'uuid': 'c8aa2b1c-801a-11e5-a9e5-8ca98228593c',
             'workflow_id': '03501d7626bd192f'}
        """
        url = self._make_url(invocation_id)
        return self._get(url=url)

    def rerun_invocation(self, invocation_id: str, inputs_update: Optional[dict] = None,
                         params_update: Optional[dict] = None, history_id: Optional[str] = None,
                         history_name: Optional[str] = None, import_inputs_to_history: bool = False,
                         replacement_params: Optional[dict] = None, allow_tool_state_corrections: bool = False,
                         inputs_by: Optional[str] = None, parameters_normalized: bool = False):
        """
        Rerun a workflow invocation. For more extensive documentation of all
        parameters, see the ``gi.workflows.invoke_workflow()`` method.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID to be rerun

        :type inputs_update: dict
        :param inputs_update: If different datasets should be used to the original
          invocation, this should contain a mapping of workflow inputs to the new
          datasets and dataset collections.

        :type params_update: dict
        :param params_update: If different non-dataset tool parameters should be
          used to the original invocation, this should contain a mapping of the
          new parameter values.

        :type history_id: str
        :param history_id: The encoded history ID where to store the workflow
          outputs. Alternatively, ``history_name`` may be specified to create a
          new history.

        :type history_name: str
        :param history_name: Create a new history with the given name to store
          the workflow outputs. If both ``history_id`` and ``history_name`` are
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
          actions

        :type inputs_by: str
        :param inputs_by: Determines how inputs are referenced. Can be
          "step_index|step_uuid" (default), "step_index", "step_id", "step_uuid", or "name".

        :type parameters_normalized: bool
        :param parameters_normalized: Whether Galaxy should normalize the input
          parameters to ensure everything is referenced by a numeric step ID.
          Default is ``False``, but when setting parameters for a subworkflow,
          ``True`` is required.

        :rtype: dict
        :return: A dict describing the new workflow invocation.

        .. note::
          This method can only be used with Galaxy ``release_21.01`` or later.
        """
        invocation_details = self.show_invocation(invocation_id)
        workflow_id = invocation_details['workflow_id']
        inputs = invocation_details['inputs']
        wf_params = invocation_details['input_step_parameters']
        if inputs_update:
            for inp, input_value in inputs_update.items():
                inputs[inp] = input_value
        if params_update:
            for param, param_value in params_update.items():
                wf_params[param] = param_value
        payload = {'inputs': inputs, 'params': wf_params}

        if replacement_params:
            payload['replacement_params'] = replacement_params
        if history_id:
            payload['history'] = f'hist_id={history_id}'
        elif history_name:
            payload['history'] = history_name
        if not import_inputs_to_history:
            payload['no_add_to_history'] = True
        if allow_tool_state_corrections:
            payload['allow_tool_state_corrections'] = allow_tool_state_corrections
        if inputs_by is not None:
            payload['inputs_by'] = inputs_by
        if parameters_normalized:
            payload['parameters_normalized'] = parameters_normalized
        api_params = {'instance': True}
        url = '/'.join((self.gi.url, 'workflows', workflow_id, 'invocations'))
        return self.gi.make_post_request(url=url, payload=payload, params=api_params)

    def cancel_invocation(self, invocation_id):
        """
        Cancel the scheduling of a workflow.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :rtype: dict
        :return: The workflow invocation being cancelled
        """
        url = self._make_url(invocation_id)
        return self._delete(url=url)

    def show_invocation_step(self, invocation_id, step_id):
        """
        See the details of a particular workflow invocation step.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :type step_id: str
        :param step_id: Encoded workflow invocation step ID

        :rtype: dict
        :return: The workflow invocation step.
          For example::

            {'action': None,
             'id': '63cd3858d057a6d1',
             'job_id': None,
             'model_class': 'WorkflowInvocationStep',
             'order_index': 2,
             'state': None,
             'update_time': '2015-10-31T22:11:14',
             'workflow_step_id': '52e496b945151ee8',
             'workflow_step_label': None,
             'workflow_step_uuid': '4060554c-1dd5-4287-9040-8b4f281cf9dc'}
        """
        url = self._invocation_step_url(invocation_id, step_id)
        return self._get(url=url)

    def run_invocation_step_action(self, invocation_id, step_id, action):
        """ Execute an action for an active workflow invocation step. The
        nature of this action and what is expected will vary based on the
        the type of workflow step (the only currently valid action is True/False
        for pause steps).

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :type step_id: str
        :param step_id: Encoded workflow invocation step ID

        :type action: object
        :param action: Action to use when updating state, semantics depends on
           step type.

        :rtype: dict
        :return: Representation of the workflow invocation step
        """
        url = self._invocation_step_url(invocation_id, step_id)
        payload = {"action": action}
        return self._put(payload=payload, url=url)

    def get_invocation_summary(self, invocation_id):
        """
        Get a summary of an invocation, stating the number of jobs which
        succeed, which are paused and which have errored.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :rtype: dict
        :return: The invocation summary.
          For example::

            {'states': {'paused': 4, 'error': 2, 'ok': 2},
             'model': 'WorkflowInvocation',
             'id': 'a799d38679e985db',
             'populated_state': 'ok'}
        """
        url = self._make_url(invocation_id) + '/jobs_summary'
        return self._get(url=url)

    def get_invocation_step_jobs_summary(self, invocation_id):
        """
        Get a detailed summary of an invocation, listing all jobs with
        their job IDs and current states.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :rtype: list of dicts
        :return: The invocation step jobs summary.
          For example::

            [{'id': 'e85a3be143d5905b',
              'model': 'Job',
              'populated_state': 'ok',
              'states': {'ok': 1}},
             {'id': 'c9468fdb6dc5c5f1',
              'model': 'Job',
              'populated_state': 'ok',
              'states': {'running': 1}},
             {'id': '2a56795cad3c7db3',
              'model': 'Job',
              'populated_state': 'ok',
              'states': {'new': 1}}]
        """
        url = self._make_url(invocation_id) + '/step_jobs_summary'
        return self._get(url=url)

    def get_invocation_report(self, invocation_id):
        """
        Get a Markdown report for an invocation.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :rtype: dict
        :return: The invocation report.
          For example::

            {'markdown': '\\n# Workflow Execution Summary of Example workflow\\n\\n
             ## Workflow Inputs\\n\\n\\n## Workflow Outputs\\n\\n\\n
             ## Workflow\\n```galaxy\\n
             workflow_display(workflow_id=f2db41e1fa331b3e)\\n```\\n',
             'render_format': 'markdown',
             'workflows': {'f2db41e1fa331b3e': {'name': 'Example workflow'}}}
        """
        url = self._make_url(invocation_id) + '/report'
        return self._get(url=url)

    def get_invocation_report_pdf(self, invocation_id, file_path, chunk_size=CHUNK_SIZE):
        """
        Get a PDF report for an invocation.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :type file_path: str
        :param file_path: Path to save the report
        """
        url = self._make_url(invocation_id) + '/report.pdf'
        r = self.gi.make_get_request(url, stream=True)
        if r.status_code != 200:
            raise Exception("Failed to get the PDF report, the necessary dependencies may not be installed on the Galaxy server.")
        with open(file_path, 'wb') as outf:
            for chunk in r.iter_content(chunk_size):
                outf.write(chunk)

    def get_invocation_biocompute_object(self, invocation_id):
        """
        Get a BioCompute object for an invocation.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :rtype: dict
        :return: The BioCompute object
        """
        url = self._make_url(invocation_id) + '/biocompute'
        return self._get(url=url)

    def wait_for_invocation(self, invocation_id, maxwait=12000, interval=3, check=True):
        """
        Wait until an invocation is in a terminal state.

        :type invocation_id: str
        :param invocation_id: Invocation ID to wait for.

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the invocation state
          to become terminal. If the invocation state is not terminal within
          this time, a ``TimeoutException`` will be raised.

        :type interval: float
        :param interval: Time (in seconds) to wait between 2 consecutive checks.

        :type check: bool
        :param check: Whether to check if the invocation terminal state is
          'scheduled'.

        :rtype: dict
        :return: Details of the workflow invocation.
        """
        assert maxwait >= 0
        assert interval > 0

        time_left = maxwait
        while True:
            invocation = self.gi.invocations.show_invocation(invocation_id)
            state = invocation['state']
            if state in INVOCATION_TERMINAL_STATES:
                if check and state != 'scheduled':
                    raise Exception(f"Invocation {invocation_id} is in terminal state {state}")
                return invocation
            if time_left > 0:
                log.info(f"Invocation {invocation_id} is in non-terminal state {state}. Will wait {time_left} more s")
                time.sleep(min(time_left, interval))
                time_left -= interval
            else:
                raise TimeoutException(f"Invocation {invocation_id} is still in non-terminal state {state} after {maxwait} s")

    def _invocation_step_url(self, invocation_id, step_id):
        return '/'.join((self._make_url(invocation_id), "steps", step_id))


__all__ = ('InvocationClient',)
