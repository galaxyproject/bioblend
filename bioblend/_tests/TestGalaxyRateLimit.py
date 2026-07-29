"""
Tests on the handling of HTTP status 429 (Too Many Requests) responses.

These tests do not need a Galaxy instance: they run against a minimal HTTP
server replying with a canned sequence of status codes. A real server is needed
because the retrying happens inside urllib3, below the layer at which HTTP
mocking libraries usually work.
"""

import threading
import time
import unittest
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from typing import Any

import pytest
from typing_extensions import Self

from bioblend import ConnectionError
from bioblend.galaxy import GalaxyInstance


class MockServer:
    """
    HTTP server replying with a canned sequence of status codes.

    The last status code of the sequence is repeated for any further request.
    """

    def __init__(self, statuses: list[int], retry_after: int | None = None) -> None:
        self.statuses = statuses
        self.retry_after = retry_after
        self.requests: list[tuple[str, str]] = []
        lock = threading.Lock()
        server = self

        class Handler(BaseHTTPRequestHandler):
            def _reply(self) -> None:
                # The request body must be consumed, otherwise the client may
                # block while writing it.
                content_length = int(self.headers.get("Content-Length") or 0)
                if content_length:
                    self.rfile.read(content_length)
                with lock:
                    index = len(server.requests)
                    server.requests.append((self.command, self.path))
                status = server.statuses[min(index, len(server.statuses) - 1)]
                body = b'{"ok": true}' if status == 200 else b'{"error": "nope"}'
                self.send_response(status)
                if status == 429 and server.retry_after is not None:
                    self.send_header("Retry-After", str(server.retry_after))
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_GET = _reply
            do_POST = _reply
            do_PUT = _reply
            do_PATCH = _reply
            do_DELETE = _reply

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._httpd.server_address[1]}"

    @property
    def request_count(self) -> int:
        return len(self.requests)

    def __enter__(self) -> Self:
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join()


def galaxy_instance(server: MockServer, **kwargs: object) -> GalaxyInstance:
    """
    Return a ``GalaxyInstance`` pointing at ``server``, with retry delays short
    enough to keep the tests fast.
    """
    gi = GalaxyInstance(server.url, key="whatever")
    gi.max_retry_after = 0.1
    gi.max_total_retry_delay = 1.0
    for name, value in kwargs.items():
        setattr(gi, name, value)
    return gi


class TestGalaxyRateLimit(unittest.TestCase):
    def test_get_is_retried(self):
        with MockServer([429, 429, 200], retry_after=1) as server:
            gi = galaxy_instance(server)
            r = gi.make_get_request(f"{gi.url}/libraries")
            assert r.status_code == 200
            assert server.request_count == 3

    def test_post_is_retried(self):
        # A 429 response means the request was rejected before being processed,
        # so even a non-idempotent method can safely be replayed.
        with MockServer([429, 429, 200], retry_after=1) as server:
            gi = galaxy_instance(server)
            assert gi.make_post_request(f"{gi.url}/histories", payload={"name": "test"}) == {"ok": True}
            assert server.request_count == 3
            assert [method for method, _ in server.requests] == ["POST"] * 3

    def test_put_and_delete_are_retried(self):
        with MockServer([429, 200], retry_after=1) as server:
            gi = galaxy_instance(server)
            assert gi.make_put_request(f"{gi.url}/histories/abc", payload={"name": "test"}) == {"ok": True}
            assert server.request_count == 2
        with MockServer([429, 200], retry_after=1) as server:
            gi = galaxy_instance(server)
            r = gi.make_delete_request(f"{gi.url}/histories/abc")
            assert r.status_code == 200
            assert server.request_count == 2

    def test_multipart_post_is_not_retried(self):
        # The body of a multipart request is a stream which is not rewound
        # between attempts, so replaying it would send a truncated body.
        with MockServer([429, 200], retry_after=1) as server:
            gi = galaxy_instance(server)
            with pytest.raises(ConnectionError) as excinfo:
                gi.make_post_request(f"{gi.url}/tools", payload={"name": "test"}, files_attached=True)
            assert excinfo.value.status_code == 429
            assert server.request_count == 1

    def test_retries_exhausted_raises_connection_error(self):
        with MockServer([429], retry_after=1) as server:
            gi = galaxy_instance(server)
            with pytest.raises(ConnectionError) as excinfo:
                gi.make_post_request(f"{gi.url}/histories", payload={})
            assert excinfo.value.status_code == 429
            assert excinfo.value.body == '{"error": "nope"}'
            assert server.request_count > 1

    def test_max_total_retry_delay_caps_the_wait(self):
        # The server asks to wait much longer than the budget allows.
        with MockServer([429], retry_after=3600) as server:
            gi = galaxy_instance(server, max_retry_after=0.2, max_total_retry_delay=0.5)
            start = time.monotonic()
            assert gi.make_get_request(f"{gi.url}/libraries").status_code == 429
            duration = time.monotonic() - start
            # Worst case is max_total_retry_delay + max_retry_after, plus the
            # time spent on the requests themselves.
            assert duration < 3, f"Retrying took {duration} s, ignoring the delay budget"

    def test_max_total_retry_delay_of_zero_disables_retrying(self):
        with MockServer([429, 200], retry_after=1) as server:
            gi = galaxy_instance(server, max_total_retry_delay=0)
            assert gi.make_get_request(f"{gi.url}/libraries").status_code == 429
            assert server.request_count == 1

    def test_max_429_retries_limits_retrying_without_delays(self):
        # With no delay between attempts the budget is never consumed, so the
        # number of retries is what stops the loop.
        with MockServer([429], retry_after=0) as server:
            gi = galaxy_instance(server, max_retry_after=0, max_total_retry_delay=60, max_429_retries=3)
            assert gi.make_get_request(f"{gi.url}/libraries").status_code == 429
            assert server.request_count == 4

    def test_other_error_statuses_are_not_retried(self):
        with MockServer([500]) as server:
            gi = galaxy_instance(server)
            with pytest.raises(ConnectionError) as excinfo:
                gi.make_post_request(f"{gi.url}/histories", payload={})
            assert excinfo.value.status_code == 500
            assert server.request_count == 1

    def test_get_client_does_not_retry_429_again(self):
        # `_get()` retries failed GET requests, but a 429 response has already
        # been retried by the session, so it must not be tried again.
        with MockServer([429], retry_after=0) as server:
            gi = galaxy_instance(
                server,
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
            assert server.request_count == 1
            assert duration < 5, f"Took {duration} s, the GET retry loop was not skipped"

    def test_get_client_still_retries_other_errors(self):
        with MockServer([500, 500, 200]) as server:
            gi = galaxy_instance(server, max_get_attempts=3, get_retry_delay=0)
            libraries: Any = gi.libraries.get_libraries()
            assert libraries == {"ok": True}
            assert server.request_count == 3

    def test_streamed_response_is_readable(self):
        with MockServer([429, 200], retry_after=1) as server:
            gi = galaxy_instance(server)
            r = gi.make_get_request(f"{gi.url}/datasets/abc/display", stream=True)
            assert r.status_code == 200
            assert b"".join(r.iter_content(4)) == b'{"ok": true}'


class TestGalaxySession(unittest.TestCase):
    def test_session_is_not_used_by_default(self):
        with MockServer([200]) as server:
            gi = galaxy_instance(server)
            assert gi.use_session is False
            assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200

    def test_session_is_used_and_retries_when_enabled(self):
        with MockServer([429, 200], retry_after=1) as server:
            gi = galaxy_instance(server, use_session=True)
            assert gi.use_session is True
            assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200
            assert server.request_count == 2

    def test_requests_keep_working_after_closing_the_session(self):
        with MockServer([200]) as server:
            gi = galaxy_instance(server, use_session=True)
            gi.close()
            assert gi.use_session is False
            assert gi.make_get_request(f"{gi.url}/libraries").status_code == 200

    def test_context_manager_enables_and_closes_the_session(self):
        with MockServer([200]) as server:
            gi = galaxy_instance(server)
            with gi as entered:
                assert entered is gi
                used_inside = gi.use_session
                # Accessing a GalaxyInstance-only attribute also checks that
                # entering the context manager preserves the subclass.
                assert entered.libraries.gi is entered
                assert entered.make_get_request(f"{gi.url}/libraries").status_code == 200
            assert used_inside is True
            assert gi.use_session is False

    def test_changing_settings_keeps_the_session_usable(self):
        with MockServer([429, 200], retry_after=1) as server:
            gi = galaxy_instance(server, use_session=True)
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
