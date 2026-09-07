# Independent L3 Audit Request

Packet: TP-DMX-CI-AUDIT-EVIDENCE-GATE-001-A5-R2-LIVE-COLLECTOR-COMPAT
Repo: DDD-Enterprises/dopemux-mvp
PR: #1330
Source head: 3858be0d93da9176b121fdbfcbc6baa8ff05196a
Frozen content head: 83fef3c528b4eb77c09eda15df40735a41c8d45c
Frozen content tree: 735ad8956e0395927a4d827605d681f4d8ee4b8c
Trusted base main: 6a728f74c0311967f83213513308f97613e3f28d

Mode: independent audit. Do not edit files. Evaluate only supplied bundle files and exact diff. Old local R2 commit 7e699be... and its failed audit are historical FAIL evidence only; do not treat as content PASS and do not require a new repair solely because that old audit bound wrong subject.

Required review:
- Confirm diff only changes allowed LIVE packet paths.
- Check collector._proof_state preserves embedded_audit.required and embedded_audit.skip_reason only after existing independent proof validation path.
- Check invalid/malformed proof remains fail-closed: NEEDS_SUPERVISOR or blocking, no NOT_REQUIRED bypass.
- Check exact trusted NOT_REQUIRED remains only status=SKIPPED, required=false, skip_reason=AUDIT_NOT_REQUIRED_BY_TRUSTED_CHANGE_CONTRACT.
- Check tests exercise live collect_from_github -> build_artifacts/readiness path, not only classifier field injection.
- Check no security-release, proof freshness, review, schema, or CI model-call gate is weakened.
- Check packet/proof portability risk: no operator-specific absolute path in committed LIVE packet/diff.

Return exactly one JSON object, no markdown fences, matching:
{
  "verdict": "PASS" | "PASS_WITH_RISKS" | "FAIL" | "NEEDS_SUPERVISOR",
  "subject_head": "83fef3c528b4eb77c09eda15df40735a41c8d45c",
  "subject_tree": "735ad8956e0395927a4d827605d681f4d8ee4b8c",
  "head_match": true,
  "auditor_independence": "PROVEN" | "UNKNOWN",
  "blocking_findings": [{"file": "path", "line": 1, "issue": "..."}],
  "nonblocking_risks": ["..."],
  "summary": "..."
}

Evidence files:
- SUBJECT_IDENTITY.json
- DETERMINISTIC_VALIDATION.json
- FULL_DIFF.patch
- files/tools/pr_steward/collector.py
- files/tests/pr_steward/test_intake.py
- files/tests/pr_steward/test_collector_proof_state.py
- files/task-packets/TP-DMX-CI-AUDIT-EVIDENCE-GATE-001-A5-R2-LIVE-COLLECTOR-COMPAT.json
- manifest.json
