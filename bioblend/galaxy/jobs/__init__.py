"""
Contains possible interactions with the Galaxy Jobs
"""
from bioblend.galaxy.client import Client


class JobsClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'jobs'
        super(JobsClient, self).__init__(galaxy_instance)

    def get_jobs(self):
        """
        Get the list of jobs of the current user.

        :rtype: list
        :returns: list of dictionaries containing summary job information.
          For example::

            [{u'create_time': u'2014-03-01T16:16:48.640550',
              u'exit_code': 0,
              u'id': u'ebfb8f50c6abde6d',
              u'model_class': u'Job',
              u'state': u'ok',
              u'tool_id': u'fasta2tab',
              u'update_time': u'2014-03-01T16:16:50.657399'},
             {u'create_time': u'2014-03-01T16:05:34.851246',
              u'exit_code': 0,
              u'id': u'1cd8e2f6b131e891',
              u'model_class': u'Job',
              u'state': u'ok',
              u'tool_id': u'upload1',
              u'update_time': u'2014-03-01T16:05:39.558458'}]
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

            {u'create_time': u'2014-03-01T16:17:29.828624',
             u'exit_code': 0,
             u'id': u'a799d38679e985db',
             u'inputs': {u'input': {u'id': u'ebfb8f50c6abde6d',
               u'src': u'hda'}},
             u'model_class': u'Job',
             u'outputs': {u'output': {u'id': u'a799d38679e985db',
               u'src': u'hda'}},
             u'params': {u'chromInfo': u'"/opt/galaxy-central/tool-data/shared/ucsc/chrom/?.len"',
               u'dbkey': u'"?"',
               u'seq_col': u'"2"',
               u'title_col': u'["1"]'},
             u'state': u'ok',
             u'tool_id': u'tab2fasta',
             u'update_time': u'2014-03-01T16:17:31.930728'}
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
        :returns: list of dictionaries containing summary job information of
          the jobs that match the requested job run

        This method is designed to scan the list of previously run jobs and find
        records of jobs that had the exact some input parameters and datasets.
        This can be used to minimize the amount of repeated work, and simply
        recycle the old results.

        """

        payload = job_info

        url = self.gi._make_url(self)
        url = '/'.join([url, "search"])

        return self._post(url=url, payload=payload)
