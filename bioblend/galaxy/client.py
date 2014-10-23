"""
An interface the clients should implement.

This class is primarily a helper for the library and user code
should not use it directly.
"""
import requests
try:
    # The following import will work only for Requests >= 2.4.0 and is
    # needed to workaround its "urllib3.exceptions.ProtocolError not
    # wrapped" bug: https://github.com/kennethreitz/requests/issues/2192
    from requests.packages.urllib3.exceptions import ProtocolError
except ImportError:
    ProtocolError = None
import json
import time

import bioblend as bb


class ConnectionError(Exception):
    """
    An exception class that is raised when unexpected HTTP responses come back.

    Should make it easier to debug when strange HTTP things happen such as a
    proxy server getting in the way of the request etc.
    @see: body attribute to see the content of the http response
    """
    def __init__(self, message, body=None):
        self.message = message
        self.body = body

    def __str__(self):
        return "{0}: {1}".format(self.message, self.body)


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
        """The delay (in seconds) to wait before retrying a failed GET request."""
        return cls._get_retry_delay

    @classmethod
    def set_get_retry_delay(cls, value):
        """Set the delay (in seconds) to wait before retrying a failed GET request. Default: 1"""
        if value < 0:
            raise ValueError("Retry delay must be >= 0 (got: %s)" % value)
        cls._get_retry_delay = value
        return cls

    def __init__(self, galaxy_instance):
        """
        A generic Client interface defining the common fields.

        All clients *must* define the following field (which will be used as part
        of the URL composition (eg, http://<galaxy_instance>/api/libraries):
        ``self.module = 'workflows' | 'libraries' | 'histories' | ...``
        """
        self.gi = galaxy_instance
        self.url = '/'.join([self.gi.url, self.module])

    def _raw_get(self, id=None, deleted=False, contents=None, url=None,
                 params=None):
        """
        Do a GET request, composing the URL from ``id``, ``deleted`` and
        ``contents``.  Alternatively, an explicit ``url`` can be provided.

        The request will optionally be retried as configured by
        ``max_get_retries`` and ``get_retry_delay``: this offers some
        resilience in the presence of temporary failures.

        **NOTE:** Galaxy sometimes temporarily returns an empty body
        with HTTP 200 even when an API call went bad. For this reason,
        this method keeps trying until the response can be decoded as
        a valid JSON object, raising a ``ConnectionError``
        otherwise. This has to be taken into account when an empty
        response is acceptable (e.g., if this method is used to
        download an empty dataset).
        """
        attempts_left = self.max_get_retries()
        retry_delay = self.get_retry_delay()
        bb.log.debug("GET - attempts left: %s; retry delay: %s",
                     attempts_left, retry_delay)
        r = None
        while attempts_left > 0:
            attempts_left -= 1
            try:
                r = self.gi.make_get_request(url, params=params)
                if r.status_code == 200 and r.content:
                    return r
                else:
                    bb.log.info("GET request failed (response code: %s). %s attempts left",
                                r.status_code, attempts_left)
                    bb.log.debug("Response content: %s", r.content)
            except (requests.exceptions.ConnectionError, ProtocolError) as e:
                if attempts_left <= 0:
                    raise ConnectionError(e.message)  # raise client.ConnectionError
                else:
                    bb.log.warn("Error connecting to Galaxy: %s. Going to retry %s more times.", e, attempts_left)
            except ValueError as e:
                if attempts_left <= 0:
                    raise
                else:
                    bb.log.warn("Received invalid JSON reply from Galaxy: %s. Going to retry %s more times.", e, attempts_left)
            if attempts_left > 0:
                time.sleep(retry_delay)
        if r is None:
            msg = "Unable to issue request. gi.make_get_request returned None!"
        elif r.status_code != 200:
            msg = "Unexpected HTTP status code: %s" % r.status_code
        else:
            msg = "Empty reply from GET API call"
        raise ConnectionError(msg, r.content if r else None)

    def _get(self, id=None, deleted=False, contents=None, url=None,
             params=None):
        """
        Perform a :meth:`_raw_get` and return the decoded JSON.
        """
        return self._raw_get(id=id, deleted=deleted, contents=contents,
                             url=url, params=params).json()

    def _post(self, payload, id=None, deleted=False, contents=None, url=None, files_attached=False):
        """
        Do a generic POST request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that contains additional
        request arguments which will be sent along with the request body.
        The payload dict may contain file handles (in which case the files_attached
        flag must be set to true).

        The request body will be encoded in a JSON format if files_attached=False
        or will be encoded in a multipart/form-data format if files_attached=True.
        The return value will contain the response body as a JSON object.
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted, contents=contents)

        r = self.gi.make_post_request(url, payload=payload, files_attached=files_attached)

        return r

    def _put(self, payload, id=None, url=None, params=None):
        """
        Do a generic PUT request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that contains additional
        request arguments which will be sent along with the request body.

        The return value will html status code
        """
        if not url:
            url = self.gi._make_url(self, module_id=id)

        r = self.gi.make_put_request(url, payload=payload, params=params)

        return r

    def _delete(self, payload, id=None, deleted=False, contents=None, url=None):
        """
        Do a generic DELETE request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that can be converted
        into a JSON object (which will be done whthin this method)
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted, contents=contents)
        payload = json.dumps(payload)
        r = self.gi.make_delete_request(url, payload=payload)
        if r.status_code == 200:
            return r.json()
        # @see self.body for HTTP response body
        raise ConnectionError("Unexpected HTTP status code: %s" % r.status_code, body=r.text)
