"""Tests for core prescan pipeline modules: corpus_walker, classifier, batch_planner."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.classifier import Classifier
from lib.prescan.corpus_walker import CorpusWalker
from lib.prescan.engine import PrescanEngine
from lib.prescan.models import FileEntry, PrescanConfig


def _write_fixture_file(root: Path, rel_path: str, text: str = "fixture\n") -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _included_paths(entries: list[FileEntry]) -> set[str]:
    return {entry.rel_path for entry in entries if entry.include}


def _all_paths(entries: list[FileEntry]) -> set[str]:
    return {entry.rel_path for entry in entries}


def test_corpus_walker_finds_files(tmp_path: Path) -> None:
    """Verify CorpusWalker traverses directory and finds files."""
    # Create test structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "util.py").write_text("def helper(): pass")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("# Doc")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    walker = CorpusWalker(config)
    entries = walker.walk()

    # Should find the 3 files but not .git
    assert len(entries) == 3
    paths = {e.rel_path for e in entries}
    assert "src/main.py" in paths
    assert "src/util.py" in paths
    assert "docs/README.md" in paths
    assert not any(".git" in p for p in paths)


def test_corpus_walker_respects_exclusions(tmp_path: Path) -> None:
    """Verify CorpusWalker excludes based on patterns."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("code")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("lib")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "bin").mkdir()
    (tmp_path / ".venv" / "bin" / "activate").write_text("activate")

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    walker = CorpusWalker(config)
    entries = walker.walk()

    # Should exclude node_modules and .venv
    paths = {e.rel_path for e in entries}
    assert "src/main.py" in paths
    assert not any("node_modules" in p for p in paths)
    assert not any(".venv" in p for p in paths)


def test_corpus_walker_excludes_generated_output_dirs_by_default(tmp_path: Path) -> None:
    """Generated RTE/proof/audit output trees must not become source corpus input."""
    legitimate = {
        "src/app.py",
        "services/example/service.py",
        "docs/source.md",
        "tests/test_example.py",
        "task-packets/INDEX.md",
        "task-packets/TP-SOURCE.json",
    }
    generated = {
        "extraction/repo-truth-extractor/v5/runs/old/PROOF_PACK.json",
        "proof/TP-OLD/PROOF.json",
        "out/report.md",
        "audit_prep/input.md",
        "task-packets/generated/TP-OLD.json",
        "_audit_out/findings.md",
        "claudedocs/old.md",
    }
    for rel_path in sorted(legitimate | generated):
        _write_fixture_file(tmp_path, rel_path)

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "prescan-output",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    entries = CorpusWalker(config).walk()

    paths = _all_paths(entries)
    included = _included_paths(entries)
    assert legitimate <= included
    assert generated.isdisjoint(paths)


def test_corpus_walker_excludes_nested_generated_output_dirs(tmp_path: Path) -> None:
    """Nested generated trees are excluded when the walker sees nested workspace copies."""
    _write_fixture_file(tmp_path, "src/app.py")
    _write_fixture_file(tmp_path, "some/project/extraction/generated.json")
    _write_fixture_file(tmp_path, "nested/proof/PROOF.json")
    _write_fixture_file(tmp_path, "nested/out/report.md")
    _write_fixture_file(tmp_path, "nested/task-packets/generated/TP-OLD.json")

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "prescan-output",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    entries = CorpusWalker(config).walk()

    paths = _all_paths(entries)
    assert "src/app.py" in _included_paths(entries)
    assert "some/project/extraction/generated.json" not in paths
    assert "nested/proof/PROOF.json" not in paths
    assert "nested/out/report.md" not in paths
    assert "nested/task-packets/generated/TP-OLD.json" not in paths


def test_corpus_walker_excludes_secret_bearing_files_by_default(tmp_path: Path) -> None:
    """Secret-bearing local files must not be inventoried for prescan input."""
    secrets = {
        ".env",
        ".env.local",
        ".env.production",
        "private.pem",
        "deploy.key",
        "id_rsa",
        "id_ed25519",
        "nested/.env",
        "nested/private.pem",
    }
    for rel_path in sorted(secrets):
        _write_fixture_file(tmp_path, rel_path, "SECRET_VALUE_SHOULD_NOT_APPEAR=true\n")
    _write_fixture_file(tmp_path, "src/app.py", "print('ok')\n")
    _write_fixture_file(tmp_path, "docs/source.md", "# source\n")

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "prescan-output",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    entries = CorpusWalker(config).walk()

    paths = _all_paths(entries)
    assert secrets.isdisjoint(paths)
    assert {"src/app.py", "docs/source.md"} <= _included_paths(entries)


def test_prescan_engine_manifest_preserves_source_and_omits_excluded_inputs(tmp_path: Path) -> None:
    """The emitted prescan manifest should not reintroduce excluded generated or secret paths."""
    _write_fixture_file(tmp_path, "src/app.py", "def app():\n    return 1\n")
    _write_fixture_file(tmp_path, "services/example/service.py", "def service():\n    return 1\n")
    _write_fixture_file(tmp_path, "docs/source.md", "# Source\n")
    _write_fixture_file(tmp_path, "tests/test_example.py", "def test_example():\n    assert True\n")
    _write_fixture_file(tmp_path, "proof/TP-OLD/PROOF.json", "{}\n")
    _write_fixture_file(tmp_path, "extraction/repo-truth-extractor/v5/runs/old/PROOF_PACK.json", "{}\n")
    _write_fixture_file(tmp_path, ".env", "SECRET_VALUE_SHOULD_NOT_APPEAR=true\n")

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "prescan-output",
        enable_code_prescan=False,
        enable_git_enrichment=False,
        batch_mode=False,
        cost_estimate=False,
    )
    result = PrescanEngine(config).run()

    assert result.success is True
    manifest = json.loads((tmp_path / "prescan-output" / "corpus_manifest.json").read_text())
    paths = {item["rel_path"] for item in manifest}
    assert {
        "src/app.py",
        "services/example/service.py",
        "docs/source.md",
        "tests/test_example.py",
    } <= paths
    assert "proof/TP-OLD/PROOF.json" not in paths
    assert "extraction/repo-truth-extractor/v5/runs/old/PROOF_PACK.json" not in paths
    assert ".env" not in paths
    assert "SECRET_VALUE_SHOULD_NOT_APPEAR" not in json.dumps(manifest)


def test_classifier_categorizes_files(tmp_path: Path) -> None:
    """Verify Classifier correctly categorizes files."""
    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    classifier = Classifier(config)

    entries = [
        FileEntry(rel_path="docs/README.md", size_bytes=50, extension=".md"),
        FileEntry(rel_path="app.py", size_bytes=120, extension=".py"),
        FileEntry(rel_path="image.png", size_bytes=50000, extension=".png"),
    ]

    classifier.classify_all(entries)

    # Verify binary files are classified as noise
    png_entry = next(e for e in entries if e.rel_path == "image.png")
    assert png_entry.authority_class == "noise"

    # Verify code files are classified properly
    py_entry = next(e for e in entries if e.rel_path == "app.py")
    assert py_entry.authority_class != "noise"


def test_classifier_detects_draft_and_adr(tmp_path: Path) -> None:
    """Verify Classifier correctly assigns authority classes."""
    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
    )
    classifier = Classifier(config)

    entries = [
        FileEntry(rel_path="docs/90-adr/ADR-001.md", size_bytes=100, extension=".md"),
        FileEntry(rel_path="docs/draft-feature.md", size_bytes=100, extension=".md"),
        FileEntry(rel_path="archive/old-spec.md", size_bytes=100, extension=".md"),
    ]

    classifier.classify_all(entries)

    adr_entry = next(e for e in entries if "ADR" in e.rel_path)
    assert adr_entry.authority_class == "canonical"

    archive_entry = next(e for e in entries if "archive" in e.rel_path)
    assert archive_entry.authority_class == "historical"


def test_prescan_engine_emits_operator_progress(caplog, tmp_path: Path) -> None:
    """Prescan should show real stage progress instead of a silent long-running wait."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Fixture\n", encoding="utf-8")

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
        batch_mode=False,
        cost_estimate=False,
    )
    engine = PrescanEngine(config)

    with caplog.at_level(logging.INFO, logger="lib.prescan.engine"):
        result = engine.run()

    assert result.success is True
    messages = [record.getMessage() for record in caplog.records]
    assert any("PRESCAN_PROGRESS walk_corpus" in message for message in messages)
    assert any("PRESCAN_PROGRESS classify_files" in message for message in messages)
    assert any("PRESCAN_PROGRESS write_prescan_artifacts" in message for message in messages)
    assert any("PRESCAN_PROGRESS complete" in message for message in messages)


def test_prescan_engine_emits_detailed_route_and_batch_progress(
    caplog, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Detailed operator telemetry should expose batch plans and selected routes."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Fixture\n", encoding="utf-8")

    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
        batch_mode=False,
        cost_estimate=False,
    )
    engine = PrescanEngine(config)

    monkeypatch.setattr(
        PrescanEngine,
        "_run_stage0",
        lambda self, passes: {
            "catalog": {"routes": [{"provider": "openrouter"}]},
            "readiness": {"status": "ready"},
            "routing_plan": {
                "status": "READY",
                "selected_routes": {
                    "dedup": {
                        "provider": "openrouter",
                        "model_id": "openai/gpt-5-nano",
                        "selected_tier": "budget",
                        "tier_adjustment": "none",
                    }
                },
                "fallback_decisions": {
                    "dedup": [
                        {
                            "decision": "admitted",
                            "provider": "openai",
                            "model_id": "gpt-5-mini",
                        },
                        {
                            "decision": "excluded",
                            "provider": "anthropic",
                            "model_id": "claude-sonnet-4.5",
                            "reason": "missing_credentials",
                        },
                    ]
                },
            },
        },
    )

    with caplog.at_level(logging.INFO, logger="lib.prescan.engine"):
        result = engine.run(passes=["dedup"])

    assert result.success is True
    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "PRESCAN_PROGRESS plan_llm_pass_detail" in message and "pass_id=dedup" in message
        for message in messages
    )
    assert any(
        "PRESCAN_PROGRESS provider_readiness_detail" in message
        and "route=openrouter/openai/gpt-5-nano" in message
        and "excluded_fallbacks=1" in message
        for message in messages
    )




if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
