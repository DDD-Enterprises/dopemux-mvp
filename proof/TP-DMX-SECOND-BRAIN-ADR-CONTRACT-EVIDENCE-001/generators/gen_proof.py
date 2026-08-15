#!/usr/bin/env python3
"""S8 — assemble PROOF.json with every hash recomputed from actual bytes."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path.cwd()
D = REPO / "proof" / "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"
C = REPO / "schemas" / "second_brain" / "contracts"
PACKET = "TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001"

C1 = (D / "C1_CONTENT_HEAD.txt").read_text().strip()
BASE = "6153bd4fb30ed3d038e51b371ad9ebfb4916bfac"


def h(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


bundle = [
    "BASELINE_CONTRACT_INVENTORY.json",
    "ADR_CLAUSE_INVENTORY.json",
    "CONTRACT_COVERAGE_RECEIPT.json",
    "FO01_RECONCILIATION_RECEIPT.json",
    "VALIDATION.json",
    "COMMAND_LOG.md",
    "AUDITOR_REPORT.md",
    "HANDOFF.md",
    "AUDIT_PROMPT.md",
    "AUDIT_PROMPT_CUSTODY.json",
    "C1_CONTENT_HEAD.txt",
]
missing = [n for n in bundle if not (D / n).is_file()]
if missing:
    sys.exit(f"FATAL: missing bundle artifacts: {missing}")

changed = git("diff", "--name-only", BASE, "HEAD").splitlines()
val = json.loads(subprocess.run(
    [sys.executable, "scripts/governance/validate_second_brain_adr_contracts.py", "--json"],
    capture_output=True, text=True).stdout)

proof = {
    "schema_version": "1.0.0",
    "task_id": PACKET,
    "program": "SECOND_BRAIN",
    "repository": "DDD-Enterprises/dopemux-mvp",
    "phase": "CONTRACT_EVIDENCE",
    "terminal_verdict": "BLOCKED_INDEPENDENT_AUDIT",
    "risk_lane": "L2",
    "execution_base": BASE,
    "issue_baseline_main": BASE,
    "drift_from_issue_baseline": "NONE",
    "content_head": C1,
    "branch": "tp/DMX-SB-ADR-CONTRACT-EVIDENCE-001",
    "pr_number": 1227,
    "clause_inventory_frozen_in_commit": "a9397e5630577ac5a2b0c8f89ad7d62d8ff7b296",
    "authority": {
        "candidate_document": "docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md",
        "candidate_sha256": h(REPO / "docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md"),
        "ratification_binding_sha256": "a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c7539e2350ba07b34",
        "candidate_document_modified": False,
        "adr_status": "10x PROPOSED",
        "accepted_adr_count": 0,
        "operator_dispositions_changed": 0,
        "sb_dec_reference_count": 28,
        "sb_dec_026": "A_LEAVE_UNLINKED",
    },
    "coverage": {
        "adr_coverage": "10/10",
        "clause_coverage": "97/97",
        "missing": 0,
        "ambiguous": 0,
        "not_applicable_proven": 0,
        "contract_artifact_count": len(list(C.glob("*.json"))),
    },
    "validation": {
        "validator_checks_total": val["checks_total"],
        "validator_checks_failed": val["checks_failed"],
        "validator_result": val["result"],
        "coverage_group": val["coverage_group"],
        "fo01_group": val["fo01_group"],
        "adversarial_tests": 52,
        "adversarial_failures": 0,
        "change_contract": {
            "status": "FAIL",
            "max_lane": "L2",
            "reason": "embedded-audit representation gap only; every path and lane check passes",
        },
        "packet_schema": "PASS",
        "pre_commit": "FAIL — proof bundle embedded_audit schema hook, same single cause",
        "diff_whitespace": "PASS",
    },
    "not_run": {
        "denial_fixtures": "NOT_IMPLEMENTED",
        "runtime_conformance": "NOT_RUN",
        "retrieval_benchmarks": "NOT_RUN",
        "purge_completeness": "NOT_RUN",
        "multi_project_isolation": "NOT_RUN",
        "split_brain_proof": "NOT_RUN",
        "encryption_implementation": "ABSENT",
    },
    "authority_state_unchanged": {
        "implementation_execution": "NOT_AUTHORIZED",
        "runtime_mutation": "NONE",
        "production_mutation": "NONE",
        "merge": "OPERATOR_ONLY",
        "adr_disposition": "OPERATOR_ONLY",
    },
    "independent_audit": {
        "verdict": "FAIL",
        "blockers": 3,
        "must_fix": 5,
        "audited_head": C1,
        "controlling": True,
        "producer_disputes": 0,
        "report": "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/AUDITOR_REPORT.md",
        "custody": "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/AUDIT_PROMPT_CUSTODY.json",
        "effect": (
            "Packet §19 requires PASS with BLOCKERS=0 and MUST_FIX=0. The verdict is "
            "FAIL, so publication does not progress: the PR stays a draft, is not "
            "marked ready, and no ADR disposition changes."
        ),
    },
    "post_c1_mutation_boundary": {
        "rule": "Commits after C1 contain producer record about the audited content, never audited content.",
        "allowed_prefixes": ["proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/", "task-packets/"],
        "verification_command": (
            "git diff --name-only 7955ef33d7c0ab29daecbab966bc6a9497dc69ce..<pr head> "
            "| grep -vE '^(proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/|task-packets/)'"
        ),
        "expected_result": "no output — any line printed is a violation of the boundary",
        "why_not_a_snapshot": (
            "A precomputed list here would be captured while HEAD still equalled C1, "
            "so it would record an empty set and prove nothing. The boundary is stated "
            "as a command the consumer runs against the live PR head instead."
        ),
    },
    "embedded_audit": {
        "required": True,
        "status": "FAIL",
        "auditor_tool": "none",
        "auditor_model": "unknown",
        "invocation": (
            "grok --cwd /private/tmp/sb-audit-c1 --always-approve --max-turns 60 "
            "--output-format plain -p \"$(cat proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/AUDIT_PROMPT.md)\""
        ),
        "exit_code": 0,
        "report_path": "proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/AUDITOR_REPORT.md",
        "findings": [
            {"id": 'B1', "severity": 'BLOCKING', "title": 'Coverage PASS survives silent architecture rewrites',
             "status": "OPEN", "body": 'Editing inventory and contract consistently changes an ADR decision while the validator exits 0, on roughly 75 of 97 clauses. Producer-confirmed twice: canonical capture rerouted Dope-Memory -> ConPort, and recall fusion inverted to the explicitly rejected vector-first order.'},
            {"id": 'B2', "severity": 'BLOCKING', "title": "'dopeTask' is an invented canonical authority",
             "status": "OPEN", "body": "grep -c dopeTask against the ratified candidate returns 0. The token came from this task packet's own architecture-boundary list, not from the audited authority, yet it entered AUTHORITY_TARGETS and two AUTHORITY_TARGET/IN clause values."},
            {"id": 'B3', "severity": 'BLOCKING', "title": 'A21 enum grounding is one-way',
             "status": "OPEN", "body": 'It rejects widening but accepts shrinking. Dropping PURGE from the ADR-SB-007 deletion-operation set and Review from the ADR-SB-010 UX operation set both still pass. Producer-confirmed.'},
            {"id": 'M1', "severity": 'HIGH', "title": 'Denominator omits material decision content',
             "status": "OPEN", "body": "Missing: ADR-SB-004 policy-evaluation dimensions (only the stage ordering was captured); ADR-SB-007 purge completion receipt; 'ConPort never owns task state' and the Dope-Memory PM-authority forbid; the ADR-SB-003 historical-vs-current distinction; ADR-SB-008 open/close/cancel event kinds. Repair requires re-freezing the denominator, superseding the freeze at a9397e5630."},
            {"id": 'M2', "severity": 'HIGH', "title": 'Typed artifacts invent API and schema surface',
             "status": "OPEN", "body": 'LocalSpoolPort/CustodyPort operation lists and several property and enum sets assert structure the candidate never states, and the validator does not constrain them.'},
            {"id": 'M3', "severity": 'HIGH', "title": 'ADR-SB-003-C01 invents a total fusion ranking',
             "status": "OPEN", "body": "The candidate states 'authority-first'; the clause asserts a four-way total order over authority, chronology, source-native and advisory retrieval."},
            {"id": 'M4', "severity": 'MEDIUM', "title": 'Many rules are token labels rather than machine expression',
             "status": "OPEN", "body": "REQUIRE/MUST_EXIST rules name an artifact class (PURGE_DEPENDENCY_GRAPH, FRESHNESS_METADATA, ...) without giving it a shape, so 'cover' is naming."},
            {"id": 'M5', "severity": 'MEDIUM', "title": 'FO-01 check group B leaves status fields unlocked',
             "status": "OPEN", "body": 'nonblocking_observations, authority.architecture_accepted_as_law and the expanded coverage metrics can diverge from the receipt while group B still passes.'},
        ],
        "fixes_applied": [],
        "remaining_risks": [
            "Native embedded-audit lane cannot represent the auditor that actually ran; auditor_tool and auditor_model are the schema's fallback values, not a claim that no audit occurred.",
            "The controlling verdict is FAIL with 3 blockers and 5 must-fix. This packet is BLOCKED_INDEPENDENT_AUDIT: the PR remains a draft, is not marked ready, and no ADR disposition changes.",
            "Repairing MUST_FIX 1 requires re-freezing the coverage denominator, which supersedes the freeze recorded at a9397e5630577ac5a2b0c8f89ad7d62d8ff7b296. That is an operator decision, not a producer patch.",
            "The audit prompt names content head 8a9b0ee53c while the audit ran against 7955ef33d7 (the A21 fix landed after the prompt was written). The auditor detected this itself and verified the real head. The prompt was not rewritten, because editing it to name a head it did not name would falsify custody.",
        ],
        "skip_reason": (
            "GROK_AUDIT_VALID_SCHEMA_REPRESENTATION_UNSUPPORTED. The substantive independent audit was executed by the grok CLI 1.0.0 in a throwaway detached worktree at the audited head, session 019ff54e-59b1-7a12-bc2a-1cc88f3e3189, and returned FAIL with 3 blockers and 5 must-fix. schemas/proof/embedded_audit.schema.json enumerates auditor_tool as [agy, antigravity, claude-code-cli, copilot-cli, gemini-cli, pal-mcp-clink, none] and auditor_model as [sonnet, claude-sonnet-4.6, opus, gemini, gemini-3.1-pro-high, unknown]; neither can name this runner. The fallback values are recorded rather than fabricating a representable identity. status=FAIL is the true verdict and is representable. See AUDITOR_REPORT.md and AUDIT_PROMPT_CUSTODY.json, which also records three audit routes that failed before this one."
        ),
    },
    "changed_paths": changed,
    "changed_path_count": len(changed),
    "artifact_sha256": {n: h(D / n) for n in bundle},
    "contract_sha256": {p.name: h(p) for p in sorted(C.glob("*.json"))},
}

(D / "PROOF.json").write_text(json.dumps(proof, indent=2) + "\n")
print(f"PROOF.json written: {len(bundle)} bundle artifacts, "
      f"{len(proof['contract_sha256'])} contracts, {len(changed)} changed paths")
print(f"  validator {val['checks_total']} checks / {val['checks_failed']} failed")
print(f"  content head {C1}")
