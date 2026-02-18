from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "UPGRADES" / "run_extraction_v3.py"


def _load_runner_module():
    spec = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runner = _load_runner_module()


def _decode_error(text: str) -> json.JSONDecodeError:
    with pytest.raises(json.JSONDecodeError) as exc_info:
        json.loads(text)
    return exc_info.value


def test_semantic_eof_gate_uses_rstrip_length() -> None:
    raw_text = '{"outer":{"inner":1}   '
    exc = _decode_error(raw_text)

    assert exc.pos > len(raw_text.rstrip())
    assert runner._is_semantic_eof_eligible(exc, raw_text) is True


def test_semantic_eof_gate_allows_pos_equal_len_minus_one() -> None:
    raw_text = '{"a":1]'
    exc = _decode_error(raw_text)

    assert exc.pos == len(raw_text.rstrip()) - 1
    assert runner._is_semantic_eof_eligible(exc, raw_text) is True


def test_semantic_eof_gate_blocks_non_eof_errors() -> None:
    raw_text = '{"a":1} trailing tokens'
    exc = _decode_error(raw_text)

    assert exc.pos < len(raw_text.rstrip()) - 1
    assert runner._is_semantic_eof_eligible(exc, raw_text) is False
    assert runner.try_repair_json_truncation(raw_text, exc) is None
    assert runner.parse_json_from_response(raw_text) is None


def test_semantic_eof_gate_blocks_unterminated_string_errors() -> None:
    raw_text = '{"a":"x'
    exc = json.JSONDecodeError("Unterminated string starting at", raw_text, len(raw_text))

    assert runner._is_semantic_eof_eligible(exc, raw_text) is False
    assert runner.try_repair_json_truncation(raw_text, exc) is None
