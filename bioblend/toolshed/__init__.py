"""
A base representation of an instance of Tool Shed 
"""
from bioblend.toolshed import (repositories)
from bioblend.galaxyclient import GalaxyClient
import urlparse
import requests

class ToolShedInstance(GalaxyClient):
    def __init__(self, url, key):
        """
        A base representation of an instance of ToolShed, identified by a
        URL and a user's API key.

        After you have created an ``ToolShed`` object, access various
        modules via the class fields (see the source for the most up-to-date
        list): ``repositories`` are the minimum set supported. For example, to work with
        a repositories, and get a list of all the public repositories, the following
        should be done::

            from bioblend import toolshed

            ts = toolshed.ToolshedInstance(url='http://127.0.0.1:8000', key='your_api_key')

            hl = ts.histories.get_repositories()
            print "List of repositories:", hl

        :type url: string
        :param url: A FQDN or IP for a given instance of ToolShed. For example:
                    http://127.0.0.1:8080

        :type key: string
        :param key: User's API key for the given instance of ToolShed, obtained
                    from the user preferences.
        """
        # Make sure the url scheme is defined (otherwise requests will not work)
        if not urlparse.urlparse(url).scheme:
            url = "http://" + url
        # All of ToolShed 's API's are rooted at <url>/api so make that the base url
        self.base_url = url
        self.url = urlparse.urljoin(url, 'api')
        self.key = key
        self.default_params = {'key': key}
        self.json_headers = {'Content-Type': 'application/json'}
        self.verify = False  # Should SSL verification be done
        self.repositories = repositories.ToolShedClient(self)


