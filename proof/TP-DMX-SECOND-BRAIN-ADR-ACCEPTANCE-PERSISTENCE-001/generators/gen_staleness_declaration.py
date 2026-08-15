#!/usr/bin/env python3
"""Derive the FO-01 staleness declaration over EVERY leaf of the status record.

Round 1 of the independent audit returned MUST_FIX: the first declaration named
three stale fields and presented that list as complete. It was not. The auditor
found `other_adr_acceptance_conditions` and the "ADR acceptance" element of
`stale_record_reconciliation.still_forbidden`.

A first repair enumerated the validator's PINNED table instead of hand-listing --
and still missed `still_forbidden`, because that path lives in NARRATIVE_PREFIXES,
not in PINNED. Enumerating one collection inside the validator is not the same as
enumerating the universe.

So the universe here is the status record itself: every leaf, plus the receipt
fields checks B05/B07 read. Two rules make an omission structurally hard rather
than merely unlikely:

  1. Every leaf must be classified. An unclassified leaf is a hard error.
  2. A leaf whose path or string value mentions acceptance may NOT be covered by a
     category default. It must carry an explicit, individually reasoned entry.

Rule 2 is the one that matters. Rule 1 alone would have let a category default
swallow the exact fields round 1 missed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

STATUS = Path("docs/03-reference/architecture/second-brain/adr-candidates/"
              "fo-01-repair-status.json")
RECEIPT = Path("proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/"
               "FO01_RESOLUTION_RECEIPT.json")
OUT = Path("proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001/"
           "FO01_STALENESS_DECLARATION.json")

STALE, OK = "STALE", "NOT_STALE"
ACCEPTANCE_TOKEN = re.compile(
    r"adr[_ ]acceptance|acceptance[_ ]condition|promoted_to_accepted|still_forbidden"
    r"|ADR acceptance|accepted", re.I)

# Explicit, individually reasoned. Every acceptance-touching leaf must appear here.
EXPLICIT: dict[str, tuple[str, str]] = {
    "/adr_acceptance_authorized": (STALE,
        "Reads false. Its own gloss says 'Only the human operator may authorize ADR "
        "acceptance.' The operator did so on 2026-08-14."),
    "/other_adr_acceptance_conditions": (STALE,
        "Reads STILL_REQUIRED. The other conditions are no longer outstanding: AC#1 met "
        "by four independent audits, AC#2 by the merged contract family, AC#3 "
        "structurally, AC#4 by the fresh MA-08. MISSED by the round-1 declaration."),
    "/gates/adr_acceptance": (STALE,
        "Reads CLOSED. Its gloss ties that to the other conditions being outstanding; "
        "they are not."),
    "/adr_statuses/promoted_to_accepted": (STALE,
        "Reads 0. Ten ADRs are now promoted to accepted under docs/90-adr/."),
    "/stale_record_reconciliation/still_forbidden/[0]": (STALE,
        "Reads 'ADR acceptance', which is no longer forbidden. Exactly this one element "
        "of the list is stale. MISSED by the round-1 declaration."),
    "/gate_field_semantics/gates.adr_acceptance": (STALE,
        "Prose, but it asserts the gate 'remains shut because the other acceptance "
        "conditions ... are still outstanding'. That assertion is now false. Prose that "
        "makes a checkable claim is not exempt from being stale."),
    "/gate_field_semantics/adr_acceptance_authorized": (STALE,
        "Prose. Its second sentence ('Only the human operator may authorize ADR "
        "acceptance') stays true; its first ('Unchanged and still false') does not."),

    "/adr_statuses/all_remain": (OK,
        "Reads 'PROPOSED (candidate)'. Scoped by its own parenthetical to the candidate "
        "document, where all ten do still read PROPOSED. Flagged as arguable: true of "
        "the candidate, false if read as a claim about the repository."),
    "/adr_statuses/document_status": (OK,
        "Reads CANDIDATE. The candidate is untouched; acceptance was persisted as new "
        "records rather than by promoting it."),
    "/adr_acceptance_gate_eligible": (OK, "FO-01 specifically is satisfied. Still true."),
    "/gate_field_semantics/adr_acceptance_gate_eligible": (OK,
        "Describes the deliberate scoping of eligibility versus authorization. Still true."),
    "/gate_field_semantics/fo01_gate_condition": (OK,
        "Describes the FO-01 blocker being closed. Unaffected by acceptance."),
    "/fo01_gate_condition": (OK, "FO-01 defect repaired. Still true."),
    "/required_resolution": (OK,
        "States what FO-01 required before any ADR acceptance. It was satisfied; the "
        "statement of the requirement stays true."),
    "/stale_record_reconciliation/still_forbidden/[1]": (OK, "Implementation execution is still forbidden."),
    "/stale_record_reconciliation/still_forbidden/[2]": (OK, "Runtime enablement is still forbidden."),
    "/stale_record_reconciliation/still_forbidden/[3]": (OK, "Merge authorization is still forbidden."),
    "/stale_record_reconciliation/semantics_unchanged/adr_statuses_modified": (OK,
        "Scoped to the CONTRACT-EVIDENCE-001 reconciliation, which modified no ADR "
        "status. This persistence modified none inside the candidate either."),
    "/authority/architecture_accepted_as_law": (OK,
        "Reads true, and refers to the 32 ratified SB-DEC architecture decisions being "
        "accepted as law -- not to the ten ADRs. Unchanged by ADR acceptance. Flagged by "
        "rule 2 on the word 'accepted' and reasoned individually rather than defaulted."),
    "/sb_dec_031/rationale": (OK,
        "Historical rationale for SB-DEC-031. It quotes every ADR's acceptance condition "
        "#3 ('No runtime, implementation, or production claim is inferred from "
        "acceptance'), which acceptance does not falsify -- it is precisely the condition "
        "the accepted records preserve on their face."),
    "/stale_record_reconciliation/defect": (OK,
        "Historical description of the FO-01 status/receipt disagreement that the "
        "CONTRACT-EVIDENCE-001 reconciliation fixed. A true account of a past defect, "
        "unaffected by ADR acceptance."),
    "/coverage/adrs_correct_as_written": (OK, "A traceability-coverage count. Unaffected."),
    "/independent_verification/verdict": (OK, "A historical FO-01 audit verdict."),
}

# Category defaults. May NOT cover an acceptance-touching leaf -- see rule 2.
CATEGORIES: list[tuple[str, str]] = [
    ("/gates/merge", "Merge is genuinely still NOT_AUTHORIZED."),
    ("/gates/implementation_", "Implementation planning/execution posture is unchanged by acceptance."),
    ("/preserved_not_run/", "Implementation-time gates, all still NOT_RUN or ABSENT."),
    ("/source_hashes/", "Content hashes of frozen historical sources."),
    ("/authority/", "Ratification authority facts, unchanged by ADR acceptance."),
    ("/repaired_candidate/", "Facts about the FO-01 repair of the candidate document."),
    ("/coverage/", "Traceability coverage counts from the FO-01 repair."),
    ("/sb_dec_031/", "SB-DEC-031 disposition, unchanged."),
    ("/sb_dec_032/", "SB-DEC-032 disposition, unchanged."),
    ("/independent_verification/", "Historical facts about the FO-01 independent verification."),
    ("/stale_record_reconciliation/", "Historical facts about the CONTRACT-EVIDENCE-001 reconciliation."),
    ("/content_head", "Content-head pointer/prose, unchanged."),
    ("/fo01_status", "The FO-01 repair status itself, unaffected by acceptance."),
    ("/schema_version", "Record metadata."),
    ("/task_id", "Record metadata."),
    ("/architecture_semantics_modified", "Unchanged by acceptance."),
    ("/adr_semantics_modified", "Unchanged by acceptance."),
    ("/decision_references_modified", "A fact about the FO-01 repair."),
]

ASSERTED = {
    ("FO01_RESOLUTION_RECEIPT.json", "/adr_acceptance_authorized"): (OK,
        "That receipt does not authorize ADR acceptance. Permanently true of it."),
    ("FO01_RESOLUTION_RECEIPT.json", "/accepts_any_adr"): (OK,
        "That receipt accepts no ADR. Permanently true of it."),
    ("FO01_RESOLUTION_RECEIPT.json", "/merge_authorized"): (OK, "Merge is still not authorized."),
}


def leaves(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, f"{p}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, f"{p}/[{i}]")
    else:
        yield p, o


def main() -> None:
    status = json.loads(STATUS.read_text())
    receipt = json.loads(RECEIPT.read_text())

    rows, unclassified, rule_covered_acceptance = [], [], []
    for path, value in leaves(status):
        touches = bool(ACCEPTANCE_TOKEN.search(path) or
                       (isinstance(value, str) and ACCEPTANCE_TOKEN.search(value)))
        if path in EXPLICIT:
            verdict, why = EXPLICIT[path]
            how = "EXPLICIT"
        else:
            hit = next((c for c in CATEGORIES if path.startswith(c[0])), None)
            if hit is None:
                unclassified.append(path)
                continue
            if touches:
                # Rule 2: an acceptance-touching leaf may not be rule-defaulted.
                rule_covered_acceptance.append(path)
                continue
            verdict, why, how = OK, hit[1], "CATEGORY"
        rows.append({"source": STATUS.name, "path": path, "observed_value": value,
                     "classification": verdict, "reason": why,
                     "classified_by": how, "touches_acceptance": touches})

    for (src, path), (verdict, why) in ASSERTED.items():
        cur = receipt
        for part in path.strip("/").split("/"):
            cur = cur.get(part, "<absent>") if isinstance(cur, dict) else "<absent>"
        rows.append({"source": src, "path": path, "observed_value": cur,
                     "classification": verdict, "reason": why,
                     "classified_by": "EXPLICIT", "touches_acceptance": True,
                     "asserted_by": "validator check group B (B05/B07)"})

    if unclassified:
        raise SystemExit(f"FAIL: unclassified leaves: {unclassified}")
    if rule_covered_acceptance:
        raise SystemExit("FAIL: acceptance-touching leaves covered only by a category "
                         f"default, which rule 2 forbids: {rule_covered_acceptance}")

    stale = [r for r in rows if r["classification"] == STALE]
    out = {
        "schema_version": "1.0.0",
        "record_kind": "FO01_STALENESS_DECLARATION",
        "task_id": "TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001",
        "supersedes": "the three-field staleness list in ADR_ACCEPTANCE_BINDING.json, "
                      "which the independent audit proved incomplete (MF-1)",
        "why_this_record_exists":
            "Persisting acceptance additively leaves fields in fo-01-repair-status.json "
            "describing a world that has changed. Naming them by hand produced an "
            "incomplete list presented as complete, which is the defect class this "
            "programme exists to prevent. This record derives the list instead.",
        "method": {
            "universe": "every leaf of fo-01-repair-status.json, plus the three receipt "
                        "fields validator checks B05 and B07 read directly",
            "rule_1": "every leaf must be classified; an unclassified leaf is a hard error",
            "rule_2": "a leaf whose path or string value mentions acceptance may not be "
                      "covered by a category default and must carry an explicit, "
                      "individually reasoned entry",
            "why_rule_2":
                "Rule 1 alone is insufficient. A first repair enumerated the validator's "
                "PINNED table and still missed still_forbidden, which lives in "
                "NARRATIVE_PREFIXES. Rule 2 is what makes the miss structurally hard "
                "rather than merely unlikely.",
        },
        "leaves_enumerated": len(rows),
        "status_file_leaf_total": len(list(leaves(status))),
        "unclassified": [],
        "acceptance_touching_leaves_rule_defaulted": [],
        "stale_count": len(stale),
        "stale_fields": [r["path"] for r in stale],
        "round_1_declared_stale_count": 3,
        "round_1_missed": [r["path"] for r in stale
                           if r["path"] not in ("/adr_acceptance_authorized",
                                                "/gates/adr_acceptance",
                                                "/adr_statuses/promoted_to_accepted")],
        "found_by": "independent audit round 1, grok-4.5, MF-1 (two of them); the "
                    "remaining two were found by this derivation and were missed by the "
                    "auditor as well",
        "fields": rows,
        "why_none_are_fixed_here":
            "Every stale field is validator-pinned, directly asserted by B05/B06/B07, or "
            "prose inside a record the validator requires to be an exact whole projection "
            "of a historical receipt belonging to another packet (B02). The status file "
            "cannot express post-acceptance state without falsifying its projection or "
            "rewriting audited history. Reconciling requires changing the validator "
            "invariant from 'no ADR is accepted' to 'acceptance matches the operator "
            "ledger' -- a separate packet with its own independent audit.",
        "follow_up_required": True,
        "follow_up_authorized": False,
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"leaves": out["status_file_leaf_total"],
                      "enumerated": len(rows),
                      "stale_count": len(stale),
                      "stale": out["stale_fields"],
                      "missed_by_round_1": out["round_1_missed"]}, indent=2))


if __name__ == "__main__":
    main()
