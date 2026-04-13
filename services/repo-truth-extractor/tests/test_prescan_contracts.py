from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.dependency_graph import DependencyGraph
from lib.prescan.engine import PrescanEngine
from lib.prescan.grok_passes import GrokPassRunner
from lib.prescan.models import FileEntry, PrescanConfig
from lib.prescan.partition_brief_generator import PartitionBriefGenerator
from lib.prescan.schemas import PRESCAN_INTELLIGENCE_SCHEMA


def _make_config(tmp_path: Path) -> PrescanConfig:
    return PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
        batch_mode=False,
    )


def test_engine_intelligence_base_exposes_downstream_contract_fields(tmp_path: Path) -> None:
    engine = PrescanEngine(_make_config(tmp_path))
    entries = [
        FileEntry(
            rel_path="docs/90-adr/ADR-001.md",
            size_bytes=100,
            extension=".md",
            authority_class="canonical",
            lifecycle_stage="frozen",
            is_proposed_adr=True,
        ),
        FileEntry(
            rel_path="src/feature/stub.py",
            size_bytes=80,
            extension=".py",
            authority_class="canonical",
            lifecycle_stage="stale",
            has_stub_methods=True,
        ),
        FileEntry(
            rel_path="src/feature/todo.py",
            size_bytes=70,
            extension=".py",
            authority_class="canonical",
            lifecycle_stage="active",
            has_todo_markers=True,
        ),
        FileEntry(
            rel_path="docs/draft-feature.md",
            size_bytes=60,
            extension=".md",
            authority_class="canonical",
            lifecycle_stage="fresh",
            is_draft_doc=True,
        ),
        FileEntry(
            rel_path="docs/archive/old-spec.md",
            size_bytes=40,
            extension=".md",
            authority_class="ghost",
            lifecycle_stage="unknown",
            is_ghost=True,
            deleted_at_sha="deadbeef",
            deleted_date="2026-03-15",
            recovery_source="git_history",
        ),
        FileEntry(
            rel_path="docs/topic-v1.md",
            size_bytes=30,
            extension=".md",
            authority_class="canonical",
            lifecycle_stage="active",
            version_chain_id="chain-topic",
            version_ordinal=1,
            is_latest_version=False,
        ),
        FileEntry(
            rel_path="docs/topic-v2.md",
            size_bytes=35,
            extension=".md",
            authority_class="canonical",
            lifecycle_stage="active",
            version_chain_id="chain-topic",
            version_ordinal=2,
            is_latest_version=True,
        ),
    ]

    intelligence = engine._build_intelligence_base(entries)

    assert intelligence["lifecycle_distribution"] == {
        "fresh": 1,
        "active": 3,
        "stale": 1,
        "frozen": 1,
        "unknown": 1,
    }
    assert intelligence["ghost_files"] == [
        {
            "path": "docs/archive/old-spec.md",
            "deleted_at_sha": "deadbeef",
            "deleted_date": "2026-03-15",
            "recovery_source": "git_history",
        }
    ]
    assert intelligence["planned_features"] == {
        "proposed_adrs": ["docs/90-adr/ADR-001.md"],
        "stub_files": ["src/feature/stub.py"],
        "todo_files": ["src/feature/todo.py"],
        "draft_docs": ["docs/draft-feature.md"],
    }
    assert intelligence["version_chain_count"] == 1
    assert intelligence["compression_potential_files"] == 1
    assert intelligence["corpus_summary"]["ghost_files"] == 1
    assert isinstance(intelligence["corpus_summary"]["corpus_health_score"], int)


def test_optimize_payload_includes_prior_pass_summaries(tmp_path: Path) -> None:
    runner = GrokPassRunner(_make_config(tmp_path))
    payload = runner._build_optimize_payload(
        {
            "corpus_summary": {"included_files": 4},
            "extraction_hints": {"skip_duplicates": ["docs/topic-v1.md"]},
        },
        {
            "dedup": {
                "duplicate_assessments": [
                    {
                        "group_id": "dup-1",
                        "canonical_path": "docs/topic-v2.md",
                        "superseded_paths": ["docs/topic-v1.md"],
                    }
                ]
            },
            "discover": {
                "hidden_features": [
                    {
                        "path": "docs/hidden.md",
                        "feature_name": "Hidden Feature",
                    }
                ]
            },
            "feasibility": {
                "planned_features": [
                    {
                        "path": "docs/90-adr/ADR-001.md",
                        "feature_name": "Feature ADR",
                    }
                ]
            },
        },
    )

    assert "duplicate_assessments" in payload
    assert "docs/topic-v2.md" in payload
    assert "hidden_features" in payload
    assert "Hidden Feature" in payload
    assert "planned_features" in payload
    assert "Feature ADR" in payload


def test_dependency_graph_resolves_python_relative_imports() -> None:
    graph = DependencyGraph()
    manifest = [
        {"rel_path": "lib/prescan/engine.py"},
        {"rel_path": "lib/prescan/models.py"},
    ]
    code_intel = [{"rel_path": "lib/prescan/engine.py", "imports": [".models"]}]

    graph.build_from_code_intelligence(code_intel, manifest)

    assert ("lib/prescan/engine.py", "lib/prescan/models.py") in graph.edges


def test_partition_brief_trim_preserves_dependency_and_api_sections() -> None:
    generator = PartitionBriefGenerator(
        {
            "pagerank_scores": {"src/app.py": 0.8, "src/worker.py": 0.2},
            "signature_index": {
                "src/app.py": [
                    {
                        "name": "main",
                        "signature": "def main() -> None:",
                        "kind": "function",
                        "decorators": ["@click.command()"],
                    },
                    {
                        "name": "serve",
                        "signature": "def serve() -> None:",
                        "kind": "function",
                        "decorators": ["@app.get('/health')"],
                    },
                ],
                "src/worker.py": [
                    {
                        "name": "run_worker",
                        "signature": "def run_worker() -> None:",
                        "kind": "function",
                        "decorators": [],
                    }
                ],
            },
            "entry_points": ["src/app.py"],
            "hub_files": [{"rel_path": "src/app.py"}],
        },
        token_budget=20,
    )

    brief = generator.generate_brief("C", ["src/app.py", "src/worker.py"])

    assert "=== Partition Context ===" in brief
    assert "Dependency Flow:" in brief
    assert "API Surfaces:" in brief


def test_schema_declares_intelligence_fields_used_by_prescan_readers() -> None:
    properties = PRESCAN_INTELLIGENCE_SCHEMA["properties"]
    corpus_summary_properties = properties["corpus_summary"]["properties"]

    assert "lifecycle_distribution" in properties
    assert "ghost_files" in properties
    assert "planned_features" in properties
    assert "version_chain_count" in properties
    assert "compression_potential_files" in properties
    assert "corpus_health_score" in corpus_summary_properties


def test_batch_response_validator_rejects_malformed_nested_discover_payload(
    tmp_path: Path,
) -> None:
    runner = GrokPassRunner(_make_config(tmp_path))
    valid, _data, error = runner._validator.validate(
        "discover",
        """
        {
          "hidden_features": [
            {
              "path": "docs/hidden.md",
              "feature_name": "Hidden Feature"
            }
          ]
        }
        """,
    )

    assert valid is False
    assert "hidden_features[0] missing required fields" in error


def test_batch_response_validator_rejects_non_list_optimize_skip_list(
    tmp_path: Path,
) -> None:
    runner = GrokPassRunner(_make_config(tmp_path))
    valid, _data, error = runner._validator.validate(
        "optimize",
        """
        {
          "skip_list": "docs/topic-v1.md"
        }
        """,
    )

    assert valid is False
    assert error == "skip_list must be a list"
