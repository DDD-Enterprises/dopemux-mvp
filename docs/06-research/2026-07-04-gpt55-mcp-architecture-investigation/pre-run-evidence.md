---
id: gpt55-mcp-architecture-pre-run-evidence
title: GPT55 MCP Architecture Pre Run Evidence
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Current pre-run evidence for the GPT-5.5 MCP architecture packet.
---
# Pre-Run Evidence

Collected at `2026-07-04T19:50:15Z` from worktree:
`/Users/hue/code/dopemux-mvp/.worktrees/gpt55-mcp-architecture-investigation-20260704`

This file is an upload companion for Phase 0 and Phase 1. It records current
repo, branch, PR, service-inventory, and validation evidence before running the
GPT-5.5 phased architecture prompts.

## Evidence Status

- `OBSERVED`: command output from this worktree or live GitHub CLI.
- `ADVISORY`: external synthesis attachment content not independently proven here.
- `UNKNOWN`: requested evidence missing, not fetchable, or not run.
- `FAIL`: command failed and the failure is preserved as evidence.

## Attachment Preflight

The two recent synthesis attachments are included as advisory inputs only. They
do not outrank repo source, live GitHub state, tests, config, or runtime output.

| Attachment | Lines | SHA-256 | Pre-run use |
| --- | ---: | --- | --- |
| `/Users/hue/.codex/attachments/252931e6-3387-4b90-a8c0-47fa3f942310/pasted-text.txt` | 643 | `16d34204631fc84cc05b50b5de5476b7f31d0b7d0897158a39357d0b0f0814e7` | `ADVISORY`: P0/P1 packetization warning; defer mutating UX until F001 callable/degraded contracts are honest. |
| `/Users/hue/.codex/attachments/ad6a0ce8-671c-4ddc-9dda-a6c7d93ed2f8/pasted-text.txt` | 1007 | `dcff43f7b4ac6cfc0d96aaddf380faed1fa35cd00a72098dc4a3085199f54b47` | `ADVISORY`: PR #1002/live reconciliation warning; especially Docker Scout, PAL, Redis promotion, Exa, and review-thread state. |

## Ref Refresh

### `git fetch origin main claude/mcp-fleet-audit-complete claude/trusting-engelbart-d2fbfe --prune`

`FAIL`, exit code `128`.

```text
fatal: couldn't find remote ref claude/trusting-engelbart-d2fbfe
```

### `git fetch origin main claude/mcp-fleet-audit-complete --prune`

`PASS`, exit code `0`.

```text
From https://github.com/DDD-Enterprises/dopemux-mvp
 * branch                main       -> FETCH_HEAD
 * branch                claude/mcp-fleet-audit-complete -> FETCH_HEAD
```

### `git ls-remote --heads origin 'claude/trusting-engelbart-d2fbfe' 'claude/mcp-fleet-audit-complete'`

`PASS`, exit code `0`.

```text
baeeeb38e8a3ba14e273cffbf755b2fff8c7f8f0    refs/heads/claude/mcp-fleet-audit-complete
```

Interpretation: `claude/trusting-engelbart-d2fbfe` exists locally, but no
matching remote head was observed. Treat it as local/transcript evidence, not
live GitHub branch truth.

## Phase 0 Required Commands

### `git rev-parse HEAD`

`PASS`, exit code `0`.

```text
2cb0d92b4216ab7a11b93738694f70b863a4f13a
```

### `git status --short --branch`

`PASS`, exit code `0`.

```text
## codex/gpt55-mcp-architecture-investigation-20260704...origin/codex/gpt55-mcp-architecture-investigation-20260704
 M .claude/claude_config.json
```

Interpretation: investigation branch is in sync with origin. The only dirty
file is generated local Claude config and is outside this packet.

### `git log --oneline --decorate -20`

`PASS`, exit code `0`.

```text
2cb0d92b4 (HEAD -> codex/gpt55-mcp-architecture-investigation-20260704, origin/codex/gpt55-mcp-architecture-investigation-20260704) docs(mcp): split GPT-5.5 prompt bundles by phase
3951439e8 docs(mcp): package GPT-5.5 architecture investigation
8f71ab9af (origin/main, origin/HEAD, main, claude/focused-mahavira-5bd29b) chore(mcp): quarantine dead fleet surfaces (#1001)
b5952cd47 fix(mcp): apply quarantine to global sync
2a2580cf1 Merge remote-tracking branch 'origin/main' into codex/mcp-fleet-dead-surface-quarantine
5a7bfdc55 chore(mcp): quarantine dead fleet surfaces
f32f80973 MCP fleet audit + Phase-0 safe fixes (fail-closed conport verify, chronicle capture, honest healthchecks, registry dedupe, ensure-pal) (#993)
0805dae06 (claude/trusting-engelbart-d2fbfe) Merge remote-tracking branch 'origin/main' into claude/trusting-engelbart-d2fbfe
c463b4822 fix(capture): bound Redis fan-out socket timeouts to prevent hook stalls
d61e63141 feat(dcp): expose read-only facade packet tools (#1000)
f447920d1 test(dcp): tighten facade MCP proof wiring
b7df66d8e feat(dcp): expose read-only facade packet tools
f3577303a feat(mcp): declare fleet server personalities (#999)
614dc9759 fix(memory): capture promotable source events (#998)
689aba1f4 feat(mcp): add fleet ensure command (#997)
fb95af7dd feat(mcp): generate fleet config outputs (#996)
a98e4e254 test(mcp): gate canonical fleet catalog drift
e36820323 fix(pal): return 503 from /health when MCP subprocess is dead
42279e38c fix(mcp): address Copilot review - fleet-shape health payload, generic pal build hint
bb122e3ae docs(mcp): correct chronicle-fix claim per promotion allowlist reality
```

### `git branch --contains claude/trusting-engelbart-d2fbfe --all`

`PASS`, exit code `0`.

```text
+ claude/focused-mahavira-5bd29b
+ claude/mcp-fleet-audit-complete
  claude/trusting-engelbart-d2fbfe
+ claude/wizardly-franklin-1ca4ea
+ codex/dopemux-service-investigation-20260704
* codex/gpt55-mcp-architecture-investigation-20260704
  main
  remotes/origin/HEAD -> origin/main
  remotes/origin/claude/mcp-fleet-audit-complete
  remotes/origin/claude/wizardly-franklin-1ca4ea
  remotes/origin/codex/dopemux-service-investigation-20260704
  remotes/origin/codex/gpt55-mcp-architecture-investigation-20260704
  remotes/origin/main
  remotes/origin/pr-1002
```

### Merge bases

Command:

```bash
git merge-base origin/main claude/trusting-engelbart-d2fbfe
git merge-base origin/main claude/mcp-fleet-audit-complete
```

`PASS`, exit code `0`.

```text
0805dae06d45745011d4df2a8946ba1fbda34bb3
8f71ab9aff4802fb15d406fe654c6c601893cc42
```

Interpretation:

- `claude/trusting-engelbart-d2fbfe` currently has merge-base `0805dae06...`.
- `claude/mcp-fleet-audit-complete` currently has merge-base `8f71ab9af...`, matching `origin/main`.

## PR #1002 Snapshot

### `gh pr view 1002 --json number,state,mergedAt,headRefOid,baseRefName,mergeable,statusCheckRollup`

`PASS`, exit code `0`.

Key fields:

```json
{
  "number": 1002,
  "state": "OPEN",
  "mergedAt": null,
  "baseRefName": "main",
  "headRefOid": "baeeeb38e8a3ba14e273cffbf755b2fff8c7f8f0",
  "mergeable": "MERGEABLE"
}
```

Status rollup summary:

- `SUCCESS`: most checks, including CodeQL, container builds, docs, preflight,
  embedded audit, PR Steward advisory check-only intake, unit tests, and most
  Docker Scout jobs.
- `FAILURE`: `Scout dope-memory`.
- `SKIPPED`: installer smoke, scoped coverage, integration tests.

### `gh pr checks 1002`

`FAIL`, exit code `1`, because one PR check is failing.

```text
Scout dope-memory    fail    1m16s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802819/job/85156920250
Analyze (javascript-typescript)    pass    1m7s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802821/job/85156899897
Analyze (python)    pass    5m5s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802821/job/85156899914
Analyze (ruby)    pass    53s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802821/job/85156899885
Build adhd-engine    pass    8m19s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802817/job/85156917163
Build claude-brain    pass    22s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802817/job/85156917179
Build conport    pass    32s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802817/job/85156917182
Build dope-memory    pass    1m21s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802817/job/85156917175
Build dopecon-bridge    pass    20s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802817/job/85156917166
Build dopemux-backend    pass    28s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802817/job/85156917164
Build litellm    pass    21s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802817/job/85156917176
Build task-orchestrator    pass    22s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802817/job/85156917165
Build webhook-receiver    pass    27s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802817/job/85156917169
CodeQL    pass    2s    https://github.com/DDD-Enterprises/dopemux-mvp/runs/85156954501
Scout adhd-engine    pass    10m39s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802819/job/85156920256
Scout claude-brain    pass    3m52s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802819/job/85156920255
Scout conport    pass    3m47s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802819/job/85156920252
Scout dopecon-bridge    pass    3m44s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802819/job/85156920253
Scout dopemux-backend    pass    2m56s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802819/job/85156920243
Scout litellm    pass    2m15s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802819/job/85156920247
Scout task-orchestrator    pass    3m40s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802819/job/85156920241
Scout webhook-receiver    pass    3m29s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802819/job/85156920245
advisory check-only intake    pass    12s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802829/job/85156899923
checks    pass    35s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802845/job/85156899982
identity-check    pass    10s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802020/job/85156897386
identity-check    pass    8s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802810/job/85156899918
independent embedded audit    pass    14s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802841/job/85156899930
preflight    pass    43s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802851/job/85156899984
Code Quality & Linting    pass    39s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900022
ADHD-Friendly Security Summary    pass    3s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802816/job/85156912756
CI Pipeline Summary    pass    2s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85157210932
Documentation Check    pass    13s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900003
Audit Proof Validator (--all)    pass    18s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900015
Security Review    pass    12s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900011
Model Routing Consistency    pass    13s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900027
Claude Code Security Analysis    pass    9s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802816/job/85156899896
Auditor Router    pass    29s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900050
Extractor Full    pass    4m28s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900047
Extractor Smoke    pass    1m49s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900034
Unit Tests    pass    1m18s    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900025
Scoped Coverage    skipping    0    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900298
Integration Tests    skipping    0    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156909259
Installer Smoke    skipping    0    https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/28715802849/job/85156900283
```

Interpretation: PR #1002 is open and mergeable but not clean. Do not allow
target architecture to depend on PR #1002 changes as if they are merged until
`Scout dope-memory` and any review-thread gates are reconciled.

## Phase 1 Inventory Commands

### Service count script

`PASS`, exit code `0`.

```text
services_dirs 43
compose_services 24
registry_services 21
```

### `docker compose -f compose.yml config --services`

`PASS`, exit code `0`.

Docker Compose printed warnings for unset environment variable names:
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `XAI_API_KEY`, `OPENROUTER_API_KEY`,
`GEMINI_API_KEY`, `LITELLM_MASTER_KEY`, `LEANTIME_TOKEN`,
`HOST_CODE_PARENT_DIR`, and `HOST_PROJECT_RELATIVE_PATH`.

Rendered service names:

```text
mysql_leantime
redis_leantime
leantime
mcp-qdrant
leantime-bridge
pal-stdio
postgres
redis-primary
dope-context
exa
redis-ui
serena
webhook-receiver
redis-events
dopecon-bridge
conport
desktop-commander
dope-memory
gptr-mcp
pal
adhd-engine
litellm
task-orchestrator
webhook-poller
```

### `docker compose -f compose.yml config`

`PASS`, exit code `0`.

Raw rendered config was redirected to `/tmp/dopemux-compose-config-pre-run.txt`
and not pasted here because compose config may contain environment-derived
values. Output length was `802` lines.

### `dopemux mcp status`

`PASS`, exit code `0`.

Observed container/service status summary:

| Service | Observed status |
| --- | --- |
| `dopecon-bridge` | Up 26 hours, healthy |
| `dope-memory` | Up 26 hours, healthy |
| `desktop-commander` | Up 26 hours, healthy |
| `gptr-mcp` | Up 26 hours, healthy |
| `leantime-bridge` | Up 26 hours, healthy |
| `serena` | Up 26 hours, healthy |
| `postgres` | Up 26 hours, healthy |
| `leantime` | Up 26 hours, healthy |
| `conport` | Up 26 hours, healthy |
| `dope-context` | Up 26 hours, healthy |
| `exa` | Up 26 hours, healthy |
| `litellm` | Up 12 seconds, health starting |
| `pal` | Up 26 hours, healthy |
| `pal-stdio` | Up 2 hours |
| `mcp-qdrant` | Up 26 hours |
| `mysql_leantime` | Up 26 hours, healthy |
| `redis-events` | Up 26 hours, healthy |
| `redis-primary` | Up 26 hours, healthy |
| `redis_leantime` | Up 26 hours, healthy |
| `task-orchestrator` | Up 26 hours, healthy |

Interpretation: this was a status read only. It did not start stopped services
for this audit. Exa and desktop-commander are currently observable as running
containers despite decision-required/retirement discussions elsewhere.

## Phase 4 Validation Inputs

These validations were run early so GPT-5.5 can see current pass/fail shape.
They should be refreshed again immediately before implementation packets.

### MCP fleet catalog tests

Command:

```bash
pytest -q tests/arch/test_mcp_fleet_catalog_contract.py tests/unit/test_mcp_fleet_catalog.py tests/unit/test_mcp_commands_catalog.py
```

`PASS`, exit code `0`.

```text
....................................................                     [100%]
```

### MCP and Cockpit tests

Command:

```bash
pytest -q tests/mcp tests/unit/dopemux/ui/cockpit
```

`PASS`, exit code `0`.

```text
........................................................................ [ 39%]
........................................................................ [ 78%]
.......................................                                  [100%]
```

### Serena F001/MCP tests

Command:

```bash
pytest -q services/serena/test_f001_enhanced.py services/serena/tests/test_mcp_server_local.py
```

`FAIL`, exit code `3`.

Key failure:

```text
Testing imports...
Import failed: No module named 'untracked_work_detector'
mainloop: caught unexpected SystemExit!
INTERNALERROR> File "services/serena/test_f001_enhanced.py", line 15, in <module>
INTERNALERROR>     from untracked_work_detector import UntrackedWorkDetector
INTERNALERROR> ModuleNotFoundError: No module named 'untracked_work_detector'
INTERNALERROR> ...
INTERNALERROR> File "services/serena/test_f001_enhanced.py", line 23, in <module>
INTERNALERROR>     exit(1)
INTERNALERROR> SystemExit: 1
```

Interpretation: this confirms the earlier research risk. The enhanced F001 test
file is not pytest-safe in this invocation and fails collection before proving
MCP exposure.

### ADHD Engine tests

Command:

```bash
pytest -q services/adhd_engine/tests tests/unit/test_adhd_*.py
```

`FAIL`, exit code `2`.

Key failures:

```text
ERROR services/adhd_engine/tests/test_attention_calibrator.py
ModuleNotFoundError: No module named 'services.adhd_engine.attention_calibrator'

ERROR services/adhd_engine/tests/test_engine.py
ModuleNotFoundError: No module named 'ml'

ERROR services/adhd_engine/tests/test_feature_flags.py
ModuleNotFoundError: No module named 'adhd_engine.feature_flags'

ERROR services/adhd_engine/tests/test_voice_assistant.py
ModuleNotFoundError: No module named 'services.adhd_engine.voice_assistant'

Interrupted: 4 errors during collection
```

Interpretation: ADHD test collection currently reflects import/module drift.
Do not infer integrated ADHD behavior from passing tests.

### `git diff --check`

`PASS`, exit code `0`.

No output.

## Pre-Run Gate Verdict

`READY_FOR_GPT55_PHASE_0_WITH_STOP_GATES`.

Phase 0 can proceed because the required evidence was collected. However:

- PR #1002 is still open and has a failing `Scout dope-memory` check.
- `claude/trusting-engelbart-d2fbfe` is local-only in current evidence.
- Serena enhanced F001 tests fail collection.
- ADHD Engine tests fail collection.
- Runtime status shows live containers already running, including Exa and
  desktop-commander; this is observed state, not design approval.

GPT-5.5 should treat these as active constraints and should not proceed from
Phase 2 into final architecture if its design assumes PR #1002 is already
merged or that F001/ADHD validation is clean.
