"""
A base representation of an instance of Galaxy
"""
from bioblend.galaxy import (config, datasets, datatypes, folders, forms,
                             ftpfiles, genomes, groups, histories, jobs,
                             libraries, quotas, roles, tool_data, tools,
                             toolshed, users, visual, workflows)
from bioblend.galaxy.client import Client
from bioblend.galaxyclient import GalaxyClient


class GalaxyInstance(GalaxyClient):
    def __init__(self, url, key=None, email=None, password=None, verify=True):
        """
        A base representation of a connection to a Galaxy instance, identified
        by the server URL and user credentials.

        After you have created a ``GalaxyInstance`` object, access various
        modules via the class fields. For example, to work with histories and
        get a list of all the user's histories, the following should be done::

            from bioblend import galaxy

            gi = galaxy.GalaxyInstance(url='http://127.0.0.1:8000', key='your_api_key')

            hl = gi.histories.get_histories()

        :type url: str
        :param url: A FQDN or IP for a given instance of Galaxy. For example:
                    http://127.0.0.1:8080 . If a Galaxy instance is served under
                    a prefix (e.g., http://127.0.0.1:8080/galaxy/), supply the
                    entire URL including the prefix (note that the prefix must
                    end with a slash).

        :type key: str
        :param key: User's API key for the given instance of Galaxy, obtained
                    from the user preferences. If a key is not supplied, an
                    email address and password must be and the key will
                    automatically be created for the user.

        :type email: str
        :param email: Galaxy e-mail address corresponding to the user.
                      Ignored if key is supplied directly.

        :type password: str
        :param password: Password of Galaxy account corresponding to the above
                         e-mail address. Ignored if key is supplied directly.

        :param verify: Whether to verify the server's TLS certificate
        :type verify: boolean
        """
        super(GalaxyInstance, self).__init__(url, key, email, password, verify=verify)
        self.libraries = libraries.LibraryClient(self)
        self.histories = histories.HistoryClient(self)
        self.workflows = workflows.WorkflowClient(self)
        self.datasets = datasets.DatasetClient(self)
        self.users = users.UserClient(self)
        self.genomes = genomes.GenomeClient(self)
        self.tools = tools.ToolClient(self)
        self.toolShed = toolshed.ToolShedClient(self)
        self.config = config.ConfigClient(self)
        self.visual = visual.VisualClient(self)
        self.quotas = quotas.QuotaClient(self)
        self.groups = groups.GroupsClient(self)
        self.roles = roles.RolesClient(self)
        self.datatypes = datatypes.DatatypesClient(self)
        self.jobs = jobs.JobsClient(self)
        self.forms = forms.FormsClient(self)
        self.ftpfiles = ftpfiles.FTPFilesClient(self)
        self.tool_data = tool_data.ToolDataClient(self)
        self.folders = folders.FoldersClient(self)

    @property
    def max_get_attempts(self):
        return Client.max_get_retries()

    @max_get_attempts.setter
    def max_get_attempts(self, v):
        Client.set_max_get_retries(v)

    @property
    def get_retry_delay(self):
        return Client.get_retry_delay()

    @get_retry_delay.setter
    def get_retry_delay(self, v):
        Client.set_get_retry_delay(v)

    def __repr__(self):
        """
        A nicer representation of this GalaxyInstance object
        """
        return "GalaxyInstance object for Galaxy at {0}".format(self.base_url)
