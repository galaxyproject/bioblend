"""
A representation of a Galaxy instance based on oo wrappers.
"""

import time

import bioblend
import bioblend.galaxy

from . import client


# dataset states corresponding to a 'pending' condition
_PENDING_DS_STATES = set(
    ["new", "upload", "queued", "running", "setting_metadata"]
)


def _get_error_info(hda):
    msg = hda.id
    try:
        msg += ' (%s): ' % hda.name
        msg += hda.wrapped['misc_info']
    except Exception:  # avoid 'error while generating an error report'
        msg += ': error'
    return msg


class GalaxyInstance(object):
    """
    A representation of an instance of Galaxy, identified by a URL and
    a user's API key.

    :type url: str
    :param url: a FQDN or IP for a given instance of Galaxy. For example:
      ``http://127.0.0.1:8080``

    :type api_key: str
    :param api_key: user's API key for the given instance of Galaxy, obtained
      from the Galaxy web UI.

    This is actually a factory class which instantiates the entity-specific
    clients.

    Example: get a list of all histories for a user with API key 'foo'::

      from bioblend.galaxy.objects import *
      gi = GalaxyInstance('http://127.0.0.1:8080', 'foo')
      histories = gi.histories.list()
    """
    def __init__(self, url, api_key=None, email=None, password=None):
        self.gi = bioblend.galaxy.GalaxyInstance(url, api_key, email, password)
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

    def _wait_datasets(self, datasets, polling_interval, break_on_error=True):
        """
        Wait for datasets to come out of the pending states.

        :type datasets: :class:`~collections.Iterable` of
          :class:`~.wrappers.Dataset`
        :param datasets: datasets

        :type polling_interval: float
        :param polling_interval: polling interval in seconds

        :type break_on_error: bool
        :param break_on_error: if ``True``, raise a RuntimeError exception as
          soon as at least one of the datasets is in the 'error' state.

        .. warning::

          This is a blocking operation that can take a very long time.
          Also, note that this method does not return anything;
          however, each input dataset is refreshed (possibly multiple
          times) during the execution.
        """
        def poll(ds_list):
            pending = []
            for ds in ds_list:
                ds.refresh()
                self.log.info('{0.id}: {0.state}'.format(ds))
                if break_on_error and ds.state == 'error':
                    raise RuntimeError(_get_error_info(ds))
                if ds.state in _PENDING_DS_STATES:
                    pending.append(ds)
            return pending

        self.log.info('waiting for datasets')
        while datasets:
            datasets = poll(datasets)
            time.sleep(polling_interval)
