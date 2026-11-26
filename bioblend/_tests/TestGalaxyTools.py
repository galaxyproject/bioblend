"""
Tests for the bioblend.galaxy.tools module.
"""

import os
from typing import Any

import pytest

from bioblend import ConnectionError
from bioblend.galaxy.tools.inputs import (
    conditional,
    dataset,
    inputs,
    repeat,
)
from . import (
    GalaxyTestBase,
    test_util,
)


class TestGalaxyTools(GalaxyTestBase.GalaxyTestBase):
    def test_get_tools(self):
        # Test requires target Galaxy is configured with at least one tool.
        tools = self.gi.tools.get_tools()
        assert len(tools) > 0
        assert all(map(self._assert_is_tool_rep, tools))

    def test_get_tool_panel(self):
        # Test requires target Galaxy is configured with at least one tool
        # section.
        tool_panel = self.gi.tools.get_tool_panel()
        sections = [s for s in tool_panel if "elems" in s]
        assert len(sections) > 0
        assert all(map(self._assert_is_tool_rep, sections[0]["elems"]))

    def _assert_is_tool_rep(self, data):
        assert data["model_class"].endswith("Tool")
        # Special tools like SetMetadataTool may have different model_class
        # than Tool - but they all seem to end in tool.

        for key in ["name", "id", "version"]:
            assert key in data
        return True

    def test_paste_content(self):
        history = self.gi.histories.create_history(name="test_paste_data history")
        paste_text = "line 1\nline 2\rline 3\r\nline 4"
        tool_output = self.gi.tools.paste_content(paste_text, history["id"])
        assert len(tool_output["outputs"]) == 1
        # All lines in the resulting dataset should end with "\n"
        expected_contents = ("\n".join(paste_text.splitlines()) + "\n").encode()
        self._wait_and_verify_dataset(tool_output["outputs"][0]["id"], expected_contents)
        # Same with space_to_tab=True
        tool_output = self.gi.tools.paste_content(paste_text, history["id"], space_to_tab=True)
        assert len(tool_output["outputs"]) == 1
        expected_contents = ("\n".join("\t".join(_.split()) for _ in paste_text.splitlines()) + "\n").encode()
        self._wait_and_verify_dataset(tool_output["outputs"][0]["id"], expected_contents)

    def test_upload_file(self):
        history = self.gi.histories.create_history(name="test_upload_file history")

        fn = test_util.get_abspath("test_util.py")
        file_name = "test1"
        tool_output = self.gi.tools.upload_file(
            fn,
            # First param could be a regular path also of course...
            history_id=history["id"],
            file_name=file_name,
            dbkey="?",
            file_type="txt",
        )
        self._wait_for_and_verify_upload(tool_output, file_name, fn, expected_dbkey="?")

    def test_upload_file_dbkey(self):
        history = self.gi.histories.create_history(name="test_upload_file history")
        fn = test_util.get_abspath("test_util.py")
        file_name = "test1"
        dbkey = "hg19"
        tool_output = self.gi.tools.upload_file(
            fn,
            history_id=history["id"],
            file_name=file_name,
            dbkey=dbkey,
            file_type="txt",
        )
        self._wait_for_and_verify_upload(tool_output, file_name, fn, expected_dbkey=dbkey)

    @test_util.skip_unless_tool("random_lines1")
    def test_run_random_lines(self):
        # Run second test case from randomlines.xml
        history_id = self.gi.histories.create_history(name="test_run_random_lines history")["id"]
        with open(test_util.get_abspath(os.path.join("data", "1.bed"))) as f:
            contents = f.read()
        dataset_id = self._test_dataset(history_id, contents=contents)
        tool_inputs = (
            inputs()
            .set("num_lines", "1")
            .set("input", dataset(dataset_id))
            .set("seed_source", conditional().set("seed_source_selector", "set_seed").set("seed", "asdf"))
        )
        tool_output = self.gi.tools.run_tool(history_id=history_id, tool_id="random_lines1", tool_inputs=tool_inputs)
        assert len(tool_output["outputs"]) == 1
        # TODO: Wait for results and verify has 1 line and is
        # chr5  131424298   131424460   CCDS4149.1_cds_0_0_chr5_131424299_f 0   +

    @test_util.skip_unless_tool("cat1")
    def test_run_cat1(self):
        history_id = self.gi.histories.create_history(name="test_run_cat1 history")["id"]
        dataset1_id = self._test_dataset(history_id, contents="1 2 3")
        dataset2_id = self._test_dataset(history_id, contents="4 5 6")
        dataset3_id = self._test_dataset(history_id, contents="7 8 9")
        tool_inputs = (
            inputs()
            .set("input1", dataset(dataset1_id))
            .set(
                "queries",
                repeat()
                .instance(inputs().set("input2", dataset(dataset2_id)))
                .instance(inputs().set("input2", dataset(dataset3_id))),
            )
        )
        tool_output = self.gi.tools.run_tool(history_id=history_id, tool_id="cat1", tool_inputs=tool_inputs)
        assert len(tool_output["outputs"]) == 1
        # TODO: Wait for results and verify it has 3 lines - 1 2 3, 4 5 6,
        # and 7 8 9.

    @test_util.skip_unless_galaxy("release_26.0")
    @test_util.skip_unless_tool("random_lines1")
    def test_run_tool_request_random_lines(self):
        history_id = self.gi.histories.create_history(name="test_run_tool_request_random_lines history")["id"]
        with open(test_util.get_abspath(os.path.join("data", "1.bed"))) as f:
            contents = f.read()
        dataset_id = self._test_dataset(history_id, contents=contents)
        tool_inputs = (
            inputs()
            .set("num_lines", 1)
            .set("input", dataset(dataset_id))
            .set("seed_source", conditional().set("seed_source_selector", "set_seed").set("seed", "asdf"))
        )
        tool_request = self.gi.tools.run_tool_request(
            history_id=history_id,
            tool_id="random_lines1",
            tool_inputs=tool_inputs,
            maxwait=GalaxyTestBase.BIOBLEND_TEST_JOB_TIMEOUT,
        )
        assert tool_request["state"] == "submitted"
        assert tool_request["request"]["num_lines"] == 1
        assert tool_request["request"]["seed_source"]["seed"] == "asdf"
        assert len(tool_request["jobs"]) == 1
        job_ref = tool_request["jobs"][0]
        assert job_ref["src"] == "job"
        assert self.gi.tools.get_tool_request(tool_request["id"])["state"] == "submitted"
        assert self.gi.tools.get_tool_request(tool_request["id"])["jobs"] == tool_request["jobs"]
        job = self.gi.jobs.wait_for_job(job_ref["id"], maxwait=GalaxyTestBase.BIOBLEND_TEST_JOB_TIMEOUT)
        assert job["tool_id"] == "random_lines1"
        outputs = self.gi.jobs.get_outputs(job_ref["id"])
        assert len(outputs) == 1
        output_contents = self.gi.datasets.download_dataset(
            outputs[0]["dataset"]["id"], maxwait=GalaxyTestBase.BIOBLEND_TEST_JOB_TIMEOUT
        )
        output_lines = output_contents.decode().splitlines()
        assert len(output_lines) == 1
        assert output_lines[0] in contents.splitlines()

    @test_util.skip_unless_galaxy("release_26.0")
    @test_util.skip_unless_tool("random_lines1")
    def test_run_tool_request_rejects_invalid_inputs(self):
        history_id = self.gi.histories.create_history(name="test_run_tool_request_rejects_invalid_inputs history")["id"]
        dataset_id = self._test_dataset(history_id)
        valid_inputs = {
            "num_lines": 1,
            "input": {"src": "hda", "id": dataset_id},
            "seed_source": {"seed_source_selector": "no_seed"},
        }
        # An input not matching any tool parameter
        with pytest.raises(ConnectionError) as excinfo:
            self.gi.tools.run_tool_request(history_id, "random_lines1", {**valid_inputs, "nonexistent_param": "x"})
        assert excinfo.value.status_code == 400
        # An integer parameter value given as a string
        with pytest.raises(ConnectionError) as excinfo:
            self.gi.tools.run_tool_request(history_id, "random_lines1", {**valid_inputs, "num_lines": "1"})
        assert excinfo.value.status_code == 400
        # A flat legacy key
        with pytest.raises(ConnectionError) as excinfo:
            self.gi.tools.run_tool_request(history_id, "random_lines1", {**valid_inputs, "seed_source|seed": "asdf"})
        assert excinfo.value.status_code == 400
        # No job has been created
        assert self.gi.jobs.get_jobs(history_id=history_id, tool_id="random_lines1") == []

    @test_util.skip_unless_galaxy("release_26.0")
    @test_util.skip_unless_tool("cat1")
    def test_run_tool_request_without_waiting(self):
        history_id = self.gi.histories.create_history(name="test_run_tool_request_without_waiting history")["id"]
        dataset1_id = self._test_dataset(history_id, contents="1 2 3")
        dataset2_id = self._test_dataset(history_id, contents="4 5 6")
        tool_inputs = {
            "input1": {"src": "hda", "id": dataset1_id},
            "queries": [{"input2": {"src": "hda", "id": dataset2_id}}],
        }
        response = self.gi.tools.run_tool_request(history_id, "cat1", tool_inputs, wait=False)
        assert "task_result" in response
        tool_request_id = response["tool_request_id"]
        assert self.gi.tools.get_tool_request(tool_request_id)["state"] in ("new", "submitted")
        tool_request = self.gi.tools.wait_for_tool_request(
            tool_request_id, maxwait=GalaxyTestBase.BIOBLEND_TEST_JOB_TIMEOUT
        )
        assert tool_request["id"] == tool_request_id
        assert tool_request["state"] == "submitted"
        assert len(tool_request["jobs"]) == 1
        job_id = tool_request["jobs"][0]["id"]
        self.gi.jobs.wait_for_job(job_id, maxwait=GalaxyTestBase.BIOBLEND_TEST_JOB_TIMEOUT)
        outputs = self.gi.jobs.get_outputs(job_id)
        assert len(outputs) == 1
        self._wait_and_verify_dataset(outputs[0]["dataset"]["id"], b"1 2 3\n4 5 6\n")

    @test_util.skip_unless_galaxy("release_26.0")
    @test_util.skip_unless_tool("random_lines1")
    def test_run_tool_strict(self):
        history_id = self.gi.histories.create_history(name="test_run_tool_strict history")["id"]
        with open(test_util.get_abspath(os.path.join("data", "1.bed"))) as f:
            contents = f.read()
        dataset_id = self._test_dataset(history_id, contents=contents)
        legacy_output = self._run_random_lines1(history_id, dataset_id, input_format="21.01")
        tool_inputs = {
            "num_lines": 1,
            "input": {"src": "hda", "id": dataset_id},
            "seed_source": {"seed_source_selector": "set_seed", "seed": "asdf"},
        }
        strict_output = self.gi.tools.run_tool(
            history_id=history_id, tool_id="random_lines1", tool_inputs=tool_inputs, input_format="21.01", strict=True
        )
        # Same keys as without strict=True, except for the ones not about the
        # created jobs and outputs (e.g. "produces_entry_points")
        for key in ("jobs", "outputs", "output_collections", "implicit_collections"):
            assert len(strict_output[key]) == len(legacy_output[key]), key
        assert self.gi.tools.get_tool_request(strict_output["tool_request_id"])["state"] == "submitted"
        for key in ("id", "model_class", "state", "tool_id"):
            assert key in strict_output["jobs"][0], key
        assert strict_output["jobs"][0]["tool_id"] == "random_lines1"
        legacy_dataset = legacy_output["outputs"][0]
        strict_dataset = strict_output["outputs"][0]
        for key in ("id", "hid", "name", "state"):
            assert key in strict_dataset, key
        for key in ("output_name", "name", "history_id", "history_content_type", "model_class"):
            assert strict_dataset[key] == legacy_dataset[key], key
        assert strict_dataset["hid"] == legacy_dataset["hid"] + 1
        self._wait_and_verify_dataset(strict_dataset["id"], self.gi.datasets.download_dataset(legacy_dataset["id"]))
        # The same inputs with a mistyped name are run with the default value
        # by default, and rejected with strict=True
        mistyped_inputs = {**tool_inputs, "num_line": 2}
        del mistyped_inputs["num_lines"]
        with pytest.raises(ConnectionError) as excinfo:
            self.gi.tools.run_tool(history_id, "random_lines1", mistyped_inputs, input_format="21.01", strict=True)
        assert excinfo.value.status_code == 400
        with pytest.raises(ValueError):
            self.gi.tools.run_tool(history_id, "random_lines1", tool_inputs, strict=True)

    @test_util.skip_unless_tool("CONVERTER_fasta_to_bowtie_color_index")
    def test_tool_dependency_install(self):
        installed_dependencies = self.gi.tools.install_dependencies("CONVERTER_fasta_to_bowtie_color_index")
        assert any(
            True for d in installed_dependencies if d.get("name") == "bowtie" and d.get("dependency_type") == "conda"
        ), f"installed_dependencies is {installed_dependencies}"
        status = self.gi.tools.uninstall_dependencies("CONVERTER_fasta_to_bowtie_color_index")
        assert status[0]["model_class"] == "NullDependency", status

    @test_util.skip_unless_tool("CONVERTER_fasta_to_bowtie_color_index")
    def test_tool_requirements(self):
        tool_requirements = self.gi.tools.requirements("CONVERTER_fasta_to_bowtie_color_index")
        assert any(
            True
            for tr in tool_requirements
            if {"dependency_type", "version"} <= set(tr.keys()) and tr.get("name") == "bowtie"
        ), f"tool_requirements is {tool_requirements}"

    @test_util.skip_unless_tool("CONVERTER_fasta_to_bowtie_color_index")
    def test_reload(self):
        response = self.gi.tools.reload("CONVERTER_fasta_to_bowtie_color_index")
        assert isinstance(response, dict)
        assert "message" in response
        assert "id" in response["message"]

    @test_util.skip_unless_tool("sra_source")
    def test_get_citations(self):
        citations = self.gi.tools.get_citations("sra_source")
        assert len(citations) == 2

    def _wait_for_and_verify_upload(
        self, tool_output: dict[str, Any], file_name: str, fn: str, expected_dbkey: str = "?"
    ) -> None:
        assert len(tool_output["outputs"]) == 1
        output = tool_output["outputs"][0]
        assert output["name"] == file_name
        with open(fn, "rb") as f:
            expected_contents = f.read()
        self._wait_and_verify_dataset(output["id"], expected_contents)
        assert output["genome_build"] == expected_dbkey

    @test_util.skip_unless_tool("random_lines1")
    def test_get_tool_model(self):
        history_id = self.gi.histories.create_history(name="test_run_random_lines history")["id"]
        tool_model = self.gi.tools.build(tool_id="random_lines1", history_id=history_id)
        assert len(tool_model["inputs"]) == 3

    @test_util.skip_unless_tool("random_lines1")
    def test_get_tool_tests(self):
        tests = self.gi.tools.get_tool_tests("random_lines1")
        assert isinstance(tests, list)
        first_test = tests[0]
        assert first_test["tool_id"] == "random_lines1", first_test
        assert "inputs" in first_test
        assert "outputs" in first_test

    @test_util.skip_unless_galaxy("release_22.01")
    @test_util.skip_unless_tool("random_lines1")
    def test_get_tool_source(self):
        tool_source = self.gi.tools.get_tool_source("random_lines1")
        assert tool_source.startswith("<tool")
        assert tool_source.endswith("</tool>")
