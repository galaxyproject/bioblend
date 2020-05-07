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
