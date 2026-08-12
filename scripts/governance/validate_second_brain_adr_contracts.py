#!/usr/bin/env python3
"""Deterministic Second Brain ADR machine-contract validator.

Governance tooling, not product runtime. No network, no model calls, no file
mutation. Fails closed: any exception, missing dependency, missing file,
unresolved pointer, or parse error exits nonzero. There is no
exception-to-PASS path.

Two check groups, both of which must pass for exit 0:

  A. Machine-contract coverage  -> PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
  B. FO-01 record reconciliation -> FO01_STALE_RECORD_RECONCILED

Exit codes:
  0 — PASS (both groups)
  1 — FAIL (one or more checks failed)
  2 — usage / environment error
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

CANDIDATE_SHA256 = "e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c"
RATIFICATION_BINDING_SHA256 = (
    "a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c7539e2350ba07b34"
)

CONTRACT_DIR = "schemas/second_brain/contracts"
CANDIDATE_PATH = (
    "docs/03-reference/architecture/second-brain/adr-candidates/"
    "second-brain-adr-candidates.md"
)
FO01_STATUS_PATH = (
    "docs/03-reference/architecture/second-brain/adr-candidates/"
    "fo-01-repair-status.json"
)
FO01_RECEIPT_PATH = (
    "proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/"
    "FO01_RESOLUTION_RECEIPT.json"
)
TRACEABILITY_PATH = (
    "docs/03-reference/architecture/second-brain/adr-candidates/"
    "traceability-matrix.json"
)
CLAUSE_INVENTORY_PATH = (
    "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json"
)

ADR_IDS = [f"ADR-SB-{i:03d}" for i in range(1, 11)]

RULE_TYPES = {
    "REQUIRE", "FORBID", "ENUM", "CONSTANT", "MAXIMUM", "AUTHORITY_TARGET",
    "FAIL_CLOSED", "STATE_TRANSITION", "LIFECYCLE", "CAPABILITY_GATE",
    "INTERFACE_REQUIREMENT", "HASH_BINDING", "ORDERING",
}
OPERATORS = {
    "EQUALS", "NOT_EQUALS", "IN", "NOT_IN", "SET_EQUALS", "SUPERSET_OF",
    "LESS_THAN_OR_EQUAL", "MUST_EXIST", "MUST_NOT_EXIST", "PRECEDES",
    "DEFAULTS_TO",
}

# Closed set of canonical authority targets. Second Brain and Dope-Context are
# never members: the Second Brain is a control plane and Dope-Context is
# advisory retrieval.
AUTHORITY_TARGETS = {"ConPort", "Dope-Memory", "Leantime", "Task Orchestrator", "dopeTask"}
NEVER_AUTHORITY = {
    "second_brain", "Second Brain", "SecondBrain", "Dope-Context", "dope-context",
}

PORT_CONTRACTS = ["local-spool-port.contract.json", "custody-port.contract.json"]
DATA_CONTRACTS = [
    "open-loop-candidate.schema.json",
    "task-proposal.schema.json",
    "task-promotion-request.schema.json",
    "project-identity-envelope.schema.json",
    "service-capability-receipt.schema.json",
]

# Keys that would assert implementation / runtime / enablement authority.
FORBIDDEN_TRUTHY_KEYS = {
    "implemented", "runtime_implemented", "enablement_authorized",
    "runtime_authorized", "production_authorized", "implementation_authorized",
    "implementation_execution_authorized", "adr_accepted", "accepted",
    "runtime_claims_permitted", "denial_fixtures_implemented",
}
FORBIDDEN_VALUE_TOKENS = {
    "IMPLEMENTED", "ENABLEMENT_AUTHORIZED", "RUNTIME_AUTHORIZED",
    "PRODUCTION_AUTHORIZED", "IMPLEMENTATION_AUTHORIZED", "ACCEPTED",
}
ALLOWED_DENIAL_FIXTURE_VALUES = (
    "NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE",
    "NOT_IMPLEMENTED",
    False,
)

PM_FORBIDDEN_PROPERTIES = {
    "assignee", "owner", "ownership", "priority", "pm_priority", "status",
    "workflow_status", "sprint", "sprint_state", "task_completion_state",
    "completed", "done", "escalation", "escalation_policy", "scheduled_at",
    "schedule", "estimate", "story_points",
}


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, bool, str]] = []

    def check(self, group: str, cid: str, ok: bool, detail: str = "") -> bool:
        self.rows.append((group, cid, bool(ok), detail))
        return bool(ok)

    def failures(self, group: str | None = None) -> list[tuple[str, str, bool, str]]:
        return [
            r for r in self.rows if not r[2] and (group is None or r[0] == group)
        ]

    def emit(self) -> None:
        for group, cid, ok, detail in self.rows:
            mark = "PASS" if ok else "FAIL"
            line = f"  [{mark}] {group}/{cid}"
            if detail:
                line += f" — {detail}"
            print(line)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_pointer(doc: Any, pointer: str) -> Any:
    """Strict RFC-6901 resolution. Raises KeyError/IndexError when absent."""
    if pointer in ("", "#"):
        return doc
    if pointer.startswith("#"):
        pointer = pointer[1:]
    if not pointer.startswith("/"):
        raise KeyError(f"pointer must be rooted: {pointer!r}")
    node = doc
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            node = node[int(token)]
        elif isinstance(node, dict):
            node = node[token]
        else:
            raise KeyError(f"cannot descend into {type(node).__name__} at {token!r}")
    return node


def asserted_value(val: Any) -> Any:
    """Unwrap a JSON-Schema pin to the value it actually asserts.

    In a schema file a field appears as ``{"const": false, "description": ...}``.
    That node asserts ``false``; treating the dict itself as the value would
    read every const-pinned prohibition as a truthy claim.
    """
    if isinstance(val, dict) and "const" in val:
        return val["const"]
    return val


def walk(node: Any, path: str = ""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k, v
            yield from walk(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}/{i}")


def parse_candidate_sb_dec(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for adr_id in ADR_IDS:
        marker = f"## {adr_id}:"
        if marker not in text:
            continue
        start = text.index(marker)
        nxt = text.find("\n## ADR-SB-", start + 1)
        section = text[start : nxt if nxt != -1 else len(text)]
        ev = section.index("### Evidence and traceability")
        acc = section.index("### Acceptance conditions", ev)
        out[adr_id] = re.findall(r"`(SB-DEC-\d+)`", section[ev:acc])
    return out


# --------------------------------------------------------------------------
# Group A — machine-contract coverage
# --------------------------------------------------------------------------


def group_a(root: Path, rep: Report) -> None:
    try:
        from jsonschema import Draft7Validator
    except ImportError as exc:  # fail closed on missing dependency
        rep.check("A", "A00-dependency", False, f"jsonschema unavailable: {exc}")
        return

    cdir = root / CONTRACT_DIR

    # A01 — all ten ADR contract files exist.
    missing = [a for a in ADR_IDS if not (cdir / f"{a}.contract.json").is_file()]
    rep.check("A", "A01-ten-adr-contracts-exist", not missing, f"missing={missing}")

    # A12/A13 — mandatory typed artifacts exist.
    named = PORT_CONTRACTS + DATA_CONTRACTS
    missing_named = [n for n in named if not (cdir / n).is_file()]
    rep.check(
        "A", "A13-named-typed-artifacts-exist", not missing_named,
        f"missing={missing_named}",
    )

    meta = cdir / "adr-machine-contract.schema.json"
    iface = cdir / "interface-contract.schema.json"
    cov_path = cdir / "ADR_CONTRACT_COVERAGE.json"
    for label, p in (
        ("meta-schema", meta), ("interface-schema", iface), ("coverage-matrix", cov_path)
    ):
        rep.check("A", f"A01-{label}-exists", p.is_file(), str(p.relative_to(root)))
    if missing or missing_named or not meta.is_file() or not cov_path.is_file():
        return

    # A02 — every artifact parses as JSON.
    docs: dict[str, Any] = {}
    for p in sorted(cdir.glob("*.json")):
        rel = str(p.relative_to(root))
        try:
            docs[rel] = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            rep.check("A", f"A02-parse:{p.name}", False, str(exc))
            return
    rep.check("A", "A02-all-artifacts-parse", True, f"{len(docs)} files")

    meta_schema = docs[f"{CONTRACT_DIR}/adr-machine-contract.schema.json"]
    iface_schema = docs[f"{CONTRACT_DIR}/interface-contract.schema.json"]
    coverage = docs[f"{CONTRACT_DIR}/ADR_CONTRACT_COVERAGE.json"]

    # A03 — schema validation of every contract against its governing schema.
    for label, schema in (("meta", meta_schema), ("interface", iface_schema)):
        try:
            Draft7Validator.check_schema(schema)
            rep.check("A", f"A03-{label}-schema-well-formed", True)
        except Exception as exc:
            rep.check("A", f"A03-{label}-schema-well-formed", False, str(exc))
            return

    for adr_id in ADR_IDS:
        rel = f"{CONTRACT_DIR}/{adr_id}.contract.json"
        errs = sorted(
            Draft7Validator(meta_schema).iter_errors(docs[rel]),
            key=lambda e: list(e.path),
        )
        rep.check(
            "A", f"A03-validates:{adr_id}", not errs,
            "; ".join(f"{list(e.path)}: {e.message}" for e in errs[:3]),
        )
    for name in PORT_CONTRACTS:
        rel = f"{CONTRACT_DIR}/{name}"
        errs = sorted(
            Draft7Validator(iface_schema).iter_errors(docs[rel]),
            key=lambda e: list(e.path),
        )
        rep.check(
            "A", f"A03-validates:{name}", not errs,
            "; ".join(f"{list(e.path)}: {e.message}" for e in errs[:3]),
        )
    for name in DATA_CONTRACTS:
        rel = f"{CONTRACT_DIR}/{name}"
        try:
            Draft7Validator.check_schema(docs[rel])
            rep.check("A", f"A03-draft7-well-formed:{name}", True)
        except Exception as exc:
            rep.check("A", f"A03-draft7-well-formed:{name}", False, str(exc))

    # A04 — candidate binding, recomputed from the document itself.
    cand_path = root / CANDIDATE_PATH
    if not cand_path.is_file():
        rep.check("A", "A04-candidate-present", False, CANDIDATE_PATH)
        return
    cand_bytes = cand_path.read_bytes()
    live = sha256_bytes(cand_bytes)
    rep.check(
        "A", "A04-candidate-sha256", live == CANDIDATE_SHA256,
        f"live={live}",
    )
    cand_text = cand_bytes.decode("utf-8")

    bad = [
        rel for rel, d in docs.items()
        if isinstance(d, dict) and "candidate_sha256" in d
        and d["candidate_sha256"] != CANDIDATE_SHA256
    ]
    rep.check("A", "A04-contracts-bind-candidate", not bad, f"divergent={bad}")

    # A05 — ratification binding matches the candidate's own frontmatter.
    fm = re.search(r"^ratification_binding_sha256:\s*(\S+)$", cand_text, re.M)
    rep.check(
        "A", "A05-ratification-binding",
        bool(fm) and fm.group(1) == RATIFICATION_BINDING_SHA256,
        f"frontmatter={fm.group(1) if fm else None}",
    )
    bad = [
        rel for rel, d in docs.items()
        if isinstance(d, dict) and "ratification_binding_sha256" in d
        and d["ratification_binding_sha256"] != RATIFICATION_BINDING_SHA256
    ]
    rep.check("A", "A05-contracts-bind-ratification", not bad, f"divergent={bad}")

    # A06 — ADR ids exactly 001..010, no duplicates.
    ids = [docs[f"{CONTRACT_DIR}/{a}.contract.json"]["adr_id"] for a in ADR_IDS]
    rep.check(
        "A", "A06-adr-ids-exact",
        sorted(ids) == ADR_IDS and len(set(ids)) == 10, f"ids={sorted(ids)}",
    )

    # A07 — SB-DEC lists equal the candidate's, parsed live.
    live_refs = parse_candidate_sb_dec(cand_text)
    total = 0
    for adr_id in ADR_IDS:
        contract_refs = docs[f"{CONTRACT_DIR}/{adr_id}.contract.json"]["sb_dec_references"]
        expected = live_refs.get(adr_id, [])
        total += len(expected)
        rep.check(
            "A", f"A07-sb-dec:{adr_id}", contract_refs == expected,
            f"contract={contract_refs} candidate={expected}",
        )
    rep.check("A", "A07-sb-dec-total-28", total == 28, f"total={total}")

    # A19 — SB-DEC-026 remains unlinked, in the candidate and in every contract.
    in_candidate = any("SB-DEC-026" in v for v in live_refs.values())
    in_contracts = [
        rel for rel, d in docs.items()
        if "SB-DEC-026" in json.dumps(d)
    ]
    rep.check(
        "A", "A19-sb-dec-026-unlinked",
        not in_candidate and not in_contracts,
        f"candidate={in_candidate} contracts={in_contracts}",
    )

    # A16/A17/A18 — ADR status frozen at PROPOSED, document status CANDIDATE.
    n_proposed = cand_text.count("**Status:** `PROPOSED`")
    rep.check("A", "A16-ten-proposed", n_proposed == 10, f"count={n_proposed}")
    rep.check(
        "A", "A18-no-accepted-token", "ACCEPTED" not in cand_text,
        "candidate contains the ACCEPTED token" if "ACCEPTED" in cand_text else "",
    )
    status_fm = re.search(r"^status:\s*(\S+)$", cand_text, re.M)
    rep.check(
        "A", "A17-document-status-candidate",
        bool(status_fm) and status_fm.group(1) == "CANDIDATE",
        f"status={status_fm.group(1) if status_fm else None}",
    )
    bad_status = [
        f"{CONTRACT_DIR}/{a}.contract.json" for a in ADR_IDS
        if docs[f"{CONTRACT_DIR}/{a}.contract.json"].get(
            "adr_status_at_contract_authoring"
        ) != "PROPOSED"
    ]
    rep.check("A", "A16-contracts-record-proposed", not bad_status, f"bad={bad_status}")

    # A08 — frozen denominator: three-way hash agreement + exact 1:1 coverage.
    inv_path = root / CLAUSE_INVENTORY_PATH
    if not inv_path.is_file():
        rep.check("A", "A08-inventory-present", False, CLAUSE_INVENTORY_PATH)
        return
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    inv_live = sha256_bytes(inv_path.read_bytes())
    rep.check(
        "A", "A08-inventory-hash-agrees-with-coverage",
        coverage.get("clause_inventory_sha256") == inv_live,
        f"coverage={coverage.get('clause_inventory_sha256')} live={inv_live}",
    )

    inv_clauses = {
        c["clause_id"]: c for adr in inv["adrs"] for c in adr["clauses"]
    }
    rep.check(
        "A", "A08-inventory-total",
        len(inv_clauses) == inv["clause_total"] == 97,
        f"inventory={len(inv_clauses)} declared={inv['clause_total']}",
    )

    entries = coverage.get("entries", [])
    seen: dict[str, int] = {}
    for e in entries:
        seen[e["clause_id"]] = seen.get(e["clause_id"], 0) + 1
    absent = sorted(set(inv_clauses) - set(seen))
    extra = sorted(set(seen) - set(inv_clauses))
    dupes = sorted(k for k, v in seen.items() if v > 1)
    rep.check("A", "A08-every-clause-covered-once",
              not absent and not extra and not dupes,
              f"absent={absent} extra={extra} duplicated={dupes}")

    # A08b — denominator integrity: fragments really are candidate substrings.
    frag_bad, hash_bad = [], []
    for cid, c in inv_clauses.items():
        for frag in c["source_fragments"]:
            if frag not in cand_text:
                frag_bad.append(cid)
                break
        if sha256_text("\n".join(c["source_fragments"])) != c["source_decision_text_hash"]:
            hash_bad.append(cid)
    rep.check("A", "A08-fragments-are-candidate-substrings", not frag_bad,
              f"not-found={frag_bad[:5]}")
    rep.check("A", "A08-fragment-hashes-recompute", not hash_bad,
              f"mismatch={hash_bad[:5]}")

    # A08c — coverage source_text_hash must equal the frozen inventory hash.
    drift = [
        e["clause_id"] for e in entries
        if e["clause_id"] in inv_clauses
        and e.get("source_text_hash")
        != inv_clauses[e["clause_id"]]["source_decision_text_hash"]
    ]
    rep.check("A", "A08-coverage-hash-matches-inventory", not drift, f"drift={drift[:5]}")

    # A10/A11 — no MISSING, no AMBIGUOUS.
    statuses = [e.get("coverage_status") for e in entries]
    n_missing = statuses.count("MISSING")
    n_ambig = statuses.count("AMBIGUOUS")
    bad_status_vals = sorted(
        {s for s in statuses if s not in
         {"COVERED", "NOT_APPLICABLE_PROVEN", "MISSING", "AMBIGUOUS"}}
    )
    rep.check("A", "A10-missing-zero", n_missing == 0, f"MISSING={n_missing}")
    rep.check("A", "A11-ambiguous-zero", n_ambig == 0, f"AMBIGUOUS={n_ambig}")
    rep.check("A", "A11-status-values-known", not bad_status_vals, f"bad={bad_status_vals}")
    counts = coverage.get("coverage_status_counts", {})
    rep.check(
        "A", "A10-declared-counts-agree",
        counts.get("MISSING") == n_missing and counts.get("AMBIGUOUS") == n_ambig
        and counts.get("COVERED") == statuses.count("COVERED"),
        f"declared={counts}",
    )

    # A09 — every coverage pointer resolves to a real structured machine rule
    #       that AGREES with the clause it claims to cover.
    def load_rel(rel: str) -> Any:
        if rel in docs:
            return docs[rel]
        p = root / rel
        if not p.is_file():
            raise FileNotFoundError(rel)
        return json.loads(p.read_text(encoding="utf-8"))

    unresolved, unstructured, disagreeing = [], [], []
    for e in entries:
        cid = e["clause_id"]
        clause = inv_clauses.get(cid)
        if clause is None:
            continue
        targets = [(e["contract_artifact"], e["contract_rule_pointer"])]
        targets += [
            (a["contract_artifact"], a["contract_rule_pointer"])
            for a in e.get("additional_coverage", [])
        ]
        for rel, ptr in targets:
            try:
                node = resolve_pointer(load_rel(rel), ptr)
            except Exception as exc:
                unresolved.append(f"{cid}->{rel}{ptr} ({type(exc).__name__})")
                continue
            if not (
                isinstance(node, dict)
                and {"subject", "rule_type", "operator", "machine_value"} <= set(node)
                and node["rule_type"] in RULE_TYPES
                and node["operator"] in OPERATORS
            ):
                unstructured.append(f"{cid}->{rel}{ptr}")
                continue
            if (
                node["subject"] != clause["subject"]
                or node["rule_type"] != clause["rule_type"]
                or node["operator"] != clause["operator"]
                or node["machine_value"] != clause["machine_value"]
            ):
                disagreeing.append(f"{cid}->{rel}{ptr}")
            ep = node.get("enforced_by")
            if ep is not None:
                try:
                    resolve_pointer(load_rel(rel), ep)
                except Exception:
                    unresolved.append(f"{cid}->{rel}{ep} (enforced_by)")

    rep.check("A", "A09-pointers-resolve", not unresolved, f"unresolved={unresolved[:5]}")
    rep.check(
        "A", "A09-pointers-are-structured-rules", not unstructured,
        f"prose-or-shapeless={unstructured[:5]}",
    )
    rep.check(
        "A", "A09-rules-agree-with-clause", not disagreeing,
        f"disagreeing={disagreeing[:5]}",
    )

    # A12 — declared required_artifacts exist.
    absent_req = []
    for adr_id in ADR_IDS:
        for rel in docs[f"{CONTRACT_DIR}/{adr_id}.contract.json"].get(
            "required_artifacts", []
        ):
            if not (root / rel).is_file():
                absent_req.append(f"{adr_id}->{rel}")
    rep.check("A", "A12-required-artifacts-exist", not absent_req, f"absent={absent_req}")

    # A14 — no contract grants implementation / runtime authority.
    offenders = []
    for rel, d in docs.items():
        for _, key, raw in walk(d):
            val = asserted_value(raw)
            if key in FORBIDDEN_TRUTHY_KEYS and val not in (False, None):
                offenders.append(f"{rel}:{key}={val!r}")
            if isinstance(val, str) and val in FORBIDDEN_VALUE_TOKENS:
                offenders.append(f"{rel}:{key}={val!r}")
    rep.check("A", "A14-no-runtime-or-implementation-authority", not offenders,
              f"offenders={offenders[:5]}")

    for name in PORT_CONTRACTS:
        d = docs[f"{CONTRACT_DIR}/{name}"]
        rep.check(
            "A", f"A14-port-not-implemented:{name}",
            d.get("implementation_status") == "NOT_IMPLEMENTED"
            and d.get("runtime_claims_permitted") is False,
            f"status={d.get('implementation_status')}",
        )

    # A15 — no contract claims denial fixtures exist.
    df_bad = []
    for rel, d in docs.items():
        for _, key, raw in walk(d):
            val = asserted_value(raw)
            if (
                "denial_fixture" in key.lower()
                and val not in ALLOWED_DENIAL_FIXTURE_VALUES
            ):
                df_bad.append(f"{rel}:{key}={val!r}")
    rep.check("A", "A15-no-denial-fixture-claim", not df_bad, f"claims={df_bad[:5]}")
    no_defer = [
        a for a in ADR_IDS
        if "DENIAL_FIXTURES"
        not in docs[f"{CONTRACT_DIR}/{a}.contract.json"]["implementation_deferred"]
    ]
    rep.check("A", "A15-denial-fixtures-deferred", not no_defer, f"missing={no_defer}")

    # A20 — no new canonical authority introduced.
    authority_bad, never_bad = [], []
    for adr_id in ADR_IDS:
        d = docs[f"{CONTRACT_DIR}/{adr_id}.contract.json"]
        if not d.get("forbidden_authority_claims"):
            authority_bad.append(f"{adr_id}: empty forbidden_authority_claims")
        for c in d.get("decision_clauses", []):
            # A malformed clause is already reported by A03/A09; skip it here so
            # this pass still produces a report instead of an opaque traceback.
            if not isinstance(c, dict):
                authority_bad.append(f"{adr_id}: non-object decision clause")
                continue
            if c.get("rule_type") != "AUTHORITY_TARGET":
                continue
            vals = c["machine_value"]
            vals = vals if isinstance(vals, list) else [vals]
            for v in vals:
                if not isinstance(v, (str, int, float, bool, type(None))):
                    authority_bad.append(f"{c.get('clause_id')}: non-scalar target")
                    continue
                if v not in AUTHORITY_TARGETS:
                    authority_bad.append(f"{c['clause_id']}: {v!r} not a canonical authority")
                if v in NEVER_AUTHORITY:
                    never_bad.append(f"{c['clause_id']}: {v!r}")
    rep.check("A", "A20-authority-targets-closed-set", not authority_bad,
              f"violations={authority_bad[:5]}")
    rep.check("A", "A20-second-brain-never-authority", not never_bad,
              f"violations={never_bad[:5]}")

    semantic_invariants(root, docs, inv_clauses, rep)


def semantic_invariants(
    root: Path, docs: dict[str, Any], inv_clauses: dict[str, Any], rep: Report
) -> None:
    """Hard invariants keyed to specific artifacts.

    A purely structural pass would green-light a contract that says the right
    shape but the wrong thing. These checks pin the values that carry the
    architecture decision, so the §9 semantic mutations fail here even when the
    artifact still validates against its schema.
    """
    def clause(cid: str) -> dict[str, Any]:
        return inv_clauses.get(cid, {})

    def doc(name: str) -> dict[str, Any]:
        return docs.get(f"{CONTRACT_DIR}/{name}", {})

    # S01 — spool custody gates.
    spool = doc("local-spool-port.contract.json")
    cm = spool.get("classification_matrix", {})
    rep.check(
        "S", "S01-restricted-spool-requires-encryption",
        cm.get("restricted") == "DISABLED_UNTIL_VERIFIED_ENCRYPTION_AND_KEY_OWNERSHIP"
        and cm.get("confidential")
        == "DISABLED_UNTIL_VERIFIED_ENCRYPTION_AND_KEY_OWNERSHIP",
        f"confidential={cm.get('confidential')} restricted={cm.get('restricted')}",
    )
    rep.check(
        "S", "S01-unknown-class-denied", cm.get("unknown") == "DENY",
        f"unknown={cm.get('unknown')}",
    )
    rep.check(
        "S", "S01-internal-requires-os-protection",
        cm.get("internal") == "ALLOWED_REQUIRES_OS_PROTECTED_STORAGE",
        f"internal={cm.get('internal')}",
    )

    # S02 — OpenLoopCandidate carries no PM semantics.
    olc = doc("open-loop-candidate.schema.json")
    props = set(olc.get("properties", {}))
    leaked = sorted(props & PM_FORBIDDEN_PROPERTIES)
    rep.check("S", "S02-open-loop-no-pm-properties", not leaked, f"leaked={leaked}")
    rep.check(
        "S", "S02-open-loop-closed-shape",
        olc.get("additionalProperties") is False,
        f"additionalProperties={olc.get('additionalProperties')!r}",
    )
    due = olc.get("properties", {}).get("due_at", {})
    rep.check(
        "S", "S02-due-at-advisory-only",
        due.get("x-semantics") == "ADVISORY_DISPLAY_METADATA_ONLY"
        and {"SCHEDULING", "ESCALATION"} <= set(due.get("x-forbidden-behaviors", [])),
        f"x-semantics={due.get('x-semantics')}",
    )
    tp = doc("task-proposal.schema.json")
    tp_leaked = sorted(set(tp.get("properties", {})) & PM_FORBIDDEN_PROPERTIES)
    rep.check("S", "S02-task-proposal-no-pm-properties", not tp_leaked, f"leaked={tp_leaked}")
    rep.check(
        "S", "S02-task-proposal-closed-shape",
        tp.get("additionalProperties") is False,
    )

    # S03 — task promotion disabled by construction, not by default.
    tpr = doc("task-promotion-request.schema.json")
    enabled = tpr.get("properties", {}).get("enabled", {})
    rep.check(
        "S", "S03-task-promotion-disabled",
        enabled.get("const") is False and enabled.get("default") in (False, None),
        f"const={enabled.get('const')!r} default={enabled.get('default')!r}",
    )
    req = set(tpr.get("required", []))
    rep.check(
        "S", "S03-promotion-requires-both-proofs-and-approval",
        {"leantime_proof_ref", "task_orchestrator_proof_ref", "operator_approval",
         "enabled"} <= req,
        f"required={sorted(req)}",
    )
    rep.check(
        "S", "S03-promotion-target-is-pm-authority",
        set(tpr.get("properties", {}).get("target_authority", {}).get("enum", []))
        == {"Leantime", "Task Orchestrator"},
    )
    c = clause("ADR-SB-008-C07")
    rep.check(
        "S", "S03-clause-promotion-disabled",
        c.get("machine_value") is False and c.get("rule_type") == "CAPABILITY_GATE",
        f"machine_value={c.get('machine_value')!r}",
    )

    # S04 — unknown policy eligibility denies.
    c = clause("ADR-SB-004-C04")
    rep.check(
        "S", "S04-unknown-eligibility-denies",
        c.get("machine_value") == "DENY" and c.get("rule_type") == "FAIL_CLOSED",
        f"machine_value={c.get('machine_value')!r} rule_type={c.get('rule_type')!r}",
    )
    c = clause("ADR-SB-004-C07")
    rep.check(
        "S", "S04-no-confidential-restricted-indexing",
        sorted(c.get("machine_value") or []) == ["internal", "public"],
        f"machine_value={c.get('machine_value')!r}",
    )

    # S05 — wrong-project writes deny across clause and both typed artifacts.
    c = clause("ADR-SB-009-C06")
    rep.check(
        "S", "S05-wrong-project-clause-denies",
        c.get("machine_value") == "DENY" and c.get("rule_type") == "FAIL_CLOSED",
        f"machine_value={c.get('machine_value')!r}",
    )
    pie = doc("project-identity-envelope.schema.json").get("properties", {})
    rep.check(
        "S", "S05-envelope-denies-wrong-project",
        pie.get("wrong_project_write_disposition", {}).get("const") == "DENY",
    )
    rep.check(
        "S", "S05-envelope-single-active-project",
        pie.get("active_automatic_capture_project_count", {}).get("maximum") == 1,
        f"maximum={pie.get('active_automatic_capture_project_count', {}).get('maximum')!r}",
    )
    rep.check(
        "S", "S05-multi-project-capture-disabled",
        pie.get("multi_project_background_capture_enabled", {}).get("const") is False,
    )
    rep.check(
        "S", "S05-identity-sources-rejected",
        set(pie.get("rejected_identity_sources", {}).get("const", []))
        == {"PORT", "PATH_HASH", "CURRENT_DIRECTORY", "SINGLETON_EVENT_STREAM"},
    )
    scr = doc("service-capability-receipt.schema.json").get("properties", {})
    rep.check(
        "S", "S05-receipt-denies-wrong-project",
        scr.get("wrong_project_disposition", {}).get("const") == "DENY"
        and scr.get("unknown_capability_disposition", {}).get("const") == "DENY",
    )

    # S06 — UX bounds.
    c = clause("ADR-SB-010-C03")
    rep.check(
        "S", "S06-visible-queue-max-7",
        c.get("machine_value") == 7 and c.get("operator") == "LESS_THAN_OR_EQUAL",
        f"machine_value={c.get('machine_value')!r} operator={c.get('operator')!r}",
    )
    c = clause("ADR-SB-010-C08")
    rep.check(
        "S", "S06-consequential-default-defer-or-cancel",
        sorted(c.get("machine_value") or []) == ["CANCEL", "DEFER"],
        f"machine_value={c.get('machine_value')!r}",
    )

    # S07 — no surprise writes, no productivity scoring.
    for cid, label in (
        ("ADR-SB-010-C10", "S07-no-surprise-writes"),
        ("ADR-SB-010-C09", "S07-no-productivity-scoring"),
    ):
        c = clause(cid)
        rep.check(
            "S", label,
            c.get("machine_value") is False and c.get("rule_type") == "FORBID",
            f"machine_value={c.get('machine_value')!r} rule_type={c.get('rule_type')!r}",
        )

    # S08 — purge completeness threshold is zero, not "best effort".
    c = clause("ADR-SB-007-C07")
    rep.check(
        "S", "S08-searchable-residual-zero",
        c.get("machine_value") == 0 and c.get("rule_type") == "FAIL_CLOSED",
        f"machine_value={c.get('machine_value')!r}",
    )


# --------------------------------------------------------------------------
# Group B — FO-01 stale-record reconciliation
# --------------------------------------------------------------------------


def group_b(root: Path, rep: Report) -> None:
    status_path = root / FO01_STATUS_PATH
    receipt_path = root / FO01_RECEIPT_PATH
    for label, p in (("status", status_path), ("receipt", receipt_path)):
        if not p.is_file():
            rep.check("B", f"B01-{label}-exists", False, str(p))
            return
    rep.check("B", "B01-records-exist", True)

    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.check("B", "B01-records-parse", False, str(exc))
        return
    rep.check("B", "B01-records-parse", True)

    # B02 — the reconciled status mirrors the later receipt verbatim.
    rep.check(
        "B", "B02-status-matches-receipt",
        status.get("fo01_status") == receipt["status"]
        == "TRACEABILITY_REPAIRED_AND_INDEPENDENTLY_REVERIFIED",
        f"status={status.get('fo01_status')!r}",
    )

    # B03 — independent verification asserted only with receipt evidence.
    iv = status.get("independent_verification", {})
    rep.check(
        "B", "B03-independent-verification-performed",
        iv.get("performed") is True,
        f"performed={iv.get('performed')!r}",
    )
    rep.check(
        "B", "B03-verdict-matches-receipt",
        iv.get("verdict") == receipt["audit_verdict"]
        == "PASS_FO01_TRACEABILITY_REPAIR_WITH_NONBLOCKING_OBSERVATIONS",
        f"verdict={iv.get('verdict')!r}",
    )
    for field, key in (
        ("audited_content_head", "audited_content_head"),
        ("auditor_report_sha256", "auditor_report_sha256"),
    ):
        rep.check(
            "B", f"B03-receipt-derived:{field}",
            iv.get(field) == receipt[key],
            f"status={iv.get(field)!r} receipt={receipt[key]!r}",
        )
    rep.check(
        "B", "B03-blockers-and-must-fix-zero",
        iv.get("blockers") == receipt["audit_blockers"] == 0
        and iv.get("must_fix") == receipt["audit_must_fix"] == 0,
        f"blockers={iv.get('blockers')!r} must_fix={iv.get('must_fix')!r}",
    )

    # B04/B05 — the FO-01 blocker is closed; ADR acceptance is still not authorized.
    rep.check(
        "B", "B04-adr-acceptance-not-authorized",
        status.get("adr_acceptance_authorized") is False
        and receipt["adr_acceptance_authorized"] is False,
        f"authorized={status.get('adr_acceptance_authorized')!r}",
    )
    rep.check(
        "B", "B05-fo01-gate-eligible",
        status.get("fo01_gate_condition") == "CLOSED"
        and status.get("adr_acceptance_gate_eligible") is True
        and receipt["adr_acceptance_gate_eligible"] is True,
        f"gate={status.get('fo01_gate_condition')!r} "
        f"eligible={status.get('adr_acceptance_gate_eligible')!r}",
    )
    rep.check(
        "B", "B06-other-conditions-still-required",
        status.get("other_adr_acceptance_conditions") == "STILL_REQUIRED",
        f"value={status.get('other_adr_acceptance_conditions')!r}",
    )

    # B07 — execution authority untouched.
    gates = status.get("gates", {})
    rep.check(
        "B", "B07-implementation-execution-not-authorized",
        gates.get("implementation_execution") == "NOT_AUTHORIZED"
        == receipt["implementation_execution"],
        f"gates={gates}",
    )
    rep.check(
        "B", "B07-merge-not-authorized",
        gates.get("merge") == "NOT_AUTHORIZED" and receipt["merge_authorized"] is False,
    )

    # B08 — candidate/authority semantics were NOT altered while reconciling.
    rep.check(
        "B", "B08-repaired-candidate-unchanged",
        status.get("repaired_candidate", {}).get("sha256")
        == receipt["repaired_candidate_sha256"],
    )
    rep.check(
        "B", "B08-ratification-binding-unchanged",
        status.get("authority", {}).get("ratification_binding_sha256")
        == receipt["ratification_binding_sha256"] == RATIFICATION_BINDING_SHA256,
    )
    rep.check(
        "B", "B08-source-hashes-unchanged",
        status.get("source_hashes", {}).get("24_ADR_CANDIDATES.md")
        == receipt["source_adr_candidates_sha256"]
        and status.get("source_hashes", {}).get(
            "03_ARCHITECTURE_DECISION_REGISTER.yaml"
        ) == receipt["decision_register_sha256"],
    )
    rep.check(
        "B", "B08-sb-dec-031-032-dispositions-unchanged",
        status.get("sb_dec_031", {}).get("disposition")
        == receipt["sb_dec_031_disposition"]
        and status.get("sb_dec_032", {}).get("disposition")
        == receipt["sb_dec_032_disposition"],
    )
    rep.check(
        "B", "B08-adr-statuses-unchanged",
        status.get("adr_statuses", {}).get("document_status") == "CANDIDATE"
        and status.get("adr_statuses", {}).get("promoted_to_accepted") == 0,
    )
    rep.check(
        "B", "B08-decision-reference-count",
        status.get("coverage", {}).get("decisions_linked") == 26
        and receipt["decision_reference_changes"] == 28,
    )

    # B09 — the NOT_RUN discipline survives reconciliation verbatim.
    rep.check(
        "B", "B09-not-run-preserved",
        status.get("preserved_not_run") == receipt["preserved_not_run"],
        f"status={status.get('preserved_not_run')}",
    )

    tm = root / TRACEABILITY_PATH
    if tm.is_file():
        matrix = json.loads(tm.read_text(encoding="utf-8"))
        rep.check(
            "B", "B08-coverage-matches-traceability-matrix",
            status.get("coverage") == matrix.get("coverage"),
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Validate Second Brain ADR machine contracts (fail-closed).",
    )
    ap.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root to validate (default: this script's repository).",
    )
    ap.add_argument(
        "--json", action="store_true", help="Emit a machine-readable result object."
    )
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    if not root.is_dir():
        print(f"ERROR: --repo-root is not a directory: {root}", file=sys.stderr)
        return 2

    rep = Report()
    group_a(root, rep)
    group_b(root, rep)

    a_fail = rep.failures("A") + rep.failures("S")
    b_fail = rep.failures("B")
    ok = not a_fail and not b_fail

    if args.json:
        print(json.dumps(
            {
                "repo_root": str(root),
                "checks_total": len(rep.rows),
                "checks_failed": len(a_fail) + len(b_fail),
                "coverage_group": "PASS" if not a_fail else "FAIL",
                "fo01_group": "PASS" if not b_fail else "FAIL",
                "failures": [
                    {"group": g, "check": c, "detail": d}
                    for g, c, _, d in (a_fail + b_fail)
                ],
                "result": (
                    "PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE"
                    if ok else "FAIL"
                ),
            },
            indent=2,
        ))
        return 0 if ok else 1

    print("Second Brain ADR machine-contract validation")
    print(f"  repo root: {root}")
    rep.emit()
    print()
    print(f"  checks: {len(rep.rows)}  failed: {len(a_fail) + len(b_fail)}")
    if a_fail:
        print("FAIL: machine-contract coverage")
    if b_fail:
        print("FAIL: FO-01 record reconciliation")
    if not ok:
        return 1
    print("PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE")
    print("FO01_STALE_RECORD_RECONCILED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:  # fail closed — never an exception-to-PASS path
        print(f"FAIL: unhandled {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
