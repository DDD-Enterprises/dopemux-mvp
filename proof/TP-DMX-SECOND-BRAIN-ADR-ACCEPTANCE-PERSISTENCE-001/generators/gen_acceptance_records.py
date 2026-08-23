#!/usr/bin/env python3
"""Append the ten accepted ADRs to the index and emit the acceptance records.

Deterministic and idempotent: re-running produces byte-identical output and never
double-appends an index row. Run from the repository root after
gen_accepted_adrs.py.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

P = Path("proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001")
INDEX = Path("docs/90-adr/adr-index.md")
CANDIDATE = Path("docs/03-reference/architecture/second-brain/adr-candidates/"
                 "second-brain-adr-candidates.md")
HEAD_JSON = Path("docs/03-reference/architecture/second-brain/adr-candidates/"
                 "ADR_ACCEPTANCE_HEAD.json")

CANDIDATE_SHA256 = "e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c"
RATIFICATION_BINDING_SHA256 = ("a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c"
                               "7539e2350ba07b34")
FROZEN_INVENTORY_SHA256 = ("b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dc"
                           "d58af7f78a439")
MA08_MAIN_SHA = "75b4cfc581786a53445e412bfc8e25a6e0fdb978"
DATE = "2026-08-14"

# One-line purposes, each a compression of that ADR's own Proposed decision. They
# are index prose, not authority; the ADR file carries the byte-slice.
PURPOSE = {
    "ADR-SB-001": "Second Brain is a PCP/DCP-compatible extension owning control logic, derived read models, projections, spool and purge coordination, and receipts only; canonical writes go to existing authorities.",
    "ADR-SB-002": "Append captures and candidates to Dope-Memory, review through a non-canonical read model, require digest-bound affirmative review, and route approved actions to exact canonical targets.",
    "ADR-SB-003": "Deterministic authority-first recall fusion with pre-model policy filtering, freshness and contradiction detection, and evidence, access and uncertainty metadata on every response.",
    "ADR-SB-004": "Separate domain and classification dimensions, evaluate identity, grants, provider, embedding, custody, backup and operation policy before disclosure, and deny on unknown.",
    "ADR-SB-005": "Compile deterministic Markdown from canonical snapshot revisions with stable paths, managed and manual regions, visible freshness, purge propagation, and no silent write-back.",
    "ADR-SB-006": "Define LocalSpoolPort and CustodyPort; spool records are non-canonical, scoped, integrity-protected, short-lived, purge-aware and never remotely backed up.",
    "ADR-SB-007": "Model Archive, Forget and Purge separately with dependency graph, impact preview, explicit approval, per-surface receipts, residual scan and zero searchable residual before success.",
    "ADR-SB-008": "Represent detected loops as suggested candidates carrying no PM semantics; task proposals are separate candidates and task creation stays disabled behind Leantime plus Task Orchestrator proof.",
    "ADR-SB-009": "Require registry-backed identity envelopes and current capability receipts for authority operations, one active automatic-capture project, writer epochs and wrong-project denial.",
    "ADR-SB-010": "Capture, Recall, Review with one dominant next action, at most seven visible queue items, answer-first recall, session-end batching, and DEFER or CANCEL as consequential defaults.",
}
RELATED = "Second Brain architecture authority, SB-DEC ratified decision register, machine contracts"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    text = CANDIDATE.read_text(encoding="utf-8")
    assert sha(CANDIDATE) == CANDIDATE_SHA256, "candidate moved"
    heads = list(re.finditer(r"^## (ADR-SB-(\d{3})): (.+)$", text, re.M))
    assert len(heads) == 10

    adrs = []
    for m in heads:
        adr_id, num, title = m.group(1), m.group(2), m.group(3).strip()
        matches = sorted(Path("docs/90-adr").glob(f"adr-sb-{num}-*.md"))
        assert len(matches) == 1, f"{adr_id}: expected one file, found {matches}"
        f = matches[0]
        body = f.read_text(encoding="utf-8")
        assert "\nstatus: accepted\n" in body, f"{adr_id} not accepted"
        adrs.append({
            "adr_id": adr_id,
            "title": title,
            "path": f.as_posix(),
            "sha256": sha(f),
            "machine_contract": f"schemas/second_brain/contracts/{adr_id}.contract.json",
            "operator_disposition": "ACCEPT",
        })

    # ---- index rows, appended in ADR order, never duplicated -----------
    idx = INDEX.read_text(encoding="utf-8")
    added = 0
    for a in adrs:
        name = Path(a["path"]).name
        if f"({name})" in idx:
            continue
        row = (f"| [{name}]({name}) | {a['adr_id']}: {a['title']} | Accepted | "
               f"{PURPOSE[a['adr_id']]} | {RELATED} |\n")
        idx = idx.rstrip("\n") + "\n" + row
        added += 1
    INDEX.write_text(idx, encoding="utf-8")

    # ---- acceptance head, in adr-candidates per 19fa74faa9 precedent ---
    head = {
        "schema_version": "1.0.0",
        "record_kind": "ADR_ACCEPTANCE_HEAD",
        "task_id": "TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001",
        "acceptance_date": DATE,
        "authority": "HUMAN_OPERATOR_EXPLICIT",
        "accepted_adr_count": 10,
        "candidate_document": CANDIDATE.as_posix(),
        "candidate_sha256": CANDIDATE_SHA256,
        "candidate_document_status": "CANDIDATE",
        "candidate_document_modified_by_acceptance": False,
        "candidate_document_note": (
            "The candidate remains a candidate and is untouched. Acceptance is "
            "persisted as ten NEW accepted records under docs/90-adr/, not by "
            "promoting the candidate. The candidate is frozen authority pinned by "
            "sha256 in the validator and in all ten machine contracts."),
        "ratification_binding_sha256": RATIFICATION_BINDING_SHA256,
        "clause_inventory_sha256": FROZEN_INVENTORY_SHA256,
        "ma08_main_sha": MA08_MAIN_SHA,
        "adrs": adrs,
        "confers": [],
        "confers_note": (
            "Acceptance confers architecture-record status only. It confers no "
            "implementation, runtime, production or enablement authority."),
        "implementation_execution": "NOT_AUTHORIZED",
        "runtime_enablement": "NOT_AUTHORIZED",
        "denial_fixtures": "NOT_IMPLEMENTED",
    }
    HEAD_JSON.write_text(json.dumps(head, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "index_rows_added": added,
        "index_total_rows": idx.count("\n| ["),
        "accepted": [a["adr_id"] for a in adrs],
        "acceptance_head": HEAD_JSON.as_posix(),
    }, indent=2))


if __name__ == "__main__":
    main()
