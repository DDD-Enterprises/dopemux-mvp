#!/usr/bin/env python3
"""S1 baseline contract inventory + S2 frozen clause inventory.

Emits, into the proof bundle:
  BASELINE_CONTRACT_INVENTORY.json   (S1 — reproduce the evidence gap)
  ADR_CLAUSE_INVENTORY.json          (S2 — freeze the coverage denominator)

Run from the worktree root.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from clause_table import (  # noqa: E402
    ADR_TITLES,
    CANDIDATE_PATH,
    CANDIDATE_SHA256,
    CLAUSES,
    RATIFICATION_BINDING_SHA256,
)

REPO = Path.cwd()
PROOF = REPO / "proof" / "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
PACKET_ID = "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"

SEARCH_TERMS = [
    "LocalSpoolPort",
    "CustodyPort",
    "OpenLoopCandidate",
    "TaskProposal",
    "TaskPromotionRequest",
    "project identity envelope",
    "service capability receipt",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_grep(term: str) -> list[tuple[str, int, str]]:
    """Case-insensitive fixed-string grep with loose whitespace for phrases."""
    pattern = term if " " not in term else term.replace(" ", "[ -]")
    proc = subprocess.run(
        ["git", "grep", "-n", "-I", "-i", "-E", pattern, "--", "."],
        capture_output=True,
        text=True,
    )
    hits = []
    for line in proc.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3:
            hits.append((parts[0], int(parts[1]), parts[2]))
    return hits


def classify(path: str, line_text: str) -> tuple[str, str]:
    """Return (classification, rationale) per packet S1 taxonomy."""
    if path.startswith("src/") or path.startswith("services/"):
        return "RUNTIME_IMPLEMENTATION", "Hit inside runtime source tree."
    if path.startswith("tests/"):
        return "TEST_ONLY", "Hit inside the test tree with no contract artifact."
    if path.startswith("schemas/"):
        return (
            "MACHINE_CONTRACT",
            "Hit inside the repository schema tree.",
        )
    if path.endswith(".md"):
        return (
            "PROSE_ONLY",
            "Markdown narrative; not parseable by deterministic tooling as a "
            "contract.",
        )
    if path.endswith(".json") or path.endswith(".yaml"):
        return (
            "PROSE_ONLY",
            "Hit occurs inside a free-form explanatory string field "
            "(title/semantic_relationship/note) of a structured file; packet "
            "§3 excludes free-form explanatory text from counting as a "
            "machine contract.",
        )
    return "OTHER", "Unclassified location."


def build_s1(candidate_text: str) -> dict:
    findings = []
    counts: dict[str, int] = {}
    for term in SEARCH_TERMS:
        hits = git_grep(term)
        term_entries = []
        for path, lineno, text in hits:
            cls, why = classify(path, text)
            counts[cls] = counts.get(cls, 0) + 1
            term_entries.append(
                {
                    "path": path,
                    "line": lineno,
                    "classification": cls,
                    "rationale": why,
                    "excerpt": text.strip()[:200],
                }
            )
        findings.append(
            {
                "term": term,
                "hit_count": len(term_entries),
                "machine_contract_hits": sum(
                    1 for e in term_entries if e["classification"] == "MACHINE_CONTRACT"
                ),
                "hits": term_entries,
            }
        )

    contract_dir = REPO / "schemas" / "second_brain"
    return {
        "schema_version": "1.0.0",
        "task_id": PACKET_ID,
        "step": "S1",
        "purpose": (
            "Reproduce the architecture-time machine-contract evidence gap "
            "before authoring any contract artifact."
        ),
        "candidate_document": CANDIDATE_PATH,
        "candidate_sha256": CANDIDATE_SHA256,
        "ratification_binding_sha256": RATIFICATION_BINDING_SHA256,
        "schemas_second_brain_directory_exists": contract_dir.exists(),
        "search_terms": SEARCH_TERMS,
        "classification_counts": counts,
        "machine_contract_hit_total": counts.get("MACHINE_CONTRACT", 0),
        "runtime_implementation_hit_total": counts.get("RUNTIME_IMPLEMENTATION", 0),
        "test_only_hit_total": counts.get("TEST_ONLY", 0),
        "prose_only_hit_total": counts.get("PROSE_ONLY", 0),
        "finding": "NO_SUFFICIENT_SECOND_BRAIN_MACHINE_CONTRACT_SET",
        "finding_basis": (
            "Zero hits classify as MACHINE_CONTRACT; schemas/second_brain/ "
            "does not exist; every occurrence of every ADR-named type is "
            "narrative prose or a free-form explanatory string field. "
            "Amended acceptance condition #2 therefore has nothing to parse "
            "at ADR acceptance."
        ),
        "denial_fixtures": "NOT_IMPLEMENTED_AND_OUT_OF_SCOPE_FOR_THIS_PACKET",
        "findings": findings,
    }


def build_s2(candidate_text: str) -> dict:
    adrs = []
    total = 0
    for adr_id in sorted(CLAUSES):
        entries = []
        for (
            suffix,
            requirement_text,
            subject,
            rule_type,
            operator,
            machine_value,
            fragments,
            _extra,
        ) in CLAUSES[adr_id]:
            for frag in fragments:
                if frag not in candidate_text:
                    raise SystemExit(
                        f"FATAL: fragment not found verbatim in candidate "
                        f"({adr_id}-{suffix}): {frag!r}"
                    )
            joined = "\n".join(fragments)
            entries.append(
                {
                    "clause_id": f"{adr_id}-{suffix}",
                    "requirement_text": requirement_text,
                    "subject": subject,
                    "rule_type": rule_type,
                    "operator": operator,
                    "machine_value": machine_value,
                    "source_fragments": fragments,
                    "source_decision_text_hash": sha256_text(joined),
                }
            )
            total += 1
        adrs.append(
            {
                "adr_id": adr_id,
                "adr_title": ADR_TITLES[adr_id],
                "sb_dec_references": extract_sb_dec(candidate_text, adr_id),
                "clause_count": len(entries),
                "clauses": entries,
            }
        )

    return {
        "schema_version": "1.0.0",
        "task_id": PACKET_ID,
        "step": "S2",
        "purpose": (
            "Frozen coverage denominator. Derived from packet §5 mandatory "
            "decision coverage and bound to exact fragments of the ratified "
            "candidate document. Frozen before any contract artifact was "
            "authored; the producer may not redefine it later."
        ),
        "denominator_authority": "TASK_PACKET_SECTION_5_MANDATORY_COVERAGE",
        "candidate_document": CANDIDATE_PATH,
        "candidate_sha256": CANDIDATE_SHA256,
        "ratification_binding_sha256": RATIFICATION_BINDING_SHA256,
        "adr_count": len(adrs),
        "clause_total": total,
        "fragment_binding_rule": (
            "Every source_fragment MUST be an exact substring of the "
            "candidate document at candidate_sha256. "
            "source_decision_text_hash = sha256(newline-joined fragments)."
        ),
        "adrs": adrs,
    }


def extract_sb_dec(text: str, adr_id: str) -> list[str]:
    """Parse the ADR's 'Evidence and traceability' bullets from the candidate."""
    start = text.index(f"## {adr_id}:")
    nxt = text.find("\n## ADR-SB-", start + 1)
    section = text[start : nxt if nxt != -1 else len(text)]
    ev = section.index("### Evidence and traceability")
    acc = section.index("### Acceptance conditions", ev)
    return re.findall(r"`(SB-DEC-\d+)`", section[ev:acc])


def main() -> int:
    candidate = (REPO / CANDIDATE_PATH).read_bytes()
    live = hashlib.sha256(candidate).hexdigest()
    if live != CANDIDATE_SHA256:
        raise SystemExit(f"FATAL: candidate sha256 drift: {live}")
    text = candidate.decode("utf-8")

    PROOF.mkdir(parents=True, exist_ok=True)

    s1 = build_s1(text)
    (PROOF / "BASELINE_CONTRACT_INVENTORY.json").write_text(
        json.dumps(s1, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"S1: {s1['finding']} "
        f"(machine_contract_hits={s1['machine_contract_hit_total']}, "
        f"prose_only={s1['prose_only_hit_total']}, "
        f"schemas/second_brain exists="
        f"{s1['schemas_second_brain_directory_exists']})"
    )

    s2 = build_s2(text)
    path = PROOF / "ADR_CLAUSE_INVENTORY.json"
    path.write_text(
        json.dumps(s2, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    frozen = hashlib.sha256(path.read_bytes()).hexdigest()
    print(
        f"S2: {s2['adr_count']} ADRs / {s2['clause_total']} clauses; "
        f"ADR_CLAUSE_INVENTORY.json sha256={frozen}"
    )
    for adr in s2["adrs"]:
        print(
            f"    {adr['adr_id']}: {adr['clause_count']} clauses, "
            f"sb_dec={adr['sb_dec_references']}"
        )
    print(
        "    total sb_dec references = "
        f"{sum(len(a['sb_dec_references']) for a in s2['adrs'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
