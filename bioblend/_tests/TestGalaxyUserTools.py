import json
from typing import (
    Any,
    cast,
)
from unittest.mock import patch

import pytest
import requests

from bioblend import ConnectionError
from bioblend.galaxy import GalaxyInstance

TOOL_UUID = "c9d94e82-4dc3-4d9a-a01f-1b60bb98dc80"
REPRESENTATION = {
    "class": "GalaxyUserTool",
    "id": "copy-file",
    "version": "1.0.0",
    "name": "Copy a file",
    "shell_command": "cp input output",
    "container": "quay.io/biocontainers/coreutils:9.5--h4bc722e_0",
}


def response(payload: Any, status_code: int = 200) -> requests.Response:
    result = requests.Response()
    result.status_code = status_code
    result._content = json.dumps(payload).encode()
    result.encoding = "utf-8"
    return result


class TestGalaxyUserTools:
    def setup_method(self):
        self.gi = GalaxyInstance("http://localhost:56789", key="secret-api-key")

    def test_methods_are_available(self):
        for method in (
            "get_user_tools",
            "show_user_tool",
            "create_user_tool",
            "delete_user_tool",
            "run_user_tool",
        ):
            assert callable(getattr(self.gi.tools, method))

    def test_get_user_tools_passes_exact_active_query_parameter(self):
        with patch("requests.get", return_value=response([])) as get:
            assert self.gi.tools.get_user_tools(active=False) == []

        assert get.call_args.args[0] == "http://localhost:56789/api/unprivileged_tools"
        assert get.call_args.kwargs["params"] == {"active": False}

    def test_show_user_tool_uses_uuid_url(self):
        user_tool = {"uuid": TOOL_UUID}
        with patch("requests.get", return_value=response(user_tool)) as get:
            assert self.gi.tools.show_user_tool(TOOL_UUID) == user_tool

        assert get.call_args.args[0] == f"http://localhost:56789/api/unprivileged_tools/{TOOL_UUID}"

    def test_create_user_tool_wraps_inner_representation_once(self):
        created = {"uuid": TOOL_UUID, "representation": REPRESENTATION}
        with patch("requests.post", return_value=response(created)) as post:
            assert self.gi.tools.create_user_tool(REPRESENTATION) == created

        assert post.call_args.args[0] == "http://localhost:56789/api/unprivileged_tools"
        assert json.loads(post.call_args.kwargs["data"]) == {
            "src": "representation",
            "representation": REPRESENTATION,
        }

    def test_create_user_tool_validates_representation(self):
        with pytest.raises(TypeError, match="representation must be a dict"):
            self.gi.tools.create_user_tool(cast(Any, []))

        for field in REPRESENTATION:
            incomplete = REPRESENTATION.copy()
            del incomplete[field]
            with pytest.raises(ValueError, match=field):
                self.gi.tools.create_user_tool(incomplete)

        wrong_class = {**REPRESENTATION, "class": "GalaxyTool"}
        with pytest.raises(ValueError, match="GalaxyUserTool"):
            self.gi.tools.create_user_tool(wrong_class)

        wrong_container = {**REPRESENTATION, "container": {"type": "docker"}}
        with pytest.raises(TypeError, match="container must be a string"):
            self.gi.tools.create_user_tool(wrong_container)

    def test_delete_user_tool_follows_delete_conventions(self):
        with patch("requests.delete", return_value=response(None)) as delete:
            assert self.gi.tools.delete_user_tool(TOOL_UUID) is None

        assert delete.call_args.args[0] == f"http://localhost:56789/api/unprivileged_tools/{TOOL_UUID}"

    def test_run_user_tool_looks_up_uuid_then_posts_exact_tools_payload(self):
        calls: list[tuple[str, str]] = []
        user_tool = {
            "uuid": TOOL_UUID,
            "active": True,
            "tool_id": "copy-file",
            "representation": {"version": "1.0.0"},
        }
        result = {"jobs": [{"id": "job-id"}], "outputs": [], "output_collections": []}
        inputs = {
            "dataset": {"src": "hda", "id": "dataset-id"},
            "collection": {"src": "hdca", "id": "collection-id"},
            "count": 3,
        }

        def get_response(url: str, **kwargs: Any) -> requests.Response:
            calls.append(("GET", url))
            return response(user_tool)

        def post_response(url: str, **kwargs: Any) -> requests.Response:
            calls.append(("POST", url))
            return response(result)

        with patch("requests.get", side_effect=get_response), patch("requests.post", side_effect=post_response) as post:
            assert self.gi.tools.run_user_tool("history-id", TOOL_UUID, inputs) == result

        assert calls == [
            ("GET", f"http://localhost:56789/api/unprivileged_tools/{TOOL_UUID}"),
            ("POST", "http://localhost:56789/api/tools"),
        ]
        assert json.loads(post.call_args.kwargs["data"]) == {
            "history_id": "history-id",
            "tool_uuid": TOOL_UUID,
            "tool_version": "1.0.0",
            "inputs": inputs,
            "input_format": "legacy",
        }
        assert "tool_id" not in json.loads(post.call_args.kwargs["data"])
        assert all("/api/jobs" not in url for _, url in calls)

    def test_empty_identifiers_and_non_dict_inputs_are_rejected(self):
        with pytest.raises(ValueError, match="tool_uuid"):
            self.gi.tools.show_user_tool("")
        with pytest.raises(ValueError, match="tool_uuid"):
            self.gi.tools.delete_user_tool("")
        with pytest.raises(ValueError, match="history_id"):
            self.gi.tools.run_user_tool("", TOOL_UUID, {})
        with pytest.raises(ValueError, match="tool_uuid"):
            self.gi.tools.run_user_tool("history-id", "", {})
        with pytest.raises(TypeError, match="inputs must be a dict"):
            self.gi.tools.run_user_tool("history-id", TOOL_UUID, cast(Any, []))

    @pytest.mark.parametrize(
        ("user_tool", "message"),
        [
            (None, "returned no user-defined tool"),
            ({"active": False, "representation": {"version": "1.0.0"}}, "is inactive"),
            ({"active": True, "representation": {}}, "has no representation version"),
            ({"active": True}, "has no representation version"),
        ],
    )
    def test_run_user_tool_rejects_unusable_lookup_responses(self, user_tool, message):
        with patch("requests.get", return_value=response(user_tool)), pytest.raises(ValueError, match=message):
            self.gi.tools.run_user_tool("history-id", TOOL_UUID, {})

    def test_galaxy_http_error_preserves_status_and_body_without_credentials(self):
        error_body = {"err_msg": "User-defined tool was not found"}
        with patch("requests.get", return_value=response(error_body, 404)), pytest.raises(ConnectionError) as exc:
            self.gi.tools.run_user_tool("history-id", TOOL_UUID, {})

        assert exc.value.status_code == 404
        assert isinstance(exc.value.body, (bytes, str))
        assert json.loads(exc.value.body) == error_body
        assert "secret-api-key" not in str(exc.value)

    def test_run_submission_error_preserves_status_and_body_without_credentials(self):
        user_tool = {"active": True, "representation": {"version": "1.0.0"}}
        error_body = {"err_msg": "Invalid tool inputs"}
        with (
            patch("requests.get", return_value=response(user_tool)),
            patch("requests.post", return_value=response(error_body, 400)),
            pytest.raises(ConnectionError) as exc,
        ):
            self.gi.tools.run_user_tool("history-id", TOOL_UUID, {})

        assert exc.value.status_code == 400
        assert isinstance(exc.value.body, (bytes, str))
        assert json.loads(exc.value.body) == error_body
        assert "secret-api-key" not in str(exc.value)
