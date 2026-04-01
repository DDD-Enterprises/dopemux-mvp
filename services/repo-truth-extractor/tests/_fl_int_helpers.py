from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from typing import Any, Dict


PHASE_DIR_NAMES = {
    "D": "D_docs_pipeline",
    "C": "C_code_surfaces",
    "R": "R_arbitration",
    "X": "X_feature_index",
}


def ensure_service_root_on_path() -> Path:
    root = Path(__file__).resolve().parents[3]
    service_root = root / "services" / "repo-truth-extractor"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))
    return root


def load_collect_module():
    ensure_service_root_on_path()
    return importlib.import_module("fl_int.collect_input")


def load_run_module():
    ensure_service_root_on_path()
    return importlib.import_module("fl_int.run_fl_int")


def load_reduce_module():
    ensure_service_root_on_path()
    return importlib.import_module("fl_int.reduce_input")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _item(row_id: str, path: str, line_range: list[int], **extra: Any) -> Dict[str, Any]:
    base = {
        "id": row_id,
        "path": path,
        "line_range": line_range,
    }
    base.update(extra)
    return base


def build_fl_int_run_root(tmp_path: Path, *, include_x: bool = True) -> Path:
    run_root = tmp_path / "runs" / "fl_int_case"
    for phase_dir in PHASE_DIR_NAMES.values():
        (run_root / phase_dir / "norm").mkdir(parents=True, exist_ok=True)

    write_json(
        run_root / PHASE_DIR_NAMES["D"] / "norm" / "DOC_CONTRACT_CLAIMS.json",
        {
            "schema": "DOC_CONTRACT_CLAIMS@v1",
            "items": [
                _item(
                    "doc_claim_pm",
                    "docs/pm-plane.md",
                    [10, 12],
                    name="PM plane preserved",
                    evidence=[
                        {"path": "docs/pm-plane.md", "line_range": [10, 12], "excerpt": "PM plane governs planning surfaces."}
                    ],
                ),
                _item(
                    "doc_claim_control",
                    "docs/architecture.md",
                    [20, 24],
                    name="Control plane current state",
                    evidence=[
                        {"path": "docs/architecture.md", "line_range": [20, 24], "excerpt": "Control plane is implemented in the runner."}
                    ],
                ),
            ],
        },
    )
    write_json(
        run_root / PHASE_DIR_NAMES["C"] / "norm" / "COGNITIVE_FEATURES_SURFACE.json",
        {
            "schema": "COGNITIVE_FEATURES_SURFACE@v1",
            "items": [
                _item(
                    "code_feature_pm",
                    "services/task-orchestrator/server.py",
                    [30, 35],
                    component="task-orchestrator",
                    evidence=[
                        {
                            "path": "services/task-orchestrator/server.py",
                            "line_range": [30, 35],
                            "excerpt": "publish planning updates into PM plane",
                        }
                    ],
                )
            ],
        },
    )
    (run_root / PHASE_DIR_NAMES["R"] / "norm" / "CONFLICT_LEDGER.md").write_text(
        "# Conflict Ledger\n\n- contradiction FL-1 remains unresolved.\n",
        encoding="utf-8",
    )
    if include_x:
        write_json(
            run_root / PHASE_DIR_NAMES["X"] / "norm" / "FEATURE_SURFACE.json",
            {
                "schema": "FEATURE_SURFACE@v1",
                "items": [
                    _item(
                        "x_feature_pm",
                        "services/task-orchestrator/server.py",
                        [30, 35],
                        component="task-orchestrator",
                        symbol="sync_to_pm_plane",
                        evidence=[
                            {
                                "path": "services/task-orchestrator/server.py",
                                "line_range": [30, 35],
                                "excerpt": "sync_to_pm_plane",
                            }
                        ],
                    )
                ],
            },
        )
    else:
        x_norm = run_root / PHASE_DIR_NAMES["X"] / "norm"
        for child in list(x_norm.iterdir()):
            child.unlink()
        x_norm.rmdir()
    return run_root


def build_large_fl_int_run_root(tmp_path: Path) -> Path:
    run_root = build_fl_int_run_root(tmp_path, include_x=True)
    docs_norm = run_root / PHASE_DIR_NAMES["D"] / "norm"
    repeated_status = "\n".join(f"{line_no:04d}: status report placeholder" for line_no in range(1, 161))
    repeated_design = "\n".join(
        [
            "0001: # Architecture Overview",
            "0002: The system design and integration workflow controls runtime behavior.",
            "0003: Authority and policy govern the PM control plane and memory ledger.",
            "0004: ## Governance",
            "0005: PM governance and policy surfaces remain authoritative.",
        ]
        * 24
    )
    (docs_norm / "LONG_ARCHITECTURE.md").write_text(repeated_design + "\n", encoding="utf-8")
    for index in range(1, 7):
        (docs_norm / f"LONG_STATUS_{index:02d}.md").write_text(repeated_status + "\n", encoding="utf-8")
    write_json(
        docs_norm / "DESIGN_LEDGER.json",
        {
            "schema": "DESIGN_LEDGER@v1",
            "items": [
                _item(
                    "ledger_pm",
                    "docs/governance.md",
                    [11, 14],
                    title="PM governance",
                    claim_text="PM governance policy controls orchestration and authority routing.",
                    evidence=[{"path": "docs/governance.md", "line_range": [11, 14], "excerpt": "PM governance policy controls orchestration and authority routing."}],
                ),
                _item(
                    "ledger_status",
                    "docs/status.md",
                    [3, 4],
                    title="Status report",
                    claim_text="Daily status report without design-bearing detail.",
                    evidence=[{"path": "docs/status.md", "line_range": [3, 4], "excerpt": "Daily status report without design-bearing detail."}],
                ),
            ],
        },
    )
    return run_root


def fake_fl_int_payload(step_id: str) -> Dict[str, Any]:
    if step_id == "F0":
        return {
            "status": "OK",
            "design_claims_raw": {
                "schema": "DESIGN_CLAIMS_RAW@v1",
                "items": [
                    _item(
                        "claim_pm_current",
                        "docs/pm-plane.md",
                        [10, 12],
                        claim_text="PM plane governs planning surfaces.",
                        source_artifact="DOC_CONTRACT_CLAIMS.json",
                        plane="pm",
                        evidence=[{"path": "docs/pm-plane.md", "line_range": [10, 12], "excerpt": "PM plane governs planning surfaces."}],
                    ),
                    _item(
                        "claim_control_historical",
                        "docs/architecture.md",
                        [20, 24],
                        claim_text="Legacy control plane design remains in docs.",
                        source_artifact="DOC_CONTRACT_CLAIMS.json",
                        plane="control",
                        evidence=[{"path": "docs/architecture.md", "line_range": [20, 24], "excerpt": "Legacy control plane design remains in docs."}],
                    ),
                ],
            },
            "missing_evidence": [],
        }
    if step_id == "F1":
        return {
            "status": "OK",
            "design_claims_classified": {
                "schema": "DESIGN_CLAIMS_CLASSIFIED@v1",
                "items": [
                    _item(
                        "claim_pm_current",
                        "docs/pm-plane.md",
                        [10, 12],
                        claim_text="PM plane governs planning surfaces.",
                        plane="pm",
                        evidence_class="REPO_PROVEN_CURRENT",
                        temporal_status="current",
                        confidence="high",
                        implementation_completeness="implemented",
                        contradiction_ids=[],
                        evidence=[{"path": "docs/pm-plane.md", "line_range": [10, 12], "excerpt": "PM plane governs planning surfaces."}],
                    ),
                    _item(
                        "claim_control_historical",
                        "docs/architecture.md",
                        [20, 24],
                        claim_text="Legacy control plane design remains in docs.",
                        plane="control",
                        evidence_class="HISTORICAL_DOC",
                        temporal_status="historical",
                        confidence="medium",
                        implementation_completeness="unknown",
                        contradiction_ids=["FL-1"],
                        evidence=[{"path": "docs/architecture.md", "line_range": [20, 24], "excerpt": "Legacy control plane design remains in docs."}],
                    ),
                ],
            },
            "missing_evidence": [],
        }
    if step_id == "F2":
        return {
            "status": "OK",
            "design_contradictions": {
                "schema": "DESIGN_CONTRADICTIONS@v1",
                "items": [
                    _item(
                        "FL-1",
                        "docs/architecture.md",
                        [20, 24],
                        summary="Historical control-plane docs conflict with current PM-plane evidence.",
                        status="unresolved",
                        claim_ids=["claim_pm_current", "claim_control_historical"],
                        evidence=[{"path": "docs/architecture.md", "line_range": [20, 24], "excerpt": "Legacy control plane design remains in docs."}],
                    )
                ],
            },
            "missing_evidence": [],
        }
    if step_id == "F4":
        return {
            "status": "OK",
            "canonical_design_markdown": "# Canonical Design\n\n## 1. Verified current state\n- PM plane governs planning surfaces.\n\n## 4. Contradictions\n- FL-1 remains unresolved.\n",
            "meta": {
                "section_summaries": [
                    {"section_id": "1", "title": "Verified current state", "claim_count": 1},
                    {"section_id": "4", "title": "Contradictions", "claim_count": 1},
                ],
                "contradictions": [{"contradiction_id": "FL-1", "status": "unresolved"}],
                "statistics": {
                    "repo_proven_current_count": 1,
                    "historical_count": 1,
                    "target_count": 0,
                    "unknown_count": 0,
                },
            },
            "missing_evidence": [],
        }
    if step_id == "L0":
        return {
            "status": "OK",
            "feature_candidates_raw": {
                "schema": "FEATURE_CANDIDATES_RAW@v1",
                "items": [
                    _item(
                        "feature_pm_sync",
                        "services/task-orchestrator/server.py",
                        [30, 35],
                        title="PM plane sync",
                        trigger="task update",
                        outcome="sync planning state",
                        domain="planning",
                        plane="pm",
                        evidence_class="REPO_PROVEN_CURRENT",
                        temporal_status="current",
                        evidence=[{"path": "services/task-orchestrator/server.py", "line_range": [30, 35], "excerpt": "sync_to_pm_plane"}],
                    ),
                    _item(
                        "feature_legacy_control",
                        "docs/architecture.md",
                        [20, 24],
                        title="Legacy control surface",
                        trigger="legacy workflow",
                        outcome="legacy control routing",
                        domain="control",
                        plane="control",
                        evidence_class="HISTORICAL_DOC",
                        temporal_status="historical",
                        evidence=[{"path": "docs/architecture.md", "line_range": [20, 24], "excerpt": "Legacy control plane design remains in docs."}],
                    ),
                    _item(
                        "feature_non_feature",
                        "docs/notes.md",
                        [1, 1],
                        title="Implementation note",
                        trigger="note",
                        outcome="none",
                        domain="misc",
                        plane="unknown",
                        evidence_class="UNKNOWN",
                        temporal_status="unknown",
                        evidence=[{"path": "docs/notes.md", "line_range": [1, 1], "excerpt": "Implementation note"}],
                    ),
                ],
            },
            "missing_evidence": [],
        }
    if step_id == "L1":
        return {
            "status": "OK",
            "feature_candidates_normalized": {
                "schema": "FEATURE_CANDIDATES_NORMALIZED@v1",
                "items": [
                    _item(
                        "feature_pm_sync",
                        "services/task-orchestrator/server.py",
                        [30, 35],
                        title="PM plane sync",
                        trigger="task update",
                        outcome="sync planning state",
                        domain="planning",
                        plane="pm",
                        evidence_class="REPO_PROVEN_CURRENT",
                        temporal_status="current",
                        source_feature_ids=["feature_pm_sync"],
                        evidence=[{"path": "services/task-orchestrator/server.py", "line_range": [30, 35], "excerpt": "sync_to_pm_plane"}],
                    ),
                    _item(
                        "feature_legacy_control",
                        "docs/architecture.md",
                        [20, 24],
                        title="Legacy control surface",
                        trigger="legacy workflow",
                        outcome="legacy control routing",
                        domain="control",
                        plane="control",
                        evidence_class="HISTORICAL_DOC",
                        temporal_status="historical",
                        source_feature_ids=["feature_legacy_control"],
                        evidence=[{"path": "docs/architecture.md", "line_range": [20, 24], "excerpt": "Legacy control plane design remains in docs."}],
                    ),
                    _item(
                        "feature_non_feature",
                        "docs/notes.md",
                        [1, 1],
                        title="Implementation note",
                        trigger="note",
                        outcome="none",
                        domain="misc",
                        plane="unknown",
                        evidence_class="UNKNOWN",
                        temporal_status="unknown",
                        source_feature_ids=["feature_non_feature"],
                        evidence=[{"path": "docs/notes.md", "line_range": [1, 1], "excerpt": "Implementation note"}],
                    ),
                ],
            },
            "feature_merge_log": {
                "schema": "FEATURE_MERGE_LOG@v1",
                "items": [
                    _item(
                        "merge_pm_sync",
                        "services/task-orchestrator/server.py",
                        [30, 35],
                        canonical_feature_id="feature_pm_sync",
                        merged_feature_ids=["feature_pm_sync"],
                        reason="single canonical feature",
                        evidence=[{"path": "services/task-orchestrator/server.py", "line_range": [30, 35], "excerpt": "sync_to_pm_plane"}],
                    )
                ],
            },
            "missing_evidence": [],
        }
    if step_id == "L3":
        return {
            "status": "OK",
            "feature_ledger_routing": {
                "schema": "FEATURE_LEDGER_ROUTING@v1",
                "items": [
                    _item(
                        "route_pm_sync",
                        "services/task-orchestrator/server.py",
                        [30, 35],
                        feature_id="feature_pm_sync",
                        routing_bucket="canonical",
                        plane="pm",
                        evidence_class="REPO_PROVEN_CURRENT",
                        temporal_status="current",
                        reason="implemented PM-plane capability",
                        evidence=[{"path": "services/task-orchestrator/server.py", "line_range": [30, 35], "excerpt": "sync_to_pm_plane"}],
                    ),
                    _item(
                        "route_legacy_control",
                        "docs/architecture.md",
                        [20, 24],
                        feature_id="feature_legacy_control",
                        routing_bucket="historical_appendix",
                        plane="control",
                        evidence_class="HISTORICAL_DOC",
                        temporal_status="historical",
                        reason="historical-only evidence",
                        evidence=[{"path": "docs/architecture.md", "line_range": [20, 24], "excerpt": "Legacy control plane design remains in docs."}],
                    ),
                    _item(
                        "route_uncertain",
                        "docs/notes.md",
                        [1, 1],
                        feature_id="feature_non_feature",
                        routing_bucket="uncertain_appendix",
                        plane="unknown",
                        evidence_class="UNKNOWN",
                        temporal_status="unknown",
                        reason="insufficient evidence",
                        evidence=[{"path": "docs/notes.md", "line_range": [1, 1], "excerpt": "Implementation note"}],
                    ),
                    _item(
                        "route_excluded",
                        "docs/notes.md",
                        [1, 1],
                        feature_id="feature_note_only",
                        routing_bucket="excluded_non_feature",
                        plane="unknown",
                        evidence_class="UNKNOWN",
                        temporal_status="unknown",
                        reason="not a feature",
                        evidence=[{"path": "docs/notes.md", "line_range": [1, 1], "excerpt": "Implementation note"}],
                    ),
                ],
            },
            "missing_evidence": [],
        }
    if step_id == "L4":
        return {
            "status": "OK",
            "master_feature_ledger": {
                "canonical_items": [
                    {"feature_id": "feature_pm_sync", "title": "PM plane sync", "plane": "pm", "domain": "planning"}
                ],
                "historical_appendix": [
                    {"feature_id": "feature_legacy_control", "title": "Legacy control surface", "plane": "control", "domain": "control"}
                ],
                "uncertain_appendix": [
                    {"feature_id": "feature_non_feature", "title": "Implementation note", "plane": "unknown", "domain": "misc"}
                ],
                "excluded_non_features": [
                    {"feature_id": "feature_note_only", "title": "Note only", "plane": "unknown", "domain": "misc"}
                ],
                "contradictions": [{"contradiction_id": "FL-1", "status": "unresolved"}],
                "statistics": {
                    "canonical_count": 1,
                    "historical_count": 1,
                    "uncertain_count": 1,
                    "excluded_count": 1,
                    "by_plane": {
                        "pm": 1,
                        "cognitive": 0,
                        "control": 1,
                        "unknown": 2,
                    },
                },
            },
            "missing_evidence": [],
        }
    raise KeyError(step_id)
