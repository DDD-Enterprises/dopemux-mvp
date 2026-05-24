from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "gpt-researcher"
    / "two_phase_runner.py"
)
SPEC = importlib.util.spec_from_file_location("two_phase_runner", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_build_report_prompt_keeps_evidence_out_of_search_query(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.md"
    evidence.write_text("LOCAL FACT: repo truth beats docs\n", encoding="utf-8")

    args = MODULE.parse_args(
        [
            "--query",
            "AI-assisted development governance workflows",
            "--evidence-file",
            str(evidence),
            "--label-policy",
            "OBSERVED,INFERRED,PROPOSED,UNKNOWN",
        ]
    )

    MODULE.validate_research_query(args.query, max_chars=args.max_query_chars)
    prompt = MODULE.build_report_prompt(args)

    assert args.query == "AI-assisted development governance workflows"
    assert "LOCAL FACT: repo truth beats docs" in prompt
    assert "Label every material claim as one of: OBSERVED, INFERRED, PROPOSED, UNKNOWN" in prompt


def test_validate_research_query_rejects_oversized_local_evidence() -> None:
    oversized_query = "local evidence " * 80

    with pytest.raises(ValueError, match="too long"):
        MODULE.validate_research_query(oversized_query, max_chars=120)


def test_dry_run_writes_prompt_and_metadata_without_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence = tmp_path / "evidence.md"
    evidence.write_text("Evidence body\n", encoding="utf-8")
    output_dir = tmp_path / "out"
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-secret-value-that-must-not-appear")

    exit_code = MODULE.main(
        [
            "--query",
            "AI-assisted development governance workflows",
            "--evidence-file",
            str(evidence),
            "--include-env-key",
            "TAVILY_API_KEY",
            "--output-dir",
            str(output_dir),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    prompt = (output_dir / "report_prompt.md").read_text(encoding="utf-8")
    metadata = json.loads((output_dir / "run.json").read_text(encoding="utf-8"))
    assert "Evidence body" in prompt
    assert "tvly-secret-value" not in prompt
    assert metadata["status"] == "dry_run"
    assert metadata["env"]["TAVILY_API_KEY"] == "<set>"
    assert "tvly-secret-value" not in json.dumps(metadata)


def test_env_snapshot_treats_empty_string_as_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMPTY_PROVIDER_KEY", "")

    snapshot = MODULE.build_env_snapshot(["EMPTY_PROVIDER_KEY", "MISSING_PROVIDER_KEY"])

    assert snapshot == {
        "EMPTY_PROVIDER_KEY": "<set>",
        "MISSING_PROVIDER_KEY": "<unset>",
    }


def test_metadata_redacts_secret_like_query(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"

    exit_code = MODULE.main(
        [
            "--query",
            "compare GPT Researcher with token sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
            "--output-dir",
            str(output_dir),
            "--dry-run",
        ]
    )

    metadata_text = (output_dir / "run.json").read_text(encoding="utf-8")
    metadata = json.loads(metadata_text)
    assert exit_code == 0
    assert metadata["query"] == "compare GPT Researcher with token <redacted>"
    assert "sk-proj-" not in metadata_text


def test_read_evidence_truncates_and_redacts_secret_patterns(tmp_path: Path) -> None:
    evidence = tmp_path / "secretish.md"
    evidence.write_text(
        "OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz1234567890\n"
        "safe line\n",
        encoding="utf-8",
    )

    body = MODULE.read_evidence_file(evidence, max_bytes=200)

    assert "OPENAI_API_KEY=<redacted>" in body
    assert "sk-proj-" not in body
    assert "safe line" in body


def test_read_evidence_redacts_secret_prefix_at_truncation_boundary(tmp_path: Path) -> None:
    evidence = tmp_path / "truncated-secret.md"
    evidence.write_text("prefix tvly-secret-value-that-gets-cut\n", encoding="utf-8")

    body = MODULE.read_evidence_file(evidence, max_bytes=18)

    assert "tvly-" not in body
    assert "<redacted>" in body
    assert "[TRUNCATED after 18 bytes]" in body


def test_prompt_setup_failure_writes_redacted_failure_metadata(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"

    exit_code = MODULE.main(
        [
            "--query",
            "AI-assisted development governance workflows",
            "--evidence-file",
            str(tmp_path / "missing-tvly-secret-value-that-must-not-appear.md"),
            "--output-dir",
            str(output_dir),
            "--dry-run",
        ]
    )

    metadata_text = (output_dir / "run.json").read_text(encoding="utf-8")
    metadata = json.loads(metadata_text)
    assert exit_code == 1
    assert metadata["status"] == "fail"
    assert metadata["error_type"] == "FileNotFoundError"
    assert "tvly-secret-value" not in metadata_text
    assert "<redacted>" in metadata_text


def test_failure_metadata_redacts_exception_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_dir = tmp_path / "out"

    async def fail_run(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("provider rejected key tvly-secret-value-that-must-not-appear")

    monkeypatch.setattr(MODULE, "run_gpt_researcher", fail_run)

    exit_code = MODULE.main(
        [
            "--query",
            "AI-assisted development governance workflows",
            "--output-dir",
            str(output_dir),
        ]
    )

    metadata_text = (output_dir / "run.json").read_text(encoding="utf-8")
    assert exit_code == 1
    assert "tvly-secret-value" not in metadata_text
    assert "<redacted>" in metadata_text
