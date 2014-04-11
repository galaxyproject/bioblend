"""
A representation of a Galaxy instance based on oo wrappers.
"""

import bioblend
import bioblend.galaxy

import client


class GalaxyInstance(object):
    """
    A representation of an instance of Galaxy, identified by a URL and
    a user's API key.

    :type url: str
    :param url: a FQDN or IP for a given instance of Galaxy. For example:
      ``http://127.0.0.1:8080``

    :type key: str
    :param key: user's API key for the given instance of Galaxy, obtained
      from the Galaxy web UI.

    This is actually a factory class which instantiates the entity-specific
    clients.

    Example: get a list of all histories for a user with API key 'foo'::

      from bioblend.galaxy.objects import *
      gi = GalaxyInstance('http://127.0.0.1:8080', 'foo')
      histories = gi.histories.list()
    """
    def __init__(self, url, api_key):
        self.gi = bioblend.galaxy.GalaxyInstance(url, api_key)
        self.log = bioblend.log
        self.__histories = client.ObjHistoryClient(self)
        self.__libraries = client.ObjLibraryClient(self)
        self.__workflows = client.ObjWorkflowClient(self)
        self.__tools = client.ObjToolClient(self)

    @property
    def histories(self):
        """
        Client module for Galaxy histories.
        """
        return self.__histories

    @property
    def libraries(self):
        """
        Client module for Galaxy libraries.
        """
        return self.__libraries

    @property
    def workflows(self):
        """
        Client module for Galaxy workflows.
        """
        return self.__workflows

    @property
    def tools(self):
        """
        Client module for Galaxy tools.
        """
        return self.__tools
