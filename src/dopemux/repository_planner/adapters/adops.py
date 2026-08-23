from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path

from jsonschema import Draft202012Validator

from ..models import Claim, LaneEvidence, SourceRef, SourceSnapshot


_PROJECT_ID = "DDD-Enterprises/adOps"
_PINNED_HEAD = "864915b9cc8ff254eaa877627df1e510dc49dbec"
_ACTIVE_PACKET = "TP-ADOPS-ELITELUXE24-MODE-V1"
_LEGACY_CANDIDATE = "4ce6b644afa72231c24b3cdac58f251e1ca03321"
_TRANSFORMATION_ID = "adops-project-adapter.v1"
_FIXTURE_REL = Path("reports/project-control-plane/fixtures/adops_fixture")
_INVENTORY_LOCATOR = (_FIXTURE_REL / "SOURCES.json").as_posix()
_SHA1_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")

_EXPECTED_SOURCES = {
    "PROJECT_INSTRUCTIONS.md": (
        "f91238c23f5dc63ad872844b1c15569b7a514113",
        "f85f1003500f16b754424afa0c0aa6a83af291d7ca9ec2f2749f1deda1276437",
    ),
    ".claude/PROJECT_INSTRUCTIONS.md": (
        "ba3b038c4d70769c75a97b1ef7ef2a01273e17ff",
        "331690e44f4901529dfef442ba86024b58dbb0bc51427d10e14eb2871768b642",
    ),
    ".github/copilot-instructions.md": (
        "2ed6882d45692249be9a0f76f09a972842184c65",
        "99e71fa2ed639f76a968327f17fb2352a4efcafcd583d128872dfa8d2a458c04",
    ),
    "task-packets/ACTIVE.md": (
        "90b5ee6be2c24e8dc0fad5988d306b79d556ede6",
        "4b35575f2535d4356543a202f4cb67826051d44f9321eb9f343c6a3432a6db79",
    ),
    "task-packets/TP-ADOPS-ELITELUXE24-MODE-V1.md": (
        "dcc97c1c881f281847ac17e5c0b10a0ce42101d3",
        "eb72e358ab582778d1ebc8e3a4af2be1068891001d840268ef390692dddf2e1b",
    ),
    "proof/TP-ADOPS-ELITELUXE24-MODE-V1/01_head_binding.txt": (
        "ac7db8438cee08180685fe53709e57524c7abafe",
        "aa3f84b4f06583cebe00a304f60087d4b5d0c2012843cada447377eec72f45a3",
    ),
    "proof/TP-ADOPS-ELITELUXE24-MODE-V1/IMPLEMENTER_REPORT.md": (
        "57269e213fd5db5f4224c04d92218f54f0106509",
        "f0edbc8af7ffea79393dc8c782dbcdb03908a31805b76e82a7f97e4b9b426459",
    ),
}
_EXPECTED_ABSENT = {
    "proof/TP-ADOPS-ELITELUXE24-MODE-V1/AUDITOR_REPORT.md",
    "acceptance/TP-ADOPS-ELITELUXE24-MODE-V1.json",
}
_PR_METADATA_SHA256 = (
    "1ab6784917e812516f1338df758528adc4a8b901f1f482b315e65e02b2620ee9"
)


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _read_json(path: Path) -> tuple[dict[str, object], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"required verified JSON is unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"required verified JSON must be an object: {path.name}")
    return value, raw


def _validate_schema(
    instance: Mapping[str, object], schema_path: Path, label: str
) -> None:
    schema, _ = _read_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValueError(f"{label} schema validation failed: {errors[0].message}")


def _source_index(inventory: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    entries: dict[str, Mapping[str, object]] = {}
    for index, raw in enumerate(_array(inventory.get("sources"), "sources")):
        entry = _object(raw, f"sources[{index}]")
        path = _text(entry.get("path"), f"sources[{index}].path")
        if path in entries:
            raise ValueError(f"duplicate source inventory path: {path}")
        entries[path] = entry

    expected = set(_EXPECTED_SOURCES) | _EXPECTED_ABSENT
    if set(entries) != expected:
        raise ValueError("source inventory paths conflict with the frozen allowlist")

    prefix = f"https://github.com/DDD-Enterprises/adOps/blob/{_PINNED_HEAD}/"
    for path, (expected_blob_sha, expected_sha256) in _EXPECTED_SOURCES.items():
        entry = entries[path]
        if entry.get("state") != "PRESENT":
            raise ValueError(f"required source is not present: {path}")
        if entry.get("sha256") != expected_sha256:
            raise ValueError(f"source SHA-256 conflicts with frozen inventory: {path}")
        if (
            _SHA1_RE.fullmatch(str(entry.get("blob_sha"))) is None
            or entry.get("blob_sha") != expected_blob_sha
        ):
            raise ValueError(f"source blob SHA conflicts with frozen inventory: {path}")
        if entry.get("url") != prefix + path:
            raise ValueError(f"source URL is not pinned: {path}")
        _text(entry.get("fetched_at"), f"source fetched_at: {path}")

    for path in _EXPECTED_ABSENT:
        entry = entries[path]
        if (
            entry.get("state") != "ABSENT"
            or entry.get("blob_sha") is not None
            or entry.get("sha256") is not None
        ):
            raise ValueError(f"absent source is not fail-closed: {path}")
    return entries


def _validate_inventory(
    inventory: Mapping[str, object], inventory_bytes: bytes
) -> tuple[dict[str, Mapping[str, object]], str, str]:
    if inventory.get("schema_version") != "adops.source_inventory.v1":
        raise ValueError("source inventory schema version is unsupported")
    if inventory.get("repository") != _PROJECT_ID:
        raise ValueError("source inventory repository identity conflicts")
    if inventory.get("pinned_head") != _PINNED_HEAD:
        raise ValueError("source inventory pinned head conflicts")
    fetched_at = _text(inventory.get("fetched_at"), "inventory fetched_at")
    entries = _source_index(inventory)

    legacy = _object(inventory.get("legacy_candidate"), "legacy_candidate")
    if (
        legacy.get("commit_sha") != _LEGACY_CANDIDATE
        or legacy.get("status") != "REMOTE_COMMIT_ABSENT"
    ):
        raise ValueError("legacy candidate evidence conflicts with remote absence")

    observations = _array(
        inventory.get("github_observations"), "github_observations"
    )
    if len(observations) != 1:
        raise ValueError("exactly one GitHub design observation is required")
    pr = _object(observations[0], "github_observations[0]")
    if (
        pr.get("locator") != "https://github.com/DDD-Enterprises/adOps/pull/277"
        or pr.get("number") != 277
        or pr.get("title")
        != "docs(governance): define AdOps PCP extension boundary"
        or pr.get("state") != "open"
        or pr.get("classification") != "DESIGN_EVIDENCE_ONLY"
        or pr.get("implementation_acceptance") is not False
        or pr.get("draft") is not True
        or pr.get("merged") is not False
        or pr.get("base_sha") != _PINNED_HEAD
        or pr.get("head_sha") != "cbb7a9a43bc2cbd0e38b01588908aa69a91fdbd1"
        or pr.get("updated_at") != "2026-08-22T08:04:05Z"
        or pr.get("canonical_metadata_sha256") != _PR_METADATA_SHA256
    ):
        raise ValueError("PR #277 must remain non-authoritative design evidence")

    inventory_sha256 = hashlib.sha256(inventory_bytes).hexdigest()
    return entries, fetched_at, inventory_sha256


def _ref(
    locator: str, sha256: str, fetched_at: str
) -> SourceRef:
    if _SHA256_RE.fullmatch(sha256) is None:
        raise ValueError("source reference SHA-256 is invalid")
    return SourceRef(
        locator=locator,
        sha256=sha256,
        observed_head=_PINNED_HEAD,
        fetched_at=fetched_at,
    )


class AdOpsExtensionAdapter:
    extension_id = "adops-project"

    def matches(self, generic_export: Mapping[str, object]) -> bool:
        return generic_export.get("project_id") == _PROJECT_ID

    def enrich(
        self, generic_export: Mapping[str, object], source_root: Path
    ) -> SourceSnapshot:
        if not self.matches(generic_export):
            raise ValueError("generic export does not match the AdOps extension")

        root = source_root.resolve()
        schema_root = root / "schemas/project_control_plane"
        _validate_schema(
            generic_export,
            schema_root / "project_evidence_export.schema.json",
            "generic export",
        )
        repo_state = _object(generic_export.get("repo_state"), "repo_state")
        if repo_state.get("head_sha") != _PINNED_HEAD:
            raise ValueError("generic export does not match the pinned head")
        dirty_state = _object(generic_export.get("dirty_state"), "dirty_state")
        if (
            repo_state.get("root_verified") is not True
            or repo_state.get("worktree_state") != "CLEAN"
            or dirty_state.get("state") != "CLEAN"
            or dirty_state.get("paths") != []
        ):
            raise ValueError("AdOps enrichment requires a clean source state")

        if generic_export.get("active_packet") != {
            "state": "PRESENT",
            "packet_id": _ACTIVE_PACKET,
            "path": f"task-packets/{_ACTIVE_PACKET}.md",
        }:
            raise ValueError("generic export active packet conflicts with AdOps evidence")
        if generic_export.get("proof_manifest") != {
            "state": "PRESENT",
            "path": f"proof/{_ACTIVE_PACKET}/IMPLEMENTER_REPORT.md",
            "freshness": "STALE",
        }:
            raise ValueError("generic export proof manifest conflicts with AdOps evidence")

        fixture_root = root / _FIXTURE_REL
        inventory, inventory_bytes = _read_json(fixture_root / "SOURCES.json")
        entries, fetched_at, inventory_sha256 = _validate_inventory(
            inventory, inventory_bytes
        )
        profile, _ = _read_json(fixture_root / "project_profile.json")
        frozen_export, _ = _read_json(fixture_root / "evidence_export.json")
        _validate_schema(
            profile,
            schema_root / "project_profile.schema.json",
            "AdOps project profile",
        )
        _validate_schema(
            frozen_export,
            schema_root / "project_evidence_export.schema.json",
            "AdOps evidence fixture",
        )
        if profile.get("project_id") != _PROJECT_ID:
            raise ValueError("AdOps project profile identity conflicts")
        frozen_repo_state = _object(frozen_export.get("repo_state"), "repo_state")
        if frozen_repo_state.get("head_sha") != _PINNED_HEAD:
            raise ValueError("AdOps evidence fixture does not match the pinned head")
        if frozen_export.get("active_packet") != {
            "state": "PRESENT",
            "packet_id": _ACTIVE_PACKET,
            "path": f"task-packets/{_ACTIVE_PACKET}.md",
        }:
            raise ValueError("active packet evidence conflicts")
        if frozen_export.get("proof_manifest") != {
            "state": "PRESENT",
            "path": f"proof/{_ACTIVE_PACKET}/IMPLEMENTER_REPORT.md",
            "freshness": "STALE",
        }:
            raise ValueError("proof evidence must remain stale and fail closed")

        inventory_ref = _ref(_INVENTORY_LOCATOR, inventory_sha256, fetched_at)
        active = entries["task-packets/ACTIVE.md"]
        head_binding = entries[f"proof/{_ACTIVE_PACKET}/01_head_binding.txt"]
        observations = _array(
            inventory.get("github_observations"), "github_observations"
        )
        pr = _object(observations[0], "github_observations[0]")
        claims = (
            Claim(
                claim_id="adops:active-packet",
                project_id=_PROJECT_ID,
                lane_id=_ACTIVE_PACKET,
                field="active_packet",
                value=_ACTIVE_PACKET,
                materiality="BLOCKING",
                freshness="STALE",
                transformation_id=_TRANSFORMATION_ID,
                source=_ref(
                    _text(active.get("url"), "active packet URL"),
                    _text(active.get("sha256"), "active packet SHA-256"),
                    fetched_at,
                ),
            ),
            Claim(
                claim_id="adops:proof-freshness",
                project_id=_PROJECT_ID,
                lane_id=_ACTIVE_PACKET,
                field="proof_freshness",
                value="STALE",
                materiality="BLOCKING",
                freshness="STALE",
                transformation_id=_TRANSFORMATION_ID,
                source=_ref(
                    _text(head_binding.get("url"), "head binding URL"),
                    _text(head_binding.get("sha256"), "head binding SHA-256"),
                    fetched_at,
                ),
            ),
            Claim(
                claim_id="adops:audit-status",
                project_id=_PROJECT_ID,
                lane_id=_ACTIVE_PACKET,
                field="audit_status",
                value="UNKNOWN",
                materiality="BLOCKING",
                freshness="STALE",
                transformation_id=_TRANSFORMATION_ID,
                source=inventory_ref,
            ),
            Claim(
                claim_id="adops:acceptance-status",
                project_id=_PROJECT_ID,
                lane_id=_ACTIVE_PACKET,
                field="acceptance_status",
                value="UNKNOWN",
                materiality="BLOCKING",
                freshness="STALE",
                transformation_id=_TRANSFORMATION_ID,
                source=inventory_ref,
            ),
            Claim(
                claim_id="adops:remote-candidate",
                project_id=_PROJECT_ID,
                lane_id=_ACTIVE_PACKET,
                field="remote_candidate",
                value="REMOTE_COMMIT_PRESENT",
                materiality="BLOCKING",
                freshness="STALE",
                transformation_id=_TRANSFORMATION_ID,
                source=inventory_ref,
            ),
            Claim(
                claim_id="adops:legacy-candidate",
                project_id=_PROJECT_ID,
                lane_id=_ACTIVE_PACKET,
                field="legacy_candidate",
                value="REMOTE_COMMIT_ABSENT",
                materiality="BLOCKING",
                freshness="STALE",
                transformation_id=_TRANSFORMATION_ID,
                source=inventory_ref,
            ),
            Claim(
                claim_id="adops:governance-pr-277",
                project_id=_PROJECT_ID,
                lane_id=_ACTIVE_PACKET,
                field="governance_pr_277",
                value="DESIGN_EVIDENCE_ONLY",
                materiality="NON_BLOCKING",
                freshness="STALE",
                transformation_id=_TRANSFORMATION_ID,
                source=_ref(
                    _text(pr.get("locator"), "PR #277 locator"),
                    _text(
                        pr.get("canonical_metadata_sha256"),
                        "PR #277 metadata SHA-256",
                    ),
                    fetched_at,
                ),
            ),
        )
        lane = LaneEvidence(
            project_id=_PROJECT_ID,
            lane_id=_ACTIVE_PACKET,
            candidate_sha=_PINNED_HEAD,
            dependencies=(),
            gate_status="FAIL",
            audit_status="UNKNOWN",
            lifecycle_state="IMPLEMENTED_NOT_ACCEPTED",
        )
        return SourceSnapshot(
            schema_version="pcp.repository_planner_source.v1",
            project_id=_PROJECT_ID,
            authority="NONE",
            surface_class="PROJECTION",
            is_proof=False,
            evidence_class="ADOPS_PROJECT_EXTENSION",
            observed_head=_PINNED_HEAD,
            fetched_at=fetched_at,
            freshness="STALE",
            claims=claims,
            lanes=(lane,),
        )
