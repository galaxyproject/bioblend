"""
Helper class for Galaxy and ToolShed Instance object

This class is primarily a helper for the library and user code
should not use it directly.
A base representation of an instance
"""

import base64
import contextlib
import json
import logging
import time
from collections.abc import Iterator
from types import TracebackType
from typing import (
    Any,
)

import requests
import tusclient.client
import tusclient.exceptions
from requests.adapters import HTTPAdapter
from requests_toolbelt import MultipartEncoder
from tusclient.storage.filestorage import FileStorage
from tusclient.uploader.uploader import Uploader
from typing_extensions import Self
from urllib3 import BaseHTTPResponse
from urllib3.connectionpool import ConnectionPool
from urllib3.util.retry import Retry

from bioblend import ConnectionError
from bioblend.util import FileStream

log = logging.getLogger(__name__)

UPLOAD_CHUNK_SIZE = 10**7

# Default settings for retrying requests rejected with HTTP status 429 (Too
# Many Requests). ``MAX_TOTAL_RETRY_DELAY`` is the limit which normally applies:
# retrying stops once that much time has been spent waiting. ``MAX_429_RETRIES``
# is a backstop for the case where the waits are all zero, e.g. when
# ``max_retry_after`` is set to 0, since the delay budget is then never used up.
DEFAULT_MAX_TOTAL_RETRY_DELAY = 60.0
DEFAULT_MAX_RETRY_AFTER = 30.0
DEFAULT_MAX_429_RETRIES = 10
# Base of the exponential backoff used when a 429 response carries no
# Retry-After header, and the random fraction added on top of it.
RETRY_BACKOFF_FACTOR = 1.0
RETRY_BACKOFF_JITTER = 0.5
# Number of connections kept in the pool when ``use_session`` is enabled.
SESSION_POOL_MAXSIZE = 20


class _RateLimitRetry(Retry):
    """
    Retry policy for requests rejected with HTTP status 429 (Too Many Requests).

    urllib3 already honours the ``Retry-After`` header, but puts no upper bound
    on it, nor on the total time spent sleeping. This subclass adds both, so
    that a rate-limited request fails within a predictable amount of time
    instead of blocking for as long as the server asks for.
    """

    def __init__(
        self,
        *args: Any,
        max_retry_after: float = DEFAULT_MAX_RETRY_AFTER,
        max_total_retry_delay: float = DEFAULT_MAX_TOTAL_RETRY_DELAY,
        total_delay: float = 0.0,
        **kwargs: Any,
    ) -> None:
        self.max_retry_after = max_retry_after
        self.max_total_retry_delay = max_total_retry_delay
        self.total_delay = total_delay
        super().__init__(*args, **kwargs)

    def new(self, **kwargs: Any) -> "_RateLimitRetry":
        # Retry objects are immutable: urllib3 builds a new one for each
        # attempt, so the extra attributes must be carried over explicitly,
        # otherwise both the cap and the accumulated delay would be lost after
        # the first retry.
        kwargs.setdefault("max_retry_after", self.max_retry_after)
        kwargs.setdefault("max_total_retry_delay", self.max_total_retry_delay)
        kwargs.setdefault("total_delay", self.total_delay)
        return super().new(**kwargs)

    def get_retry_after(self, response: BaseHTTPResponse) -> float | None:
        retry_after = super().get_retry_after(response)
        if retry_after is None:
            return None
        return min(retry_after, self.max_retry_after)

    def sleep(self, response: BaseHTTPResponse | None = None) -> None:
        start = time.monotonic()
        super().sleep(response)
        self.total_delay += time.monotonic() - start

    def is_exhausted(self) -> bool:
        return self.total_delay >= self.max_total_retry_delay or super().is_exhausted()

    def increment(
        self,
        method: str | None = None,
        url: str | None = None,
        response: BaseHTTPResponse | None = None,
        error: Exception | None = None,
        _pool: ConnectionPool | None = None,
        _stacktrace: TracebackType | None = None,
    ) -> "_RateLimitRetry":
        # Raises MaxRetryError when the budget or the backstop count is spent,
        # in which case urllib3 returns the last response (raise_on_status is
        # disabled) and BioBlend reports it as usual.
        new_retry = super().increment(method, url, response, error, _pool, _stacktrace)
        if response is not None:
            log.warning(
                "%s %s was rate-limited with HTTP status %s, retrying (%.1f of %.1f s of retry delay budget used)",
                method,
                url,
                response.status,
                self.total_delay,
                self.max_total_retry_delay,
            )
        return new_retry


class GalaxyClient:
    def __init__(
        self,
        url: str,
        key: str | None = None,
        email: str | None = None,
        password: str | None = None,
        *,
        token: str | None = None,
        verify: bool = True,
        timeout: float | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        :param verify: Whether to verify the server's TLS certificate
        :type verify: bool
        :param timeout: Timeout for requests operations, set to None for no timeout (the default).
        :type timeout: float
        """
        self.verify = verify
        self.timeout = timeout
        # Settings for retrying requests rejected with HTTP status 429, used to
        # build the session, so they need to be set before any request is made.
        self._max_429_retries = DEFAULT_MAX_429_RETRIES
        self._max_retry_after = DEFAULT_MAX_RETRY_AFTER
        self._max_total_retry_delay = DEFAULT_MAX_TOTAL_RETRY_DELAY
        # Persistent session, only used when `use_session` is enabled.
        self._session: requests.Session | None = None
        # Make sure the URL scheme is defined (otherwise requests will not work)
        if not url.lower().startswith("http"):
            found_scheme = None
            # Try to guess the scheme, starting from the more secure
            for scheme in ("https://", "http://"):
                log.warning("Missing scheme in url, trying with %s", scheme)
                with contextlib.suppress(requests.RequestException), self._session_ctx() as session:
                    r = session.get(
                        scheme + url,
                        timeout=self.timeout,
                        verify=self.verify,
                    )
                    r.raise_for_status()
                    found_scheme = scheme
                    break
            else:
                raise ValueError(f"Missing scheme in url {url}")
            url = found_scheme + url
        self.base_url = url.rstrip("/")
        # All of Galaxy's and ToolShed's API's are rooted at <url>/api so make that the url
        self.url = f"{self.base_url}/api"
        # If key has been supplied, use it; otherwise just set email and
        # password and grab user's key before first request.
        if key:
            self._key: str | None = key
        elif token:
            self.token: str | None = token
        else:
            self._key = None
            self.email = email
            self.password = password
        self.json_headers: dict[str, str | bytes | None] = {"Content-Type": "application/json"}
        if user_agent:
            self.json_headers["User-Agent"] = user_agent
        # json_headers needs to be set before key can be defined, otherwise authentication with email/password causes an error
        if token:
            self.json_headers["Authorization"] = f"Bearer {token}"
        else:
            self.json_headers["x-api-key"] = self.key
        # Number of attempts before giving up on a GET request.
        self._max_get_attempts = 1
        # Delay in seconds between subsequent retries.
        self._get_retry_delay = 10.0

    def _new_session(self) -> requests.Session:
        """
        Create a session which retries requests rejected with HTTP status 429.

        Only 429 responses are retried: connection and read errors are re-raised
        immediately, as they were before sessions were introduced.
        """
        retry = _RateLimitRetry(
            # Only the status counter limits retrying, so that `total` does not
            # allow connection and read errors to be retried too. Those are
            # counted down to a negative value on their first occurrence, which
            # makes urllib3 give up immediately and raise the same exceptions
            # requests raises with its own default (non-retrying) adapter.
            total=None,
            status=self._max_429_retries,
            connect=0,
            read=False,
            other=0,
            status_forcelist=frozenset({429}),
            # Retry all methods, including POST: a 429 response means that the
            # request was rejected before being processed, so replaying it
            # cannot duplicate any server-side action.
            allowed_methods=None,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            backoff_max=self._max_retry_after,
            backoff_jitter=RETRY_BACKOFF_JITTER,
            respect_retry_after_header=True,
            # Return the last response instead of raising, so that the caller
            # gets the usual ConnectionError with its body and status code.
            raise_on_status=False,
            max_retry_after=self._max_retry_after,
            max_total_retry_delay=self._max_total_retry_delay,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=SESSION_POOL_MAXSIZE)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @contextlib.contextmanager
    def _session_ctx(self, retry: bool = True) -> Iterator[requests.Session]:
        """
        Yield the session to use for a single request.

        Unless ``use_session`` is enabled, a new session is created for each
        request and closed afterwards, which is what ``requests.get()`` and
        friends do internally anyway.

        Retrying must be disabled for requests whose body is a stream which
        cannot be rewound, e.g. a multipart upload: neither urllib3 nor requests
        rewind the body between attempts, so a replayed request would send a
        truncated body and hang waiting on its own Content-Length.
        """
        if not retry:
            with requests.Session() as session:
                yield session
        elif self._session is not None:
            yield self._session
        else:
            session = self._new_session()
            try:
                yield session
            finally:
                session.close()

    def _reset_session(self) -> None:
        """
        Rebuild the persistent session, if any, e.g. after a settings change.
        """
        if self._session is not None:
            self._session.close()
            self._session = self._new_session()

    @property
    def use_session(self) -> bool:
        """
        Whether a single session is reused for all requests. Default: ``False``

        Enabling this reuses connections across requests, which is faster when
        making many of them. The resulting object should not be shared between
        threads, and ``close()`` should be called when done with it.
        """
        return self._session is not None

    @use_session.setter
    def use_session(self, value: bool) -> None:
        if value:
            if self._session is None:
                self._session = self._new_session()
        else:
            self.close()

    def close(self) -> None:
        """
        Close the persistent session, if any, releasing its connections.
        """
        if self._session is not None:
            self._session.close()
            self._session = None

    def __enter__(self) -> Self:
        self.use_session = True
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @property
    def max_429_retries(self) -> int:
        """
        The maximum number of retries of a request rejected with HTTP status
        429 (Too Many Requests). Default: 10

        This is a backstop for the case where the waits between attempts are all
        zero: the limit which normally applies is ``max_total_retry_delay``.
        """
        return self._max_429_retries

    @max_429_retries.setter
    def max_429_retries(self, value: int) -> None:
        if value < 0:
            raise ValueError(f"Number of retries must be >= 0 (got: {value})")
        self._max_429_retries = value
        self._reset_session()

    @property
    def max_total_retry_delay(self) -> float:
        """
        The maximum total time (in seconds) to spend waiting before giving up on
        a request rejected with HTTP status 429. Default: 60.0

        Set this to 0 to disable retrying of rate-limited requests. Since the
        budget is checked after each wait, a request can take up to
        ``max_total_retry_delay`` + ``max_retry_after`` seconds.
        """
        return self._max_total_retry_delay

    @max_total_retry_delay.setter
    def max_total_retry_delay(self, value: float) -> None:
        if value < 0:
            raise ValueError(f"Retry delay budget must be >= 0 (got: {value})")
        self._max_total_retry_delay = value
        self._reset_session()

    @property
    def max_retry_after(self) -> float:
        """
        The maximum time (in seconds) to wait before a single retry of a request
        rejected with HTTP status 429. Default: 30.0

        Longer delays requested by the server through the ``Retry-After`` header
        are capped to this value.
        """
        return self._max_retry_after

    @max_retry_after.setter
    def max_retry_after(self, value: float) -> None:
        if value < 0:
            raise ValueError(f"Retry delay must be >= 0 (got: {value})")
        self._max_retry_after = value
        self._reset_session()

    @property
    def max_get_attempts(self) -> int:
        """
        The maximum number of attempts for a GET request. Default: 1
        """
        return self._max_get_attempts

    @max_get_attempts.setter
    def max_get_attempts(self, value: int) -> None:
        """
        Set the maximum number of attempts for GET requests. A value greater
        than one causes failed GET requests to be retried `value` - 1 times.
        """
        if value < 1:
            raise ValueError(f"Number of attempts must be >= 1 (got: {value})")
        self._max_get_attempts = value

    @property
    def get_retry_delay(self) -> float:
        """
        The delay (in seconds) to wait before retrying a failed GET request.
        Default: 10.0
        """
        return self._get_retry_delay

    @get_retry_delay.setter
    def get_retry_delay(self, value: float) -> None:
        """
        Set the delay (in seconds) to wait before retrying a failed GET
        request.
        """
        if value < 0:
            raise ValueError(f"Retry delay must be >= 0 (got: {value})")
        self._get_retry_delay = value

    def make_get_request(self, url: str, **kwargs: Any) -> requests.Response:
        """
        Make a GET request using the provided ``url``.

        Keyword arguments are the same as in requests.request.

        If ``verify`` is not provided, ``self.verify`` will be used.

        :rtype: requests.Response
        :return: the response object.
        """
        headers = self.json_headers
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.verify)
        with self._session_ctx() as session:
            r = session.get(url, headers=headers, **kwargs)
        return r

    def make_post_request(
        self, url: str, payload: dict | None = None, params: dict | None = None, files_attached: bool = False
    ) -> Any:
        """
        Make a POST request using the provided ``url`` and ``payload``.
        The ``payload`` must be a dict that contains the request values.
        The payload dict may contain file handles (in which case the files_attached
        flag must be set to true).

        :return: The decoded response.
        """

        def my_dumps(d: dict) -> dict:
            """
            Apply ``json.dumps()`` to the values of the dict ``d`` if they are
            not of type ``FileStream``.
            """
            for k, v in d.items():
                if not isinstance(v, (FileStream, str, bytes)):
                    d[k] = json.dumps(v)
            return d

        # Compute data, headers, params arguments for request.post,
        # leveraging the requests-toolbelt library if any files have
        # been attached.
        if files_attached:
            payload_copy = payload.copy() if payload is not None else {}
            if params:
                payload_copy.update(params)
            data = MultipartEncoder(fields=my_dumps(payload_copy))
            headers = self.json_headers.copy()
            headers["Content-Type"] = data.content_type
            post_params = None
        else:
            data = json.dumps(payload) if payload is not None else None
            headers = self.json_headers
            post_params = params

        # A multipart body is a stream which cannot be replayed, so such
        # requests are not retried on HTTP status 429.
        with self._session_ctx(retry=not files_attached) as session:
            r = session.post(
                url,
                params=post_params,
                data=data,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False,
                verify=self.verify,
            )
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:
                raise ConnectionError(
                    f"Request was successful, but cannot decode the response content: {e}",
                    body=r.content,
                    status_code=r.status_code,
                )
        # @see self.body for HTTP response body
        raise ConnectionError(
            f"Unexpected HTTP status code: {r.status_code}",
            body=r.text,
            status_code=r.status_code,
        )

    def make_delete_request(
        self, url: str, payload: dict | None = None, params: dict | None = None
    ) -> requests.Response:
        """
        Make a DELETE request using the provided ``url`` and the optional
        arguments.

        :type payload: dict
        :param payload: a JSON-serializable dictionary

        :rtype: requests.Response
        :return: the response object.
        """
        data = json.dumps(payload) if payload is not None else None
        headers = self.json_headers
        with self._session_ctx() as session:
            r = session.delete(
                url,
                params=params,
                data=data,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False,
                verify=self.verify,
            )
        return r

    def make_put_request(self, url: str, payload: dict | None = None, params: dict | None = None) -> Any:
        """
        Make a PUT request using the provided ``url`` with required payload.

        :type payload: dict
        :param payload: a JSON-serializable dictionary

        :return: The decoded response.
        """
        data = json.dumps(payload) if payload is not None else None
        headers = self.json_headers
        with self._session_ctx() as session:
            r = session.put(
                url,
                params=params,
                data=data,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False,
                verify=self.verify,
            )
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:
                raise ConnectionError(
                    f"Request was successful, but cannot decode the response content: {e}",
                    body=r.content,
                    status_code=r.status_code,
                )
        # @see self.body for HTTP response body
        raise ConnectionError(
            f"Unexpected HTTP status code: {r.status_code}",
            body=r.text,
            status_code=r.status_code,
        )

    def make_patch_request(self, url: str, payload: dict | None = None, params: dict | None = None) -> Any:
        """
        Make a PATCH request using the provided ``url`` with required payload.

        :type payload: dict
        :param payload: a JSON-serializable dictionary

        :return: The decoded response.
        """
        data = json.dumps(payload) if payload is not None else None
        headers = self.json_headers
        with self._session_ctx() as session:
            r = session.patch(
                url,
                params=params,
                data=data,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False,
                verify=self.verify,
            )
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:
                raise ConnectionError(
                    f"Request was successful, but cannot decode the response content: {e}",
                    body=r.content,
                    status_code=r.status_code,
                )
        # @see self.body for HTTP response body
        raise ConnectionError(
            f"Unexpected HTTP status code: {r.status_code}",
            body=r.text,
            status_code=r.status_code,
        )

    def get_tus_uploader(
        self,
        path: str,
        url: str = "/upload/resumable_upload",
        storage: str | None = None,
        metadata: dict | None = None,
        chunk_size: int | None = UPLOAD_CHUNK_SIZE,
    ) -> Uploader:
        """
        Return the tus client uploader object for uploading to the Galaxy tus endpoint

        :type path: str
        :param path: path of the file to upload

        :type url: str
        :param url: URL (relative to base URL) of the upload endpoint

        :type storage: str
        :param storage: Local path to store URLs resuming uploads

        :type metadata: dict
        :param metadata: Metadata to send with upload request

        :type chunk_size: int
        :param chunk_size: Number of bytes to send in each chunk

        :rtype: tusclient.uploader.Uploader
        :return: tus uploader object
        """
        key = self.key
        assert key is not None
        headers = {"x-api-key": key}
        client = tusclient.client.TusClient(self.url + url, headers=headers)
        url_storage = FileStorage(storage) if storage else None  # type: ignore[no-untyped-call]
        try:
            return client.uploader(
                file_path=path,
                chunk_size=chunk_size,
                metadata=metadata,
                store_url=url_storage is not None,
                url_storage=url_storage,
            )
        except tusclient.exceptions.TusCommunicationError as exc:
            raise ConnectionError(
                f"Unexpected HTTP status code: {exc.status_code}",
                body=str(exc),
                status_code=exc.status_code,
            )

    @property
    def key(self) -> str | None:
        if not self._key and self.email is not None and self.password is not None:
            unencoded_credentials = f"{self.email}:{self.password}"
            authorization = base64.b64encode(unencoded_credentials.encode())
            headers = self.json_headers.copy()
            headers["Authorization"] = authorization
            auth_url = f"{self.url}/authenticate/baseauth"
            # Use lower level method instead of make_get_request() because we
            # need the additional Authorization header.
            with self._session_ctx() as session:
                r = session.get(
                    auth_url,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify,
                )
            if r.status_code != 200:
                raise Exception("Failed to authenticate user.")
            response = r.json()
            if isinstance(response, str):
                # bug in Tool Shed
                response = json.loads(response)
            self._key = response["api_key"]
        return self._key


def _tus_uploader_session_id(self: Uploader) -> str:
    assert self.url
    return self.url.rsplit("/", 1)[1]  # type: ignore[unreachable]


# monkeypatch a session_id property on to uploader
Uploader.session_id = property(_tus_uploader_session_id)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
