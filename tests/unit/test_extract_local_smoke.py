from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from dopemux.cli import cli
from dopemux.commands.extract_commands import extract


def test_extract_docs_smoke_uses_local_classifier(tmp_path: Path) -> None:
    source_dir = tmp_path / "docs"
    source_dir.mkdir()
    (source_dir / "decision.md").write_text(
        "# Local Extraction\n\nDecision: keep local extraction credential-free.\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(extract, ["docs", str(source_dir), "--format", "json"])

    assert result.exit_code == 0, result.output
    assert "headers" in result.output
    assert "decisions" in result.output


def test_extract_pipeline_no_embeddings_no_synthesis_smoke(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    source_dir = tmp_path / "docs"
    output_dir = tmp_path / "out"
    source_dir.mkdir()
    (source_dir / "decision.md").write_text(
        "# Local Pipeline\n\nDecision: keep deterministic local smoke paths.\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        extract,
        [
            "pipeline",
            str(source_dir),
            "--output",
            str(output_dir),
            "--no-embeddings",
            "--no-synthesis",
            "--no-tsv",
            "--no-multi-angle",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "extraction_results.json").exists()
    assert not (output_dir / "embedding_manifest.json").exists()


def test_extract_pipeline_auto_embeddings_skip_without_credentials(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    source_dir = tmp_path / "docs"
    output_dir = tmp_path / "out"
    source_dir.mkdir()
    (source_dir / "decision.md").write_text(
        "# Local Pipeline\n\nDecision: write an embedding manifest.\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        extract,
        [
            "pipeline",
            str(source_dir),
            "--output",
            str(output_dir),
            "--no-synthesis",
            "--no-tsv",
            "--no-multi-angle",
        ],
    )

    manifest = json.loads((output_dir / "embedding_manifest.json").read_text(encoding="utf-8"))
    assert result.exit_code == 0, result.output
    assert manifest["embedding_status"] == "skipped_no_credentials"
    assert manifest["resolved_provider"] == "none"
    assert manifest["indexed_count"] >= 1
    assert manifest["embedded_count"] == 0


def test_extract_pipeline_voyage_embeddings_are_mockable(tmp_path: Path, monkeypatch) -> None:
    class FakeVoyageClient:
        def __init__(self, config):
            self.config = config

        async def embed_texts(self, texts):
            return [[0.1] * self.config.embedding_dimension for _ in texts]

    monkeypatch.setenv("VOYAGE_API_KEY", "test-key")
    monkeypatch.setattr(
        "dopemux.embeddings.storage.hybrid_store.VoyageAPIClient",
        FakeVoyageClient,
    )

    source_dir = tmp_path / "docs"
    output_dir = tmp_path / "out"
    source_dir.mkdir()
    (source_dir / "decision.md").write_text(
        "# Cloud Mock\n\nDecision: use mocked Voyage embeddings in tests.\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        extract,
        [
            "pipeline",
            str(source_dir),
            "--output",
            str(output_dir),
            "--no-synthesis",
            "--no-tsv",
            "--no-multi-angle",
        ],
    )

    manifest = json.loads((output_dir / "embedding_manifest.json").read_text(encoding="utf-8"))
    assert result.exit_code == 0, result.output
    assert manifest["embedding_status"] == "completed"
    assert manifest["resolved_provider"] == "voyage"
    assert manifest["embedded_count"] >= 1


def test_extract_chatlog_basic_smoke_copy_archive_and_manifest(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    source_dir = tmp_path / "chatlogs"
    output_dir = tmp_path / "out"
    source_dir.mkdir()
    chatlog = source_dir / "chat.md"
    chatlog.write_text(
        "User: We decided to use SQLite locally.\n"
        "Assistant: Feature request: add embeddings.\n"
        "User: Risk: credentials may be missing.\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "extract",
            "chatlog",
            "basic",
            str(source_dir),
            "--output",
            str(output_dir),
            "--archive-mode",
            "copy",
            "--no-persist-conport",
        ],
    )

    manifest = json.loads((output_dir / "embeddings" / "embedding_manifest.json").read_text(encoding="utf-8"))
    assert result.exit_code == 0, result.output
    assert chatlog.exists()
    assert (output_dir / "archive" / "chat.md").exists()
    assert manifest["embedding_status"] == "skipped_no_credentials"
    assert manifest["indexed_count"] >= 1


def test_extract_chatlog_pro_smoke(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    source_dir = tmp_path / "chatlogs"
    output_dir = tmp_path / "out"
    source_dir.mkdir()
    (source_dir / "chat.md").write_text(
        "User: We decided to use SQLite locally.\n"
        "Assistant: Constraint: source chatlogs must not move by default.\n"
        "User: Security risk: credentials may be missing.\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "extract",
            "chatlog",
            "pro",
            str(source_dir),
            "--output",
            str(output_dir),
            "--archive-mode",
            "copy",
            "--no-persist-conport",
            "--max-documents",
            "2",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "knowledge_graph.json").exists()
    assert (output_dir / "embeddings" / "embedding_manifest.json").exists()
