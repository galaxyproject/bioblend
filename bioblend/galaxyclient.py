"""
Helper class for Galaxy and ToolShed Instance object

This class is primarily a helper for the library and user code
should not use it directly.
A base representation of an instance
"""
import base64
import json

import requests
from requests_toolbelt import MultipartEncoder
import six

from .galaxy.client import ConnectionError


class GalaxyClient(object):

    def _make_url(self, module, module_id=None, deleted=False, contents=False):
        """
        Compose a URL based on the provided arguments.

        :type module: :class:`~.galaxy.Client` subclass
        :param module: The base module for which to make the URL. For
          example: an object of class LibraryClient, WorkflowClient,
          HistoryClient, ToolShedClient

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

    def make_get_request(self, url, **kwargs):
        """
        Make a GET request using the provided ``url``.

        Keyword arguments are the same as in requests.request.

        If ``verify`` is not provided, ``self.verify`` will be used.

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.
        """
        params = kwargs.get('params')
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
        kwargs['params'] = params
        kwargs.setdefault('verify', self.verify)
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

        The return value will contain the response body as a JSON object.
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
                          verify=self.verify, params=post_params)
        if r.status_code == 200:
            return r.json()
        # @see self.body for HTTP response body
        raise ConnectionError("Unexpected response from galaxy: %s" %
                              r.status_code, body=r.text)

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
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
        r = requests.delete(url, verify=self.verify, data=payload, params=params)
        return r

    def make_put_request(self, url, payload=None, params=None):
        """
        Make a PUT request using the provided ``url`` with required playload
        The ``payload`` must be a dict that can be converted into a JSON
        object (via ``json.dumps``)
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params

        payload = json.dumps(payload)
        r = requests.put(url, verify=self.verify, data=payload, params=params)
        return r

    @property
    def key(self):
        if not self._key and self.email is not None and self.password is not None:
            unencoded_credentials = "%s:%s" % (self.email, self.password)
            authorization = base64.b64encode(unencoded_credentials)
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

    def _init_auth(self, key, email, password):
        # If key supplied use it, otherwise just set email and password and
        # grab users key before first request.
        if key:
            self._key = key
        else:
            self._key = None
            self.email = email
            self.password = password

    @property
    def default_params(self):
        return {'key': self.key}
