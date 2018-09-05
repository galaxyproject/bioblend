"""
Helper class for Galaxy and ToolShed Instance object

This class is primarily a helper for the library and user code
should not use it directly.
A base representation of an instance
"""
import base64
import json

import requests
import six
from requests_toolbelt import MultipartEncoder
from six.moves.urllib.parse import urljoin, urlparse

from bioblend import ConnectionError


class GalaxyClient(object):

    def __init__(self, url, key=None, email=None, password=None, verify=True, timeout=None):
        """
        :param verify: Whether to verify the server's TLS certificate
        :type verify: boolean
        :param timeout: Timeout for requests operations, set to None for no timeout (the default).
        :type timeout: float
        """
        # Make sure the url scheme is defined (otherwise requests will not work)
        if not urlparse(url).scheme:
            url = "http://" + url
        # All of Galaxy's and ToolShed's API's are rooted at <url>/api so make that the url
        self.base_url = url
        self.url = urljoin(url, 'api')
        # If key has been supplied, use it; otherwise just set email and
        # password and grab user's key before first request.
        if key:
            self._key = key
        else:
            self._key = None
            self.email = email
            self.password = password
        self.json_headers = {'Content-Type': 'application/json'}
        self.verify = verify
        self.timeout = timeout

    def _make_url(self, module, module_id=None, deleted=False, contents=False):
        """
        Compose a URL based on the provided arguments.

        :type module: :class:`~.galaxy.Client` subclass
        :param module: The base module for which to make the URL. For
          example: an object of class LibraryClient, WorkflowClient,
          HistoryClient, ToolShedClient

        :type module_id: str
        :param module_id: The encoded ID for a specific module (eg, library ID)

        :type deleted: bool
        :param deleted: If ``True``, include ``deleted`` in the URL, after the module
                        name (eg, ``<base_url>/api/libraries/deleted``)

        :type contents: bool
        :param contents: If ``True``, include 'contents' in the URL, after the module ID:
                         ``<base_url>/api/libraries/<encoded_library_id>/contents``
        """
        c_url = '/'.join([self.url, module.module])
        if deleted is True:
            c_url = '/'.join([c_url, 'deleted'])
        if module_id is not None:
            c_url = '/'.join([c_url, module_id])
            if contents is True:
                c_url = '/'.join([c_url, 'contents'])
        return c_url

    def make_get_request(self, url, **kwargs):
        """
        Make a GET request using the provided ``url``.

        Keyword arguments are the same as in requests.request.

        If ``verify`` is not provided, ``self.verify`` will be used.

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.

        :rtype: requests.Response
        :return: the response object.
        """
        params = kwargs.get('params')
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
        kwargs['params'] = params
        kwargs.setdefault('verify', self.verify)
        kwargs.setdefault('timeout', self.timeout)
        r = requests.get(url, **kwargs)
        return r

    def make_post_request(self, url, payload, params=None, files_attached=False):
        """
        Make a POST request using the provided ``url`` and ``payload``.
        The ``payload`` must be a dict that contains the request values.
        The payload dict may contain file handles (in which case the files_attached
        flag must be set to true).

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.

        :return: The decoded response.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params

        # Compute data, headers, params arguments for request.post,
        # leveraging the requests-toolbelt library if any files have
        # been attached.
        if files_attached:
            payload.update(params)
            payload = MultipartEncoder(fields=payload)
            headers = self.json_headers.copy()
            headers['Content-Type'] = payload.content_type
            post_params = {}
        else:
            payload = json.dumps(payload)
            headers = self.json_headers
            post_params = params

        r = requests.post(url, data=payload, headers=headers,
                          verify=self.verify, params=post_params,
                          timeout=self.timeout)
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:
                raise ConnectionError("Request was successful, but cannot decode the response content: %s" %
                                      e, body=r.content, status_code=r.status_code)
        # @see self.body for HTTP response body
        raise ConnectionError("Unexpected HTTP status code: %s" % r.status_code,
                              body=r.text, status_code=r.status_code)

    def make_delete_request(self, url, payload=None, params=None):
        """
        Make a DELETE request using the provided ``url`` and the optional
        arguments.
        The ``payload`` must be a dict that can be converted into a JSON
        object (via ``json.dumps``)

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.

        :rtype: requests.Response
        :return: the response object.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
        if payload is not None:
            payload = json.dumps(payload)
        headers = self.json_headers
        r = requests.delete(url, verify=self.verify, data=payload, params=params,
                            headers=headers, timeout=self.timeout)
        return r

    def make_put_request(self, url, payload=None, params=None):
        """
        Make a PUT request using the provided ``url`` with required payload.
        The ``payload`` must be a dict that can be converted into a JSON
        object (via ``json.dumps``).

        :return: The decoded response.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params

        payload = json.dumps(payload)
        headers = self.json_headers
        r = requests.put(url, data=payload, params=params, headers=headers,
                         verify=self.verify, timeout=self.timeout)
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:
                raise ConnectionError("Request was successful, but cannot decode the response content: %s" %
                                      e, body=r.content, status_code=r.status_code)
        # @see self.body for HTTP response body
        raise ConnectionError("Unexpected HTTP status code: %s" % r.status_code,
                              body=r.text, status_code=r.status_code)

    def make_patch_request(self, url, payload=None, params=None):
        """
        Make a PATCH request using the provided ``url`` with required payload.
        The ``payload`` must be a dict that can be converted into a JSON
        object (via ``json.dumps``).

        :return: The decoded response.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params

        payload = json.dumps(payload)
        headers = self.json_headers
        r = requests.patch(url, data=payload, params=params, headers=headers,
                           verify=self.verify, timeout=self.timeout)
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:
                raise ConnectionError("Request was successful, but cannot decode the response content: %s" %
                                      e, body=r.content, status_code=r.status_code)
        # @see self.body for HTTP response body
        raise ConnectionError("Unexpected HTTP status code: %s" % r.status_code,
                              body=r.text, status_code=r.status_code)

    @property
    def key(self):
        if not self._key and self.email is not None and self.password is not None:
            unencoded_credentials = "%s:%s" % (self.email, self.password)
            authorization = base64.b64encode(unencoded_credentials.encode())
            headers = self.json_headers.copy()
            headers["Authorization"] = authorization
            auth_url = "%s/authenticate/baseauth" % self.url
            # make_post_request uses default_params, which uses this and
            # sets wrong headers - so using lower level method.
            r = requests.get(auth_url, verify=self.verify, headers=headers)
            if r.status_code != 200:
                raise Exception("Failed to authenticate user.")
            response = r.json()
            if isinstance(response, (six.string_types, six.text_type)):
                # bug in Tool Shed
                response = json.loads(response)
            self._key = response["api_key"]
        return self._key

    @property
    def default_params(self):
        return {'key': self.key}
