"""
Contains possible interactions with the Galaxy Workflows
"""
from bioblend.galaxy.client import Client
import simplejson
import os

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

    def get_workflow_inputs(self, workflow_id, label):
        """
        Get a list of workflow input IDs that match the given label. 
        If no input matches the given label, an empty list is returned. 
        """
        wf = Client._get(self, id=workflow_id)
        inputs = wf['inputs']
        return [id for id in inputs if inputs[id]['label'] == label]

    def import_workflow_json(self, workflow_json):
        """
        Imports a new workflow given a json representation of a previously exported
        workflow.
        """
        payload = {}
        payload['workflow'] = workflow_json

        url = self.gi._make_url(self)
        url = '/'.join([url, "upload"])
        return Client._post(self, url=url, payload=payload)

    def import_workflow_from_local_path(self, file_local_path):
        """
        Imports a new workflow given the path to a file containing a previously
        exported workflow.
        """
        with open(file_local_path, 'rb') as fp:
            workflow_json = simplejson.load(fp)

        return self.import_workflow_json(workflow_json)

    def export_workflow_json(self, workflow_id):
        """
        Exports a workflow in json format

        :type workflow_id: string
        :param workflow_id: Encoded workflow ID
        """
        url = self.gi._make_url(self)
        url = '/'.join([url, "download"])
        url = '/'.join([url, workflow_id])
        return Client._get(self, url=url)

    def export_workflow_to_local_path(self, workflow_id, file_local_path, use_default_filename=True):
        """
        Exports a workflow in json format to a given local path.

        :type workflow_id: string
        :param workflow_id: Encoded workflow ID

        :type file_local_path: string
        :param file_local_path: Local path to which the exported file will be saved.
                                (Should not contain filename if use_default_name=True)

        :type use_default_name: boolean
        :param use_default_name: If the use_default_name parameter is True, the exported
                                 file will be saved as file_local_path/Galaxy-Workflow-%s.ga,
                                 where %s is the workflow name.
                                 If use_default_name is False, file_local_path is assumed to
                                 contain the full file path including filename.
        """
        workflow_json = self.export_workflow_json(workflow_id)

        if use_default_filename:
            filename = 'Galaxy-Workflow-%s.ga' % workflow_json['name']
            file_local_path = os.path.join(file_local_path, filename)

        with open(file_local_path, 'wb') as fp:
            workflow_json = simplejson.dump(workflow_json, fp)

        return workflow_json

    def run_workflow(self, workflow_id, dataset_map,params=None, history_id=None, history_name=None,
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
        :type params: string or dict
        :param params: A mapping of tool parameters that are non-datasets parameters. The map must be in the
                         following format:
                         ``{'blastn': {'param': 'evalue', 'value': '1e-06'}}``

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
        
        if params:
            payload['parameters'] = params
            
        if history_id:
            payload['history'] = 'hist_id={0}'.format(history_id)
        elif history_name:
            payload['history'] = history_name
        else:
            print "Must provide history_id or history_name argument"
        if import_inputs_to_history is False:
            payload['no_add_to_history'] = True
        return Client._post(self, payload)
