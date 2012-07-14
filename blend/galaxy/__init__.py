"""
A base representation of an instance of Galaxy
"""
import requests
import urlparse
from blend.galaxy import (libraries, histories, workflows, datasets, users)


class GalaxyInstance(object):
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

            from blend import galaxy

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

    def _make_url(self, module, module_id=None, deleted=False, contents=False):
        """
        Compose a URL based on the provided arguments.

        :type module: string
        :param module: The name of the base module for which to make the URL.
                       For example: ``libraries``, ``workflows``, ``histories``

        :type module_id: string
        :param module_id: The encoded ID for a specific module (eg, library ID)

        :type deleted: bool
        :param deleted: If ``True``, include ``deleted`` in the URL, after the module
                        name (eg, ``<base_url>/api/libraries/deleted``)

        :type contents: bool
        :param contents: If ``True``, include 'contents' in the URL, after the module ID:
                         ``<base_url>/api/libraries/<encoded_library_id>/contents``
        """
        c_url = self.url
        c_url = '/'.join([c_url, module.module])
        if deleted is True:
            c_url = '/'.join([c_url, 'deleted'])
        if module_id is not None:
            c_url = '/'.join([c_url, module_id])
            if contents is True:
                c_url = '/'.join([c_url, 'contents'])
        return c_url

    def make_get_request(self, url, params=None):
        """
        Make a GET request using the provided url.

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
        r = requests.get(url, verify=self.verify, params=params)
        return r

    def make_post_request(self, url, payload, params=None):
        """
        Make a POST request using the provided ``url`` and ``payload``.
        The ``payload`` must be a dict that can be converted into a JSON
        object (via ``simplejson.dumps``)

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
        r = requests.post(url, data=payload, headers=self.json_headers,
                verify=self.verify, params=params)
        return r

    def make_delete_request(self, url, payload=None, params=None):
        """
        Make a DELETE request using the provided ``url`` and the optional
        arguments.
        The ``payload`` must be a dict that can be converted into a JSON
        object (via ``simplejson.dumps``)

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
        r = requests.delete(url, verify=self.verify, data=payload, params=params)
        return r
