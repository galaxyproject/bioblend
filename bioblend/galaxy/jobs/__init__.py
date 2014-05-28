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
        Get a list of jobs for current user

        :type   state: string or list
        :param  state: limit listing of jobs to those that match one of the included states. If none, all are returned.
        Valid Galaxy job states include:
        'new', 'upload', 'waiting', 'queued', 'running', 'ok', 'error', 'paused', 'deleted', 'deleted_new'

        :type   tool_id: string or list
        :param  tool_id: limit listing of jobs to those that match one of the included tool_ids. If none, all are returned.

        :type   history_id: string
        :param  history_id: limit listing of jobs to those that match the history_id. If none, all are returned.

        :rtype:     list
        :returns:   list of dictionaries containing summary job information
                 For example::

                 [{ u'create_time': u'2014-03-01T16:16:48.640550',
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
        return Client._get(self)

    def show_job(self, job_id):
        """
        Display information on a single job from current user

        :type job_id: string
        :param job_id: Specific job ID

        :rtype: dict
        :return: A description of single job
                 For example::

                 {   u'create_time': u'2014-03-01T16:17:29.828624',
                 u'exit_code': 0,
                 u'id': u'a799d38679e985db',
                 u'inputs': {   u'input': {   u'id': u'ebfb8f50c6abde6d', u'src': u'hda'}},
                 u'model_class': u'Job',
                 u'outputs': {   u'output': {   u'id': u'a799d38679e985db', u'src': u'hda'}},
                 u'params': {   u'chromInfo': u'"/opt/galaxy-central/tool-data/shared/ucsc/chrom/?.len"',
                 u'dbkey': u'"?"',
                 u'seq_col': u'"2"',
                 u'title_col': u'["1"]'},
                 u'state': u'ok',
                 u'tool_id': u'tab2fasta',
                 u'update_time': u'2014-03-01T16:17:31.930728'}



        """

        return Client._get(self, id=job_id)

    def search_jobs(self, job_info):
        """
        Return jobs for current user based payload content

        :type   payload: dict
        :param  payload: Dictionary containing description of requested job. This is in the same format as
        a request to POST /api/tools would take to initiate a job

        :rtype:     list
        :returns:   list of dictionaries containing summary job information of the jobs that match the requested job run

        This method is designed to scan the list of previously run jobs and find records of jobs that had
        the exact some input parameters and datasets. This can be used to minimize the amount of repeated work, and simply
        recycle the old results.

        """

        payload = job_info

        url = self.gi._make_url(self)
        url = '/'.join([url, "search"])

        return Client._post(self, url=url, payload=payload)
