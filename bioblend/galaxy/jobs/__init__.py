"""
Contains possible interactions with the Galaxy Jobs
"""
import logging
import time

from bioblend import TimeoutException
from bioblend.galaxy.client import Client

log = logging.getLogger(__name__)

JOB_TERMINAL_STATES = {'deleted', 'error', 'ok'}
# Job non-terminal states are: 'deleted_new', 'failed', 'new', 'paused',
# 'queued', 'resubmitted', 'running', 'upload', 'waiting'


class JobsClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'jobs'
        super().__init__(galaxy_instance)

    def get_jobs(self, state=None, tool_id=None, user_details=False,
                 date_range_min=None, date_range_max=None, history_id=None):
        """
        Get all jobs, or select a subset by specifying optional arguments for
        filtering (e.g. a state).

        If the user is an admin, this will return jobs for all the users,
        otherwise only for the current user.

        :type state: str or list of str
        :param state: Job states to filter on.

        :type tool_id: str or list of str
        :param tool_id: Tool IDs to filter on.

        :type user_details: bool
        :param user_details: If ``True`` and the user is an admin, add the user
          email to each returned job dictionary.

        :type date_range_min: str
        :param date_range_min: Mininum job update date (in YYYY-MM-DD format) to
          filter on.

        :type date_range_max: str
        :param date_range_max: Maximum job update date (in YYYY-MM-DD format) to
          filter on.

        :type history_id: str
        :param history_id: Encoded history ID to filter on.

        :rtype: list of dict
        :return: Summary information for each selected job.
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
        params = {}
        if state:
            params['state'] = state
        if tool_id:
            params['tool_id'] = tool_id
        if user_details:
            params['user_details'] = user_details
        if date_range_min:
            params['date_range_min'] = date_range_min
        if date_range_max:
            params['date_range_max'] = date_range_max
        if history_id:
            params['history_id'] = history_id
        return self._get(params=params)

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
          This method can only be used with Galaxy ``release_21.01`` or later.
        """
        job_rerun_params = self._build_for_rerun(job_id)
        job_inputs = job_rerun_params['state_inputs']

        if remap:
            if not job_rerun_params['job_remap']:
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

    def get_state(self, job_id: str) -> str:
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

    def search_jobs(self, job_info: dict) -> list:
        """
        Return jobs matching input parameters specified in ``job_info``.

        :type job_info: dict
        :param job_info: dictionary of input datasets and parameters, formatted in
          the same way as the ``tool_inputs`` parameter of the ``gi.tools.run_tool()``
          method.

        :rtype: list
        :return: list of dictionaries containing summary job information of
          the jobs that match the requested job run

        This method is designed to scan the list of previously run jobs and find
        records of jobs with identical input parameters and datasets. This can
        be used to minimize the amount of repeated work by simply recycling the
        old results.

        .. note::
          This method only supports Galaxy 18.01 or later.
        """

        url = self._make_url() + '/search'
        return self._post(url=url, payload=job_info)

    def get_metrics(self, job_id: str) -> list:
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

    def report_error(self, job_id: str, dataset_id: str, message: str, email=None) -> dict:
        """
        Report an error for a given job and dataset to the server administrators.

        :type job_id: str
        :param job_id: job ID

        :type dataset_id: str
        :param dataset_id: Dataset ID

        :type message: str
        :param message: Error message

        :type email: str
        :param email: Email for error report submission. If not specified, the email
          associated with the Galaxy user account is used by default.

        :rtype: dict
        :return: dict containing job error reply

        .. note::
          This method only supports Galaxy 20.01 or later.
        """
        payload = {
            "message": message,
            "dataset_id": dataset_id,
        }
        if email is not None:
            payload["email"] = email

        url = self._make_url(module_id=job_id) + '/error'
        return self._post(url=url, payload=payload)

    def get_common_problems(self, job_id: str) -> dict:
        """
        Query inputs and jobs for common potential problems that might
        have resulted in job failure.

        :type job_id: str
        :param job_id: job ID

        :rtype: dict
        :return: dict containing potential problems

        .. note::
          This method only supports Galaxy 19.05 or later.
        """
        url: str = self._make_url(module_id=job_id) + '/common_problems'
        return self._get(url=url)

    def get_inputs(self, job_id: str) -> dict:
        """
        Get dataset inputs used by a specific job ID.

        :type job_id: str
        :param job_id: job ID

        :rtype: dict
        :return: dict containing inputs for this job ID
        """
        url: str = self._make_url(module_id=job_id) + '/inputs'
        return self._get(url=url)

    def get_outputs(self, job_id: str) -> dict:
        """
        Get dataset outputs produced by a specific job ID.

        :type job_id: str
        :param job_id: job ID

        :rtype: dict
        :return: dict containing outputs for this job ID
        """
        url: str = self._make_url(module_id=job_id) + '/outputs'
        return self._get(url=url)

    def resume_job(self, job_id: str) -> dict:
        """
        Resume a job if it is paused.

        :type job_id: str
        :param job_id: job ID

        :rtype: dict
        :return: dict containing output dataset associations

        .. note::
          This method only supports Galaxy 18.09 or later.
        """
        url: str = self._make_url(module_id=job_id) + '/resume'
        return self._put(url=url, payload={})

    def get_destination_params(self, job_id: str) -> dict:
        """
        Get destination parameters for the specific job ID, describing
        the environment and location where the job is run.

        :type job_id: str
        :param job_id: job ID

        :rtype: dict
        :return: dict containing destination params

        .. note::
          This method only supports Galaxy 20.05 or later.
        """
        url: str = self._make_url(module_id=job_id) + '/destination_params'
        return self._get(url=url)

    def show_job_lock(self) -> bool:
        """
        Show whether the job lock is active or not. If it is active,
        no jobs will dispatch on the Galaxy server.

        :rtype: bool
        :return: boolean indication the status of the job lock

        .. note::
          This method can only be used by admin users.

        .. note::
          This method only supports Galaxy 20.05 or later.
        """
        url: str = self.gi.url + '/job_lock'
        response: dict = self._get(url=url)
        return response['active']

    def update_job_lock(self, active=False) -> dict:
        """
        Update the job lock status by setting ``active`` to either
        ``True`` or ``False``. If ``True``, all job dispatching will
        be blocked.

        :rtype: bool
        :return: boolean indication the status of the job lock

        .. note::
          This method can only be used by admin users.

        .. note::
          This method only supports Galaxy 20.05 or later.
        """
        payload = {
            'active': active,
        }
        url: str = self.gi.url + '/job_lock'
        response: dict = self._put(url=url, payload=payload)
        return response['active']

    def wait_for_job(self, job_id, maxwait=12000, interval=3, check=True):
        """
        Wait until a job is in a terminal state.

        :type job_id: str
        :param job_id: job ID

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the job state to
          become terminal. If the job state is not terminal within this time, a
          ``TimeoutException`` will be raised.

        :type interval: float
        :param interval: Time (in seconds) to wait between 2 consecutive checks.

        :type check: bool
        :param check: Whether to check if the job terminal state is 'ok'.

        :rtype: dict
        :return: Details of the given job.
        """
        assert maxwait >= 0
        assert interval > 0

        time_left = maxwait
        while True:
            job = self.show_job(job_id)
            state = job['state']
            if state in JOB_TERMINAL_STATES:
                if check and state != 'ok':
                    raise Exception(f"Job {job_id} is in terminal state {state}")
                return job
            if time_left > 0:
                log.info(f"Job {job_id} is in non-terminal state {state}. Will wait {time_left} more s")
                time.sleep(min(time_left, interval))
                time_left -= interval
            else:
                raise TimeoutException(f"Job {job_id} is still in non-terminal state {state} after {maxwait} s")
