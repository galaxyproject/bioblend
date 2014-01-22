"""
A representation of a Galaxy instance based on oo wrappers.
"""

import bioblend
import bioblend.galaxy

from client import ObjDatasetClient, ObjHistoryClient, ObjLibraryClient, ObjWorkflowClient


class GalaxyInstance(object):
    """
    A representation of an instance of Galaxy, identified by a URL and
    a user's API key.

    Example: get a list of all histories for a user with API key 'foo'::

      from bioblend.galaxy.objects import *
      gi = GalaxyInstance('http://127.0.0.1:8080', 'foo')
      histories = gi.get_histories()

    :type url: str
    :param url: a FQDN or IP for a given instance of Galaxy. For example:
      ``http://127.0.0.1:8080``

    :type key: str
    :param key: user's API key for the given instance of Galaxy, obtained
      from the Galaxy web UI.

    This is actually a factory class which instantiates the entity-specific
    clients.
    """
    def __init__(self, url, api_key):
        self.gi = bioblend.galaxy.GalaxyInstance(url, api_key)
        self.log = bioblend.log
        self.datasets = ObjDatasetClient(self)
        self.histories = ObjHistoryClient(self)
        self.libraries = ObjLibraryClient(self)
        self.workflows = ObjWorkflowClient(self)
