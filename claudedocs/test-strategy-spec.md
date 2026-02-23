# Test Strategy + E2E Smoke Test Design (F-16, F-17)

**Date**: 2026-02-22
**Findings**: F-16 (no E2E test), F-17 (v4 norm assembly untested)
**Goal**: Define test specs that cheaper models can implement directly

---

## 1. E2E Smoke Test: `--phase A --dry-run` (F-16)

### Test File
`services/repo-truth-extractor/tests/test_e2e_smoke_v4.py`

### Purpose
Validate the full v4 → v3 delegation pipeline works without API calls.

### Test Spec

```python
"""E2E smoke test: v4 runner --phase A --dry-run produces valid command structure."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # dopemux-mvp root
V4_RUNNER = ROOT / "services" / "repo-truth-extractor" / "run_extraction_v4.py"


@pytest.mark.e2e
class TestE2ESmokeV4:
    """Smoke tests that run the real v4 CLI in --dry-run mode."""

    def test_phase_a_dry_run_exits_zero(self):
        """v4 --phase A --dry-run should exit 0 (or exit with known v3 dry-run code)."""
        result = subprocess.run(
            [sys.executable, str(V4_RUNNER), "--phase", "A", "--dry-run",
             "--run-id", "test_smoke_001", "--no-strict-audit"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        # v3 dry-run may print plan and exit 0
        assert result.returncode == 0, (
            f"v4 dry-run failed with rc={result.returncode}\n"
            f"stdout: {result.stdout[:2000]}\n"
            f"stderr: {result.stderr[:2000]}"
        )

    def test_phase_a_dry_run_contains_step_ids(self):
        """Dry-run output should reference phase A step IDs."""
        result = subprocess.run(
            [sys.executable, str(V4_RUNNER), "--phase", "A", "--dry-run",
             "--run-id", "test_smoke_002", "--no-strict-audit"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        combined = result.stdout + result.stderr
        # At minimum, A0 should appear in the output
        assert "A0" in combined, f"Expected A0 in dry-run output, got:\n{combined[:2000]}"

    def test_promptset_audit_passes(self):
        """The promptset audit script should pass (validates YAML/prompt consistency)."""
        audit_script = ROOT / "scripts" / "repo_truth_extractor_promptset_audit_v4.py"
        if not audit_script.exists():
            pytest.skip("Audit script not found")
        result = subprocess.run(
            [sys.executable, str(audit_script), "--repo-root", str(ROOT)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Promptset audit failed:\n{result.stdout[:2000]}\n{result.stderr[:2000]}"
        )

    def test_status_json_produces_valid_json(self):
        """--status-json should produce valid JSON output."""
        result = subprocess.run(
            [sys.executable, str(V4_RUNNER), "--status-json",
             "--run-id", "nonexistent_run", "--no-sync"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should exit 0 even for nonexistent run (just shows NOT_STARTED)
        assert result.returncode == 0
        # Find JSON in output (may have other lines before it)
        lines = result.stdout.strip().splitlines()
        # The JSON output starts with { — find it
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                json_start = i
                break
        assert json_start is not None, f"No JSON found in output:\n{result.stdout[:2000]}"
        json_text = "\n".join(lines[json_start:])
        payload = json.loads(json_text)
        assert "phases" in payload
        assert "summary" in payload
```

### Pytest Marker
Add to `pyproject.toml` or `pytest.ini`:
```ini
[tool:pytest]
markers =
    e2e: End-to-end tests (may be slow, require full repo)
```

### Run Command
```bash
pytest services/repo-truth-extractor/tests/test_e2e_smoke_v4.py -v -m e2e
```

---

## 2. v4 Norm Assembly Test: `sync_phase_from_v3` (F-17)

### Test File
`services/repo-truth-extractor/tests/test_run_extraction_v4_norm_assembly.py`

### Purpose
Test that `sync_phase_from_v3` correctly merges raw v3 outputs into deterministic v4 norm artifacts.

### Test Spec

```python
"""Tests for v4 norm assembly: sync_phase_from_v3 and related functions."""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Tuple
from unittest.mock import patch

import pytest
import yaml

# Import from v4 runner
ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT / "services" / "repo-truth-extractor"))

from run_extraction_v4 import (
    ArtifactRule,
    extract_step_partition_payloads,
    merge_item_list_payloads,
    merge_payloads,
    normalize_evidence,
    parse_raw_artifacts,
    stable_item_key,
    strip_forbidden_keys,
    sync_phase_from_v3,
)


@pytest.fixture
def tmp_run_dirs(tmp_path):
    """Create v3 and v4 run directory structures."""
    run_id = "test_run_001"
    v3_root = tmp_path / "v3" / "runs" / run_id / "B_boundary_plane"
    v4_root = tmp_path / "v4" / "runs" / run_id / "B_boundary_plane"

    # Create v3 raw output files (simulate v3 runner output)
    raw_dir = v3_root / "raw"
    raw_dir.mkdir(parents=True)

    # B0 produces BOUNDARY_INVENTORY.json across 2 partitions
    (raw_dir / "B0__partition_001.json").write_text(json.dumps({
        "artifacts": [{
            "artifact_name": "BOUNDARY_INVENTORY.json",
            "payload": {"items": [
                {"id": "BOUNDARY:auth_check", "path": "src/auth.py", "line_range": [10, 15],
                 "evidence": [{"path": "src/auth.py", "line_range": [10, 15], "excerpt": "def check_auth()"}]}
            ]}
        }]
    }))
    (raw_dir / "B0__partition_002.json").write_text(json.dumps({
        "artifacts": [{
            "artifact_name": "BOUNDARY_INVENTORY.json",
            "payload": {"items": [
                {"id": "BOUNDARY:input_val", "path": "src/validate.py", "line_range": [5, 8],
                 "evidence": [{"path": "src/validate.py", "line_range": [5, 8], "excerpt": "def validate_input()"}]}
            ]}
        }]
    }))

    return {
        "run_id": run_id,
        "v3_root": tmp_path / "v3" / "runs",
        "v4_root": tmp_path / "v4" / "runs",
        "v3_phase_dir": v3_root,
        "v4_phase_dir": v4_root,
    }


@pytest.fixture
def simple_promptset():
    """Minimal promptset for phase B."""
    return {
        "phases": {
            "B": {
                "steps": [
                    {"step_id": "B0", "outputs": ["BOUNDARY_INVENTORY.json", "BOUNDARY_PARTITIONS.json"]},
                    {"step_id": "B9", "outputs": ["BOUNDARY_MERGED.json", "BOUNDARY_QA.json"]},
                ]
            }
        }
    }


@pytest.fixture
def simple_artifact_rules():
    """Minimal artifact rules for phase B."""
    return {
        ("B", "BOUNDARY_INVENTORY.json"): ArtifactRule(
            phase="B", artifact_name="BOUNDARY_INVENTORY.json",
            canonical_writer_step_id="B0", kind="json_item_list",
            norm_artifact=True, allow_timestamp_keys=False,
            merge_strategy="itemlist_by_id", required_fields=("path", "line_range", "id"),
        ),
        ("B", "BOUNDARY_PARTITIONS.json"): ArtifactRule(
            phase="B", artifact_name="BOUNDARY_PARTITIONS.json",
            canonical_writer_step_id="B0", kind="json_item_list",
            norm_artifact=True, allow_timestamp_keys=False,
            merge_strategy="itemlist_by_id", required_fields=("path", "line_range", "id"),
        ),
        ("B", "BOUNDARY_MERGED.json"): ArtifactRule(
            phase="B", artifact_name="BOUNDARY_MERGED.json",
            canonical_writer_step_id="B9", kind="json_item_list",
            norm_artifact=True, allow_timestamp_keys=False,
            merge_strategy="itemlist_by_id", required_fields=("path", "line_range", "id"),
        ),
        ("B", "BOUNDARY_QA.json"): ArtifactRule(
            phase="B", artifact_name="BOUNDARY_QA.json",
            canonical_writer_step_id="B9", kind="json_item_list",
            norm_artifact=False, allow_timestamp_keys=True,
            merge_strategy="itemlist_by_id", required_fields=("path", "line_range", "id"),
        ),
    }


class TestSyncPhaseFromV3:
    """Tests for the core v4 norm assembly pipeline."""

    def test_merges_partitions_into_by_step(self, tmp_run_dirs, simple_promptset, simple_artifact_rules):
        """Two v3 partitions for B0 should merge into norm/by_step/B0/BOUNDARY_INVENTORY.json."""
        with patch("run_extraction_v4.V3_RUNS_ROOT", tmp_run_dirs["v3_root"]), \
             patch("run_extraction_v4.V4_RUNS_ROOT", tmp_run_dirs["v4_root"]), \
             patch("run_extraction_v4.PHASE_DIR_NAMES", {"B": "B_boundary_plane"}):

            sync_phase_from_v3(
                run_id=tmp_run_dirs["run_id"],
                phase="B",
                promptset=simple_promptset,
                artifact_rules=simple_artifact_rules,
                forbidden_norm_keys=["generated_at", "timestamp"],
            )

        by_step_b0 = tmp_run_dirs["v4_phase_dir"] / "norm" / "by_step" / "B0"
        inventory_path = by_step_b0 / "BOUNDARY_INVENTORY.json"
        assert inventory_path.exists(), "B0 norm artifact should exist"

        payload = json.loads(inventory_path.read_text())
        items = payload.get("items", [])
        assert len(items) == 2, f"Expected 2 merged items, got {len(items)}"
        ids = {item["id"] for item in items}
        assert ids == {"BOUNDARY:auth_check", "BOUNDARY:input_val"}

    def test_canonical_promotion(self, tmp_run_dirs, simple_promptset, simple_artifact_rules):
        """Canonical artifacts should be promoted to phase norm root."""
        with patch("run_extraction_v4.V3_RUNS_ROOT", tmp_run_dirs["v3_root"]), \
             patch("run_extraction_v4.V4_RUNS_ROOT", tmp_run_dirs["v4_root"]), \
             patch("run_extraction_v4.PHASE_DIR_NAMES", {"B": "B_boundary_plane"}):

            sync_phase_from_v3(
                run_id=tmp_run_dirs["run_id"],
                phase="B",
                promptset=simple_promptset,
                artifact_rules=simple_artifact_rules,
                forbidden_norm_keys=["generated_at"],
            )

        norm_root = tmp_run_dirs["v4_phase_dir"] / "norm" / "BOUNDARY_INVENTORY.json"
        assert norm_root.exists(), "Canonical artifact should be promoted to norm root"

    def test_forbidden_keys_stripped(self, tmp_run_dirs, simple_promptset, simple_artifact_rules):
        """Forbidden norm keys should be stripped from norm artifacts."""
        # Add a timestamp key to raw output
        raw_dir = tmp_run_dirs["v3_phase_dir"] / "raw"
        (raw_dir / "B0__partition_001.json").write_text(json.dumps({
            "artifacts": [{
                "artifact_name": "BOUNDARY_INVENTORY.json",
                "payload": {"items": [
                    {"id": "BOUNDARY:test", "path": "test.py", "line_range": [1, 1],
                     "generated_at": "2026-01-01T00:00:00Z",
                     "evidence": [{"path": "test.py", "line_range": [1, 1], "excerpt": "test"}]}
                ]}
            }]
        }))

        with patch("run_extraction_v4.V3_RUNS_ROOT", tmp_run_dirs["v3_root"]), \
             patch("run_extraction_v4.V4_RUNS_ROOT", tmp_run_dirs["v4_root"]), \
             patch("run_extraction_v4.PHASE_DIR_NAMES", {"B": "B_boundary_plane"}):

            sync_phase_from_v3(
                run_id=tmp_run_dirs["run_id"],
                phase="B",
                promptset=simple_promptset,
                artifact_rules=simple_artifact_rules,
                forbidden_norm_keys=["generated_at", "timestamp"],
            )

        inventory = json.loads(
            (tmp_run_dirs["v4_phase_dir"] / "norm" / "by_step" / "B0" / "BOUNDARY_INVENTORY.json")
            .read_text()
        )
        for item in inventory.get("items", []):
            assert "generated_at" not in item, "Forbidden key should be stripped"

    def test_collision_qa_written(self, tmp_run_dirs, simple_promptset, simple_artifact_rules):
        """Phase collision QA file should always be written."""
        with patch("run_extraction_v4.V3_RUNS_ROOT", tmp_run_dirs["v3_root"]), \
             patch("run_extraction_v4.V4_RUNS_ROOT", tmp_run_dirs["v4_root"]), \
             patch("run_extraction_v4.PHASE_DIR_NAMES", {"B": "B_boundary_plane"}):

            sync_phase_from_v3(
                run_id=tmp_run_dirs["run_id"],
                phase="B",
                promptset=simple_promptset,
                artifact_rules=simple_artifact_rules,
                forbidden_norm_keys=[],
            )

        collision_file = tmp_run_dirs["v4_phase_dir"] / "qa" / "PHASE_B_COLLISIONS.json"
        assert collision_file.exists()
        payload = json.loads(collision_file.read_text())
        assert payload["status"] == "PASS"

    def test_canonical_index_written(self, tmp_run_dirs, simple_promptset, simple_artifact_rules):
        """Canonical index QA file should list promoted artifacts with SHA256."""
        with patch("run_extraction_v4.V3_RUNS_ROOT", tmp_run_dirs["v3_root"]), \
             patch("run_extraction_v4.V4_RUNS_ROOT", tmp_run_dirs["v4_root"]), \
             patch("run_extraction_v4.PHASE_DIR_NAMES", {"B": "B_boundary_plane"}):

            sync_phase_from_v3(
                run_id=tmp_run_dirs["run_id"],
                phase="B",
                promptset=simple_promptset,
                artifact_rules=simple_artifact_rules,
                forbidden_norm_keys=[],
            )

        index_file = tmp_run_dirs["v4_phase_dir"] / "qa" / "PHASE_B_CANONICAL_INDEX.json"
        assert index_file.exists()
        payload = json.loads(index_file.read_text())
        assert len(payload["canonical_index"]) >= 1
        assert "sha256" in payload["canonical_index"][0]


class TestMergeItemListPayloads:
    """Unit tests for merge logic."""

    def test_merge_two_payloads_by_id(self):
        """Items with different IDs should both appear in merged output."""
        p1 = {"items": [{"id": "A", "value": 1}]}
        p2 = {"items": [{"id": "B", "value": 2}]}
        merged = merge_item_list_payloads([p1, p2])
        items = merged["items"]
        assert len(items) == 2

    def test_merge_duplicate_ids_merges_fields(self):
        """Items with same ID should merge fields."""
        p1 = {"items": [{"id": "A", "value": 1, "evidence": [{"path": "a.py", "line_range": [1, 1], "excerpt": "x"}]}]}
        p2 = {"items": [{"id": "A", "value": 2, "evidence": [{"path": "b.py", "line_range": [2, 2], "excerpt": "y"}]}]}
        merged = merge_item_list_payloads([p1, p2])
        items = merged["items"]
        assert len(items) == 1
        # Evidence should be merged
        assert len(items[0]["evidence"]) == 2

    def test_empty_payloads(self):
        """Empty payloads should produce empty items list."""
        merged = merge_item_list_payloads([])
        assert merged["items"] == []

    def test_id_less_items_get_synthetic_ids(self):
        """Items without 'id' field should get sha256-based synthetic IDs."""
        p1 = {"items": [{"path": "a.py", "line_range": [1, 1]}]}
        merged = merge_item_list_payloads([p1])
        items = merged["items"]
        assert len(items) == 1
        assert items[0].get("id", "").startswith("sha256:") or "id" not in items[0]


class TestStripForbiddenKeys:
    """Unit tests for forbidden key stripping."""

    def test_strips_top_level(self):
        result = strip_forbidden_keys({"generated_at": "x", "id": "y"}, ["generated_at"])
        assert "generated_at" not in result
        assert result["id"] == "y"

    def test_strips_nested(self):
        result = strip_forbidden_keys({"items": [{"generated_at": "x", "id": "y"}]}, ["generated_at"])
        assert "generated_at" not in result["items"][0]

    def test_empty_forbidden(self):
        data = {"generated_at": "x"}
        result = strip_forbidden_keys(data, [])
        assert result == data


class TestNormalizeEvidence:
    """Unit tests for evidence normalization."""

    def test_deduplicates(self):
        evidence = [
            {"path": "a.py", "line_range": [1, 1], "excerpt": "x"},
            {"path": "a.py", "line_range": [1, 1], "excerpt": "x"},
        ]
        result = normalize_evidence(evidence)
        assert len(result) == 1

    def test_sorts_by_path(self):
        evidence = [
            {"path": "b.py", "line_range": [1, 1], "excerpt": "x"},
            {"path": "a.py", "line_range": [1, 1], "excerpt": "y"},
        ]
        result = normalize_evidence(evidence)
        assert result[0]["path"] == "a.py"

    def test_truncates_excerpt(self):
        evidence = [{"path": "a.py", "line_range": [1, 1], "excerpt": "x" * 300}]
        result = normalize_evidence(evidence)
        assert len(result[0]["excerpt"]) <= 200
```

---

## 3. Chunking Edge Case Tests (F-17)

### Test File
`services/repo-truth-extractor/tests/test_chunking_edge_cases.py`

### Test Spec

```python
"""Edge case tests for plan_chunks_for_step and build_partition_context."""

from pathlib import Path

import pytest

import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "repo-truth-extractor" / "lib"))

from chunking import (
    build_file_manifest_hash,
    build_partition_context,
    estimate_tokens_from_text,
    plan_chunks_for_step,
)


class TestPlanChunksForStep:
    """Tests for partition → chunk planning logic."""

    def test_empty_partitions(self):
        """Empty partition list should produce no chunks."""
        result = plan_chunks_for_step([], {}, max_files=10, max_chars=100000)
        assert result == []

    def test_partition_with_no_paths(self):
        """Partition with empty paths list should produce one empty chunk."""
        partitions = [{"id": "P1", "paths": []}]
        result = plan_chunks_for_step(partitions, {}, max_files=10, max_chars=100000)
        assert len(result) == 1
        assert result[0]["file_count"] == 0
        assert result[0]["base_partition_id"] == "P1"

    def test_single_file_single_chunk(self):
        """One file should produce one chunk."""
        partitions = [{"id": "P1", "paths": ["src/a.py"]}]
        inventory = {"src/a.py": {"char_count_estimate": 1000, "size": 1000}}
        result = plan_chunks_for_step(partitions, inventory, max_files=10, max_chars=100000)
        assert len(result) == 1
        assert result[0]["file_count"] == 1

    def test_max_files_splits_chunks(self):
        """Exceeding max_files should split into multiple chunks."""
        paths = [f"src/file_{i}.py" for i in range(5)]
        partitions = [{"id": "P1", "paths": paths}]
        inventory = {p: {"char_count_estimate": 100} for p in paths}
        result = plan_chunks_for_step(partitions, inventory, max_files=2, max_chars=1000000)
        assert len(result) == 3  # ceil(5/2) = 3 chunks

    def test_max_chars_splits_chunks(self):
        """Exceeding max_chars (soft target = 70%) should split chunks."""
        paths = ["src/big_a.py", "src/big_b.py"]
        partitions = [{"id": "P1", "paths": paths}]
        inventory = {
            "src/big_a.py": {"char_count_estimate": 50000},
            "src/big_b.py": {"char_count_estimate": 50000},
        }
        # soft_target = 70000, each file ~50080 chars → first file fills chunk
        result = plan_chunks_for_step(partitions, inventory, max_files=100, max_chars=100000)
        assert len(result) == 2

    def test_chunk_ids_are_sequential(self):
        """Chunk IDs should be sequential across partitions."""
        partitions = [
            {"id": "P1", "paths": ["a.py"]},
            {"id": "P2", "paths": ["b.py"]},
        ]
        inventory = {"a.py": {"char_count_estimate": 100}, "b.py": {"char_count_estimate": 100}}
        result = plan_chunks_for_step(partitions, inventory, max_files=10, max_chars=100000)
        ids = [c["chunk_id"] for c in result]
        assert ids == ["P1_C0001", "P2_C0002"]

    def test_missing_inventory_entries(self):
        """Files not in inventory should get minimal char estimates."""
        partitions = [{"id": "P1", "paths": ["unknown.py"]}]
        result = plan_chunks_for_step(partitions, {}, max_files=10, max_chars=100000)
        assert len(result) == 1
        assert result[0]["file_count"] == 1


class TestBuildPartitionContext:
    """Tests for file content assembly with truncation."""

    def _read_fn(self, content_map):
        """Create a read_text_fn from a content map."""
        def read_text(path_str):
            return content_map.get(path_str, "")
        return read_text

    def test_empty_paths(self):
        """No paths should produce empty context."""
        context, stats, entries = build_partition_context(
            [], self._read_fn({}), file_truncate_chars=10000,
            max_files=10, max_chars=100000, tail_chars=500,
        )
        assert context == ""
        assert stats["files_total"] == 0

    def test_single_small_file(self):
        """Small file should appear in full."""
        content_map = {"src/a.py": "def hello():\n    return 'world'\n"}
        context, stats, entries = build_partition_context(
            ["src/a.py"], self._read_fn(content_map),
            file_truncate_chars=10000, max_files=10, max_chars=100000, tail_chars=500,
        )
        assert "def hello():" in context
        assert stats["files_included"] == 1
        assert stats["truncated_files"] == 0

    def test_file_truncation_with_tail(self):
        """Large file should be truncated with head+tail snippets."""
        big_content = "x" * 20000
        content_map = {"big.py": big_content}
        context, stats, entries = build_partition_context(
            ["big.py"], self._read_fn(content_map),
            file_truncate_chars=5000, max_files=10, max_chars=100000, tail_chars=500,
        )
        assert "[TRUNCATED_HEAD]" in context
        assert stats["truncated_files"] == 1
        assert stats["tail_snippet_files"] == 1

    def test_max_files_skips_excess(self):
        """Files beyond max_files should be skipped."""
        content_map = {f"f{i}.py": f"content_{i}" for i in range(5)}
        context, stats, entries = build_partition_context(
            [f"f{i}.py" for i in range(5)], self._read_fn(content_map),
            file_truncate_chars=10000, max_files=2, max_chars=100000, tail_chars=500,
        )
        assert stats["files_included"] == 2
        assert stats["files_skipped"] == 3

    def test_max_chars_skips_excess(self):
        """Files that would exceed max_chars should be skipped."""
        content_map = {
            "a.py": "a" * 500,
            "b.py": "b" * 500,
        }
        context, stats, entries = build_partition_context(
            ["a.py", "b.py"], self._read_fn(content_map),
            file_truncate_chars=10000, max_files=10, max_chars=600, tail_chars=100,
        )
        # First file ~520 bytes (with header), second would exceed 600
        assert stats["files_included"] >= 1

    def test_binary_file_empty_content(self):
        """File returning empty content should still be included."""
        content_map = {"binary.dat": ""}
        context, stats, entries = build_partition_context(
            ["binary.dat"], self._read_fn(content_map),
            file_truncate_chars=10000, max_files=10, max_chars=100000, tail_chars=500,
        )
        assert stats["files_included"] == 1
        assert "binary.dat" in context

    def test_oversized_single_file(self):
        """Single file larger than max_chars should be context-truncated."""
        content_map = {"huge.py": "x" * 100000}
        context, stats, entries = build_partition_context(
            ["huge.py"], self._read_fn(content_map),
            file_truncate_chars=50000, max_files=10, max_chars=5000, tail_chars=500,
        )
        assert "[CONTEXT_TRUNCATED_FOR_LIMIT]" in context
        assert stats["truncated_files"] == 1


class TestEstimateTokens:
    """Tests for token estimation heuristic."""

    def test_empty_string(self):
        assert estimate_tokens_from_text("") == 0

    def test_short_string(self):
        assert estimate_tokens_from_text("hi") >= 1

    def test_known_length(self):
        text = "a" * 400
        result = estimate_tokens_from_text(text)
        assert result == 100  # 400 / 4
```

---

## 4. Minimal Repo Fixture (F-15 Graceful Degradation)

### Purpose
Define a tiny repo structure for integration tests that lacks optional components (no Docker, no MCP, no TaskX).

### Fixture: `services/repo-truth-extractor/tests/fixtures/minimal_repo/`

```
minimal_repo/
├── README.md                    # "# Minimal Test Repo\nA test fixture."
├── .claude/
│   └── CLAUDE.md               # "# Test Project\nMinimal config."
├── src/
│   └── main.py                 # "def main():\n    print('hello')\n"
├── services/
│   └── registry.yaml           # "services: []"
└── pyproject.toml              # "[project]\nname = 'test'\nversion = '0.1.0'"
```

**What's intentionally missing** (to test graceful degradation):
- No `docker-compose*.yml` (no Docker)
- No `.taskx/` (no TaskX)
- No `compose.yml`
- No `.github/` (no CI)
- No MCP config files
- No `docs/` directory

### Fixture Creation Script

```python
# In conftest.py or as a pytest fixture:
@pytest.fixture
def minimal_repo(tmp_path):
    """Create a minimal repo for graceful degradation testing."""
    repo = tmp_path / "minimal_repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Minimal Test Repo\nA test fixture.\n")
    (repo / ".claude").mkdir()
    (repo / ".claude" / "CLAUDE.md").write_text("# Test Project\nMinimal config.\n")
    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("def main():\n    print('hello')\n")
    (repo / "services").mkdir()
    (repo / "services" / "registry.yaml").write_text("services: []\n")
    (repo / "pyproject.toml").write_text('[project]\nname = "test"\nversion = "0.1.0"\n')
    return repo
```

---

## 5. Test File Locations and Naming

| Test File | Purpose | Pytest Markers | Fixtures |
|-----------|---------|----------------|----------|
| `tests/test_e2e_smoke_v4.py` | E2E dry-run smoke tests | `@pytest.mark.e2e` | None (uses real repo) |
| `tests/test_run_extraction_v4_norm_assembly.py` | v4 norm assembly unit tests | None | `tmp_run_dirs`, `simple_promptset`, `simple_artifact_rules` |
| `tests/test_chunking_edge_cases.py` | Chunking logic edge cases | None | `content_map` helpers |

### Run Commands

```bash
# All new tests:
pytest services/repo-truth-extractor/tests/test_e2e_smoke_v4.py \
      services/repo-truth-extractor/tests/test_run_extraction_v4_norm_assembly.py \
      services/repo-truth-extractor/tests/test_chunking_edge_cases.py \
      -v

# Just unit tests (fast):
pytest services/repo-truth-extractor/tests/test_run_extraction_v4_norm_assembly.py \
      services/repo-truth-extractor/tests/test_chunking_edge_cases.py \
      -v

# Just E2E (slow):
pytest services/repo-truth-extractor/tests/test_e2e_smoke_v4.py -v -m e2e

# All tests in repo-truth-extractor:
pytest services/repo-truth-extractor/tests/ -v
```

### Dependencies
- `pytest` (already in project)
- `pyyaml` (already in project for promptset loading)
- No new dependencies required

---

## 6. Coverage Targets After Implementation

| Area | Before | After | New Tests |
|------|--------|-------|-----------|
| v4 norm assembly | ❌ 0 tests | ✅ 5 tests | `test_run_extraction_v4_norm_assembly.py` |
| E2E pipeline | ❌ 0 tests | ✅ 4 tests | `test_e2e_smoke_v4.py` |
| Chunking edge cases | ❌ 0 tests | ✅ 13 tests | `test_chunking_edge_cases.py` |
| Merge logic | ⚠️ Partial | ✅ Extended | 4 new merge tests in norm assembly |
| Evidence normalization | ⚠️ Partial | ✅ Extended | 3 new evidence tests |
| **Total new tests** | — | — | **~29 tests** |
