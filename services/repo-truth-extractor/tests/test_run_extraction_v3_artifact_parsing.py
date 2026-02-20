from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = ROOT / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "run_extraction_v3"


def _load_runner_module():
    spec = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runner = _load_runner_module()


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_parse_and_coerce_accepts_list_form_artifacts() -> None:
    raw_text = _read_fixture("A99__A_P0006.FAILED.txt")
    parsed = runner.parse_json_from_response(raw_text)
    assert isinstance(parsed, list)

    expected = (
        "REPO_INSTRUCTION_SURFACE.json",
        "REPO_INSTRUCTION_REFERENCES.json",
        "REPO_MCP_SERVER_DEFS.json",
        "REPO_MCP_PROXY_SURFACE.json",
        "REPO_ROUTER_SURFACE.json",
        "REPO_HOOKS_SURFACE.json",
        "REPO_IMPLICIT_BEHAVIOR_HINTS.json",
        "REPO_COMPOSE_SERVICE_GRAPH.json",
        "REPO_LITELLM_SURFACE.json",
        "REPO_TASKX_SURFACE.json",
        "REPOCTRL_NORM_MANIFEST.json",
        "REPOCTRL_QA.json",
    )
    artifacts = runner.coerce_artifacts_from_response(parsed, raw_text, expected)

    assert len(artifacts) == len(expected)
    assert {row["artifact_name"] for row in artifacts} == set(expected)


def test_parse_and_coerce_repairs_real_truncated_eof_fixture() -> None:
    raw_text = _read_fixture("A1__A_P0005.FAILED.txt")
    parsed = runner.parse_json_from_response(raw_text)
    assert isinstance(parsed, dict)

    artifacts = runner.coerce_artifacts_from_response(
        parsed,
        raw_text,
        ("REPO_INSTRUCTION_SURFACE.json", "REPO_INSTRUCTION_REFERENCES.json"),
    )
    assert len(artifacts) == 2
    assert {row["artifact_name"] for row in artifacts} == {
        "REPO_INSTRUCTION_SURFACE.json",
        "REPO_INSTRUCTION_REFERENCES.json",
    }


def test_extra_data_far_from_eof_does_not_trigger_repair() -> None:
    raw_text = '{"artifacts":[{"artifact_name":"A.json","payload":{"k":1}}]} trailing ' + ("x" * 400)

    with pytest.raises(json.JSONDecodeError) as exc_info:
        json.loads(raw_text)

    repaired = runner.try_repair_json_truncation(raw_text, exc_info.value)
    assert repaired is None
    assert runner.parse_json_from_response(raw_text) is None


def test_mid_body_unmatched_closer_is_not_deleted() -> None:
    raw_text = '{"artifacts":[{"artifact_name":"A.json","payload":{] "k":1}}'

    with pytest.raises(json.JSONDecodeError) as exc_info:
        json.loads(raw_text)

    repaired = runner.try_repair_json_truncation(raw_text, exc_info.value)
    assert repaired is None


def test_real_mid_body_invalid_escape_fixture_is_fail_closed() -> None:
    raw_text = _read_fixture("A0__A_P0004.FAILED.txt")
    stripped = raw_text.strip()
    assert runner.parse_json_from_response(raw_text) is None

    with pytest.raises(json.JSONDecodeError) as exc_info:
        json.loads(stripped)
    exc = exc_info.value
    assert runner._is_string_literal_decode_error(exc) is True
    assert runner._is_semantic_eof_eligible(exc, stripped) is False
    assert runner.try_repair_json_truncation(stripped, exc) is None


def test_real_unterminated_string_fixture_is_fail_closed() -> None:
    raw_text = _read_fixture("A1__A_P0001.FAILED.txt")
    stripped = raw_text.strip()
    assert runner.parse_json_from_response(raw_text) is None

    with pytest.raises(json.JSONDecodeError) as exc_info:
        json.loads(stripped)
    exc = exc_info.value
    assert runner._is_string_literal_decode_error(exc) is True
    assert runner._is_semantic_eof_eligible(exc, stripped) is False
    assert runner.try_repair_json_truncation(stripped, exc) is None


def test_first_fenced_block_is_deterministic() -> None:
    raw_text = (
        "```json\n"
        '{"from":"first"}'
        "\n```\n"
        "```json\n"
        '{"from":"second"}'
        "\n```\n"
    )

    parsed = runner.parse_json_from_response(raw_text)
    assert parsed == {"from": "first"}


def test_existing_dict_envelope_behavior_remains_unchanged() -> None:
    raw_text = '{"artifacts":[{"artifact_name":"A.json","payload":{"k":1}}]}'
    parsed = runner.parse_json_from_response(raw_text)

    artifacts = runner.coerce_artifacts_from_response(parsed, raw_text, ("A.json",))
    assert artifacts == [{"artifact_name": "A.json", "payload": {"k": 1}}]


def test_balanced_repair_is_deterministic_for_same_input() -> None:
    raw_text = _read_fixture("A9__A_P0011.FAILED.txt")
    stripped = raw_text.strip()

    with pytest.raises(json.JSONDecodeError) as exc_info:
        json.loads(stripped)
    exc = exc_info.value
    repaired_one = runner.try_repair_json_truncation(stripped, exc)
    repaired_two = runner.try_repair_json_truncation(stripped, exc)

    assert repaired_one is not None
    assert repaired_one == repaired_two
    assert isinstance(json.loads(repaired_one), dict)


@pytest.mark.parametrize(
    "raw_text",
    [
        '{"a":"x',
        '{"a":"\\q"}',
        '{"a":"\\u12"}',
        "{\"a\":\"x\ny\"}",
    ],
)
def test_string_literal_decode_error_classifier(raw_text: str) -> None:
    with pytest.raises(json.JSONDecodeError) as exc_info:
        json.loads(raw_text)
    assert runner._is_string_literal_decode_error(exc_info.value) is True


def test_output_contract_instructions_include_hard_rules() -> None:
    instructions = runner.build_output_envelope_instructions(("A.json",))
    assert "Output MUST be a single JSON value" in instructions
    assert "No markdown, prose, code fences" in instructions
    assert "Never emit invalid JSON" in instructions
