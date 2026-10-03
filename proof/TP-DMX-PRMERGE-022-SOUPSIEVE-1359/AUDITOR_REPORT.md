# Embedded Auditor Report: TP-DMX-PRMERGE-022-SOUPSIEVE-1359

## Metadata
- **Subject**: PR #1359 (`deps(deps): bump soupsieve from 2.8.4 to 2.9`)
- **Base SHA**: `15fa198f465e180855861cfec55df2904a1646df`
- **Head SHA**: `b0f5bc95c6a9341a249efd752623cd78e4bffd26`
- **Target**: `soupsieve` 2.8.4 -> 2.9 in root `uv.lock`
- **Auditor Tool**: `agy` (v1.2.14)
- **Auditor Model**: `gemini-3.1-pro-high`
- **Reasoning Effort**: `high`
- **Execution Mode**: plan, sandbox, isolated audit root
- **Verdict**: **PASS**
- **Date**: 2026-10-02T19:43:55-07:00
- **Duration**: 84.24s
- **Conversation ID**: `0d5429e9-7970-4384-856a-8f4ec75f5734`

## Diff Summary
The diff is confined strictly to a single package block in root `uv.lock`:
- Package: `soupsieve`
- Version: `2.8.4` -> `2.9`
- sdist URL, hash (`sha256:acee8417325c5653e1377dc31eccad59eb82cbc65942afe6174c53b3aaad63fc`), size (`122122`), and upload time updated.
- wheel URL, hash (`sha256:a2b2c76d67df2382d245409fd71e321a571717e58463efa32ace87dcadac2c12`), size (`37387`), and upload time updated.
- No source code, configuration, or workflow files modified.

## Deterministic Validation Evidence
- `uv lock --check --offline`: PASS (Resolved 276 packages in 12ms)
- `git diff --check origin/main...HEAD`: PASS (clean whitespace)
- `python3 scripts/governance/validate_change_contract.py --base origin/main --head HEAD --format text`: PASS (`status=PASS`, `max_lane=L2`, `model_audit_required=True`, `paths=1: [L2] uv.lock`)

## Independence Verification
- Implementer: `dependabot[bot]` (automated GitHub Dependabot PR).
- Integration: Deterministic cherry-pick onto `15fa198f465e180855861cfec55df2904a1646df`.
- Auditor: `agy` with `gemini-3.1-pro-high`.
- Provider family separation: Implementer is GitHub/automation; Auditor is Google/Gemini. Zero Google/Gemini participation in substantive code authoring or repair.
- Independence: **PROVEN**.

## Findings
None.

## Remaining Risks
None.
