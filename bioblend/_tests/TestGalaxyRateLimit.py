"""
Tests on the handling of HTTP status 429 (Too Many Requests) responses.

These tests do not need a Galaxy instance: they run against a local HTTP server
replying with a canned sequence of status codes. A real server is needed
because the retrying happens inside urllib3, below the layer at which HTTP
mocking libraries usually work.
"""

import re
import time
import unittest
from typing import Any

import pytest
import requests
from pytest_httpserver import HTTPServer
from requests.adapters import HTTPAdapter
from werkzeug import (
    Request,
    Response,
)

from bioblend import ConnectionError
from bioblend.galaxy import GalaxyInstance
from bioblend.galaxyclient import GalaxyClient


def respond_with_statuses(server: HTTPServer, statuses: list[int], retry_after: int | str | None = None) -> None:
    """
    Make ``server`` reply to any request with a canned sequence of status codes.

    The last status code of the sequence is repeated for any further request.
    """

    def handler(request: Request) -> Response:
        # The server logs each request only after its handler has returned.
        status = statuses[min(len(server.log), len(statuses) - 1)]
        body = '{"ok": true}' if status == 200 else '{"error": "nope"}'
        headers = {"Retry-After": str(retry_after)} if status == 429 and retry_after is not None else {}
        return Response(body, status=status, headers=headers, content_type="application/json")

    server.expect_request(re.compile(".*")).respond_with_handler(handler)


@pytest.fixture
def new_sessions(monkeypatch: pytest.MonkeyPatch) -> list[requests.Session]:
    """
    Return the list of the sessions created by ``GalaxyClient`` during the test.
    """
    sessions: list[requests.Session] = []
    original_new_session = GalaxyClient._new_session

    def new_session(self: GalaxyClient) -> requests.Session:
        session = original_new_session(self)
        sessions.append(session)
        return session

    monkeypatch.setattr(GalaxyClient, "_new_session", new_session)
    return sessions


def open_pool_count(session: requests.Session, url: str) -> int:
    """
    Return the number of connection pools kept open by ``session`` for ``url``.
    """
    adapter = session.get_adapter(url)
    assert isinstance(adapter, HTTPAdapter)
    return len(adapter.poolmanager.pools)


def galaxy_instance(server: HTTPServer, **kwargs: object) -> GalaxyInstance:
    """
    Return a ``GalaxyInstance`` pointing at ``server``, with retry delays short
    enough to keep the tests fast.
    """
    gi = GalaxyInstance(server.url_for(""), key="whatever")
    gi.max_retry_after = 0.1
    gi.max_total_retry_delay = 1.0
    for name, value in kwargs.items():
        setattr(gi, name, value)
    return gi


class TestGalaxyRateLimit:
    def test_get_is_retried(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [429, 429, 200], retry_after=1)
        gi = galaxy_instance(httpserver)
        r = gi.make_get_request(f"{gi.url}/libraries")
        assert r.status_code == 200
        assert len(httpserver.log) == 3

    def test_post_is_retried(self, httpserver: HTTPServer):
        # A 429 response means the request was rejected before being processed,
        # so even a non-idempotent method can safely be replayed.
        respond_with_statuses(httpserver, [429, 429, 200], retry_after=1)
        gi = galaxy_instance(httpserver)
        assert gi.make_post_request(f"{gi.url}/histories", payload={"name": "test"}) == {"ok": True}
        assert len(httpserver.log) == 3
        assert [request.method for request, _ in httpserver.log] == ["POST"] * 3

    def test_put_and_delete_are_retried(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [429, 200], retry_after=1)
        gi = galaxy_instance(httpserver)
        assert gi.make_put_request(f"{gi.url}/histories/abc", payload={"name": "test"}) == {"ok": True}
        assert len(httpserver.log) == 2
        httpserver.clear()
        respond_with_statuses(httpserver, [429, 200], retry_after=1)
        r = gi.make_delete_request(f"{gi.url}/histories/abc")
        assert r.status_code == 200
        assert len(httpserver.log) == 2

    def test_multipart_post_is_not_retried(self, httpserver: HTTPServer):
        # The body of a multipart request is a stream which is not rewound
        # between attempts, so replaying it would send a truncated body.
        respond_with_statuses(httpserver, [429, 200], retry_after=1)
        gi = galaxy_instance(httpserver)
        with pytest.raises(ConnectionError) as excinfo:
            gi.make_post_request(f"{gi.url}/tools", payload={"name": "test"}, files_attached=True)
        assert excinfo.value.status_code == 429
        assert len(httpserver.log) == 1

    def test_retries_exhausted_raises_connection_error(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [429], retry_after=1)
        gi = galaxy_instance(httpserver)
        with pytest.raises(ConnectionError) as excinfo:
            gi.make_post_request(f"{gi.url}/histories", payload={})
        assert excinfo.value.status_code == 429
        assert excinfo.value.body == '{"error": "nope"}'
        assert len(httpserver.log) > 1

    def test_max_total_retry_delay_caps_the_wait(self, httpserver: HTTPServer):
        # The server asks to wait much longer than the budget allows.
        respond_with_statuses(httpserver, [429], retry_after=3600)
        gi = galaxy_instance(httpserver, max_retry_after=0.2, max_total_retry_delay=0.5)
        start = time.monotonic()
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 429
        duration = time.monotonic() - start
        # Worst case is max_total_retry_delay + max_retry_after, plus the
        # time spent on the requests themselves.
        assert duration < 3, f"Retrying took {duration} s, ignoring the delay budget"

    def test_max_total_retry_delay_of_zero_disables_retrying(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [429, 200], retry_after=1)
        gi = galaxy_instance(httpserver, max_total_retry_delay=0)
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 429
        assert len(httpserver.log) == 1

    def test_max_429_retries_limits_retrying_without_delays(self, httpserver: HTTPServer):
        # With no delay between attempts the budget is never consumed, so the
        # number of retries is what stops the loop.
        respond_with_statuses(httpserver, [429], retry_after=0)
        gi = galaxy_instance(httpserver, max_retry_after=0, max_total_retry_delay=60, max_429_retries=3)
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 429
        assert len(httpserver.log) == 4

    def test_other_error_statuses_are_not_retried(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [500])
        gi = galaxy_instance(httpserver)
        with pytest.raises(ConnectionError) as excinfo:
            gi.make_post_request(f"{gi.url}/histories", payload={})
        assert excinfo.value.status_code == 500
        assert len(httpserver.log) == 1

    def test_get_client_does_not_retry_429_again(self, httpserver: HTTPServer):
        # `_get()` retries failed GET requests, but a 429 response has already
        # been retried by the session, so it must not be tried again.
        respond_with_statuses(httpserver, [429], retry_after=0)
        gi = galaxy_instance(
            httpserver,
            max_retry_after=0,
            max_429_retries=0,
            max_get_attempts=3,
            get_retry_delay=30,
        )
        start = time.monotonic()
        with pytest.raises(ConnectionError) as excinfo:
            gi.libraries.get_libraries()
        duration = time.monotonic() - start
        assert excinfo.value.status_code == 429
        assert len(httpserver.log) == 1
        assert duration < 5, f"Took {duration} s, the GET retry loop was not skipped"

    def test_get_client_retries_429_when_session_retrying_is_disabled(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [429, 200])
        gi = galaxy_instance(httpserver, max_total_retry_delay=0, max_get_attempts=2, get_retry_delay=0)
        libraries: Any = gi.libraries.get_libraries()
        assert libraries == {"ok": True}
        assert len(httpserver.log) == 2

    def test_get_client_still_retries_other_errors(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [500, 500, 200])
        gi = galaxy_instance(httpserver, max_get_attempts=3, get_retry_delay=0)
        libraries: Any = gi.libraries.get_libraries()
        assert libraries == {"ok": True}
        assert len(httpserver.log) == 3

    def test_first_retry_without_retry_after_waits(self, httpserver: HTTPServer):
        # urllib3 alone would retry immediately the first time.
        respond_with_statuses(httpserver, [429, 200])
        gi = galaxy_instance(httpserver, max_retry_after=0.5)
        start = time.monotonic()
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200
        duration = time.monotonic() - start
        assert len(httpserver.log) == 2
        assert duration >= 0.5, f"First retry waited only {duration} s"

    def test_invalid_retry_after_falls_back_to_backoff(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [429, 200], retry_after="soon")
        gi = galaxy_instance(httpserver)
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200
        assert len(httpserver.log) == 2

    def test_streamed_response_is_readable(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [429, 200], retry_after=1)
        gi = galaxy_instance(httpserver)
        r = gi.make_get_request(f"{gi.url}/datasets/abc/display", stream=True)
        assert r.status_code == 200
        assert b"".join(r.iter_content(4)) == b'{"ok": true}'


class TestGalaxySession:
    def test_session_is_not_used_by_default(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [200])
        gi = galaxy_instance(httpserver)
        assert gi.use_session is False
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200

    def test_session_is_used_and_retries_when_enabled(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [429, 200], retry_after=1)
        gi = galaxy_instance(httpserver, use_session=True)
        assert gi.use_session is True
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200
        assert len(httpserver.log) == 2

    def test_requests_keep_working_after_closing_the_session(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [200])
        gi = galaxy_instance(httpserver, use_session=True)
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200
        session = gi._session
        assert session is not None
        assert open_pool_count(session, gi.url) == 1
        gi.close()
        assert open_pool_count(session, gi.url) == 0
        assert gi.use_session is True
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200

    def test_requests_keep_working_after_disabling_the_session(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [200])
        gi = galaxy_instance(httpserver, use_session=True)
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200
        session = gi._session
        assert session is not None
        assert open_pool_count(session, gi.url) == 1
        gi.use_session = False
        assert gi.use_session is False
        # Disabling the session also closes it.
        assert gi._session is None
        assert open_pool_count(session, gi.url) == 0
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200

    def test_connections_are_reused_only_with_session(
        self, httpserver: HTTPServer, new_sessions: list[requests.Session]
    ):
        respond_with_statuses(httpserver, [200])
        gi = galaxy_instance(httpserver)
        for _ in range(3):
            assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200
        assert len(new_sessions) == 3
        new_sessions.clear()
        gi = galaxy_instance(httpserver, use_session=True)
        for _ in range(3):
            assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200
        assert len(new_sessions) == 1

    def test_context_manager_enables_and_closes_the_session(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [200])
        gi = galaxy_instance(httpserver)
        with gi as entered:
            assert entered is gi
            used_inside = gi.use_session
            # Accessing a GalaxyInstance-only attribute also checks that
            # entering the context manager preserves the subclass.
            assert entered.libraries.gi is entered
            assert entered.make_get_request(f"{gi.url}/libraries").status_code == 200
        assert used_inside is True
        assert gi.use_session is False

    def test_changing_settings_keeps_the_session_usable(self, httpserver: HTTPServer):
        respond_with_statuses(httpserver, [429, 200], retry_after=1)
        gi = galaxy_instance(httpserver, use_session=True)
        gi.max_429_retries = 5
        assert gi.use_session is True
        assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200


class TestGalaxyRetrySettings(unittest.TestCase):
    def setUp(self):
        self.gi = GalaxyInstance("http://localhost:56789", key="whatever")

    def test_defaults(self):
        assert self.gi.max_429_retries == 10
        assert self.gi.max_retry_after == 30.0
        assert self.gi.max_total_retry_delay == 60.0
        assert self.gi.use_session is False

    def test_settings_can_be_changed(self):
        self.gi.max_429_retries = 2
        assert self.gi.max_429_retries == 2
        self.gi.max_retry_after = 1.5
        assert self.gi.max_retry_after == 1.5
        self.gi.max_total_retry_delay = 5.0
        assert self.gi.max_total_retry_delay == 5.0

    def test_negative_settings_are_rejected(self):
        with pytest.raises(ValueError):
            self.gi.max_429_retries = -1
        with pytest.raises(ValueError):
            self.gi.max_retry_after = -1.0
        with pytest.raises(ValueError):
            self.gi.max_total_retry_delay = -1.0
