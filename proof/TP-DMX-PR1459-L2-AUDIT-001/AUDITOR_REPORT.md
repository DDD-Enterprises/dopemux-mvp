# AUDITOR REPORT — PR #1459 L2 embedded audit (TP-DMX-PR1459-L2-AUDIT-001)

- **Auditor**: grok 1.0.62 (1474f9cbdd91) [stable], `grok-4.5` (`--effort high`), `--sandbox workspace` with cwd an empty scratch dir (no repo writes); edit, web and sub-agent tools disallowed. Operator-approved fallback ("go with grok", 2026-10-21) while AGY was over quota.
- **Implementer**: Claude Code (Anthropic Claude). Runner and model family differ from the auditor's.
- **Audited head**: `fc921797a2e4ad8930f7e9c6882cd2957e9aed0d` · **Base**: `b95aa93e8d21cf1a88c0330a2a1ce258d44dd96a` (fix/mcp-lifecycle-repair-001)
- **Verdict**: **PASS_WITH_RISKS**: findings 2, risks 6
- **Observed identity**: grok session `01a16011-ef58-7292-b592-01c20e51224b` summary records `current_model_id=grok-4.5`, `reasoning_effort=high` (CLI-reported; provider attestation UNKNOWN)
- **Run**: stopReason=end_turn, turns=7, cost_usd=0.093312864; raw sha256 `43983b00df07eca75d25aa1b13289dde973f125c6a35661e3fb15e951655e117`; prompt sha256 `63ce1b1d38169cb1e808840b9362f0ebbb964ccf1514d2e8c43dc46db4c61c75`
- **Verdict extraction**: single fenced JSON block after auditor narration, parsed by trusted parser
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Files**: `review_bundle/AUDIT_OUTPUT_RAW.json`, `review_bundle/AUDIT_INPUT.md`, `review_bundle/AUDIT_INVOCATION.txt`, `review_bundle/AUDITOR_VERDICT.json`, `review_bundle/CI_EVIDENCE.json`
- **Stacking**: base is PR #1456 branch at b95aa93e8; rebased from 9d67f28fc on 2026-10-21 (duplicate HOST_* defaults dropped for #1456 guarded version). A later rebase onto main after #1456 merges changes the head and needs this audit re-evaluated.

## Findings

- **F-01** (LOW) src/dopemux/mcp/docker_runtime.py:docker_image_exists: Absent-image detection depends on stderr containing 'no such image' with exit code 1; other docker CLI/message variants become IMAGE_PRESENCE_UNKNOWN and skip pre-build.
- **F-02** (LOW) src/dopemux/mcp/lifecycle.py:_start_services: Dry-run still executes docker image inspect (read-only side effect) to plan build vs up.

## Risks

- validation_status=NOT_RUN: unit tests and CI were not executed at fc921797a2e4ad8930f7e9c6882cd2957e9aed0d under this embedded audit (candidate not checked out/executed; tools/MCP disabled).
- Remote GitHub PR #1459 head, check runs, and workflow provenance were not re-queried in-session; subject pin rests on frozen scratchpad evidence (HEAD.txt matches trusted head SHA).
- IMAGE_PRESENCE_UNKNOWN and daemon/CLI ambiguity retain the pre-fix failure mode (compose up may build inline under the 180s up budget).
- Per-project image builds (~1.6GB + ~1.9GB) remain operator disk/time cost; documented but not gated beyond build timeout.
- compose_image_name assumes Compose v2 default '{project}-{service}' when build: is set without image:; compose.yml drift would mis-probe.
- build_timeout_secs/up_timeout_secs read os.environ (or an explicit mapping), not lifecycle process_env; hermetic callers must set process env vars for budgets.

## Auditor return (parsed, verbatim JSON)

```json
{
  "status": "PASS_WITH_RISKS",
  "verdict": "PASS_WITH_RISKS",
  "findings": [
    {
      "id": "F1",
      "severity": "low",
      "location": "src/dopemux/mcp/docker_runtime.py:docker_image_exists",
      "summary": "Absent-image detection depends on stderr containing 'no such image' with exit code 1; other docker CLI/message variants become IMAGE_PRESENCE_UNKNOWN and skip pre-build.",
      "evidence": "Candidate returns False only when exit_code==1 and 'no such image' in stderr.lower(); otherwise None. Lifecycle then runs up without compose build, which can still inline-build and exhaust DOPEMUX_MCP_UP_TIMEOUT_SECS."
    },
    {
      "id": "F2",
      "severity": "low",
      "location": "src/dopemux/mcp/lifecycle.py:_start_services",
      "summary": "Dry-run still executes docker image inspect (read-only side effect) to plan build vs up.",
      "evidence": "will_build/present are computed before the dry_run branch; tests assert dry_run runner.calls kinds == {'inspect'}."
    }
  ],
  "risks": [
    "validation_status=NOT_RUN: unit tests and CI were not executed at fc921797a2e4ad8930f7e9c6882cd2957e9aed0d under this embedded audit (candidate not checked out/executed; tools/MCP disabled).",
    "Remote GitHub PR #1459 head, check runs, and workflow provenance were not re-queried in-session; subject pin rests on frozen scratchpad evidence (HEAD.txt matches trusted head SHA).",
    "IMAGE_PRESENCE_UNKNOWN and daemon/CLI ambiguity retain the pre-fix failure mode (compose up may build inline under the 180s up budget).",
    "Per-project image builds (~1.6GB + ~1.9GB) remain operator disk/time cost; documented but not gated beyond build timeout.",
    "compose_image_name assumes Compose v2 default '{project}-{service}' when build: is set without image:; compose.yml drift would mis-probe.",
    "build_timeout_secs/up_timeout_secs read os.environ (or an explicit mapping), not lifecycle process_env; hermetic callers must set process env vars for budgets."
  ],
  "rationale": "Independent static audit of frozen PR #1459 at head fc921797a2e4ad8930f7e9c6882cd2957e9aed0d vs base b95aa93e8d21cf1a88c0330a2a1ce258d44dd96a. Scope is MCP lifecycle pre-build for conport/dope-memory when project images are missing: docker_runtime gains image probe/build helpers, explicit build/up budgets, product-aware compose interpolation defaults; lifecycle probes, optionally builds with failure short-circuit, then ups; docs and unit tests cover missing/present/unknown/fail/budget/env paths. No medium/high/critical defect was established from the supplied diff. Instruction-like scanner reported detected=false. Because validations were not re-run and remote workflow was not independently confirmed, verdict is PASS_WITH_RISKS rather than PASS.",
  "inspected_paths": [
    "docs/02-how-to/mcp-setup-other-repos.md",
    "src/dopemux/mcp/docker_runtime.py",
    "src/dopemux/mcp/lifecycle.py",
    "tests/unit/test_mcp_lifecycle.py",
    "tests/unit/test_mcp_runtime_launcher.py"
  ],
  "evidence_refs": [
    "trusted_head_sha:fc921797a2e4ad8930f7e9c6882cd2957e9aed0d",
    "trusted_base_sha:b95aa93e8d21cf1a88c0330a2a1ce258d44dd96a",
    "repo:DDD-Enterprises/dopemux-mvp",
    "pr:1459",
    "scratchpad:HEAD.txt sha256:523540cd691fbf33775d58381636a447c939afcd0085170ac5771066c7faef59",
    "scratchpad:CHANGED_FILES.txt sha256:3fe84eb67b6667d32cdd7f179b9d6625e44161a7bbb54e909e7c13810af88b6c",
    "scratchpad:UNIFIED_DIFF.patch sha256:f9b1fe8ac0b9299dee919d592c2377690122d7deccf808182c32762d73184dfe",
    "scratchpad:INSTRUCTION_LIKE.json sha256:e486d7841c47d1a9f09e5ee37ba4da8784063d01f9c8eb917db3a6bc9157e960 detected=false",
    "scratchpad:AUDIT_INVOCATION.txt subject head/base and grok embedded-audit invocation",
    "diff_behavior:IMAGE_MISSING_WILL_BUILD/IMAGE_BUILT/IMAGE_BUILD_FAILED/IMAGE_PRESENCE_UNKNOWN; build default 1800s; up default 180s; host_path_defaults retained fail-closed for dope-context starters per docs"
  ],
  "validation_status": "NOT_RUN"
}
```

## Acceptance

NOT_GRANTED by this report. Acceptance and merge belong to the operator.
