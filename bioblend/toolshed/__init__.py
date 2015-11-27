"""
A base representation of an instance of Tool Shed
"""
from bioblend.galaxyclient import GalaxyClient
from bioblend.toolshed import categories, repositories, tools


class ToolShedInstance(GalaxyClient):
    def __init__(self, url, key='', email=None, password=None):
        """
        A base representation of an instance of ToolShed, identified by a
        URL and a user's API key.

        After you have created an ``ToolShed`` object, access various
        modules via the class fields (see the source for the most up-to-date
        list): ``repositories`` are the minimum set supported. For example, to work with
        a repositories, and get a list of all the public repositories, the following
        should be done::

            from bioblend import toolshed

            ts = toolshed.ToolShedInstance(url='https://testtoolshed.g2.bx.psu.edu')

            rl = ts.repositories.get_repositories()

            tools = ts.tools.search_tools('fastq')

        :type url: str
        :param url: A FQDN or IP for a given instance of ToolShed. For example:
                    https://testtoolshed.g2.bx.psu.edu

        :type key: str
        :param key: If required, user's API key for the given instance of ToolShed,
                    obtained from the user preferences.
        """
        super(ToolShedInstance, self).__init__(url, key, email, password)
        self.categories = categories.ToolShedCategoryClient(self)
        self.repositories = repositories.ToolShedRepositoryClient(self)
        self.tools = tools.ToolShedToolClient(self)
