"""
An interface the clients should implement.

This class is primarily a helper for the library and user code
should not use it directly.
"""

import time

import requests
from requests.packages.urllib3.exceptions import ProtocolError

import bioblend
# The following import must be preserved for compatibility because
# ConnectionError class was originally defined here
from bioblend import ConnectionError  # noqa: I202


class Client(object):

    # Class variables that configure GET request retries.  Note that since these
    # are class variables their values are shared by all Client instances --
    # i.e., HistoryClient, WorkflowClient, etc.
    #
    # Number of attempts before giving up on a GET request.
    _max_get_retries = 1
    # Delay in seconds between subsequent retries.
    _get_retry_delay = 10

    @classmethod
    def max_get_retries(cls):
        """
        The maximum number of attempts for a GET request.
        """
        return cls._max_get_retries

    @classmethod
    def set_max_get_retries(cls, value):
        """
        Set the maximum number of attempts for GET requests. A value greater
        than one causes failed GET requests to be retried `value` - 1 times.

        Default: 1
        """
        if value < 1:
            raise ValueError("Number of retries must be >= 1 (got: %s)" % value)
        cls._max_get_retries = value
        return cls

    @classmethod
    def get_retry_delay(cls):
        """
        The delay (in seconds) to wait before retrying a failed GET
        request.
        """
        return cls._get_retry_delay

    @classmethod
    def set_get_retry_delay(cls, value):
        """
        Set the delay (in seconds) to wait before retrying a failed GET
        request. Default: 10
        """
        if value < 0:
            raise ValueError("Retry delay must be >= 0 (got: %s)" % value)
        cls._get_retry_delay = value
        return cls

    def __init__(self, galaxy_instance):
        """
        A generic Client interface defining the common fields.

        All clients *must* define the following field (which will be
        used as part of the URL composition (e.g.,
        ``http://<galaxy_instance>/api/libraries``): ``self.module =
        'workflows' | 'libraries' | 'histories' | ...``
        """
        self.gi = galaxy_instance
        self.url = '/'.join([self.gi.url, self.module])

    def _get(self, id=None, deleted=False, contents=None, url=None,
             params=None, json=True):
        """
        Do a GET request, composing the URL from ``id``, ``deleted`` and
        ``contents``.  Alternatively, an explicit ``url`` can be provided.
        If ``json`` is set to ``True``, return a decoded JSON object
        (and treat an empty or undecodable response as an error).

        The request will optionally be retried as configured by
        ``max_get_retries`` and ``get_retry_delay``: this offers some
        resilience in the presence of temporary failures.

        :return: The decoded response if ``json`` is set to ``True``, otherwise
          the response object
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted,
                                    contents=contents)
        attempts_left = self.max_get_retries()
        retry_delay = self.get_retry_delay()
        bioblend.log.debug("GET - attempts left: %s; retry delay: %s",
                           attempts_left, retry_delay)
        msg = ''
        while attempts_left > 0:
            attempts_left -= 1
            try:
                r = self.gi.make_get_request(url, params=params)
            except (requests.exceptions.ConnectionError, ProtocolError) as e:
                msg = str(e)
                r = requests.Response()  # empty Response object used when raising ConnectionError
            else:
                if r.status_code == 200:
                    if not json:
                        return r
                    elif not r.content:
                        msg = "GET: empty response"
                    else:
                        try:
                            return r.json()
                        except ValueError:
                            msg = "GET: invalid JSON : %r" % (r.content,)
                else:
                    msg = "GET: error %s: %r" % (r.status_code, r.content)
            msg = "%s, %d attempts left" % (msg, attempts_left)
            if attempts_left <= 0:
                bioblend.log.error(msg)
                raise ConnectionError(msg, body=r.text,
                                      status_code=r.status_code)
            else:
                bioblend.log.warning(msg)
                time.sleep(retry_delay)

    def _post(self, payload, id=None, deleted=False, contents=None, url=None,
              files_attached=False):
        """
        Do a generic POST request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that contains additional
        request arguments which will be sent along with the request body.
        The payload dict may contain file handles (in which case the
        ``files_attached`` flag must be set to true).

        If ``files_attached`` is set to ``False``, the request body will be
        JSON-encoded; otherwise, it will be encoded as multipart/form-data.

        :return: The decoded response.
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted,
                                    contents=contents)
        return self.gi.make_post_request(url, payload=payload,
                                         files_attached=files_attached)

    def _put(self, payload, id=None, url=None, params=None):
        """
        Do a generic PUT request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that contains additional
        request arguments which will be sent along with the request body.

        :return: The decoded response.
        """
        if not url:
            url = self.gi._make_url(self, module_id=id)
        return self.gi.make_put_request(url, payload=payload, params=params)

    def _patch(self, payload, id=None, url=None, params=None):
        """
        Do a generic PATCH request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that contains additional
        request arguments which will be sent along with the request body.

        :return: The decoded response.
        """
        if not url:
            url = self.gi._make_url(self, module_id=id)
        return self.gi.make_patch_request(url, payload=payload, params=params)

    def _delete(self, payload=None, id=None, deleted=False, contents=None, url=None, params=None):
        """
        Do a generic DELETE request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that contains additional
        request arguments which will be sent along with the request body.

        :return: The decoded response.
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted,
                                    contents=contents)
        r = self.gi.make_delete_request(url, payload=payload, params=params)
        if r.status_code == 200:
            return r.json()
        # @see self.body for HTTP response body
        raise ConnectionError("Unexpected HTTP status code: %s" % r.status_code,
                              body=r.text, status_code=r.status_code)
