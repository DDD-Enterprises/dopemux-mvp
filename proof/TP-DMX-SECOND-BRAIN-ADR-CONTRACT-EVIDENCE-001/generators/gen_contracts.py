#!/usr/bin/env python3
"""S3 — author the Second Brain ADR machine-contract family.

Consumes the FROZEN clause denominator (ADR_CLAUSE_INVENTORY.json) and emits
every artifact under schemas/second_brain/contracts/. The denominator is read,
never re-derived: this generator cannot widen or narrow it.

Run from the worktree root.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from clause_table import (  # noqa: E402
    ADR_TITLES,
    AUTHORITY_TARGETS,
    CANDIDATE_PATH,
    CANDIDATE_SHA256,
    CLAUSES,
    CONTRACT_DIR,
    CUSTODY,
    FORBIDDEN_AUTHORITY_CLAIMS,
    IMPLEMENTATION_DEFERRED,
    OLC,
    PIE,
    RATIFICATION_BINDING_SHA256,
    SCR,
    SPOOL,
    TP,
    TPR,
)

REPO = Path.cwd()
OUT = REPO / CONTRACT_DIR
PROOF = REPO / "proof" / "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
INVENTORY = PROOF / "ADR_CLAUSE_INVENTORY.json"
PACKET_ID = "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"

RULE_TYPES = [
    "REQUIRE",
    "FORBID",
    "ENUM",
    "CONSTANT",
    "MAXIMUM",
    "AUTHORITY_TARGET",
    "FAIL_CLOSED",
    "STATE_TRANSITION",
    "LIFECYCLE",
    "CAPABILITY_GATE",
    "INTERFACE_REQUIREMENT",
    "HASH_BINDING",
    "ORDERING",
]

OPERATORS = [
    "EQUALS",
    "NOT_EQUALS",
    "IN",
    "NOT_IN",
    "SET_EQUALS",
    "SUPERSET_OF",
    "LESS_THAN_OR_EQUAL",
    "MUST_EXIST",
    "MUST_NOT_EXIST",
    "PRECEDES",
    "DEFAULTS_TO",
]

NON_CANONICAL = {
    "const": "NON_CANONICAL",
    "description": (
        "Second Brain artifacts are never canonical. Canonical writes target "
        "existing authorities only (ADR-SB-001)."
    ),
}


def write(path: Path, obj) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifacts_for(adr_id: str, suffix: str) -> list[str]:
    for row in CLAUSES[adr_id]:
        if row[0] == suffix:
            return list(row[7])
    return []


# --------------------------------------------------------------------------
# Meta-schemas
# --------------------------------------------------------------------------

RULE_NODE_SCHEMA = {
    "type": "object",
    "required": ["subject", "rule_type", "operator", "machine_value"],
    "properties": {
        "subject": {"type": "string", "minLength": 1},
        "rule_type": {"enum": RULE_TYPES},
        "operator": {"enum": OPERATORS},
        "machine_value": {},
        "enforced_by": {
            "type": "string",
            "description": (
                "JSON Pointer, within this same artifact, to the concrete "
                "structure that carries the rule."
            ),
        },
        "note": {"type": "string"},
    },
    "additionalProperties": False,
}


def adr_machine_contract_schema() -> dict:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://dopemux.dev/schemas/second_brain/contracts/adr-machine-contract.schema.json",
        "title": "Second Brain ADR machine contract",
        "description": (
            "Architecture-time machine contract for a single Second Brain ADR "
            "candidate. Satisfies amended acceptance condition #2 "
            "(\"Machine contracts required by this ADR MUST parse and cover "
            "the decision at ADR acceptance\"). Carries no implementation, "
            "runtime, or enablement authority."
        ),
        "type": "object",
        "required": [
            "contract_version",
            "adr_id",
            "adr_title",
            "contract_kind",
            "candidate_document",
            "candidate_sha256",
            "ratification_binding_sha256",
            "adr_status_at_contract_authoring",
            "sb_dec_references",
            "decision_clauses",
            "required_artifacts",
            "forbidden_authority_claims",
            "implementation_deferred",
            "runtime_claims_permitted",
            "denial_fixtures",
        ],
        "additionalProperties": False,
        "properties": {
            "$schema": {"type": "string"},
            "contract_version": {"const": "1.0.0"},
            "adr_id": {"pattern": "^ADR-SB-0(0[1-9]|10)$", "type": "string"},
            "adr_title": {"type": "string", "minLength": 1},
            "contract_kind": {"const": "ARCHITECTURE_DECISION_CONTRACT"},
            "candidate_document": {"const": CANDIDATE_PATH},
            "candidate_sha256": {"const": CANDIDATE_SHA256},
            "ratification_binding_sha256": {"const": RATIFICATION_BINDING_SHA256},
            "adr_status_at_contract_authoring": {"const": "PROPOSED"},
            "sb_dec_references": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string", "pattern": "^SB-DEC-\\d{3}$"},
            },
            "required_artifacts": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "pattern": f"^{CONTRACT_DIR}/"},
            },
            "forbidden_authority_claims": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string"},
            },
            "implementation_deferred": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string"},
            },
            "runtime_claims_permitted": {
                "const": False,
                "description": (
                    "Structural, not conventional: a contract asserting "
                    "runtime authority fails schema validation."
                ),
            },
            "denial_fixtures": {
                "const": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE",
                "description": (
                    "Denial fixtures are an implementation/enablement gate "
                    "outside architecture-time contract evidence. No contract "
                    "may claim they exist."
                ),
            },
            "authority_targets_permitted": {
                "type": "array",
                "uniqueItems": True,
                "items": {"enum": AUTHORITY_TARGETS},
            },
            "decision_clauses": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": [
                        "clause_id",
                        "requirement_text",
                        "subject",
                        "rule_type",
                        "operator",
                        "machine_value",
                        "source_fragments",
                        "source_decision_text_hash",
                        "covered_by",
                    ],
                    "additionalProperties": False,
                    "properties": {
                        "clause_id": {
                            "type": "string",
                            "pattern": "^ADR-SB-\\d{3}-C\\d{2}$",
                        },
                        "requirement_text": {"type": "string", "minLength": 1},
                        "subject": {"type": "string", "pattern": "^second_brain\\."},
                        "rule_type": {"enum": RULE_TYPES},
                        "operator": {"enum": OPERATORS},
                        "machine_value": {},
                        "source_fragments": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"type": "string", "minLength": 1},
                        },
                        "source_decision_text_hash": {
                            "type": "string",
                            "pattern": "^[0-9a-f]{64}$",
                        },
                        "covered_by": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"type": "string", "pattern": "#/"},
                        },
                    },
                },
            },
        },
    }


def interface_contract_schema() -> dict:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://dopemux.dev/schemas/second_brain/contracts/interface-contract.schema.json",
        "title": "Second Brain interface (port) machine contract",
        "description": (
            "Machine-readable interface descriptor for a port named directly "
            "by a Second Brain ADR. Architecture-time only: describes the "
            "obligations of any future adapter without implementing one."
        ),
        "type": "object",
        "required": [
            "contract_version",
            "interface_id",
            "interface_kind",
            "source_adr",
            "candidate_sha256",
            "ratification_binding_sha256",
            "implementation_status",
            "runtime_claims_permitted",
            "denial_fixtures",
            "canonicality",
            "operations",
            "invariants",
        ],
        "additionalProperties": False,
        "properties": {
            "$schema": {"type": "string"},
            "contract_version": {"const": "1.0.0"},
            "interface_id": {"type": "string", "minLength": 1},
            "interface_kind": {"enum": ["PORT"]},
            "source_adr": {"type": "string", "pattern": "^ADR-SB-\\d{3}$"},
            "candidate_sha256": {"const": CANDIDATE_SHA256},
            "ratification_binding_sha256": {"const": RATIFICATION_BINDING_SHA256},
            "implementation_status": {"const": "NOT_IMPLEMENTED"},
            "runtime_claims_permitted": {"const": False},
            "denial_fixtures": {"const": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE"},
            "canonicality": {"const": "NON_CANONICAL"},
            "classification_matrix": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
            "operations": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["name", "inputs", "outputs", "fail_closed_on"],
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "summary": {"type": "string"},
                        "inputs": {"type": "array", "items": {"type": "string"}},
                        "outputs": {"type": "array", "items": {"type": "string"}},
                        "idempotent": {"type": "boolean"},
                        "fail_closed_on": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "invariants": {
                "type": "object",
                "minProperties": 1,
                "propertyNames": {"pattern": "^ADR-SB-\\d{3}-C\\d{2}$"},
                "additionalProperties": RULE_NODE_SCHEMA,
            },
        },
    }


# --------------------------------------------------------------------------
# Per-ADR contracts
# --------------------------------------------------------------------------


def build_adr_contracts(inv: dict) -> dict[str, str]:
    hashes = {}
    for adr in inv["adrs"]:
        adr_id = adr["adr_id"]
        clauses = []
        required: list[str] = []
        for idx, c in enumerate(adr["clauses"]):
            suffix = c["clause_id"].rsplit("-", 1)[1]
            extra = artifacts_for(adr_id, suffix)
            for a in extra:
                if a not in required:
                    required.append(a)
            covered = [f"{CONTRACT_DIR}/{adr_id}.contract.json#/decision_clauses/{idx}"]
            for a in extra:
                anchor = (
                    "x-machine-invariants" if a.endswith(".schema.json") else "invariants"
                )
                covered.append(f"{a}#/{anchor}/{c['clause_id']}")
            clauses.append(
                {
                    "clause_id": c["clause_id"],
                    "requirement_text": c["requirement_text"],
                    "subject": c["subject"],
                    "rule_type": c["rule_type"],
                    "operator": c["operator"],
                    "machine_value": c["machine_value"],
                    "source_fragments": c["source_fragments"],
                    "source_decision_text_hash": c["source_decision_text_hash"],
                    "covered_by": covered,
                }
            )

        contract = {
            "$schema": "./adr-machine-contract.schema.json",
            "contract_version": "1.0.0",
            "adr_id": adr_id,
            "adr_title": ADR_TITLES[adr_id],
            "contract_kind": "ARCHITECTURE_DECISION_CONTRACT",
            "candidate_document": CANDIDATE_PATH,
            "candidate_sha256": CANDIDATE_SHA256,
            "ratification_binding_sha256": RATIFICATION_BINDING_SHA256,
            "adr_status_at_contract_authoring": "PROPOSED",
            "sb_dec_references": adr["sb_dec_references"],
            "required_artifacts": sorted(required),
            "forbidden_authority_claims": FORBIDDEN_AUTHORITY_CLAIMS,
            "implementation_deferred": IMPLEMENTATION_DEFERRED,
            "runtime_claims_permitted": False,
            "denial_fixtures": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE",
            "authority_targets_permitted": AUTHORITY_TARGETS,
            "decision_clauses": clauses,
        }
        hashes[adr_id] = write(OUT / f"{adr_id}.contract.json", contract)
    return hashes


def invariants_for(inv: dict, artifact: str) -> dict:
    """Collect rule nodes for every clause that names `artifact`."""
    out = {}
    for adr in inv["adrs"]:
        for c in adr["clauses"]:
            suffix = c["clause_id"].rsplit("-", 1)[1]
            if artifact in artifacts_for(adr["adr_id"], suffix):
                out[c["clause_id"]] = {
                    "subject": c["subject"],
                    "rule_type": c["rule_type"],
                    "operator": c["operator"],
                    "machine_value": c["machine_value"],
                }
    return out


def attach(inv: dict, artifact: str, enforced: dict[str, str]) -> dict:
    nodes = invariants_for(inv, artifact)
    for clause_id, pointer in enforced.items():
        if clause_id not in nodes:
            raise SystemExit(f"FATAL: {artifact} enforces unknown clause {clause_id}")
        nodes[clause_id]["enforced_by"] = pointer
    return nodes


# --------------------------------------------------------------------------


def main() -> int:
    inv = json.loads(INVENTORY.read_text())
    inv_sha = hashlib.sha256(INVENTORY.read_bytes()).hexdigest()

    write(OUT / "adr-machine-contract.schema.json", adr_machine_contract_schema())
    write(OUT / "interface-contract.schema.json", interface_contract_schema())

    adr_hashes = build_adr_contracts(inv)

    # ---- ADR-SB-006 ports -------------------------------------------------
    spool = {
        "$schema": "./interface-contract.schema.json",
        "contract_version": "1.0.0",
        "interface_id": "LocalSpoolPort",
        "interface_kind": "PORT",
        "source_adr": "ADR-SB-006",
        "candidate_sha256": CANDIDATE_SHA256,
        "ratification_binding_sha256": RATIFICATION_BINDING_SHA256,
        "implementation_status": "NOT_IMPLEMENTED",
        "runtime_claims_permitted": False,
        "denial_fixtures": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE",
        "canonicality": "NON_CANONICAL",
        "classification_matrix": {
            "public": "ALLOWED",
            "internal": "ALLOWED_REQUIRES_OS_PROTECTED_STORAGE",
            "confidential": "DISABLED_UNTIL_VERIFIED_ENCRYPTION_AND_KEY_OWNERSHIP",
            "restricted": "DISABLED_UNTIL_VERIFIED_ENCRYPTION_AND_KEY_OWNERSHIP",
            "unknown": "DENY",
        },
        "operations": [
            {
                "name": "admit",
                "summary": (
                    "Eligibility decision taken before any byte is spooled. "
                    "Unknown identity, domain, or classification denies."
                ),
                "inputs": ["SpoolAdmissionRequest"],
                "outputs": ["AdmissionDecision"],
                "fail_closed_on": [
                    "UNKNOWN_CLASSIFICATION",
                    "UNKNOWN_DOMAIN",
                    "UNKNOWN_IDENTITY",
                    "CONFIDENTIAL_OR_RESTRICTED_WITHOUT_VERIFIED_ENCRYPTION",
                ],
            },
            {
                "name": "append",
                "summary": "Append an admitted, integrity-protected spool record.",
                "inputs": ["SpoolRecord"],
                "outputs": ["SpoolReceipt"],
                "idempotent": False,
                "fail_closed_on": ["ADMISSION_ABSENT", "INTEGRITY_DIGEST_ABSENT"],
            },
            {
                "name": "flush",
                "summary": "Idempotently drain eligible records to their authority target.",
                "inputs": ["FlushScope"],
                "outputs": ["FlushReceipt"],
                "idempotent": True,
                "fail_closed_on": ["AUTHORITY_TARGET_UNREACHABLE", "WRONG_PROJECT"],
            },
            {
                "name": "expire",
                "summary": "Enforce the bounded time-to-live of spool records.",
                "inputs": ["ExpiryBoundary"],
                "outputs": ["ExpiryReceipt"],
                "idempotent": True,
                "fail_closed_on": ["TTL_UNBOUNDED"],
            },
            {
                "name": "participate_in_purge",
                "summary": "Report and remove spool residue for a purge subject.",
                "inputs": ["PurgeRequest"],
                "outputs": ["PurgeSurfaceReceipt"],
                "idempotent": True,
                "fail_closed_on": ["RESIDUAL_SCAN_UNAVAILABLE"],
            },
        ],
        "invariants": attach(
            inv,
            SPOOL,
            {
                "ADR-SB-006-C01": "#/operations",
                "ADR-SB-006-C08": "#/operations/2/idempotent",
                "ADR-SB-006-C09": "#/operations/4",
                "ADR-SB-006-C11": "#/classification_matrix/public",
                "ADR-SB-006-C12": "#/classification_matrix/internal",
                "ADR-SB-006-C13": "#/classification_matrix/confidential",
                "ADR-SB-006-C14": "#/classification_matrix/unknown",
                "ADR-SB-006-C03": "#/canonicality",
            },
        ),
    }
    write(OUT / "local-spool-port.contract.json", spool)

    custody = {
        "$schema": "./interface-contract.schema.json",
        "contract_version": "1.0.0",
        "interface_id": "CustodyPort",
        "interface_kind": "PORT",
        "source_adr": "ADR-SB-006",
        "candidate_sha256": CANDIDATE_SHA256,
        "ratification_binding_sha256": RATIFICATION_BINDING_SHA256,
        "implementation_status": "NOT_IMPLEMENTED",
        "runtime_claims_permitted": False,
        "denial_fixtures": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE",
        "canonicality": "NON_CANONICAL",
        "classification_matrix": {
            "public": "REMOTE_BACKUP_FORBIDDEN_FOR_SPOOL_DERIVED_CONTENT",
            "internal": "REMOTE_BACKUP_FORBIDDEN_FOR_SPOOL_DERIVED_CONTENT",
            "confidential": "DISABLED_UNTIL_VERIFIED_ENCRYPTION_AND_KEY_OWNERSHIP",
            "restricted": "DISABLED_UNTIL_VERIFIED_ENCRYPTION_AND_KEY_OWNERSHIP",
            "unknown": "DENY",
        },
        "operations": [
            {
                "name": "put",
                "summary": "Store content-addressed bytes; the address is the integrity claim.",
                "inputs": ["CustodyBlob"],
                "outputs": ["ContentAddress"],
                "idempotent": True,
                "fail_closed_on": ["UNKNOWN_CLASSIFICATION", "REMOTE_BACKUP_REQUESTED"],
            },
            {
                "name": "verify_integrity",
                "summary": "Recompute and compare the content address.",
                "inputs": ["ContentAddress"],
                "outputs": ["IntegrityVerdict"],
                "idempotent": True,
                "fail_closed_on": ["DIGEST_MISMATCH", "CONTENT_ABSENT"],
            },
            {
                "name": "residual_scan",
                "summary": "Count searchable residue for a purge subject across custody.",
                "inputs": ["PurgeSubjectRef"],
                "outputs": ["ResidualCount"],
                "idempotent": True,
                "fail_closed_on": ["SCAN_INCOMPLETE"],
            },
            {
                "name": "backup_eligibility",
                "summary": "Decide whether content may leave local custody at all.",
                "inputs": ["Classification"],
                "outputs": ["EligibilityVerdict"],
                "idempotent": True,
                "fail_closed_on": ["UNKNOWN_CLASSIFICATION"],
            },
            {
                "name": "tombstone",
                "summary": "Record explicit tombstone plus retrieval denial where physical deletion is impossible.",
                "inputs": ["ContentAddress"],
                "outputs": ["TombstoneReceipt"],
                "idempotent": True,
                "fail_closed_on": ["RETRIEVAL_DENIAL_UNENFORCEABLE"],
            },
        ],
        "invariants": attach(
            inv,
            CUSTODY,
            {
                "ADR-SB-006-C02": "#/operations",
                "ADR-SB-006-C10": "#/operations/3",
                "ADR-SB-006-C13": "#/classification_matrix/restricted",
            },
        ),
    }
    write(OUT / "custody-port.contract.json", custody)

    # ---- ADR-SB-008 data contracts ---------------------------------------
    olc = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://dopemux.dev/schemas/second_brain/contracts/open-loop-candidate.schema.json",
        "title": "OpenLoopCandidate",
        "description": (
            "A detected, non-canonical attention marker. Per the ADR-SB-008 "
            "MA-06 PM-semantics firewall an open loop carries zero PM-semantic "
            "fields; `additionalProperties: false` is what makes that "
            "machine-enforceable rather than aspirational."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "candidate_id",
            "project_id",
            "detected_at",
            "source_event_ref",
            "loop_state",
            "canonicality",
        ],
        "properties": {
            "candidate_id": {"type": "string", "minLength": 1},
            "project_id": {"type": "string", "minLength": 1},
            "detected_at": {"type": "string", "format": "date-time"},
            "source_event_ref": {
                "type": "string",
                "description": "Pointer to the Dope-Memory event this was derived from.",
            },
            "summary": {"type": "string"},
            "loop_state": {
                "enum": ["open", "closed", "cancelled"],
                "description": (
                    "Chronological loop lifecycle only. Deliberately NOT named "
                    "`status`: workflow status is a PM semantic reserved to "
                    "Leantime and Task Orchestrator."
                ),
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "due_at": {
                "type": ["string", "null"],
                "format": "date-time",
                "x-semantics": "ADVISORY_DISPLAY_METADATA_ONLY",
                "x-forbidden-behaviors": [
                    "SCHEDULING",
                    "ESCALATION",
                    "PRIORITY_DERIVATION",
                    "NOTIFICATION_TRIGGER",
                ],
            },
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
            "canonicality": NON_CANONICAL,
        },
        "x-forbidden-properties": [
            "assignee",
            "owner",
            "ownership",
            "priority",
            "pm_priority",
            "status",
            "workflow_status",
            "sprint",
            "sprint_state",
            "task_completion_state",
            "completed",
            "done",
            "escalation",
            "escalation_policy",
            "scheduled_at",
            "schedule",
            "estimate",
            "story_points",
        ],
        "x-machine-invariants": attach(
            inv,
            OLC,
            {
                "ADR-SB-008-C01": "#/properties",
                "ADR-SB-008-C08": "#/additionalProperties",
                "ADR-SB-008-C09": "#/additionalProperties",
                "ADR-SB-008-C10": "#/additionalProperties",
                "ADR-SB-008-C11": "#/additionalProperties",
                "ADR-SB-008-C12": "#/additionalProperties",
                "ADR-SB-008-C13": "#/properties/due_at/x-forbidden-behaviors",
                "ADR-SB-008-C14": "#/properties/due_at/x-forbidden-behaviors",
                "ADR-SB-008-C15": "#/additionalProperties",
                "ADR-SB-008-C16": "#/properties/due_at/x-semantics",
            },
        ),
    }
    write(OUT / "open-loop-candidate.schema.json", olc)

    tp = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://dopemux.dev/schemas/second_brain/contracts/task-proposal.schema.json",
        "title": "TaskProposal",
        "description": (
            "A task-shaped suggestion held strictly separate from OpenLoopCandidate "
            "(ADR-SB-008). A proposal is not a task and confers no PM authority; "
            "it can only become one through TaskPromotionRequest, which is disabled."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "proposal_id",
            "project_id",
            "proposed_at",
            "title",
            "proposal_state",
            "canonicality",
        ],
        "properties": {
            "proposal_id": {"type": "string", "minLength": 1},
            "project_id": {"type": "string", "minLength": 1},
            "proposed_at": {"type": "string", "format": "date-time"},
            "derived_from_open_loop": {"type": ["string", "null"]},
            "title": {"type": "string", "minLength": 1},
            "rationale": {"type": "string"},
            "proposal_state": {"enum": ["proposed", "withdrawn", "superseded"]},
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
            "canonicality": NON_CANONICAL,
        },
        "x-forbidden-properties": [
            "assignee",
            "owner",
            "priority",
            "pm_priority",
            "status",
            "workflow_status",
            "sprint",
            "sprint_state",
            "task_completion_state",
            "completed",
            "done",
            "scheduled_at",
        ],
        "x-machine-invariants": attach(inv, TP, {"ADR-SB-008-C02": "#/properties"}),
    }
    write(OUT / "task-proposal.schema.json", tp)

    tpr = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://dopemux.dev/schemas/second_brain/contracts/task-promotion-request.schema.json",
        "title": "TaskPromotionRequest",
        "description": (
            "The only path by which a TaskProposal could ever become a real task "
            "(ADR-SB-008, Slice 6). `enabled` is const-pinned false: the disabled "
            "state is structural, not a default that a caller can override."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "request_id",
            "task_proposal_ref",
            "enabled",
            "requested_at",
            "target_authority",
            "leantime_proof_ref",
            "task_orchestrator_proof_ref",
            "operator_approval",
            "disposition",
        ],
        "properties": {
            "request_id": {"type": "string", "minLength": 1},
            "task_proposal_ref": {"type": "string", "minLength": 1},
            "enabled": {
                "const": False,
                "default": False,
                "description": (
                    "Task promotion is disabled initially (ADR-SB-008). Const, "
                    "so no instance can enable it and no default can drift."
                ),
            },
            "requested_at": {"type": "string", "format": "date-time"},
            "target_authority": {
                "enum": ["Leantime", "Task Orchestrator"],
                "description": "PM and workflow authority is never the Second Brain.",
            },
            "leantime_proof_ref": {"type": "string", "minLength": 1},
            "task_orchestrator_proof_ref": {"type": "string", "minLength": 1},
            "operator_approval": {
                "type": "object",
                "additionalProperties": False,
                "required": ["explicit", "approved_digest_sha256"],
                "properties": {
                    "explicit": {"const": True},
                    "approved_digest_sha256": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                },
            },
            "disposition": {
                "enum": ["DENIED_PROMOTION_DISABLED"],
                "default": "DENIED_PROMOTION_DISABLED",
                "description": (
                    "Only terminal disposition available at this architecture "
                    "revision. Enabling promotion is a separately authorized "
                    "implementation-time gate."
                ),
            },
        },
        "x-machine-invariants": attach(
            inv,
            TPR,
            {
                "ADR-SB-008-C03": "#/properties",
                "ADR-SB-008-C06": "#/required",
                "ADR-SB-008-C07": "#/properties/enabled/const",
            },
        ),
    }
    write(OUT / "task-promotion-request.schema.json", tpr)

    # ---- ADR-SB-009 identity contracts -----------------------------------
    pie = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://dopemux.dev/schemas/second_brain/contracts/project-identity-envelope.schema.json",
        "title": "ProjectIdentityEnvelope",
        "description": (
            "Registry-backed project identity for authority operations "
            "(ADR-SB-009). Ports, path hashes, current directory, and singleton "
            "event streams are enumerated as rejected identity sources so that "
            "the prohibition is machine-readable rather than implied."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "envelope_id",
            "project_id",
            "registry_ref",
            "registry_backed",
            "writer_epoch",
            "issued_at",
            "active_automatic_capture_project_count",
            "project_switch_mode",
            "wrong_project_write_disposition",
            "multi_project_background_capture_enabled",
            "rejected_identity_sources",
            "canonicality",
        ],
        "properties": {
            "envelope_id": {"type": "string", "minLength": 1},
            "project_id": {"type": "string", "minLength": 1},
            "registry_ref": {"type": "string", "minLength": 1},
            "registry_backed": {"const": True},
            "writer_epoch": {
                "type": "integer",
                "minimum": 0,
                "description": "Monotonic writer epoch; a stale epoch denies the write.",
            },
            "issued_at": {"type": "string", "format": "date-time"},
            "expires_at": {"type": ["string", "null"], "format": "date-time"},
            "active_automatic_capture_project_count": {
                "type": "integer",
                "minimum": 0,
                "maximum": 1,
                "description": "At most one active automatic-capture project.",
            },
            "project_switch_mode": {"const": "EXPLICIT"},
            "wrong_project_write_disposition": {"const": "DENY"},
            "multi_project_background_capture_enabled": {
                "const": False,
                "default": False,
                "description": "Disabled until isolation proof exists (NOT_RUN).",
            },
            "rejected_identity_sources": {
                "type": "array",
                "const": [
                    "PORT",
                    "PATH_HASH",
                    "CURRENT_DIRECTORY",
                    "SINGLETON_EVENT_STREAM",
                ],
            },
            "canonicality": NON_CANONICAL,
        },
        "x-machine-invariants": attach(
            inv,
            PIE,
            {
                "ADR-SB-009-C01": "#/properties/registry_backed/const",
                "ADR-SB-009-C03": "#/properties/active_automatic_capture_project_count/maximum",
                "ADR-SB-009-C04": "#/properties/project_switch_mode/const",
                "ADR-SB-009-C05": "#/properties/writer_epoch",
                "ADR-SB-009-C06": "#/properties/wrong_project_write_disposition/const",
                "ADR-SB-009-C07": "#/properties/rejected_identity_sources/const",
                "ADR-SB-009-C08": "#/properties/multi_project_background_capture_enabled/const",
            },
        ),
    }
    write(OUT / "project-identity-envelope.schema.json", pie)

    scr = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://dopemux.dev/schemas/second_brain/contracts/service-capability-receipt.schema.json",
        "title": "ServiceCapabilityReceipt",
        "description": (
            "Current capability receipt required before any authority operation "
            "(ADR-SB-009). Staleness and unknown capability both deny; a receipt "
            "is evidence of capability, never a grant of authority."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "receipt_id",
            "service",
            "project_id",
            "resolved_identity",
            "capabilities",
            "issued_at",
            "freshness_state",
            "wrong_project_disposition",
            "unknown_capability_disposition",
            "canonicality",
        ],
        "properties": {
            "receipt_id": {"type": "string", "minLength": 1},
            "service": {"type": "string", "minLength": 1},
            "project_id": {"type": "string", "minLength": 1},
            "resolved_identity": {"type": "string", "minLength": 1},
            "capabilities": {"type": "array", "items": {"type": "string"}},
            "issued_at": {"type": "string", "format": "date-time"},
            "expires_at": {"type": ["string", "null"], "format": "date-time"},
            "freshness_state": {
                "enum": ["CURRENT", "STALE"],
                "description": "Only CURRENT may gate an authority operation.",
            },
            "wrong_project_disposition": {"const": "DENY"},
            "unknown_capability_disposition": {"const": "DENY"},
            "canonicality": NON_CANONICAL,
        },
        "x-machine-invariants": attach(
            inv,
            SCR,
            {
                "ADR-SB-009-C02": "#/properties/freshness_state",
                "ADR-SB-009-C06": "#/properties/wrong_project_disposition/const",
            },
        ),
    }
    write(OUT / "service-capability-receipt.schema.json", scr)

    # ---- Coverage matrix --------------------------------------------------
    entries = []
    for adr in inv["adrs"]:
        adr_id = adr["adr_id"]
        for idx, c in enumerate(adr["clauses"]):
            suffix = c["clause_id"].rsplit("-", 1)[1]
            extra = artifacts_for(adr_id, suffix)
            additional = []
            for a in extra:
                anchor = (
                    "x-machine-invariants" if a.endswith(".schema.json") else "invariants"
                )
                additional.append(
                    {
                        "contract_artifact": a,
                        "contract_rule_pointer": f"#/{anchor}/{c['clause_id']}",
                    }
                )
            entries.append(
                {
                    "adr_id": adr_id,
                    "clause_id": c["clause_id"],
                    "requirement_text": c["requirement_text"],
                    "source_text_hash": c["source_decision_text_hash"],
                    "contract_artifact": f"{CONTRACT_DIR}/{adr_id}.contract.json",
                    "contract_rule_pointer": f"#/decision_clauses/{idx}",
                    "coverage_status": "COVERED",
                    "additional_coverage": additional,
                }
            )

    coverage = {
        "schema_version": "1.0.0",
        "task_id": PACKET_ID,
        "purpose": (
            "Maps every frozen §5 clause to the machine rule that expresses it. "
            "The denominator is ADR_CLAUSE_INVENTORY.json, frozen in an earlier "
            "commit and hash-bound below; this matrix cannot widen or narrow it."
        ),
        "candidate_document": CANDIDATE_PATH,
        "candidate_sha256": CANDIDATE_SHA256,
        "ratification_binding_sha256": RATIFICATION_BINDING_SHA256,
        "clause_inventory": (
            "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/"
            "ADR_CLAUSE_INVENTORY.json"
        ),
        "clause_inventory_sha256": inv_sha,
        "adr_count": len(inv["adrs"]),
        "clause_total": len(entries),
        "coverage_status_counts": {
            "COVERED": sum(1 for e in entries if e["coverage_status"] == "COVERED"),
            "NOT_APPLICABLE_PROVEN": 0,
            "MISSING": 0,
            "AMBIGUOUS": 0,
        },
        "adr_contract_sha256": adr_hashes,
        "entries": entries,
    }
    write(OUT / "ADR_CONTRACT_COVERAGE.json", coverage)

    n = len(list(OUT.glob("*.json")))
    print(f"S3: wrote {n} artifacts into {CONTRACT_DIR}/")
    print(f"    clause_inventory_sha256 = {inv_sha}")
    print(f"    clause_total            = {len(entries)}")
    print(f"    coverage counts         = {coverage['coverage_status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
