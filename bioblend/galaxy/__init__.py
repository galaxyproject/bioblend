"""
A base representation of an instance of Galaxy
"""
import urlparse
from bioblend.galaxy import (libraries, histories, workflows, datasets, users,
                             genomes, tools, toolshed, config, visual, quotas)
from bioblend.galaxyclient import GalaxyClient


class GalaxyInstance(GalaxyClient):
    def __init__(self, url, key):
        """
        A base representation of an instance of Galaxy, identified by a
        URL and a user's API key.

        After you have created an ``GalaxyInstance`` object, access various
        modules via the class fields (see the source for the most up-to-date
        list): ``libraries``, ``histories``, ``workflows``, ``datasets``,
        and ``users`` are the minimum set supported. For example, to work with
        histories, and get a list of all the user's histories, the following
        should be done::

            from bioblend import galaxy

            gi = galaxy.GalaxyInstance(url='http://127.0.0.1:8000', key='your_api_key')

            hl = gi.histories.get_histories()
            print "List of histories:", hl

        :type url: string
        :param url: A FQDN or IP for a given instance of Galaxy. For example:
                    http://127.0.0.1:8080

        :type key: string
        :param key: User's API key for the given instance of Galaxy, obtained
                    from the user preferences.
        """
        # Make sure the url scheme is defined (otherwise requests will not work)
        if not urlparse.urlparse(url).scheme:
            url = "http://" + url
        # All of Galaxy's API's are rooted at <url>/api so make that the base url
        self.base_url = url
        self.url = urlparse.urljoin(url, 'api')
        self.key = key
        self.default_params = {'key': key}
        self.json_headers = {'Content-Type': 'application/json'}
        self.verify = False  # Should SSL verification be done
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

    def __repr__(self):
        """
        A nicer representation of this GalaxyInstance object
        """
        return "GalaxyInstance object for Galaxy at {0}".format(self.base_url)
