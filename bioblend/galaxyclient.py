"""
Helper class for Galaxy and ToolShed Instance object

This class is primarily a helper for the library and user code
should not use it directly.
A base representation of an instance
"""
import base64
import json
from urllib.parse import (
    urljoin,
    urlparse,
)

import requests
from requests_toolbelt import MultipartEncoder

from bioblend import ConnectionError
from bioblend.util import FileStream


class GalaxyClient(object):

    def __init__(self, url, key=None, email=None, password=None, verify=True, timeout=None):
        """
        :param verify: Whether to verify the server's TLS certificate
        :type verify: bool
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

        def my_dumps(d):
            """
            Apply ``json.dumps()`` to the values of the dict ``d`` if they are
            not of type ``FileStream``.
            """
            for k, v in d.items():
                if not isinstance(v, FileStream):
                    d[k] = json.dumps(v)
            return d

        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params

        # Compute data, headers, params arguments for request.post,
        # leveraging the requests-toolbelt library if any files have
        # been attached.
        if files_attached:
            payload = my_dumps(payload)
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
                          timeout=self.timeout, allow_redirects=False)
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

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.

        :type payload: dict
        :param payload: a JSON-serializable dictionary

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
                            headers=headers, timeout=self.timeout, allow_redirects=False)
        return r

    def make_put_request(self, url, payload=None, params=None):
        """
        Make a PUT request using the provided ``url`` with required payload.

        :type payload: dict
        :param payload: a JSON-serializable dictionary

        :return: The decoded response.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params

        payload = json.dumps(payload)
        headers = self.json_headers
        r = requests.put(url, data=payload, params=params, headers=headers,
                         verify=self.verify, timeout=self.timeout, allow_redirects=False)
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

        :type payload: dict
        :param payload: a JSON-serializable dictionary

        :return: The decoded response.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params

        payload = json.dumps(payload)
        headers = self.json_headers
        r = requests.patch(url, data=payload, params=params, headers=headers,
                           verify=self.verify, timeout=self.timeout, allow_redirects=False)
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
            if isinstance(response, str):
                # bug in Tool Shed
                response = json.loads(response)
            self._key = response["api_key"]
        return self._key

    @property
    def default_params(self):
        return {'key': self.key}
