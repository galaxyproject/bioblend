"""
Contains possible interactions with the Galaxy Jobs
"""
from bioblend.galaxy.client import Client


class JobsClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'jobs'
        super().__init__(galaxy_instance)

    def get_jobs(self):
        """
        Get the list of jobs of the current user.

        :rtype: list
        :return: list of dictionaries containing summary job information.
          For example::

            [{'create_time': '2014-03-01T16:16:48.640550',
              'exit_code': 0,
              'id': 'ebfb8f50c6abde6d',
              'model_class': 'Job',
              'state': 'ok',
              'tool_id': 'fasta2tab',
              'update_time': '2014-03-01T16:16:50.657399'},
             {'create_time': '2014-03-01T16:05:34.851246',
              'exit_code': 0,
              'id': '1cd8e2f6b131e891',
              'model_class': 'Job',
              'state': 'ok',
              'tool_id': 'upload1',
              'update_time': '2014-03-01T16:05:39.558458'}]
        """
        return self._get()

    def show_job(self, job_id, full_details=False):
        """
        Get details of a given job of the current user.

        :type job_id: str
        :param job_id: job ID

        :type full_details: bool
        :param full_details: when ``True``, the complete list of details for the
          given job.

        :rtype: dict
        :return: A description of the given job.
          For example::

            {'create_time': '2014-03-01T16:17:29.828624',
             'exit_code': 0,
             'id': 'a799d38679e985db',
             'inputs': {'input': {'id': 'ebfb8f50c6abde6d', 'src': 'hda'}},
             'model_class': 'Job',
             'outputs': {'output': {'id': 'a799d38679e985db', 'src': 'hda'}},
             'params': {'chromInfo': '"/opt/galaxy-central/tool-data/shared/ucsc/chrom/?.len"',
                        'dbkey': '"?"',
                        'seq_col': '"2"',
                        'title_col': '["1"]'},
             'state': 'ok',
             'tool_id': 'tab2fasta',
             'update_time': '2014-03-01T16:17:31.930728'}
        """
        params = {}
        if full_details:
            params['full'] = full_details

        return self._get(id=job_id, params=params)

    def _build_for_rerun(self, job_id):
        """
        Get details of a given job that can be used to rerun the corresponding tool.

        :type job_id: str
        :param job_id: job ID

        :rtype: dict
        :return: A description of the given job, with all parameters required to rerun.

        """
        url = '/'.join((self._make_url(job_id), 'build_for_rerun'))
        return self._get(url=url)

    def rerun_job(self, job_id, remap=False, tool_inputs_update=None, history_id=None):
        """
        Rerun a job.

        :type job_id: str
        :param job_id: job ID

        :type remap: bool
        :param remap: when ``True``, the job output(s) will be remapped onto the dataset(s)
          created by the original job; if other jobs were waiting for this job to finish
          successfully, they will be resumed using the new outputs of this tool run. When
          ``False``, new job output(s) will be created. Note that if Galaxy does not permit
          remapping for the job in question, specifying ``True`` will result in an error.

        :type tool_inputs_update: dict
        :param tool_inputs_update: dictionary specifying any changes which should be
          made to tool parameters for the rerun job.

        :type history_id: str
        :param history_id: ID of the history in which the job should be executed; if
          not specified, the same history will be used as the original job run.

        :rtype: dict
        :return: Information about outputs and the rerun job
        .. note::
          This method can only be used with Galaxy ``release_20.09`` or later.
        """
        job_rerun_params = self._build_for_rerun(job_id)
        job_inputs = job_rerun_params['state_inputs']

        if remap:
            if not job_inputs['job_remap']:
                raise ValueError('remap was set to True, but this job is not remappable.')
            job_inputs['rerun_remap_job_id'] = job_id

        if tool_inputs_update:
            for input_param, input_value in tool_inputs_update.items():
                job_inputs[input_param] = input_value
        url = '/'.join((self.gi.url, 'tools'))
        payload = {
            "history_id": history_id if history_id else job_rerun_params['history_id'],
            "tool_id": job_rerun_params['id'],
            "inputs": job_inputs,
            "input_format": '21.01'
        }
        return self._post(url=url, payload=payload)

    def get_state(self, job_id):
        """
        Display the current state for a given job of the current user.

        :type job_id: str
        :param job_id: job ID

        :rtype: str
        :return: state of the given job among the following values: `new`,
          `queued`, `running`, `waiting`, `ok`. If the state cannot be
          retrieved, an empty string is returned.

        .. versionadded:: 0.5.3
        """
        return self.show_job(job_id).get('state', '')

    def search_jobs(self, job_info):
        """
        Return jobs for the current user based payload content.

        :type job_info: dict
        :param job_info: dictionary containing description of the requested job.
          This is in the same format as a request to POST /api/tools would take
          to initiate a job

        :rtype: list
        :return: list of dictionaries containing summary job information of
          the jobs that match the requested job run

        This method is designed to scan the list of previously run jobs and find
        records of jobs that had the exact some input parameters and datasets.
        This can be used to minimize the amount of repeated work, and simply
        recycle the old results.

        """

        payload = job_info
        url = self._make_url() + '/search'
        return self._post(url=url, payload=payload)

    def get_metrics(self, job_id):
        """
        Return job metrics for a given job.

        :type job_id: str
        :param job_id: job ID

        :rtype: list
        :return: list containing job metrics

        .. note::
          Calling ``show_job()`` with ``full_details=True`` also returns the
          metrics for a job if the user is an admin. This method allows to fetch
          metrics even as a normal user as long as the Galaxy instance has the
          ``expose_potentially_sensitive_job_metrics`` option set to ``true`` in
          the ``config/galaxy.yml`` configuration file.
        """
        url = self._make_url(module_id=job_id) + '/metrics'
        return self._get(url=url)

    def report_error(self, job_id, dataset_id, message, email=None):
        """
        Report an error for a given job and dataset.

        :type job_id: str
        :param job_id: job ID

        :type dataset_id: str
        :param dataset_id: Dataset ID

        :type message: str
        :param message: Error message

        :type email: str
        :param email: Email to submit error report to

        :rtype: dict
        :return: dict containing job error reply
        """
        payload = {
            "message": message,
            "dataset_id": dataset_id,
        }
        if email is not None:
            payload["email"] = email

        url = self._make_url(module_id=job_id) + '/error'
        return self._post(url=url, payload=payload)
