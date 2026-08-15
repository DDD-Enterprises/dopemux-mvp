#!/usr/bin/env python3
"""C0_REFREEZE — emit the replacement denominator and its supersession record.

Denominator artifacts only.  This generator writes nothing under
schemas/second_brain/contracts/ and touches no validator: the freeze must
precede the authoring it constrains, and git history is what proves that.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sb_census import ADRS, CANDIDATE_PATH, EXCLUSIONS, JUDGMENTS  # noqa: E402
from sb_ground import (  # noqa: E402
    ALLOWED_SECTIONS,
    adr_allowed_span,
    check_fragment,
    check_grounding,
    sha256_text,
)

def _repo_root() -> Path:
    """Locate the checkout from the environment or by walking up for .git.

    The archived copy of this generator lives inside the proof tree, so it must
    not carry the producing machine's absolute path.
    """
    env = os.environ.get("SB_REPO_ROOT")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists() or (parent / ".dopetaskroot").exists():
            return parent
    raise SystemExit("FAIL: cannot locate repository root; set SB_REPO_ROOT")


ROOT = _repo_root()
PROOF = ROOT / "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
OLD_INVENTORY_REL = (
    "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json"
)
RULING = Path(__file__).parent / "operator_ruling.txt"

OLD_FREEZE_COMMIT = "a9397e5630577ac5a2b0c8f89ad7d62d8ff7b296"
OLD_INVENTORY_SHA = (
    "f073ca28802e6b140dd5789d5fad5839962635f7b287cac589ec704efc663288"
)
RATIFICATION_SHA = (
    "a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c7539e2350ba07b34"
)

TASK_ID = "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"


def die(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    candidate = (ROOT / CANDIDATE_PATH).read_text(encoding="utf-8")
    candidate_sha = hashlib.sha256(
        (ROOT / CANDIDATE_PATH).read_bytes()
    ).hexdigest()

    errors: list[str] = []
    adr_records = []
    worksheet_rows = []
    total = 0

    for adr in ADRS:
        span = adr_allowed_span(candidate, adr.adr_id)
        clauses = []
        seen_suffix: set[str] = set()
        for cl in adr.clauses:
            cid = f"{adr.adr_id}-{cl.suffix}"
            if cl.suffix in seen_suffix:
                errors.append(f"{cid}: duplicate clause suffix")
            seen_suffix.add(cl.suffix)

            if cl.section not in ALLOWED_SECTIONS:
                errors.append(f"{cid}: unknown section {cl.section}")

            for frag in cl.fragments:
                err = check_fragment(frag, span, candidate)
                if err:
                    errors.append(f"{cid}: fragment {frag[:60]!r}... {err}")

            record = {
                "clause_id": cid,
                "requirement_text": cl.requirement_text,
                "subject": cl.subject,
                "rule_type": cl.rule_type,
                "operator": cl.operator,
                "machine_value": cl.machine_value,
                "section": cl.section,
                "source_fragments": list(cl.fragments),
                "source_decision_text_hash": sha256_text("\n".join(cl.fragments)),
            }
            if cl.source_enumeration is not None:
                record["source_enumeration"] = cl.source_enumeration
            if cl.covering:
                record["additional_covering_artifacts"] = list(cl.covering)

            err = check_grounding(record)
            if err:
                errors.append(f"{cid}: {err}")

            clauses.append(record)
            worksheet_rows.append(
                {
                    "adr_id": adr.adr_id,
                    "clause_id": cid,
                    "section": cl.section,
                    "disposition": "INCLUDED",
                    "requirement_text": cl.requirement_text,
                    "rule_shape": f"{cl.rule_type}/{cl.operator}",
                    "change_vs_superseded": cl.change,
                    "prior_clause_id": cl.prior_clause_id,
                }
            )
            total += 1

        adr_records.append(
            {
                "adr_id": adr.adr_id,
                "adr_title": adr.title,
                "sb_dec_references": list(adr.sb_dec),
                "clause_count": len(clauses),
                "clauses": clauses,
            }
        )

    if errors:
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        die(f"{len(errors)} census defect(s); nothing written")

    inventory = {
        "schema_version": "2.0.0",
        "task_id": TASK_ID,
        "step": "C0_REFREEZE",
        "purpose": (
            "Frozen coverage denominator, second freeze. Produced by a fresh "
            "exhaustive census of the ratified candidate under the operator "
            "ruling of 2026-08-12, which authorized superseding the first "
            "freeze after an independent audit proved it materially "
            "incomplete. Frozen before any contract artifact was re-authored; "
            "the producer may not redefine it later."
        ),
        "denominator_authority": "OPERATOR_AUTHORIZED_CANDIDATE_CENSUS_2026_08_12",
        "denominator_authority_note": (
            "The superseded inventory named "
            "TASK_PACKET_SECTION_5_MANDATORY_COVERAGE as its authority. That is "
            "the root cause of audit BLOCKER 2: the packet's own framing is not "
            "the audited authority, and an authority value ('dopeTask') that "
            "appears nowhere in the candidate entered the denominator through "
            "it. Only the ratified candidate document is authority here."
        ),
        "candidate_document": CANDIDATE_PATH,
        "candidate_sha256": candidate_sha,
        "ratification_binding_sha256": RATIFICATION_SHA,
        "adr_count": len(adr_records),
        "clause_total": total,
        "supersedes": {
            "inventory_sha256": OLD_INVENTORY_SHA,
            "clause_total": 97,
            "status": "SUPERSEDED_INCOMPLETE_DENOMINATOR",
        },
        "fragment_binding_rule": (
            "Every source_fragment MUST be an exact substring of the candidate "
            "document at candidate_sha256, and MUST fall inside its own ADR's "
            "Context / Proposed decision / Consequences span. Text under "
            "'Rejected alternatives', 'Evidence and traceability' or "
            "'Acceptance conditions' may never ground a clause. "
            "source_decision_text_hash = sha256(newline-joined fragments)."
        ),
        "rule_shape_rule": (
            "Every clause carries a testable shape. BOOLEAN/EQUALS asserts a "
            "predicate; NUMERIC asserts a bound; ENUM and AUTHORITY_TARGET "
            "SET_EQUALS assert a closed set that must equal the set "
            "deterministically tokenized from a verbatim source_enumeration; "
            "CONSTANT and AUTHORITY_TARGET EQUALS assert a value whose "
            "normalized form must appear in the cited text; "
            "INTERFACE_REQUIREMENT names a type the candidate names verbatim. "
            "No shape can carry an opaque label, which is what made the "
            "superseded REQUIRE/MUST_EXIST token rules unfalsifiable."
        ),
        "boolean_grounding_note": (
            "A boolean has no text to match. Booleans are protected instead by "
            "the const-pinned inventory sha256 inside the validator: after this "
            "freeze, any edit to a clause value changes the inventory hash and "
            "fails, and because the contract must agree with the inventory, "
            "editing both sides together fails too."
        ),
        "adrs": adr_records,
    }

    inv_bytes = json.dumps(inventory, indent=2, ensure_ascii=False).encode() + b"\n"
    new_sha = hashlib.sha256(inv_bytes).hexdigest()

    # ---- supersession diff --------------------------------------------
    # Read the superseded denominator from git, not the worktree: this
    # generator overwrites that path, so a worktree read would compare the
    # new inventory against itself on any re-run.
    old_raw = subprocess.run(
        ["git", "show", f"{OLD_FREEZE_COMMIT}:{OLD_INVENTORY_REL}"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    if hashlib.sha256(old_raw.encode()).hexdigest() != OLD_INVENTORY_SHA:
        die(
            "superseded inventory read from git does not match the sha256 the "
            "operator ruling names; refusing to write a supersession record "
            "against an unverified predecessor"
        )
    old = json.loads(old_raw)
    old_by_id = {
        c["clause_id"]: c for a in old["adrs"] for c in a["clauses"]
    }
    new_by_id = {
        c["clause_id"]: c for a in adr_records for c in a["clauses"]
    }
    prior_map = {
        f"{adr.adr_id}-{cl.suffix}": cl.prior_clause_id
        for adr in ADRS
        for cl in adr.clauses
    }
    claimed_priors = {v for v in prior_map.values() if v}

    added = sorted(cid for cid, p in prior_map.items() if p is None)
    removed = sorted(set(old_by_id) - claimed_priors)
    modified = []
    unchanged = []
    for cid, prior in sorted(prior_map.items()):
        if prior is None:
            continue
        o, n = old_by_id[prior], new_by_id[cid]
        same = all(
            o.get(k) == n.get(k)
            for k in ("subject", "rule_type", "operator", "machine_value")
        )
        entry = {
            "clause_id": cid,
            "prior_clause_id": prior,
            "prior": {
                k: o.get(k)
                for k in ("subject", "rule_type", "operator", "machine_value")
            },
            "current": {
                k: n.get(k)
                for k in ("subject", "rule_type", "operator", "machine_value")
            },
        }
        (unchanged if same else modified).append(entry)

    worksheet = {
        "schema_version": "1.0.0",
        "task_id": TASK_ID,
        "purpose": (
            "Per-unit disposition of the candidate document. Every normative "
            "unit is either mapped to clause IDs or excluded with the "
            "operator's DO-NOT-INCLUDE reason. An asserted census invites the "
            "same completeness finding twice; this is the checkable form."
        ),
        "candidate_sha256": candidate_sha,
        "included_total": total,
        "included": worksheet_rows,
        "excluded": EXCLUSIONS,
        "judgment_calls": JUDGMENTS,
    }

    receipt = {
        "schema_version": "1.0.0",
        "task_id": TASK_ID,
        "record_kind": "DENOMINATOR_REFREEZE_RECEIPT",
        "supersedes_freeze_commit": OLD_FREEZE_COMMIT,
        "supersedes_inventory_sha256": OLD_INVENTORY_SHA,
        "supersedes_clause_total": 97,
        "supersession_reason": "INCOMPLETE_MATERIAL_DECISION_DENOMINATOR",
        "supersession_evidence": (
            "Independent audit of frozen head 7955ef33d7 returned FAIL with 3 "
            "blockers and 5 must-fix findings. MUST_FIX 1 established that the "
            "denominator, derived from the task packet's §5 minimum, omitted "
            "material decision content. BLOCKER 2 established that 'dopeTask' "
            "entered the authority set from the packet rather than the "
            "candidate."
        ),
        "old_freeze_disposition": (
            "The superseded freeze remains in history and is NOT described as "
            "valid in hindsight. It is the historical denominator that the "
            "first independent audit proved incomplete."
        ),
        "candidate_document": CANDIDATE_PATH,
        "candidate_sha256": candidate_sha,
        "ratification_binding_sha256": RATIFICATION_SHA,
        "new_inventory_path": (
            "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/"
            "ADR_CLAUSE_INVENTORY.json"
        ),
        "new_inventory_sha256": new_sha,
        "new_clause_count": total,
        "added_clause_ids": added,
        "removed_clause_ids": removed,
        "modified_clauses": modified,
        "unchanged_clauses": [e["clause_id"] for e in unchanged],
        "removal_note": (
            "removed_clause_ids is empty because every superseded requirement "
            "still has a home. The invented content the audit identified was "
            "removed at value level, not by deleting the requirement that "
            "carried it, and each such change is recorded in modified_clauses "
            "with its prior and current value. The clearest cases: "
            "ADR-SB-003-C01 kept 'authority-first fusion' but dropped the "
            "invented four-way total ordering (MUST_FIX 3); ADR-SB-001-C03 and "
            "ADR-SB-002-C06 dropped the 'dopeTask' authority member (BLOCKER 2); "
            "ADR-SB-009-C07 dropped CURRENT_DIRECTORY, which was grounded only "
            "in a rejected alternative; ADR-SB-006-C04 narrowed "
            "'classification' to the candidate's own word 'class'. Two clauses "
            "were split rather than widened: ADR-SB-007-C08 into C08 + C12, and "
            "ADR-SB-008-C06 into C06 + C17 + C18."
        ),
        "counts": {
            "added": len(added),
            "removed": len(removed),
            "modified": len(modified),
            "unchanged": len(unchanged),
        },
        "operator_mandated_additions_present": {},
        "architecture_semantics_changed": False,
        "adr_dispositions_changed": False,
        "implementation_execution": "NOT_AUTHORIZED",
        "authorization": {
            "granted_by": "HUMAN_OPERATOR",
            "granted_at_session": "2026-08-12",
            "channel": "direct operator instruction in the producing session",
            "verification_class": "OPERATOR_INSTRUCTION_RECORDED_IN_REPOSITORY",
            "verification_note": (
                "The ruling was delivered in-session and is reproduced verbatim "
                "below so that the const-pinned inventory hash in the validator "
                "has an on-repository authorization record an auditor can read. "
                "The transcript itself is off-repository and unverifiable from "
                "these bytes."
            ),
            "ruling_verbatim": RULING.read_text(encoding="utf-8"),
            "ruling_sha256": sha256_text(RULING.read_text(encoding="utf-8")),
        },
    }

    # The five omissions the operator named by hand must be demonstrably present.
    mandated = {
        "ADR-SB-003 historical/current distinct":
            "second_brain.recall.historical_and_current_state_distinct",
        "ADR-SB-004 policy evaluation dimensions":
            "second_brain.policy.evaluation.dimensions",
        "ADR-SB-007 purge completion receipt":
            "second_brain.purge.completion_receipt.required",
        "ADR-SB-008 ConPort never owns task state":
            "conport.owns_task_state",
        "ADR-SB-008 Dope-Memory no PM authority":
            "dope_memory.pm_authority",
        "ADR-SB-008 confirmed loop event kinds":
            "second_brain.open_loop.confirmed_event.kinds",
    }
    subjects = {c["subject"]: c["clause_id"] for c in new_by_id.values()}
    for label, subject in mandated.items():
        if subject not in subjects:
            die(f"operator-mandated addition missing: {label} ({subject})")
        receipt["operator_mandated_additions_present"][label] = subjects[subject]

    PROOF.mkdir(parents=True, exist_ok=True)
    (PROOF / "ADR_CLAUSE_INVENTORY.json").write_bytes(inv_bytes)
    (PROOF / "DENOMINATOR_CENSUS_WORKSHEET.json").write_text(
        json.dumps(worksheet, indent=2, ensure_ascii=False) + "\n"
    )
    (PROOF / "DENOMINATOR_REFREEZE_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"clause_total       {total}  (was 97)")
    print(f"new_inventory_sha  {new_sha}")
    print(
        f"added {len(added)}  removed {len(removed)}  "
        f"modified {len(modified)}  unchanged {len(unchanged)}"
    )
    for adr in adr_records:
        print(f"  {adr['adr_id']}  {adr['clause_count']:>3}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:  # fail closed
        print(f"FAIL: unhandled {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
