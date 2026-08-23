from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

FIXTURE_ROOT = (
    Path(__file__).parents[1] / "fixtures" / "repository_planner" / "foundation"
)
DATA_FILES = ("dopemux.json", "adops.json", "dnh_crm.json")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_manifest_hashes_every_foundation_snapshot() -> None:
    manifest = _read_json(FIXTURE_ROOT / "SOURCES.json")
    entries = manifest["sources"]
    assert isinstance(entries, list)
    assert {entry["path"] for entry in entries} == set(DATA_FILES)

    for entry in entries:
        payload = (FIXTURE_ROOT / entry["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]
        assert entry["repository"]
        assert re.fullmatch(r"[0-9a-f]{40}", entry["ref"])
        assert entry["fetched_at"].endswith("Z")
        assert entry["privacy_class"] == "PUBLIC_REPOSITORY_EVIDENCE"
        assert entry["redaction_reason"]


def test_fixture_bytes_are_redacted_and_portable() -> None:
    forbidden = (
        re.compile(r"(?i)(authorization|api[_-]?key|access[_-]?token|password)\s*[:=]"),
        re.compile(r"/(?:Users|home)/[^/\s]+/"),
        re.compile(r"sha256:PLACEHOLDER"),
        re.compile(r"BEGIN (?:RSA |OPENSSH )?PRIVATE KEY"),
    )
    for name in ("SOURCES.json", *DATA_FILES):
        text = (FIXTURE_ROOT / name).read_text(encoding="utf-8")
        for pattern in forbidden:
            assert pattern.search(text) is None, f"{name} matched {pattern.pattern}"


def test_foundation_cases_cover_required_fail_closed_states() -> None:
    snapshots = [_read_json(FIXTURE_ROOT / name) for name in DATA_FILES]
    claim_values = {
        claim["value"] for snapshot in snapshots for claim in snapshot["claims"]
    }
    freshness = {snapshot["freshness"] for snapshot in snapshots}
    dependencies = {
        (
            dependency["project_id"],
            dependency["lane_id"],
            dependency["candidate_sha"],
        )
        for snapshot in snapshots
        for lane in snapshot["lanes"]
        for dependency in lane["dependencies"]
    }

    assert "REMOTE_COMMIT_ABSENT" in claim_values
    assert "UNKNOWN" in claim_values
    assert "STALE" in freshness
    assert dependencies
    assert any(
        len(
            {
                claim["value"]
                for claim in snapshot["claims"]
                if claim["field"] == "acceptance_state"
            }
        )
        > 1
        for snapshot in snapshots
    )
