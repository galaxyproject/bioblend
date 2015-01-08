"""
An interface the clients should implement.

This class is primarily a helper for the library and user code
should not use it directly.
"""

import json
import time

import requests
try:
    # The following import will work only for Requests >= 2.4.0 and is
    # needed to workaround its "urllib3.exceptions.ProtocolError not
    # wrapped" bug: https://github.com/kennethreitz/requests/issues/2192
    # pylint: disable=E0611,F0401
    from requests.packages.urllib3.exceptions import ProtocolError
    # pylint: enable=E0611,F0401
except ImportError:
    ProtocolError = None  # pylint: disable=C0103

import bioblend as bb


class ConnectionError(Exception):
    """
    An exception class that is raised when unexpected HTTP responses come back.

    Should make it easier to debug when strange HTTP things happen such as a
    proxy server getting in the way of the request etc.
    @see: body attribute to see the content of the http response
    """
    def __init__(self, message, body=None):
        super(ConnectionError, self).__init__(message)
        self.body = body

    def __str__(self):
        return "{0}: {1}".format(self.args[0], self.body)


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
        request. Default: 1
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
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted,
                                    contents=contents)
        attempts_left = self.max_get_retries()
        retry_delay = self.get_retry_delay()
        bb.log.debug("GET - attempts left: %s; retry delay: %s",
                     attempts_left, retry_delay)
        msg = ''
        while attempts_left > 0:
            attempts_left -= 1
            try:
                r = self.gi.make_get_request(url, params=params)
            except (requests.exceptions.ConnectionError, ProtocolError) as e:
                msg = str(e)
            else:
                if r is None:
                    msg = "GET: no response"
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
                bb.log.error(msg)
                raise ConnectionError(msg)
            else:
                bb.log.warn(msg)
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

        The return value will contain the response body as a JSON object.
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

        This method returns the HTTP request object.
        """
        if not url:
            url = self.gi._make_url(self, module_id=id)
        return self.gi.make_put_request(url, payload=payload, params=params)

    def _delete(self, payload, id=None, deleted=False, contents=None, url=None):
        """
        Do a generic DELETE request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that can be converted
        into a JSON object (which will be done within this method)
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted,
                                    contents=contents)
        payload = json.dumps(payload)
        r = self.gi.make_delete_request(url, payload=payload)
        if r.status_code == 200:
            return r.json()
        # @see self.body for HTTP response body
        raise ConnectionError(
            "Unexpected HTTP status code: %s" % r.status_code, body=r.text
        )
