#!/usr/bin/env python3
"""Regenerate the Second Brain machine contracts from the re-frozen denominator.

Reads ADR_CLAUSE_INVENTORY.json.  Never re-derives it: the denominator was
frozen in an earlier commit and this generator is downstream of it.

Layer B carries only surface the candidate actually states.  Every property
name, enum member and const string is bound in ``x-grounding`` to a clause and
to a verbatim candidate phrase, and the validator recomputes that binding.  That
is the class-level answer to the audit's invented-surface finding: it is not a
list of removals, it is a rule that makes a new invention fail.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    env = os.environ.get("SB_REPO_ROOT")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists() or (parent / ".dopetaskroot").exists():
            return parent
    raise SystemExit("FAIL: cannot locate repository root; set SB_REPO_ROOT")


ROOT = _repo_root()
PROOF_REL = "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
CONTRACT_REL = "schemas/second_brain/contracts"
PROOF = ROOT / PROOF_REL
OUT = ROOT / CONTRACT_REL

TASK_ID = "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
CANDIDATE_REL = (
    "docs/03-reference/architecture/second-brain/adr-candidates/"
    "second-brain-adr-candidates.md"
)

IMPLEMENTATION_DEFERRED = [
    "DENIAL_FIXTURES", "RUNTIME_CONFORMANCE", "RETRIEVAL_BENCHMARKS",
    "PURGE_COMPLETENESS", "MULTI_PROJECT_ISOLATION", "SPLIT_BRAIN_PROOF",
    "ENCRYPTION_IMPLEMENTATION",
]

RULE_TYPES = [
    "BOOLEAN", "NUMERIC", "ENUM", "CONSTANT", "AUTHORITY_TARGET",
    "INTERFACE_REQUIREMENT",
]
OPERATORS = ["EQUALS", "SET_EQUALS", "LESS_THAN_OR_EQUAL", "MUST_EXIST"]

inv = json.loads((PROOF / "ADR_CLAUSE_INVENTORY.json").read_text())
INV_SHA = hashlib.sha256((PROOF / "ADR_CLAUSE_INVENTORY.json").read_bytes()).hexdigest()
CANDIDATE_SHA = inv["candidate_sha256"]
RATIFICATION_SHA = inv["ratification_binding_sha256"]

CLAUSE = {c["clause_id"]: c for a in inv["adrs"] for c in a["clauses"]}


def frag_text(clause_id: str) -> str:
    return "\n".join(CLAUSE[clause_id]["source_fragments"])


def rule_of(clause_id: str) -> dict:
    c = CLAUSE[clause_id]
    out = {
        "subject": c["subject"],
        "rule_type": c["rule_type"],
        "operator": c["operator"],
        "machine_value": c["machine_value"],
    }
    if "source_enumeration" in c:
        out["source_enumeration"] = c["source_enumeration"]
    return out


def invariants(*clause_ids: str) -> dict:
    return {cid: rule_of(cid) for cid in clause_ids}


def g(pointer: str, clause_id: str, term: str) -> tuple[str, dict]:
    """One grounding binding: pointer -> (clause, verbatim candidate phrase)."""
    if term not in frag_text(clause_id):
        raise SystemExit(
            f"FAIL: grounding term {term!r} is not a verbatim substring of "
            f"{clause_id}'s cited fragments"
        )
    return pointer, {"clause_id": clause_id, "term": term}


def grounding(*bindings) -> dict:
    return dict(bindings)


def write(name: str, doc: dict) -> str:
    body = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    (OUT / name).write_text(body, encoding="utf-8")
    return hashlib.sha256(body.encode()).hexdigest()


# ==========================================================================
# Meta-schemas
# ==========================================================================

ADR_META = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://dopemux.dev/schemas/second_brain/contracts/adr-machine-contract.schema.json",
    "title": "Second Brain ADR machine contract",
    "description": (
        "Machine-readable form of one candidate ADR's decision. Architecture-time "
        "evidence only: it encodes what must be true of any future "
        "implementation, and asserts nothing about one existing."
    ),
    "type": "object",
    "required": [
        "contract_version", "adr_id", "adr_title", "contract_kind",
        "candidate_document", "candidate_sha256", "ratification_binding_sha256",
        "clause_inventory_sha256", "adr_status_at_contract_authoring",
        "sb_dec_references", "decision_clauses", "required_artifacts",
        "implementation_deferred", "runtime_claims_permitted", "denial_fixtures",
    ],
    "additionalProperties": False,
    "properties": {
        "$schema": {"type": "string"},
        "contract_version": {"const": "2.0.0"},
        "adr_id": {"type": "string", "pattern": "^ADR-SB-0(0[1-9]|10)$"},
        "adr_title": {"type": "string", "minLength": 1},
        "contract_kind": {"const": "ARCHITECTURE_DECISION_CONTRACT"},
        "candidate_document": {"const": CANDIDATE_REL},
        "candidate_sha256": {"const": CANDIDATE_SHA},
        "ratification_binding_sha256": {"const": RATIFICATION_SHA},
        "clause_inventory_sha256": {
            "const": INV_SHA,
            "description": (
                "The re-frozen denominator this contract was generated from. "
                "Pinned here and independently pinned in the validator, so a "
                "post-freeze edit to the inventory cannot be absorbed by "
                "editing the contracts to agree with it."
            ),
        },
        "adr_status_at_contract_authoring": {"const": "PROPOSED"},
        "sb_dec_references": {
            "type": "array", "minItems": 1, "uniqueItems": True,
            "items": {"type": "string", "pattern": r"^SB-DEC-\d{3}$"},
        },
        "required_artifacts": {
            "type": "array", "uniqueItems": True,
            "items": {"type": "string", "pattern": "^schemas/second_brain/contracts/"},
        },
        "implementation_deferred": {
            "type": "array", "minItems": 1, "uniqueItems": True,
            "items": {"type": "string"},
        },
        "runtime_claims_permitted": {
            "const": False,
            "description": (
                "Structural, not conventional: a contract asserting runtime "
                "authority fails schema validation."
            ),
        },
        "denial_fixtures": {
            "const": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE",
            "description": (
                "Denial fixtures are an implementation/enablement gate outside "
                "architecture-time contract evidence. No contract may claim "
                "they exist."
            ),
        },
        "decision_clauses": {
            "type": "array", "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "clause_id", "requirement_text", "subject", "rule_type",
                    "operator", "machine_value", "section", "source_fragments",
                    "source_decision_text_hash", "covered_by",
                ],
                "additionalProperties": False,
                "properties": {
                    "clause_id": {
                        "type": "string",
                        "pattern": r"^ADR-SB-0(0[1-9]|10)-C\d{2}$",
                    },
                    "requirement_text": {"type": "string", "minLength": 1},
                    "subject": {"type": "string", "minLength": 1},
                    "rule_type": {"enum": RULE_TYPES},
                    "operator": {"enum": OPERATORS},
                    "machine_value": {},
                    "section": {
                        "enum": [
                            "CONTEXT", "PROPOSED_DECISION", "MA06_AMENDMENT",
                            "CONSEQUENCES",
                        ],
                        "description": (
                            "Which subsection of the ADR grounds this clause. "
                            "'Rejected alternatives' is absent by construction: "
                            "a rejected design may never ground a rule."
                        ),
                    },
                    "source_fragments": {
                        "type": "array", "minItems": 1,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "source_enumeration": {
                        "type": "string", "minLength": 1,
                        "description": (
                            "Required for SET_EQUALS. The verbatim candidate "
                            "phrase the closed set is tokenized from; the "
                            "asserted set must equal that tokenization exactly, "
                            "so the set can neither widen nor shrink."
                        ),
                    },
                    "source_decision_text_hash": {
                        "type": "string", "pattern": "^[0-9a-f]{64}$",
                    },
                    "covered_by": {
                        "type": "array", "minItems": 1,
                        "items": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
    },
}

IFACE_META = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://dopemux.dev/schemas/second_brain/contracts/interface-contract.schema.json",
    "title": "Second Brain interface (port) machine contract",
    "description": (
        "Machine-readable descriptor for a port the candidate names. It carries "
        "the obligations the candidate states and nothing else. There is "
        "deliberately no `operations` catalogue: the candidate defines these "
        "ports by name and by the properties of what they hold, so an operation "
        "list would be this repository's invention rather than the "
        "architecture's decision."
    ),
    "type": "object",
    "required": [
        "contract_version", "interface_id", "interface_kind", "source_adr",
        "candidate_sha256", "ratification_binding_sha256",
        "clause_inventory_sha256", "implementation_status",
        "runtime_claims_permitted", "denial_fixtures", "assertions",
        "x-grounding", "x-machine-invariants",
    ],
    "additionalProperties": False,
    "properties": {
        "$schema": {"type": "string"},
        "contract_version": {"const": "2.0.0"},
        "interface_id": {"type": "string", "minLength": 1},
        "interface_kind": {"enum": ["PORT"]},
        "source_adr": {"type": "string", "pattern": r"^ADR-SB-\d{3}$"},
        "candidate_sha256": {"const": CANDIDATE_SHA},
        "ratification_binding_sha256": {"const": RATIFICATION_SHA},
        "clause_inventory_sha256": {"const": INV_SHA},
        "implementation_status": {"const": "NOT_IMPLEMENTED"},
        "runtime_claims_permitted": {"const": False},
        "denial_fixtures": {"const": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE"},
        "assertions": {
            "type": "object", "minProperties": 1,
            "description": (
                "Every key and every string value here must be bound in "
                "x-grounding to a clause and a verbatim candidate phrase."
            ),
        },
        "x-unspecified-in-candidate": {"type": "string"},
        "x-grounding": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["clause_id", "term"],
                "additionalProperties": False,
                "properties": {
                    "clause_id": {"type": "string"},
                    "term": {"type": "string", "minLength": 1},
                },
            },
        },
        "x-machine-invariants": {
            "type": "object", "minProperties": 1,
            "propertyNames": {"pattern": r"^ADR-SB-\d{3}-C\d{2}$"},
        },
    },
}


# ==========================================================================
# Layer B — typed artifacts, grounded surface only
# ==========================================================================

PM_FIELDS = [
    ("assignee", "assignee", "ADR-SB-008-C08"),
    ("pm_priority", "PM priority", "ADR-SB-008-C09"),
    ("workflow_status", "workflow status", "ADR-SB-008-C10"),
    ("sprint_state", "sprint state", "ADR-SB-008-C11"),
    ("ownership_assignment", "ownership assignment", "ADR-SB-008-C12"),
    ("due_driven_escalation", "due-driven escalation", "ADR-SB-008-C13"),
    ("automatic_scheduling", "automatic scheduling", "ADR-SB-008-C14"),
    ("task_completion_state", "task completion state", "ADR-SB-008-C15"),
]

open_loop = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://dopemux.dev/schemas/second_brain/contracts/open-loop-candidate.schema.json",
    "title": "OpenLoopCandidate",
    "description": (
        "A detected, non-canonical attention marker (ADR-SB-008). The MA-06 "
        "PM-semantics firewall is the whole machine content of this schema: an "
        "open loop may never carry any of eight named PM semantics, and its "
        "`due_at` is advisory display metadata. Identifier, timestamp and "
        "lifecycle fields are absent on purpose — the candidate states none, "
        "and inventing them would put this repository's design into the "
        "architecture's contract."
    ),
    "type": "object",
    "properties": {
        "due_at": {
            "x-semantics": "ADVISORY_DISPLAY_METADATA_ONLY",
            "x-forbidden-triggers": ["SCHEDULING", "ESCALATION"],
            "description": (
                "Advisory display metadata only. It may not drive scheduling or "
                "escalation, so it is not typed as a scheduling input."
            ),
        },
    },
    "not": {
        "anyOf": [{"required": [name]} for name, _, _ in PM_FIELDS],
        "description": (
            "The eight PM semantics MA-06 forbids, expressed so an instance "
            "carrying any of them fails validation. Stated as a denial rather "
            "than `additionalProperties: false`, because the candidate forbids "
            "PM semantics — it does not close the object."
        ),
    },
    "x-unspecified-in-candidate": (
        "The candidate names OpenLoopCandidate and constrains it, but specifies "
        "no identifier, timestamp, provenance or state field. None is asserted "
        "here. Those are implementation-time surface."
    ),
    "x-grounding": grounding(
        g("/properties/due_at", "ADR-SB-008-C16", "due_at"),
        g("/properties/due_at/x-semantics", "ADR-SB-008-C16",
          "advisory display metadata only"),
        g("/properties/due_at/x-forbidden-triggers/0", "ADR-SB-008-C36",
          "scheduling"),
        g("/properties/due_at/x-forbidden-triggers/1", "ADR-SB-008-C36",
          "escalation"),
        *[
            g(f"/not/anyOf/{i}/required/0", cid, term)
            for i, (_, term, cid) in enumerate(PM_FIELDS)
        ],
    ),
    "x-machine-invariants": invariants(
        "ADR-SB-008-C01", "ADR-SB-008-C08", "ADR-SB-008-C09", "ADR-SB-008-C10",
        "ADR-SB-008-C11", "ADR-SB-008-C12", "ADR-SB-008-C13", "ADR-SB-008-C14",
        "ADR-SB-008-C15", "ADR-SB-008-C16", "ADR-SB-008-C19", "ADR-SB-008-C21",
        "ADR-SB-008-C35", "ADR-SB-008-C36",
    ),
}

task_proposal = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://dopemux.dev/schemas/second_brain/contracts/task-proposal.schema.json",
    "title": "TaskProposal",
    "description": (
        "A task-shaped suggestion held strictly separate from OpenLoopCandidate "
        "(ADR-SB-008). Separateness is the decision; everything else about a "
        "proposal's shape is implementation-time."
    ),
    "type": "object",
    "required": ["separate_candidate"],
    "properties": {
        "separate_candidate": {
            "const": True,
            "description": (
                "Task proposals are separate candidates. A TaskProposal is "
                "never an OpenLoopCandidate with extra fields."
            ),
        },
    },
    "x-unspecified-in-candidate": (
        "The candidate states that task proposals are separate candidates and "
        "that task-shaped behaviour must be represented as a TaskProposal. It "
        "specifies no proposal field, state or lifecycle, so none is asserted."
    ),
    "x-grounding": grounding(
        g("/required/0", "ADR-SB-008-C23", "separate candidate"),
        g("/properties/separate_candidate", "ADR-SB-008-C23", "separate candidate"),
    ),
    "x-machine-invariants": invariants(
        "ADR-SB-008-C02", "ADR-SB-008-C23", "ADR-SB-008-C27",
    ),
}

task_promotion = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://dopemux.dev/schemas/second_brain/contracts/task-promotion-request.schema.json",
    "title": "TaskPromotionRequest",
    "description": (
        "The only path by which a TaskProposal could become a real task "
        "(ADR-SB-008, Slice 6). `disabled` is const-pinned true: the disabled "
        "state is structural, not a default a caller can override. Both proofs "
        "and explicit approval are required even so, because the preconditions "
        "are part of the decision and not merely of a future enablement."
    ),
    "type": "object",
    "required": [
        "disabled",
        "leantime_plus_task_orchestrator_proof",
        "explicit_approval",
    ],
    "properties": {
        "disabled": {"const": True},
        "leantime_plus_task_orchestrator_proof": {"const": True},
        "explicit_approval": {"const": True},
    },
    "x-unspecified-in-candidate": (
        "No request identifier, timestamp, digest or disposition vocabulary is "
        "asserted: the candidate names none. Property names are the candidate's "
        "own phrases rather than conventional API names, so that each one is "
        "traceable to the sentence that authorises it."
    ),
    "x-grounding": grounding(
        g("/required/0", "ADR-SB-008-C07", "disabled"),
        g("/required/1", "ADR-SB-008-C06", "Leantime plus Task Orchestrator proof"),
        g("/required/2", "ADR-SB-008-C18", "explicit approval"),
        g("/properties/disabled", "ADR-SB-008-C07", "disabled"),
        g("/properties/leantime_plus_task_orchestrator_proof", "ADR-SB-008-C06",
          "Leantime plus Task Orchestrator proof"),
        g("/properties/explicit_approval", "ADR-SB-008-C18", "explicit approval"),
    ),
    "x-machine-invariants": invariants(
        "ADR-SB-008-C03", "ADR-SB-008-C06", "ADR-SB-008-C07", "ADR-SB-008-C17",
        "ADR-SB-008-C18", "ADR-SB-008-C28", "ADR-SB-008-C29",
    ),
}

identity_envelope = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://dopemux.dev/schemas/second_brain/contracts/project-identity-envelope.schema.json",
    "title": "ProjectIdentityEnvelope",
    "description": (
        "Registry-backed project identity for authority operations (ADR-SB-009). "
        "Note on naming: the candidate does not use the name "
        "'ProjectIdentityEnvelope'. It requires 'registry-backed identity "
        "envelopes', and this file is this repository's name for that. The "
        "corresponding clauses are therefore stated as the obligation the "
        "candidate expresses, not as a named-type requirement."
    ),
    "type": "object",
    "required": [
        "registry_backed", "writer_epochs", "explicit_project_switching",
        "wrong_project_denial",
    ],
    "properties": {
        "registry_backed": {"const": True},
        "writer_epochs": {"const": True},
        "explicit_project_switching": {"const": True},
        "wrong_project_denial": {"const": True},
        "active_automatic_capture_project": {
            "type": "integer", "minimum": 0, "maximum": 1,
        },
        "multi_project_background_capture": {
            "const": False,
            "description": "Disabled until isolation proof, which is NOT_RUN.",
        },
        "isolation_proof": {
            "const": False,
            "description": (
                "No isolation proof exists at architecture time. Enabling "
                "multi-project background capture requires one."
            ),
        },
    },
    "not": {
        "anyOf": [
            {"required": ["path_hashes"]},
            {"required": ["ports"]},
            {"required": ["singleton_event_streams"]},
        ],
        "description": (
            "Identity may not be established from any of these. Exactly the "
            "three the candidate names — 'current directory' appears only as a "
            "rejected alternative and is therefore not a member of this machine "
            "set; the prohibition on implicit selection is carried instead by "
            "the explicit-project-switching requirement."
        ),
    },
    "x-unspecified-in-candidate": (
        "No envelope identifier, project identifier, registry reference or "
        "issuance timestamp is asserted. The candidate names none of them."
    ),
    "x-grounding": grounding(
        g("/required/0", "ADR-SB-009-C01", "registry-backed"),
        g("/required/1", "ADR-SB-009-C05", "writer epochs"),
        g("/required/2", "ADR-SB-009-C04", "explicit project switching"),
        g("/required/3", "ADR-SB-009-C06", "wrong-project denial"),
        g("/properties/registry_backed", "ADR-SB-009-C01", "registry-backed"),
        g("/properties/writer_epochs", "ADR-SB-009-C05", "writer epochs"),
        g("/properties/explicit_project_switching", "ADR-SB-009-C04",
          "explicit project switching"),
        g("/properties/wrong_project_denial", "ADR-SB-009-C06",
          "wrong-project denial"),
        g("/properties/active_automatic_capture_project", "ADR-SB-009-C03",
          "active automatic-capture project"),
        g("/properties/multi_project_background_capture", "ADR-SB-009-C08",
          "Multi-project background capture"),
        g("/properties/isolation_proof", "ADR-SB-009-C09", "isolation proof"),
        g("/not/anyOf/0/required/0", "ADR-SB-009-C07", "Path hashes"),
        g("/not/anyOf/1/required/0", "ADR-SB-009-C07", "ports"),
        g("/not/anyOf/2/required/0", "ADR-SB-009-C07", "singleton event streams"),
    ),
    "x-machine-invariants": invariants(
        "ADR-SB-009-C01", "ADR-SB-009-C03", "ADR-SB-009-C04", "ADR-SB-009-C05",
        "ADR-SB-009-C06", "ADR-SB-009-C07", "ADR-SB-009-C08", "ADR-SB-009-C09",
    ),
}

capability_receipt = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://dopemux.dev/schemas/second_brain/contracts/service-capability-receipt.schema.json",
    "title": "ServiceCapabilityReceipt",
    "description": (
        "The receipt an authority operation requires (ADR-SB-009). The candidate "
        "says exactly one thing about it — that it must be current — so that is "
        "all this schema asserts. A CURRENT/STALE enum, a capability list and a "
        "service identifier were all present in the superseded version and were "
        "all this repository's invention. Same naming caveat as "
        "ProjectIdentityEnvelope: the candidate requires 'current service "
        "capability receipts' but does not name a type."
    ),
    "type": "object",
    "required": ["current"],
    "properties": {"current": {"const": True}},
    "x-unspecified-in-candidate": (
        "No freshness vocabulary, capability list, service identifier or "
        "expiry field is asserted; the candidate names none of them."
    ),
    "x-grounding": grounding(
        g("/required/0", "ADR-SB-009-C02", "current"),
        g("/properties/current", "ADR-SB-009-C02", "current"),
    ),
    "x-machine-invariants": invariants("ADR-SB-009-C02"),
}

SPOOL_ASSERTIONS = [
    ("non_canonical", True, "ADR-SB-006-C03", "non-canonical"),
    ("scoped", ["IDENTITY", "DOMAIN", "CLASS"], "ADR-SB-006-C04", "scoped"),
    ("deterministic", True, "ADR-SB-006-C05", "deterministic"),
    ("integrity_protected", True, "ADR-SB-006-C06", "integrity-protected"),
    ("short_lived", True, "ADR-SB-006-C07", "short-lived"),
    ("idempotently_flushed", True, "ADR-SB-006-C08", "idempotently flushed"),
    ("purge_aware", True, "ADR-SB-006-C09", "purge-aware"),
    ("never_remote_backed_up", True, "ADR-SB-006-C10", "never remote backed up"),
    ("public_is_allowed", True, "ADR-SB-006-C11", "Public is allowed"),
    ("internal_requires_os_protected_storage", True, "ADR-SB-006-C12",
     "internal requires OS-protected storage"),
    ("confidential_restricted_remain_disabled_until_verified_encryption_and_"
     "key_ownership", True, "ADR-SB-006-C13",
     "confidential/restricted remain disabled until verified encryption and key "
     "ownership"),
    ("no_unknown_class_spooling", True, "ADR-SB-006-C14",
     "No unknown-class spooling"),
    ("crash_safe_eligible_capture", True, "ADR-SB-006-C15",
     "Crash-safe eligible capture"),
]

local_spool = {
    "$schema": "./interface-contract.schema.json",
    "contract_version": "2.0.0",
    "interface_id": "LocalSpoolPort",
    "interface_kind": "PORT",
    "source_adr": "ADR-SB-006",
    "candidate_sha256": CANDIDATE_SHA,
    "ratification_binding_sha256": RATIFICATION_SHA,
    "clause_inventory_sha256": INV_SHA,
    "implementation_status": "NOT_IMPLEMENTED",
    "runtime_claims_permitted": False,
    "denial_fixtures": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE",
    "assertions": {k: v for k, v, _, _ in SPOOL_ASSERTIONS},
    "x-unspecified-in-candidate": (
        "No operation catalogue. The superseded version listed admit / append / "
        "flush / expire / participate_in_purge with inputs, outputs and "
        "fail-closed conditions; the candidate defines LocalSpoolPort by name "
        "and by the properties of the records it holds, and states none of "
        "that. What survives is exactly those record properties and the "
        "classification rules."
    ),
    "x-grounding": grounding(
        *[g(f"/assertions/{k}", cid, term)
          for k, _, cid, term in SPOOL_ASSERTIONS]
    ),
    "x-machine-invariants": invariants(
        "ADR-SB-006-C01", "ADR-SB-006-C03", "ADR-SB-006-C04", "ADR-SB-006-C05",
        "ADR-SB-006-C06", "ADR-SB-006-C07", "ADR-SB-006-C08", "ADR-SB-006-C09",
        "ADR-SB-006-C10", "ADR-SB-006-C11", "ADR-SB-006-C12", "ADR-SB-006-C13",
        "ADR-SB-006-C14", "ADR-SB-006-C15", "ADR-SB-006-C17",
    ),
}

CUSTODY_ASSERTIONS = [
    ("custody_product_remains_replaceable", True, "ADR-SB-006-C16",
     "Custody product remains replaceable"),
]

custody = {
    "$schema": "./interface-contract.schema.json",
    "contract_version": "2.0.0",
    "interface_id": "CustodyPort",
    "interface_kind": "PORT",
    "source_adr": "ADR-SB-006",
    "candidate_sha256": CANDIDATE_SHA,
    "ratification_binding_sha256": RATIFICATION_SHA,
    "clause_inventory_sha256": INV_SHA,
    "implementation_status": "NOT_IMPLEMENTED",
    "runtime_claims_permitted": False,
    "denial_fixtures": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE",
    "assertions": {k: v for k, v, _, _ in CUSTODY_ASSERTIONS},
    "x-unspecified-in-candidate": (
        "The candidate names CustodyPort and says one thing about custody: the "
        "product remains replaceable. It states no operation, no content "
        "addressing scheme and no backup interface. The superseded version "
        "asserted put / verify_integrity / residual_scan / backup_eligibility / "
        "tombstone; all five were invented here. This contract is deliberately "
        "thin because the decision is thin."
    ),
    "x-grounding": grounding(
        *[g(f"/assertions/{k}", cid, term) for k, _, cid, term in CUSTODY_ASSERTIONS]
    ),
    "x-machine-invariants": invariants("ADR-SB-006-C02", "ADR-SB-006-C16"),
}

LAYER_B = {
    "open-loop-candidate.schema.json": open_loop,
    "task-proposal.schema.json": task_proposal,
    "task-promotion-request.schema.json": task_promotion,
    "project-identity-envelope.schema.json": identity_envelope,
    "service-capability-receipt.schema.json": capability_receipt,
    "local-spool-port.contract.json": local_spool,
    "custody-port.contract.json": custody,
}


# ==========================================================================
# Layer A — per-ADR contracts and the coverage matrix
# ==========================================================================

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    write("adr-machine-contract.schema.json", ADR_META)
    write("interface-contract.schema.json", IFACE_META)
    for name, doc in LAYER_B.items():
        write(name, doc)

    entries = []
    adr_sha = {}
    for adr in inv["adrs"]:
        clauses = []
        required_artifacts: list[str] = []
        for i, c in enumerate(adr["clauses"]):
            pointer = f"#/decision_clauses/{i}"
            artifact = f"{CONTRACT_REL}/{adr['adr_id']}.contract.json"
            extra = c.get("additional_covering_artifacts", [])
            for a in extra:
                if a not in required_artifacts:
                    required_artifacts.append(a)
            row = {
                "clause_id": c["clause_id"],
                "requirement_text": c["requirement_text"],
                "subject": c["subject"],
                "rule_type": c["rule_type"],
                "operator": c["operator"],
                "machine_value": c["machine_value"],
                "section": c["section"],
                "source_fragments": c["source_fragments"],
                "source_decision_text_hash": c["source_decision_text_hash"],
                "covered_by": [f"{artifact}{pointer}"] + list(extra),
            }
            if "source_enumeration" in c:
                row["source_enumeration"] = c["source_enumeration"]
            clauses.append(row)
            entries.append({
                "adr_id": adr["adr_id"],
                "clause_id": c["clause_id"],
                "requirement_text": c["requirement_text"],
                "source_text_hash": c["source_decision_text_hash"],
                "contract_artifact": artifact,
                "contract_rule_pointer": pointer,
                "coverage_status": "COVERED",
                "additional_coverage": list(extra),
            })

        contract = {
            "$schema": "./adr-machine-contract.schema.json",
            "contract_version": "2.0.0",
            "adr_id": adr["adr_id"],
            "adr_title": adr["adr_title"],
            "contract_kind": "ARCHITECTURE_DECISION_CONTRACT",
            "candidate_document": CANDIDATE_REL,
            "candidate_sha256": CANDIDATE_SHA,
            "ratification_binding_sha256": RATIFICATION_SHA,
            "clause_inventory_sha256": INV_SHA,
            "adr_status_at_contract_authoring": "PROPOSED",
            "sb_dec_references": adr["sb_dec_references"],
            "required_artifacts": sorted(required_artifacts),
            "implementation_deferred": IMPLEMENTATION_DEFERRED,
            "runtime_claims_permitted": False,
            "denial_fixtures": "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE",
            "decision_clauses": clauses,
        }
        adr_sha[adr["adr_id"]] = write(f"{adr['adr_id']}.contract.json", contract)

    coverage = {
        "schema_version": "2.0.0",
        "task_id": TASK_ID,
        "purpose": (
            "Maps every frozen clause to the machine rule that expresses it. The "
            "denominator is ADR_CLAUSE_INVENTORY.json, re-frozen in an earlier "
            "commit under operator authorization and hash-bound below; this "
            "matrix cannot widen or narrow it."
        ),
        "candidate_document": CANDIDATE_REL,
        "candidate_sha256": CANDIDATE_SHA,
        "ratification_binding_sha256": RATIFICATION_SHA,
        "clause_inventory": f"{PROOF_REL}/ADR_CLAUSE_INVENTORY.json",
        "clause_inventory_sha256": INV_SHA,
        "adr_count": inv["adr_count"],
        "clause_total": inv["clause_total"],
        "coverage_status_counts": {
            "COVERED": len(entries),
            "NOT_APPLICABLE_PROVEN": 0,
            "MISSING": 0,
            "AMBIGUOUS": 0,
        },
        "adr_contract_sha256": adr_sha,
        "entries": entries,
    }
    write("ADR_CONTRACT_COVERAGE.json", coverage)

    print(f"inventory sha256  {INV_SHA}")
    print(f"clauses           {inv['clause_total']}")
    print(f"artifacts written {len(list(OUT.glob('*.json')))}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:  # fail closed
        print(f"FAIL: unhandled {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
