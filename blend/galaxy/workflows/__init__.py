"""
Contains possible interactions with the Galaxy Workflows
"""
from blend.galaxy.client import Client


class WorkflowClient(Client):
    def __init__(self, galaxy_instance):
        self.module = 'workflows'
        super(WorkflowClient, self).__init__(galaxy_instance)

    def get_workflows(self):
        """
        Get a list of all workflows

        :rtype: list
        :return: A list of workflow dicts.
                 For example::

                   [{u'id': u'92c56938c2f9b315',
                     u'name': u'Simple',
                     u'url': u'/api/workflows/92c56938c2f9b315'}]

        """
        return Client._get(self)

    def show_workflow(self, workflow_id):
        """
        Display information needed to run a workflow

        :type workflow_id: string
        :param workflow_id: Encoded workflow ID

        :rtype: list
        :return: A description of the workflow and its inputs as a JSON object.
                 For example::

                  {u'id': u'92c56938c2f9b315',
                   u'inputs': {u'23': {u'label': u'Input Dataset', u'value': u''}},
                   u'name': u'Simple',
                   u'url': u'/api/workflows/92c56938c2f9b315'}

        """
        return Client._get(self, id=workflow_id)

    def run_workflow(self, workflow_id, dataset_map, history_id=None, history_name=None,
            import_inputs_to_history=False):
        """
        Run the workflow identified by ``workflow_id``

        :type workflow_id: string
        :param workflow_id: Encoded workflow ID

        :type dataset_map: string or dict
        :param dataset_map: A mapping of workflow inputs to datasets. The datasets
                            source can be a LibraryDatasetDatasetAssociation (``ldda``),
                            LibraryDataset (``ld``), or HistoryDatasetAssociation (``hda``).
                            The map must be in the following format:
                            ``{'<input>': {'id': <encoded dataset ID>, 'src': '[ldda, ld, hda]'}}``
                            (eg, ``{'23': {'id': '29beef4fadeed09f', 'src': 'ld'}}``)

        :type history_id: string
        :param history_id: The encoded history ID where to store the workflow output.
                           ``history_id`` OR ``history_name`` should be provided but not both!

        :type history_name: string
        :param history_name: Create a new history with the given name to store the
                             workflow output. ``history_id`` OR ``history_name``
                             should be provided but not both!

        :type import_inputs_to_history: bool
        :param import_inputs_to_history: If ``True``, used workflow inputs will be imported
                                         into the history. If ``False``, only workflow outputs
                                         will be visible in the given history.

        :rtype: dict
        :return: A dict containing the history ID where the outputs are placed as well as
                 output dataset IDs.
                 For example::

                  {u'history': u'64177123325c9cfd',
                   u'outputs': [u'aa4d3084af404259']}

        """
        payload = {}
        payload['workflow_id'] = workflow_id
        payload['ds_map'] = dataset_map
        if history_id:
            payload['history'] = 'hist_id={0}'.format(history_id)
        elif history_name:
            payload['history'] = history_name
        else:
            print "Must provide history_id or history_name argument"
        if import_inputs_to_history is False:
            payload['no_add_to_history'] = True
        return Client._post(self, payload)
