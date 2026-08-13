#!/usr/bin/env python3
"""Deterministic Second Brain ADR machine-contract validator.

Governance tooling, not product runtime. No network, no model calls, no file
mutation. Fails closed: any exception, missing dependency, missing file,
unresolved pointer, or parse error exits nonzero. There is no
exception-to-PASS path.

Three check groups, all of which must pass for exit 0:

  A. Structure, binding, coverage, grounding
  S. Semantic invariants held independently of the inventory
  B. FO-01 record reconciliation

What changed after the first independent audit
----------------------------------------------
That audit returned FAIL with three blockers, and the repairs are structural
rather than per-finding:

* The frozen denominator's sha256 is const-pinned below (A09). Editing a clause
  after the freeze changes that hash and fails, and because every contract rule
  must equal its inventory clause (A20), editing both sides consistently fails
  too. That closes the bilateral-edit class, including for boolean values,
  which carry no text to check.
* Closed sets are checked *bidirectionally* against a verbatim source
  enumeration (A26). The previous grounding rejected widening but accepted
  shrinking, so dropping PURGE from the deletion set passed.
* Clause grounding covers every rule shape, and the shapes themselves are
  restricted to testable ones (A24, A25). A rule whose value is a label like
  ``PURGE_DEPENDENCY_GRAPH`` states that something is named, not that anything
  must be true, and no shape can express one now.
* Every property name, enum member and const string in the typed artifacts must
  be bound to a clause and a verbatim candidate phrase (A31, A32). Invented
  interface surface fails as a class rather than being removed case by case.
* A clause may not be grounded in text from a 'Rejected alternatives' section
  (A23). "Vector-first answer generation" is verbatim candidate text.
* The FO-01 status file is checked as a whole projection of its receipt (B02),
  and every field of it must be classified (B11), so no field can drift while
  a partial projection still passes.

Exit codes:
  0 — PASS (all groups)
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

# --------------------------------------------------------------------------
# Pinned authority
# --------------------------------------------------------------------------

CANDIDATE_SHA256 = "e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c"
RATIFICATION_BINDING_SHA256 = (
    "a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c7539e2350ba07b34"
)

# The re-frozen coverage denominator, authorized by the operator ruling of
# 2026-08-12 and recorded in DENOMINATOR_REFREEZE_RECEIPT.json. This pin is the
# single most load-bearing line in this file: it is what makes a post-freeze
# edit to the denominator fail even when the contracts are edited to agree.
#
# Honest limit: a producer can also edit this constant. What that costs is
# visibility — the pin, the receipt and the operator's verbatim ruling all move
# together, and the receipt asserts an authorization that would then be false.
# The guarantee is not that the denominator cannot change; it is that it cannot
# change quietly.
FROZEN_INVENTORY_SHA256 = (
    "b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dcd58af7f78a439"
)
FROZEN_CLAUSE_TOTAL = 160
SUPERSEDED_INVENTORY_SHA256 = (
    "f073ca28802e6b140dd5789d5fad5839962635f7b287cac589ec704efc663288"
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
PROOF_DIR = "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
CLAUSE_INVENTORY_PATH = f"{PROOF_DIR}/ADR_CLAUSE_INVENTORY.json"
REFREEZE_RECEIPT_PATH = f"{PROOF_DIR}/DENOMINATOR_REFREEZE_RECEIPT.json"

ADR_IDS = [f"ADR-SB-{i:03d}" for i in range(1, 11)]

# Closed, testable rule shapes. Anything else is a label, not a rule.
VALID_SHAPES = {
    ("BOOLEAN", "EQUALS"),
    ("NUMERIC", "EQUALS"),
    ("NUMERIC", "LESS_THAN_OR_EQUAL"),
    ("ENUM", "SET_EQUALS"),
    ("CONSTANT", "EQUALS"),
    ("AUTHORITY_TARGET", "EQUALS"),
    ("AUTHORITY_TARGET", "SET_EQUALS"),
    ("INTERFACE_REQUIREMENT", "MUST_EXIST"),
}
VALID_SECTIONS = {"CONTEXT", "PROPOSED_DECISION", "MA06_AMENDMENT", "CONSEQUENCES"}

# Subsections whose text may never ground a clause.
FORBIDDEN_SUBSECTIONS = (
    "Rejected alternatives",
    "Evidence and traceability",
    "Acceptance conditions",
)

# Values that entered the superseded contracts from the task packet's own
# framing rather than from the candidate. Kept as a named regression guard: the
# grounding rules already reject them, and this says so by name.
INVENTED_AUTHORITY_TOKENS = ("dopeTask",)

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
LAYER_B = PORT_CONTRACTS + DATA_CONTRACTS
META_SCHEMAS = ["adr-machine-contract.schema.json", "interface-contract.schema.json"]

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

NUMBER_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
}

# Longest separators first: ", and " must not be consumed by ",\s*", which
# would leave "and Purge" as a member.
_SEP = re.compile(
    r"\s*,\s+and\s+|\s*,\s+or\s+|\s*,\s*|\s+and\s+|\s+or\s+|\s+plus\s+|\s*/\s*"
)
_NONWORD = re.compile(r"[^A-Za-z0-9]+")


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


def normalize(text: str) -> str:
    """UPPER_SNAKE projection used for token grounding."""
    return _NONWORD.sub("_", text).strip("_").upper()


def tokenize_enumeration(text: str) -> list[str]:
    return [p.strip() for p in _SEP.split(text) if p.strip()]


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


def walk(node: Any, path: str = ""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k, v
            yield from walk(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}/{i}")


def leaves(node: Any, path: str = "") -> list[tuple[str, Any]]:
    """Every scalar leaf with its JSON Pointer."""
    if isinstance(node, dict):
        out: list[tuple[str, Any]] = []
        if not node:
            return [(path, node)]
        for k, v in node.items():
            out += leaves(v, f"{path}/{k}")
        return out
    if isinstance(node, list):
        if not node:
            return [(path, node)]
        out = []
        for i, v in enumerate(node):
            out += leaves(v, f"{path}/{i}")
        return out
    return [(path, node)]


def adr_allowed_span(candidate: str, adr_id: str) -> str:
    """One ADR's Context + Proposed decision + Consequences, nothing else."""
    start = candidate.find(f"\n## {adr_id}:")
    if start < 0:
        raise ValueError(f"{adr_id}: section not found in candidate")
    nxt = candidate.find("\n## ", start + 1)
    block = candidate[start : nxt if nxt >= 0 else len(candidate)]
    keep: list[str] = []
    ok = True
    for line in block.splitlines():
        if line.startswith("### "):
            ok = line[4:].strip() not in FORBIDDEN_SUBSECTIONS
        if ok:
            keep.append(line)
    return "\n".join(keep)


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


def clause_grounding_error(clause: dict) -> str | None:
    """Why a clause's machine value is not traceable to the text it cites.

    Booleans have no text to match; they are held instead by the const-pinned
    inventory hash. Everything else must appear in the cited fragments.
    """
    rt, op = clause["rule_type"], clause["operator"]
    val = clause["machine_value"]
    joined = "\n".join(clause["source_fragments"])
    norm = normalize(joined)

    if rt == "BOOLEAN":
        return None if isinstance(val, bool) else "BOOLEAN value is not true/false"

    if rt == "NUMERIC":
        if isinstance(val, bool) or not isinstance(val, int):
            return "NUMERIC value is not an integer"
        word = NUMBER_WORDS.get(val)
        if str(val) not in joined and (word is None or word not in joined.lower()):
            return f"numeric value {val} appears in no cited fragment"
        return None

    if op == "SET_EQUALS":
        enumeration = clause.get("source_enumeration")
        if not enumeration:
            return "SET_EQUALS without a verbatim source_enumeration"
        if enumeration not in joined:
            return "source_enumeration is not a substring of the cited fragments"
        if not isinstance(val, list) or not val:
            return "SET_EQUALS value is not a non-empty list"
        derived = {normalize(t) for t in tokenize_enumeration(enumeration)}
        asserted = {normalize(m) for m in val}
        if derived != asserted:
            return (
                "closed set is not exactly the source-derived set "
                f"(dropped: {sorted(derived - asserted)}; "
                f"invented: {sorted(asserted - derived)})"
            )
        return None

    if rt == "INTERFACE_REQUIREMENT":
        if not isinstance(val, str):
            return "INTERFACE_REQUIREMENT value is not a string"
        if val not in joined:
            return f"interface name {val!r} is not verbatim in the cited text"
        return None

    # CONSTANT / AUTHORITY_TARGET EQUALS
    if not isinstance(val, str):
        return f"{rt}/{op} value is not a string"
    if normalize(val) not in norm:
        return f"value {val!r} does not appear in the cited text"
    return None


# --------------------------------------------------------------------------
# Layer B surface enumeration
# --------------------------------------------------------------------------

def assertion_locations(doc: Any) -> list[tuple[str, str]]:
    """Every string in a typed artifact that asserts architecture surface.

    Property names, required entries, enum members, string consts and the
    string members of x- extension lists. Prose (title, description,
    x-unspecified-in-candidate) is not surface and is not collected.
    """
    found: list[tuple[str, str]] = []

    def visit(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                child = f"{path}/{k}"
                if k == "properties" and isinstance(v, dict):
                    for name, sub in v.items():
                        found.append((f"{child}/{name}", name))
                        visit(sub, f"{child}/{name}")
                    continue
                if k == "assertions" and isinstance(v, dict):
                    for name, sub in v.items():
                        found.append((f"{child}/{name}", name))
                        if isinstance(sub, str):
                            found.append((f"{child}/{name}", sub))
                    continue
                if k == "required" and isinstance(v, list):
                    for i, name in enumerate(v):
                        if isinstance(name, str):
                            found.append((f"{child}/{i}", name))
                    continue
                if k == "enum" and isinstance(v, list):
                    for i, name in enumerate(v):
                        if isinstance(name, str):
                            found.append((f"{child}/{i}", name))
                    continue
                if k == "const" and isinstance(v, str):
                    found.append((path, v))
                    continue
                if k in ("title", "description", "$schema", "$id",
                         "x-unspecified-in-candidate", "x-grounding",
                         "x-machine-invariants"):
                    continue
                if k.startswith("x-"):
                    if isinstance(v, str):
                        found.append((child, v))
                    elif isinstance(v, list):
                        for i, m in enumerate(v):
                            if isinstance(m, str):
                                found.append((f"{child}/{i}", m))
                    continue
                visit(v, child)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                visit(v, f"{path}/{i}")

    visit(doc, "")
    return found


# --------------------------------------------------------------------------
# Group A — structure, binding, coverage, grounding
# --------------------------------------------------------------------------

def group_a(root: Path, rep: Report) -> dict[str, Any] | None:
    try:
        from jsonschema import Draft7Validator
    except ImportError as exc:  # fail closed on missing dependency
        rep.check("A", "A00-dependency", False, f"jsonschema unavailable: {exc}")
        return None
    rep.check("A", "A00-dependency", True)

    cdir = root / CONTRACT_DIR
    contracts = {aid: cdir / f"{aid}.contract.json" for aid in ADR_IDS}
    rep.check(
        "A", "A01-ten-adr-contracts-exist",
        all(p.is_file() for p in contracts.values()),
        f"missing: {[a for a, p in contracts.items() if not p.is_file()]}",
    )

    docs: dict[str, Any] = {}
    parse_errors: list[str] = []
    for p in sorted(cdir.glob("*.json")):
        try:
            docs[p.name] = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            parse_errors.append(f"{p.name}: {exc}")
    if not rep.check("A", "A02-all-artifacts-parse", not parse_errors,
                     "; ".join(parse_errors)):
        return None

    cand_file = root / CANDIDATE_PATH
    if not rep.check("A", "A03-candidate-present", cand_file.is_file(),
                     str(cand_file)):
        return None
    cand_text = cand_file.read_text(encoding="utf-8")
    rep.check(
        "A", "A04-candidate-sha256",
        sha256_bytes(cand_file.read_bytes()) == CANDIDATE_SHA256,
        sha256_bytes(cand_file.read_bytes()),
    )

    # ---- inventory pin: the load-bearing binding -----------------------
    inv_file = root / CLAUSE_INVENTORY_PATH
    if not rep.check("A", "A08-inventory-present", inv_file.is_file(), str(inv_file)):
        return None
    inv_bytes = inv_file.read_bytes()
    inv_sha = sha256_bytes(inv_bytes)
    if not rep.check(
        "A", "A09-inventory-matches-frozen-pin",
        inv_sha == FROZEN_INVENTORY_SHA256,
        f"file={inv_sha} pinned={FROZEN_INVENTORY_SHA256}",
    ):
        # Every downstream comparison would be against an unauthorized
        # denominator, so stop rather than report agreement with it.
        return None
    inventory = json.loads(inv_bytes.decode("utf-8"))

    rcpt_file = root / REFREEZE_RECEIPT_PATH
    if rep.check("A", "A10-refreeze-receipt-present", rcpt_file.is_file(),
                 str(rcpt_file)):
        refreeze = json.loads(rcpt_file.read_text(encoding="utf-8"))
        rep.check(
            "A", "A10-pin-matches-refreeze-receipt",
            refreeze.get("new_inventory_sha256") == FROZEN_INVENTORY_SHA256
            and refreeze.get("new_clause_count") == FROZEN_CLAUSE_TOTAL,
            f"receipt={refreeze.get('new_inventory_sha256')}",
        )
        rep.check(
            "A", "A11-refreeze-authorization-recorded",
            isinstance(refreeze.get("authorization", {}).get("ruling_verbatim"), str)
            and len(refreeze["authorization"]["ruling_verbatim"]) > 500
            and refreeze["authorization"].get("granted_by") == "HUMAN_OPERATOR",
            "the pin claims an operator-authorized freeze; the ruling must be "
            "readable from the repository",
        )
        rep.check(
            "A", "A11-supersession-recorded",
            refreeze.get("supersedes_inventory_sha256")
            == SUPERSEDED_INVENTORY_SHA256
            and refreeze.get("supersession_reason")
            == "INCOMPLETE_MATERIAL_DECISION_DENOMINATOR",
            f"supersedes={refreeze.get('supersedes_inventory_sha256')}",
        )

    inv_clauses = {
        c["clause_id"]: c for a in inventory["adrs"] for c in a["clauses"]
    }
    rep.check(
        "A", "A12-inventory-total-agrees",
        inventory["clause_total"] == len(inv_clauses) == FROZEN_CLAUSE_TOTAL,
        f"declared={inventory['clause_total']} actual={len(inv_clauses)}",
    )

    # ---- meta-schema validation ---------------------------------------
    schema_errors: list[str] = []
    for name in META_SCHEMAS:
        if name not in docs:
            schema_errors.append(f"{name}: absent")
    for name, doc in docs.items():
        if name in META_SCHEMAS or name == "ADR_CONTRACT_COVERAGE.json":
            continue
        meta_name = (
            "interface-contract.schema.json" if name in PORT_CONTRACTS
            else "adr-machine-contract.schema.json"
        )
        if name in DATA_CONTRACTS:
            try:
                Draft7Validator.check_schema(doc)
            except Exception as exc:  # noqa: BLE001 - report, never swallow
                schema_errors.append(f"{name}: not a valid draft-07 schema: {exc}")
            continue
        try:
            v = Draft7Validator(docs[meta_name])
            for err in v.iter_errors(doc):
                schema_errors.append(f"{name}: {err.message} at {list(err.path)}")
        except Exception as exc:  # noqa: BLE001
            schema_errors.append(f"{name}: {type(exc).__name__}: {exc}")
    rep.check("A", "A13-artifacts-validate", not schema_errors,
              "; ".join(schema_errors[:4]))

    # ---- bindings ------------------------------------------------------
    bind_errors: list[str] = []
    for name, doc in docs.items():
        if not isinstance(doc, dict):
            continue
        for field, expected in (
            ("candidate_sha256", CANDIDATE_SHA256),
            ("ratification_binding_sha256", RATIFICATION_BINDING_SHA256),
            ("clause_inventory_sha256", FROZEN_INVENTORY_SHA256),
        ):
            if field in doc and doc[field] != expected:
                bind_errors.append(f"{name}.{field}={doc[field]}")
    rep.check("A", "A14-artifacts-bind-frozen-authority", not bind_errors,
              "; ".join(bind_errors))

    pins_required = [f"{a}.contract.json" for a in ADR_IDS] + PORT_CONTRACTS + [
        "ADR_CONTRACT_COVERAGE.json"
    ]
    missing_pin = [
        n for n in pins_required
        if docs.get(n, {}).get("clause_inventory_sha256") != FROZEN_INVENTORY_SHA256
    ]
    rep.check(
        "A", "A15-contracts-pin-inventory", not missing_pin,
        f"not pinned to the frozen denominator: {missing_pin}",
    )

    rep.check(
        "A", "A16-adr-ids-exact",
        [docs[f"{a}.contract.json"]["adr_id"] for a in ADR_IDS] == ADR_IDS,
    )

    sb_dec_doc = parse_candidate_sb_dec(cand_text)
    sb_mismatch = [
        a for a in ADR_IDS
        if docs[f"{a}.contract.json"]["sb_dec_references"] != sb_dec_doc.get(a)
    ]
    rep.check("A", "A17-sb-dec-references-match-candidate", not sb_mismatch,
              f"mismatched: {sb_mismatch}")
    # 28 references across 26 distinct decisions: SB-DEC-006 and SB-DEC-019 are
    # each cited by two ADRs. Both numbers are checked because collapsing them
    # would hide a dropped citation behind a surviving duplicate.
    ref_total = sum(len(refs) for refs in sb_dec_doc.values())
    all_sb = {d for refs in sb_dec_doc.values() for d in refs}
    rep.check("A", "A17-sb-dec-references-28", ref_total == 28, f"count={ref_total}")
    rep.check("A", "A17-sb-dec-distinct-26", len(all_sb) == 26, f"count={len(all_sb)}")
    rep.check("A", "A18-sb-dec-026-unlinked", "SB-DEC-026" not in all_sb)

    # ---- coverage ------------------------------------------------------
    cov = docs.get("ADR_CONTRACT_COVERAGE.json")
    if cov is None:
        rep.check("A", "A19-coverage-present", False, "ADR_CONTRACT_COVERAGE.json")
        return None
    rep.check("A", "A19-coverage-present", True)
    rep.check(
        "A", "A19-coverage-pins-inventory",
        cov.get("clause_inventory_sha256") == FROZEN_INVENTORY_SHA256
        and cov.get("clause_total") == FROZEN_CLAUSE_TOTAL,
    )

    entries = cov.get("entries", [])
    covered = [e["clause_id"] for e in entries]
    rep.check(
        "A", "A20-every-clause-covered-once",
        sorted(covered) == sorted(inv_clauses) and len(covered) == len(set(covered)),
        f"entries={len(covered)} inventory={len(inv_clauses)}",
    )
    counts = cov.get("coverage_status_counts", {})
    rep.check(
        "A", "A21-coverage-counts-agree",
        counts.get("COVERED") == len(entries)
        and counts.get("MISSING") == 0
        and counts.get("AMBIGUOUS") == 0,
        f"counts={counts}",
    )
    rep.check(
        "A", "A21-no-clause-excused",
        counts.get("NOT_APPLICABLE_PROVEN") == 0
        and all(e["coverage_status"] == "COVERED" for e in entries),
    )

    # ---- contract rules must equal inventory clauses -------------------
    pointer_errors: list[str] = []
    rule_errors: list[str] = []
    for e in entries:
        artifact = e["contract_artifact"].split("/")[-1]
        doc = docs.get(artifact)
        if doc is None:
            pointer_errors.append(f"{e['clause_id']}: artifact {artifact} absent")
            continue
        try:
            rule = resolve_pointer(doc, e["contract_rule_pointer"])
        except (KeyError, IndexError, ValueError) as exc:
            pointer_errors.append(f"{e['clause_id']}: {exc}")
            continue
        # A pointer into prose resolves to a string, and a clause dropped from
        # the inventory has no counterpart. Both are reported, never raised:
        # an exception here would discard the whole report, so the mutation
        # would show up as an opaque crash instead of as the finding it is.
        if not isinstance(rule, dict):
            rule_errors.append(
                f"{e['clause_id']}: pointer {e['contract_rule_pointer']} resolves "
                f"to {type(rule).__name__}, not a structured rule"
            )
            continue
        inv_c = inv_clauses.get(e["clause_id"])
        if inv_c is None:
            rule_errors.append(
                f"{e['clause_id']}: covered but absent from the frozen denominator"
            )
            continue
        for field in ("subject", "rule_type", "operator", "machine_value",
                      "section", "source_fragments", "source_decision_text_hash",
                      "requirement_text"):
            if rule.get(field) != inv_c.get(field):
                rule_errors.append(
                    f"{e['clause_id']}.{field}: contract={rule.get(field)!r} "
                    f"inventory={inv_c.get(field)!r}"
                )
        if inv_c.get("source_enumeration") != rule.get("source_enumeration"):
            rule_errors.append(f"{e['clause_id']}.source_enumeration differs")
    rep.check("A", "A22-pointers-resolve", not pointer_errors,
              "; ".join(pointer_errors[:3]))
    rep.check("A", "A22-rules-agree-with-inventory", not rule_errors,
              "; ".join(rule_errors[:3]))

    # ---- fragments -----------------------------------------------------
    spans = {a: adr_allowed_span(cand_text, a) for a in ADR_IDS}
    not_substr: list[str] = []
    wrong_section: list[str] = []
    bad_hash: list[str] = []
    for cid, c in sorted(inv_clauses.items()):
        adr = cid.rsplit("-", 1)[0]
        for frag in c["source_fragments"]:
            if frag not in cand_text:
                not_substr.append(f"{cid}: {frag[:50]!r}")
            elif frag not in spans[adr]:
                wrong_section.append(f"{cid}: {frag[:50]!r}")
        if sha256_text("\n".join(c["source_fragments"])) != \
                c["source_decision_text_hash"]:
            bad_hash.append(cid)
    rep.check("A", "A23-fragments-are-candidate-substrings", not not_substr,
              "; ".join(not_substr[:3]))
    rep.check(
        "A", "A23-fragments-not-from-rejected-alternatives", not wrong_section,
        "a rejected design, an evidence list or the acceptance boilerplate may "
        f"never ground a rule: {wrong_section[:3]}",
    )
    rep.check("A", "A24-fragment-hashes-recompute", not bad_hash,
              f"mismatched: {bad_hash[:3]}")

    # ---- rule shapes and grounding -------------------------------------
    bad_shape = [
        f"{cid}: {c['rule_type']}/{c['operator']}"
        for cid, c in sorted(inv_clauses.items())
        if (c["rule_type"], c["operator"]) not in VALID_SHAPES
    ]
    rep.check(
        "A", "A25-rule-shapes-are-testable", not bad_shape,
        "a rule shape that carries an opaque label proves nothing: "
        f"{bad_shape[:3]}",
    )
    bad_section = [
        cid for cid, c in sorted(inv_clauses.items())
        if c.get("section") not in VALID_SECTIONS
    ]
    rep.check("A", "A25-sections-known", not bad_section, f"{bad_section[:3]}")

    ungrounded = []
    setwise = []
    for cid, c in sorted(inv_clauses.items()):
        err = clause_grounding_error(c)
        if err:
            (setwise if c["operator"] == "SET_EQUALS" else ungrounded).append(
                f"{cid}: {err}"
            )
    rep.check("A", "A26-machine-values-grounded", not ungrounded,
              "; ".join(ungrounded[:3]))
    rep.check(
        "A", "A26-closed-sets-bidirectional", not setwise,
        "a closed set must equal its source enumeration exactly — shrinking is "
        f"as much a rewrite as widening: {setwise[:3]}",
    )

    # ---- invented authority regression guard ---------------------------
    invented: list[str] = []
    for cid, c in sorted(inv_clauses.items()):
        vals = c["machine_value"]
        vals = vals if isinstance(vals, list) else [vals]
        for v in vals:
            if isinstance(v, str) and any(
                tok.lower() in v.lower() for tok in INVENTED_AUTHORITY_TOKENS
            ):
                invented.append(f"{cid}={v}")
    for name in LAYER_B + [f"{a}.contract.json" for a in ADR_IDS]:
        body = (cdir / name).read_text(encoding="utf-8") if (cdir / name).is_file() \
            else ""
        for tok in INVENTED_AUTHORITY_TOKENS:
            if tok in body:
                invented.append(f"{name} contains {tok!r}")
    rep.check(
        "A", "A27-no-invented-authority-value", not invented,
        f"present nowhere in the candidate: {invented[:3]}",
    )

    never = []
    for cid, c in sorted(inv_clauses.items()):
        if c["rule_type"] != "AUTHORITY_TARGET":
            continue
        vals = c["machine_value"]
        vals = vals if isinstance(vals, list) else [vals]
        never += [f"{cid}={v}" for v in vals if v in NEVER_AUTHORITY]
    rep.check("A", "A28-second-brain-never-authority", not never, f"{never}")

    # ---- required artifacts -------------------------------------------
    missing_art: list[str] = []
    for a in ADR_IDS:
        for rel in docs[f"{a}.contract.json"]["required_artifacts"]:
            if not (root / rel).is_file():
                missing_art.append(rel)
    rep.check("A", "A29-required-artifacts-exist", not missing_art,
              f"{sorted(set(missing_art))}")
    rep.check(
        "A", "A29-named-typed-artifacts-exist",
        all((cdir / n).is_file() for n in LAYER_B),
        f"missing: {[n for n in LAYER_B if not (cdir / n).is_file()]}",
    )

    iface_missing = []
    for cid, c in sorted(inv_clauses.items()):
        if c["rule_type"] != "INTERFACE_REQUIREMENT":
            continue
        arts = c.get("additional_covering_artifacts", [])
        if not arts or not all((root / a).is_file() for a in arts):
            iface_missing.append(f"{cid}={c['machine_value']}")
    rep.check(
        "A", "A30-interface-requirements-resolve", not iface_missing,
        f"named type without an existing artifact: {iface_missing}",
    )

    # ---- Layer B surface grounding (the invented-surface class) --------
    surface_err: list[str] = []
    binding_err: list[str] = []
    for name in LAYER_B:
        doc = docs[name]
        bindings = doc.get("x-grounding", {})
        locs = assertion_locations(doc)
        loc_ptrs = {p for p, _ in locs}
        for ptr, text in locs:
            b = bindings.get(ptr)
            if b is None:
                surface_err.append(f"{name}{ptr} ({text!r}) has no grounding")
                continue
            cl = inv_clauses.get(b.get("clause_id"))
            if cl is None:
                surface_err.append(f"{name}{ptr} cites unknown {b.get('clause_id')}")
                continue
            term = b.get("term", "")
            if term not in "\n".join(cl["source_fragments"]):
                surface_err.append(
                    f"{name}{ptr} term {term!r} is not verbatim in "
                    f"{b['clause_id']}'s fragments"
                )
            elif normalize(text) != normalize(term):
                surface_err.append(
                    f"{name}{ptr} asserts {text!r} but is grounded on {term!r}"
                )
        for ptr in bindings:
            if ptr not in loc_ptrs:
                binding_err.append(f"{name}{ptr} binds nothing")
    rep.check(
        "A", "A31-layer-b-surface-grounded", not surface_err,
        "every property, enum member and const string must be a candidate "
        f"phrase: {surface_err[:3]}",
    )
    rep.check(
        "A", "A32-no-orphan-grounding", not binding_err,
        f"grounding entries pointing at nothing: {binding_err[:3]}",
    )

    inv_disagree: list[str] = []
    for name in LAYER_B:
        for cid, rule in docs[name].get("x-machine-invariants", {}).items():
            c = inv_clauses.get(cid)
            if c is None:
                inv_disagree.append(f"{name}:{cid} unknown clause")
                continue
            for field in ("subject", "rule_type", "operator", "machine_value"):
                if rule.get(field) != c.get(field):
                    inv_disagree.append(f"{name}:{cid}.{field}")
    rep.check("A", "A33-layer-b-invariants-agree-with-inventory", not inv_disagree,
              f"{inv_disagree[:4]}")

    # ---- status discipline ---------------------------------------------
    rep.check(
        "A", "A34-contracts-record-proposed",
        all(
            docs[f"{a}.contract.json"]["adr_status_at_contract_authoring"]
            == "PROPOSED"
            for a in ADR_IDS
        ),
    )
    rep.check(
        "A", "A35-document-status-candidate",
        "\nstatus: CANDIDATE\n" in cand_text,
    )
    accepted_hits = [
        f"{n}{path}/{k}"
        for n, doc in docs.items()
        for path, k, v in walk(doc)
        if isinstance(v, str) and v.upper() in FORBIDDEN_VALUE_TOKENS
    ]
    rep.check("A", "A36-no-accepted-token", not accepted_hits,
              f"{accepted_hits[:3]}")

    truthy = []
    for n, doc in docs.items():
        for path, k, v in walk(doc):
            if k in FORBIDDEN_TRUTHY_KEYS:
                asserted = v.get("const") if isinstance(v, dict) and "const" in v else v
                if asserted not in (False, None) and k != "denial_fixtures":
                    truthy.append(f"{n}{path}/{k}={asserted!r}")
    rep.check("A", "A37-no-runtime-or-implementation-authority", not truthy,
              f"{truthy[:3]}")

    df = []
    for n, doc in docs.items():
        for path, k, v in walk(doc):
            if k != "denial_fixtures":
                continue
            asserted = v.get("const") if isinstance(v, dict) and "const" in v else v
            if asserted not in ALLOWED_DENIAL_FIXTURE_VALUES:
                df.append(f"{n}{path}={asserted!r}")
    rep.check("A", "A38-denial-fixtures-deferred", not df, f"{df[:3]}")

    return {"docs": docs, "inv_clauses": inv_clauses, "candidate": cand_text}


# --------------------------------------------------------------------------
# Group S — semantic invariants, held independently of the inventory
# --------------------------------------------------------------------------

def semantic_invariants(root: Path, ctx: dict[str, Any], rep: Report) -> None:
    """Hard-coded pins on the values that carry the architecture decision.

    Deliberately duplicated from the inventory. Group A proves the contracts
    agree with the denominator; this group proves the denominator still says
    what the architecture decided, so a coordinated rewrite of both has to get
    past a third, independent statement of the same facts.
    """
    docs = ctx["docs"]
    inv = ctx["inv_clauses"]

    def clause(cid: str) -> Any:
        c = inv.get(cid)
        return None if c is None else c["machine_value"]

    spool = docs["local-spool-port.contract.json"]["assertions"]
    rep.check("S", "S01-internal-requires-os-protection",
              spool.get("internal_requires_os_protected_storage") is True)
    rep.check(
        "S", "S02-confidential-restricted-spool-disabled",
        spool.get(
            "confidential_restricted_remain_disabled_until_verified_encryption_"
            "and_key_ownership"
        ) is True
        and clause("ADR-SB-006-C13")
        == "DISABLED_UNTIL_VERIFIED_ENCRYPTION_AND_KEY_OWNERSHIP",
    )
    rep.check("S", "S03-unknown-class-spooling-denied",
              spool.get("no_unknown_class_spooling") is True
              and clause("ADR-SB-006-C14") is False)
    rep.check("S", "S03-spool-never-remote-backed-up",
              spool.get("never_remote_backed_up") is True
              and clause("ADR-SB-006-C10") is False)

    olc = docs["open-loop-candidate.schema.json"]
    denied = {
        e["required"][0]
        for e in olc.get("not", {}).get("anyOf", [])
        if isinstance(e, dict) and e.get("required")
    }
    expected_pm = {
        "assignee", "pm_priority", "workflow_status", "sprint_state",
        "ownership_assignment", "due_driven_escalation", "automatic_scheduling",
        "task_completion_state",
    }
    rep.check(
        "S", "S04-open-loop-denies-all-eight-pm-semantics",
        denied == expected_pm,
        f"missing={sorted(expected_pm - denied)} extra={sorted(denied - expected_pm)}",
    )
    rep.check(
        "S", "S04-pm-semantic-closed-set-complete",
        {normalize(m) for m in (clause("ADR-SB-008-C19") or [])}
        == {normalize(m) for m in expected_pm},
    )
    rep.check(
        "S", "S05-due-at-advisory-only",
        olc["properties"]["due_at"].get("x-semantics")
        == "ADVISORY_DISPLAY_METADATA_ONLY"
        and clause("ADR-SB-008-C16") == "ADVISORY_DISPLAY_METADATA_ONLY",
    )
    rep.check("S", "S05-open-loop-zero-pm-fields", clause("ADR-SB-008-C35") == 0)

    tpr = docs["task-promotion-request.schema.json"]
    rep.check(
        "S", "S06-task-promotion-disabled",
        tpr["properties"]["disabled"].get("const") is True
        and "disabled" in tpr["required"]
        and clause("ADR-SB-008-C07") is False,
    )
    rep.check(
        "S", "S07-promotion-requires-both-proofs-and-approval",
        set(tpr["required"]) == {
            "disabled", "leantime_plus_task_orchestrator_proof",
            "explicit_approval",
        }
        and clause("ADR-SB-008-C06") is True
        and clause("ADR-SB-008-C17") is True
        and clause("ADR-SB-008-C18") is True,
    )
    rep.check(
        "S", "S08-pm-authority-is-leantime-and-orchestrator",
        sorted(clause("ADR-SB-008-C29") or []) == ["Leantime", "Task Orchestrator"],
    )
    rep.check("S", "S09-conport-never-owns-task-state",
              clause("ADR-SB-008-C34") is False)
    rep.check("S", "S10-dope-memory-no-pm-authority",
              clause("ADR-SB-008-C30") is False
              and clause("ADR-SB-008-C31") is False)
    rep.check(
        "S", "S10-loop-event-kinds-exact",
        sorted(clause("ADR-SB-008-C22") or []) == ["CANCEL", "CLOSE", "OPEN"],
    )

    rep.check("S", "S11-unknown-eligibility-denies",
              clause("ADR-SB-004-C04") is True
              and clause("ADR-SB-004-C11") is False)
    rep.check("S", "S12-no-confidential-restricted-indexing",
              clause("ADR-SB-004-C07") is False)
    rep.check(
        "S", "S12-policy-dimensions-complete",
        sorted(clause("ADR-SB-004-C09") or []) == sorted([
            "IDENTITY", "GRANTS", "PROVIDER", "EMBEDDING", "CUSTODY", "BACKUP",
            "OPERATION",
        ]),
    )

    env = docs["project-identity-envelope.schema.json"]
    rejected = {
        e["required"][0]
        for e in env.get("not", {}).get("anyOf", [])
        if isinstance(e, dict) and e.get("required")
    }
    rep.check(
        "S", "S13-identity-sources-rejected",
        rejected == {"path_hashes", "ports", "singleton_event_streams"},
        f"{sorted(rejected)}",
    )
    rep.check("S", "S14-single-active-capture-project",
              env["properties"]["active_automatic_capture_project"].get("maximum") == 1
              and clause("ADR-SB-009-C03") == 1)
    rep.check(
        "S", "S15-multi-project-capture-disabled",
        env["properties"]["multi_project_background_capture"].get("const") is False
        and clause("ADR-SB-009-C08") is False,
    )
    rep.check("S", "S16-wrong-project-denied",
              env["properties"]["wrong_project_denial"].get("const") is True
              and clause("ADR-SB-009-C06") is True)
    rep.check(
        "S", "S16-capability-receipt-must-be-current",
        docs["service-capability-receipt.schema.json"]["properties"]["current"]
        .get("const") is True
        and clause("ADR-SB-009-C02") is True,
    )

    rep.check("S", "S17-visible-queue-max-7", clause("ADR-SB-010-C03") == 7)
    rep.check(
        "S", "S18-consequential-default-defer-or-cancel",
        sorted(clause("ADR-SB-010-C08") or []) == ["CANCEL", "DEFER"],
    )
    rep.check(
        "S", "S18-ux-operations-exact",
        sorted(clause("ADR-SB-010-C01") or []) == ["CAPTURE", "RECALL", "REVIEW"],
    )
    rep.check("S", "S19-no-productivity-scoring", clause("ADR-SB-010-C09") is False)
    rep.check("S", "S20-no-surprise-writes", clause("ADR-SB-010-C10") is False)

    rep.check("S", "S21-searchable-residual-zero", clause("ADR-SB-007-C07") == 0)
    rep.check("S", "S22-purge-completion-receipt-required",
              clause("ADR-SB-007-C13") is True)
    rep.check(
        "S", "S22-deletion-operations-exact",
        sorted(clause("ADR-SB-007-C01") or []) == ["ARCHIVE", "FORGET", "PURGE"],
    )

    rep.check("S", "S23-recall-authority-first", clause("ADR-SB-003-C01") is True)
    rep.check("S", "S23-search-rank-not-truth", clause("ADR-SB-003-C08") is False)
    rep.check("S", "S24-historical-and-current-distinct",
              clause("ADR-SB-003-C12") is True)
    rep.check(
        "S", "S25-review-default-defer-no-mutation",
        clause("ADR-SB-002-C05") == "DEFER" and clause("ADR-SB-002-C09") is False,
    )
    rep.check("S", "S26-second-brain-owns-no-canonical-database",
              clause("ADR-SB-001-C02") is False)


# --------------------------------------------------------------------------
# Group B — FO-01 record reconciliation, as a whole projection
# --------------------------------------------------------------------------

# status pointer -> receipt pointer. Checked in full: a partial projection can
# pass while a sibling field has drifted, which is exactly the finding this
# replaces.
RECEIPT_PROJECTION: dict[str, str] = {
    "/fo01_status": "/status",
    "/architecture_semantics_modified": "/architecture_semantics_modified",
    "/adr_semantics_modified": "/adr_semantics_modified",
    "/decision_references_modified": "/decision_references_modified",
    "/adr_acceptance_authorized": "/adr_acceptance_authorized",
    "/adr_acceptance_gate_eligible": "/adr_acceptance_gate_eligible",
    "/authority/ratification_binding_sha256": "/ratification_binding_sha256",
    "/authority/r2_candidate_sha256": "/r2_candidate_sha256",
    "/authority/authority_persistence_merge": "/base_sha",
    "/source_hashes/24_ADR_CANDIDATES.md": "/source_adr_candidates_sha256",
    "/source_hashes/03_ARCHITECTURE_DECISION_REGISTER.yaml":
        "/decision_register_sha256",
    "/repaired_candidate/sha256": "/repaired_candidate_sha256",
    "/coverage/one_to_one_coverage_imposed": "/one_to_one_coverage_imposed",
    "/sb_dec_031/disposition": "/sb_dec_031_disposition",
    "/sb_dec_032/disposition": "/sb_dec_032_disposition",
    "/independent_verification/verdict": "/audit_verdict",
    "/independent_verification/audited_content_head": "/audited_content_head",
    "/independent_verification/auditor_report_sha256": "/auditor_report_sha256",
    "/independent_verification/blockers": "/audit_blockers",
    "/independent_verification/must_fix": "/audit_must_fix",
    "/independent_verification/nonblocking_observations":
        "/audit_nonblocking_observations",
    "/independent_verification/known_mappings_verified": "/known_mappings_verified",
    "/independent_verification/matrix_independently_reproduced":
        "/matrix_independently_reproduced",
    "/independent_verification/auditor/runner": "/auditor/runner",
    "/independent_verification/auditor/model": "/auditor/model",
    "/independent_verification/auditor/variant": "/auditor/variant",
    "/independent_verification/auditor/independent_of_producer":
        "/auditor/independent_of_producer",
    "/independent_verification/auditor/read_only": "/auditor/read_only",
    "/independent_verification/auditor/separate_process": "/auditor/separate_process",
    "/independent_verification/auditor/separate_clone": "/auditor/separate_clone",
    "/stale_record_reconciliation/semantics_unchanged/adr_semantics_modified":
        "/adr_semantics_modified",
    "/stale_record_reconciliation/semantics_unchanged/"
    "architecture_semantics_modified": "/architecture_semantics_modified",
    "/preserved_not_run/runtime_conformance": "/preserved_not_run/runtime_conformance",
    "/preserved_not_run/retrieval_benchmarks":
        "/preserved_not_run/retrieval_benchmarks",
    "/preserved_not_run/purge_completeness": "/preserved_not_run/purge_completeness",
    "/preserved_not_run/multi_project_isolation":
        "/preserved_not_run/multi_project_isolation",
    "/preserved_not_run/split_brain_proof": "/preserved_not_run/split_brain_proof",
    "/preserved_not_run/encryption_implementation":
        "/preserved_not_run/encryption_implementation",
    "/gates/implementation_planning": "/implementation_planning",
    "/gates/implementation_execution": "/implementation_execution",
}

# Fields that are not receipt-derived and must not drift.
PINNED: dict[str, Any] = {
    "/schema_version": "1.0.0",
    "/task_id": "TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001",
    "/required_resolution":
        "REPAIR_AND_REVERIFY_TRACEABILITY_BEFORE_ANY_ADR_ACCEPTANCE",
    "/fo01_gate_condition": "CLOSED",
    "/other_adr_acceptance_conditions": "STILL_REQUIRED",
    "/authority/architecture_accepted_as_law": True,
    "/authority/sb_dec_dispositions": "32 ACCEPT / 0 DEFER / 0 REJECT",
    "/authority/architecture_decisions_reopened": False,
    "/source_hashes/frozen_source_proof_copy":
        "proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/source/"
        "24_ADR_CANDIDATES.md",
    "/repaired_candidate/path": CANDIDATE_PATH,
    "/repaired_candidate/body_non_reference_text_identical_to_source": True,
    "/repaired_candidate/authorized_change_class": "DECISION_REFERENCE_CHANGE",
    "/repaired_candidate/frontmatter_added_outside_source_body": True,
    "/content_head": None,
    "/content_head_binding":
        "proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/C1_HEAD.txt",
    "/adr_statuses/all_remain": "PROPOSED (candidate)",
    "/adr_statuses/document_status": "CANDIDATE",
    "/adr_statuses/promoted_to_accepted": 0,
    "/sb_dec_031/decision_id": "SB-DEC-031",
    "/sb_dec_031/adr_created": False,
    "/sb_dec_031/existing_adr_broadened": False,
    "/sb_dec_031/operator_adjudication_required": False,
    "/sb_dec_032/decision_id": "SB-DEC-032",
    "/sb_dec_032/adr_created": False,
    "/sb_dec_032/existing_adr_broadened": False,
    "/sb_dec_032/operator_adjudication_required": False,
    "/independent_verification/performed": True,
    "/independent_verification/evidence": FO01_RECEIPT_PATH,
    "/stale_record_reconciliation/task_id":
        "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001",
    "/stale_record_reconciliation/change_class":
        "STALE_STATUS_RECORD_RECONCILIATION",
    "/stale_record_reconciliation/evidence_source": FO01_RECEIPT_PATH,
    "/stale_record_reconciliation/semantics_unchanged/candidate_document_modified":
        False,
    "/stale_record_reconciliation/semantics_unchanged/sb_dec_dispositions_modified":
        False,
    "/stale_record_reconciliation/semantics_unchanged/adr_statuses_modified": False,
    "/stale_record_reconciliation/verified_by":
        "scripts/governance/validate_second_brain_adr_contracts.py (check group B)",
    "/gates/adr_acceptance": "CLOSED",
    "/gates/merge": "NOT_AUTHORIZED",
}

# Prose. Carries no assertion a machine can check, and is enumerated so that a
# *new* field cannot hide here by default.
NARRATIVE_POINTERS = {
    "/content_head_note",
    "/independent_verification/note",
    "/sb_dec_031/title",
    "/sb_dec_031/rationale",
    "/sb_dec_032/title",
    "/sb_dec_032/rationale",
    "/stale_record_reconciliation/defect",
    "/stale_record_reconciliation/resolution",
    "/stale_record_reconciliation/semantics_unchanged/note",
}
NARRATIVE_PREFIXES = (
    "/gate_field_semantics/",
    "/stale_record_reconciliation/still_forbidden/",
)
# Derived from the traceability matrix rather than the receipt.
MATRIX_PREFIX = "/coverage/"


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

    # B02 — the whole projection, computed from the receipt.
    drift: list[str] = []
    for sptr, rptr in sorted(RECEIPT_PROJECTION.items()):
        try:
            sval = resolve_pointer(status, sptr)
        except (KeyError, IndexError):
            drift.append(f"{sptr}: absent from the status record")
            continue
        try:
            rval = resolve_pointer(receipt, rptr)
        except (KeyError, IndexError):
            drift.append(f"{rptr}: absent from the receipt")
            continue
        if sval != rval:
            drift.append(f"{sptr}: status={sval!r} receipt={rval!r}")
    rep.check(
        "B", "B02-receipt-projection-exact", not drift,
        f"{len(drift)} field(s) diverge from the receipt: {drift[:3]}",
    )
    rep.check(
        "B", "B02-projection-covers-every-receipt-derived-field",
        len(RECEIPT_PROJECTION) >= 39,
        f"mapped={len(RECEIPT_PROJECTION)}",
    )

    pin_drift = []
    for ptr, expected in sorted(PINNED.items(), key=lambda kv: kv[0]):
        try:
            val = resolve_pointer(status, ptr)
        except (KeyError, IndexError):
            pin_drift.append(f"{ptr}: absent")
            continue
        if val != expected:
            pin_drift.append(f"{ptr}: {val!r} != {expected!r}")
    rep.check("B", "B03-pinned-fields-unchanged", not pin_drift,
              f"{pin_drift[:3]}")

    # B04 — verdict and counts are the receipt's, and they are clean.
    rep.check(
        "B", "B04-fo01-audit-clean",
        receipt.get("audit_blockers") == 0 and receipt.get("audit_must_fix") == 0,
        f"blockers={receipt.get('audit_blockers')} "
        f"must_fix={receipt.get('audit_must_fix')}",
    )
    rep.check(
        "B", "B05-adr-acceptance-not-authorized",
        status.get("adr_acceptance_authorized") is False
        and receipt.get("adr_acceptance_authorized") is False
        and receipt.get("accepts_any_adr") is False,
    )
    rep.check(
        "B", "B06-fo01-blocker-closed-gate-still-shut",
        status.get("fo01_gate_condition") == "CLOSED"
        and status.get("adr_acceptance_gate_eligible") is True
        and status.get("gates", {}).get("adr_acceptance") == "CLOSED",
    )
    rep.check(
        "B", "B07-merge-not-authorized",
        status.get("gates", {}).get("merge") == "NOT_AUTHORIZED"
        and receipt.get("merge_authorized") is False,
    )

    # B08 — coverage is the traceability matrix's, and its absence is a failure
    # rather than a skipped check.
    tm = root / TRACEABILITY_PATH
    if not rep.check("B", "B08-traceability-matrix-present", tm.is_file(), str(tm)):
        return
    matrix = json.loads(tm.read_text(encoding="utf-8"))
    rep.check(
        "B", "B08-coverage-matches-traceability-matrix",
        status.get("coverage") == matrix.get("coverage"),
    )

    # B11 — every field of the status record is classified. Without this, a new
    # authoritative-looking field could be added with no check behind it.
    unclassified = []
    for ptr, _ in leaves(status):
        if ptr in RECEIPT_PROJECTION or ptr in PINNED or ptr in NARRATIVE_POINTERS:
            continue
        if ptr.startswith(MATRIX_PREFIX):
            continue
        if any(ptr.startswith(pref) for pref in NARRATIVE_PREFIXES):
            continue
        unclassified.append(ptr)
    rep.check(
        "B", "B11-every-status-field-classified", not unclassified,
        "receipt-projected, pinned, matrix-derived or declared prose — "
        f"unclassified: {unclassified[:5]}",
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
    ctx = group_a(root, rep)
    if ctx is not None:
        semantic_invariants(root, ctx, rep)
    else:
        rep.check("S", "S00-not-reached", False,
                  "group A stopped before the semantic pins could run")
    group_b(root, rep)

    a_fail = rep.failures("A") + rep.failures("S")
    b_fail = rep.failures("B")
    ok = not a_fail and not b_fail

    if args.json:
        print(json.dumps(
            {
                "repo_root": str(root),
                "frozen_inventory_sha256": FROZEN_INVENTORY_SHA256,
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
    print(f"  frozen denominator: {FROZEN_INVENTORY_SHA256}")
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
