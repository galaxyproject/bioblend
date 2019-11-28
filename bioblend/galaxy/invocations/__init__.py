"""
Contains possible interactions with the Galaxy workflow invocations
"""

from bioblend.galaxy.client import Client


class InvocationClient(Client):
    def __init__(self, galaxy_instance):
        self.module = 'invocations'
        super(InvocationClient, self).__init__(galaxy_instance)

    def get_invocations(self):
        """
        Get a list containing all workflow invocations.

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
        return self._get()

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
        url = self._invocation_url(invocation_id)
        return self._get(url=url)

    def cancel_invocation(self, invocation_id):
        """
        Cancel the scheduling of a workflow.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :rtype: dict
        :return: The workflow invocation being cancelled
        """
        url = self._invocation_url(invocation_id)
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
        url = _join(self._invocation_url(invocation_id), "jobs_summary")
        return self._get(url=url)

    def get_invocation_report(self, invocation_id):
        """
        Get a Markdown report for an invocation.

        :type invocation_id: str
        :param invocation_id: Encoded workflow invocation ID

        :rtype: dict
        :return: The invocation report.
          For example::

            {'markdown': '\n# Workflow Execution Summary of Example workflow\n\n
             ## Workflow Inputs\n\n\n## Workflow Outputs\n\n\n
             ## Workflow\n```galaxy\n
             workflow_display(workflow_id=f2db41e1fa331b3e)\n```\n',
             'render_format': 'markdown',
             'workflows': {'f2db41e1fa331b3e': {'name': 'Example workflow'}}}
        """
        url = _join(self._invocation_url(invocation_id), "report")
        return self._get(url=url)

    def _invocation_step_url(self, invocation_id, step_id):
        return _join(self._invocation_url(invocation_id), "steps", step_id)

    def _invocation_url(self, invocation_id):
        url = self.gi._make_url(self)
        url = _join(url, invocation_id)
        return url


def _join(*args):
    return "/".join(args)


__all__ = ('InvocationClient',)
