---
id: _AUTHORING_KIT
title: ' Authoring Kit'
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-14'
last_review: '2026-06-14'
next_review: '2026-09-12'
prelude: ' Authoring Kit (explanation) for dopemux documentation and developer workflows.'
---
# DMX-CONPORT-OPTIMAL Authoring Kit

Schema version: `dopetask-canonical-spec.json` (draft-07) as of 2026-06-13.
Validator: `.claude/commands/tp/validate.md` (Haiku skill) + inline python3.

---

## TP Schema Cheat-Sheet

All required root fields (`"required"` array in spec). No undeclared fields allowed
(`additionalProperties: false` at root and inside every object).

| Field | Type | Required? | Notes |
|-------|------|-----------|-------|
| `id` | string | YES | e.g. `DMX-CONPORT-OPTIMAL-101-<slug>` |
| `project` | string | YES | Always `"dopemux-mvp"` |
| `target` | string | YES | One sentence describing the concrete goal |
| `invariants` | array[string] | NO | Immutable rules the agent must not violate |
| `depends_on` | array[string] | NO | IDs of blocking TPs (default `[]`) |
| `repo_binding` | object | YES | See sub-fields below |
| `series` | object | YES | See sub-fields below |
| `execution` | object | NO | Required if you want agent/branch/base_branch |
| `commit` | object | YES | See sub-fields below |
| `pr` | object | YES | See sub-fields below |
| `pal_chain` | object | CONDITIONAL | Required and `enabled: true` when `execution.agent == "gemini"` |
| `steps` | array[object] | YES | minItems: 1; each step requires `id`, `task`, `validation` |

### repo_binding (all required, no extras)

| Sub-field | Type | Value for this series |
|-----------|------|-----------------------|
| `project_id` | string | `"dopemux-mvp"` |
| `repo_marker` | string | `".dopetaskroot"` |
| `origin_hint` | string | `"DDD-Enterprises/dopemux-mvp"` (optional but used) |
| `require_identity_match` | boolean | `true` |

### series (all required, no extras)

| Sub-field | Type | Notes |
|-----------|------|-------|
| `id` | string | `"dmx-conport-optimal"` (kebab-case series slug) |
| `base_branch` | string | `"origin/main"` |
| `parent_tp_id` | string or null | null for root/first TP; prior TP id for chained |
| `final_packet` | boolean | `true` only for the last TP in the series |

### execution (optional, no extras)

| Sub-field | Type | Enum |
|-----------|------|------|
| `agent` | string | `"gemini"` \| `"codex"` \| `"vibe"` \| `"shell"` |
| `branch` | string | e.g. `"codex/conport-optimal-101-<slug>"` |
| `base_branch` | string | `"origin/main"` |
| `stacked_because` | string | Only if stacked on another branch |

### commit (required: `message` + `allowlist`, no extras)

| Sub-field | Type | Notes |
|-----------|------|-------|
| `message` | string | Conventional commit e.g. `"feat(conport): ..."` |
| `allowlist` | array[string] | minItems: 1. List every file the agent may touch. Include the TP JSON itself and proof glob. |
| `verify` | array[string] | Shell commands to run before commit. Include `python -m jsonschema -i <tp.json> docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` |

### pr (all required, no extras)

| Sub-field | Type | Notes |
|-----------|------|-------|
| `title` | string | Short conventional-commit style |
| `body` | string | Full PR description |
| `base` | string | `"main"` |

### pal_chain (required when agent=gemini; recommended for codex on risky work)

| Sub-field | Type | Notes |
|-----------|------|-------|
| `enabled` | boolean | `true` (must be true for gemini) |
| `steps` | array[string] | minItems: 1. Minimum: `["analyze","planner","codereview","precommit"]` |

Risky/architecture variant: `["analyze","thinkdeep","challenge","planner","challenge","implement","codereview","precommit","challenge"]`

### steps[i] (required: `id`, `task`, `validation`; optional: `requirements`, `commands`, `expected_files`, `context_files`)

| Sub-field | Type | Required? |
|-----------|------|-----------|
| `id` | string | YES — e.g. `"S1"`, `"S2"` |
| `task` | string | YES — what to do |
| `validation` | array[string] | YES — minItems: 1, non-empty strings |
| `requirements` | array[string] | NO |
| `commands` | array[string] | NO |
| `expected_files` | array[string] | NO |
| `context_files` | array[string] | NO — files the agent should read as context |

---

## AGENTS.md §5 Constraints

1. No undeclared root fields (spec is `additionalProperties: false`).
2. Every step MUST have `id`, `task`, and non-empty `validation`.
3. Packets must be **repo-bound** (`repo_binding` present), **series-bound** (`series` present), **commit-sized** (one PR per TP), and **verifiable** (`commit.verify` commands).
4. `execution.agent == "gemini"` → `pal_chain.enabled` must be `true` (schema `allOf` enforces this).
5. Codex minimum PAL chain: `analyze → planner → codereview → precommit`.
6. Risky/architecture chain: `analyze → thinkdeep → challenge → planner → challenge → implement → codereview → precommit → challenge`.
7. `commit.allowlist` must include every file touched — including the TP JSON itself and `proof/<slug>/**`.
8. Proof bundle (§8) must include: TP path+ID, worktree path, branch, repo identity, slices completed, files changed, validations with exit codes, codereview status, precommit status, commit SHA, PR URL or exact blocker, residual risks, UNKNOWNs, cleanup status.
9. `commit: "UNKNOWN"` is a WARN (not FAIL) — packets authored before execution may omit SHA.
10. `pal_chain.steps` field name is `steps` (NOT `chain`) — the validate skill references `packet.get('pal_chain', {}).get('chain', [])` as an alias check but the schema property is `steps`.

---

## Validator Command

Run from `/Users/hue/code/dopemux-mvp` (repo root):

```bash
python3 -c "
import json, sys
from pathlib import Path

spec_path = Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json')
packet_path = Path('\$1')  # replace \$1 with the TP file path

spec = json.loads(spec_path.read_text())
packet = json.loads(packet_path.read_text())

required = spec.get('required', [])
missing = [f for f in required if f not in packet]
declared = set(spec.get('properties', {}).keys())
extra = [f for f in packet if f not in declared]
steps = packet.get('steps', [])
step_req = ['id', 'task', 'validation']
step_errors = []
for i, step in enumerate(steps):
    missing_step = [f for f in step_req if f not in step or not step[f]]
    if missing_step:
        step_errors.append(f'step[{i}] missing/empty: {missing_step}')

result = {'missing_root': missing, 'extra_fields': extra, 'step_errors': step_errors}
print(json.dumps(result))
if not missing and not step_errors:
    print('RESULT: PASS')
else:
    print('RESULT: FAIL')
"
```

**Exact command for a specific TP** (replace the path):
```bash
python3 -c "
import json
from pathlib import Path
spec = json.loads(Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text())
packet = json.loads(Path('task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-101-surface-audit.json').read_text())
required = spec.get('required', [])
missing = [f for f in required if f not in packet]
declared = set(spec.get('properties', {}).keys())
extra = [f for f in packet if f not in declared]
steps = packet.get('steps', [])
step_errors = [f'step[{i}] missing: {[f for f in [\"id\",\"task\",\"validation\"] if f not in s or not s[f]]}' for i,s in enumerate(steps) if any(f not in s or not s[f] for f in ['id','task','validation'])]
print({'missing_root': missing, 'extra_fields': extra, 'step_errors': step_errors})
print('RESULT: PASS' if not missing and not step_errors else 'RESULT: FAIL')
"
```

**Also optionally run jsonschema for full allOf checks** (requires `pip install jsonschema`):
```bash
python3 -m jsonschema -i task-packets/generated/DMX-CONPORT-OPTIMAL/<TP-FILE>.json \
  docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
# Exit 0 = PASS (no output). Non-zero = FAIL with error detail.
```

**Expected PASS output** (inline validator):
```
{"missing_root": [], "extra_fields": [], "step_errors": []}
RESULT: PASS
```

**Verified on**: `TP-DMX-COCKPIT-COMMAND-PALETTE-001.json` → PASS ✓

---

## Exemplar TP (verbatim — schema-valid, agent=codex)

Source: `task-packets/generated/TP-DMX-COCKPIT-COMMAND-PALETTE-001.json`

```json
{
  "id": "TP-DMX-COCKPIT-COMMAND-PALETTE-001",
  "project": "dopemux-mvp",
  "target": "Reconcile the Command Palette broker primitive onto current origin/main while preserving broker-only behavior, deterministic routing, fail-closed unknown handling, no execution, no final screens, and no Claude Design gate flip.",
  "invariants": [
    "This packet must run from a fresh dedicated worktree based on origin/main.",
    "This packet must not execute Cockpit actions.",
    "This packet must not add live service adapters.",
    "This packet must not add canonical writes.",
    "This packet must not upload anything to Claude Design.",
    "This packet must not generate or approve final UI screens.",
    "This packet must preserve safe_for_claude_design: NO.",
    "This packet must preserve READY_FOR_CLAUDE_DESIGN: not approved.",
    "This packet must not authorize T4 remote mutation.",
    "This packet must preserve TX and TU as non-executable in Cockpit.",
    "This packet must route unresolved, blocked, unknown, external, and authority-conflicted palette rows fail-closed.",
    "This packet must classify missing or unresolved evidence as UNKNOWN."
  ],
  "depends_on": [
    "TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA",
    "TP-DMX-COCKPIT-RUNTIME-RENDER-001",
    "TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "DDD-Enterprises/dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "dopemux-cockpit-ia-remediation",
    "base_branch": "origin/main",
    "parent_tp_id": "TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "codex/cockpit-command-palette-reconcile-001",
    "base_branch": "origin/main"
  },
  "commit": {
    "message": "feat(cockpit): reconcile command palette broker primitive",
    "allowlist": [
      "src/dopemux/ui/cockpit/runtime_contract.py",
      "tests/unit/dopemux/ui/cockpit/test_runtime_contract.py",
      "task-packets/generated/TP-DMX-COCKPIT-COMMAND-PALETTE-001.json",
      "task-packets/INDEX.md",
      "proof/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/**"
    ],
    "verify": [
      "python -m json.tool task-packets/generated/TP-DMX-COCKPIT-COMMAND-PALETTE-001.json >/dev/null",
      "python -m jsonschema -i task-packets/generated/TP-DMX-COCKPIT-COMMAND-PALETTE-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json",
      "python -m pytest tests/unit/dopemux/ui/cockpit/test_runtime_contract.py -q",
      "git diff --check"
    ]
  },
  "pr": {
    "title": "feat(cockpit): reconcile command palette broker primitive",
    "body": "Re-ports the Command Palette broker primitive onto current origin/main. Adds deterministic row normalization, broker-only routing, and fail-closed handling for unresolved, blocked, unknown, external, and authority-conflicted rows.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "thinkdeep",
      "challenge",
      "planner",
      "challenge",
      "implement",
      "codereview",
      "precommit",
      "challenge"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Preflight a fresh dedicated worktree from current origin/main. Verify repo marker, origin identity, branch, base HEAD, clean status, and that execution is not in the primary checkout.",
      "validation": [
        "Worktree path, branch, origin, marker, and clean baseline are recorded in proof.",
        "Primary checkout remains untouched."
      ],
      "context_files": [
        "AGENTS.md",
        "docs/03-reference/spec/dopetask/dopetask-canonical-spec.json"
      ]
    },
    {
      "id": "S2",
      "task": "Add failing tests before production code.",
      "validation": [
        "Focused tests fail because the broker API is absent.",
        "Tests assert broker_only true and executes false."
      ]
    },
    {
      "id": "S3",
      "task": "Implement the minimal deterministic broker primitive without execution side effects.",
      "validation": [
        "Rows normalize missing fields to literal UNKNOWN.",
        "The primitive produces no shellout, network, service, or canonical-write behavior."
      ]
    },
    {
      "id": "S4",
      "task": "Materialize the generated packet, update traceability index, create proof, validate, commit, push, open a PR, and move the orchestrator item to review.",
      "validation": [
        "Task packet JSON parses and validates against the canonical schema.",
        "Focused tests and git diff check pass or exact blockers are recorded.",
        "Only allowlisted files are staged and committed."
      ]
    }
  ]
}
```

---

## Load-Plan Format

Source: `docs/ops/load-plans/load_plan-DMX-ADHD-COGNITIVE-REMEDIATION.json`

```json
{
  "program": "<SERIES-NAME>",
  "date": "YYYY-MM-DD",
  "source_plan": "claudedocs/<plan>.md",
  "validation": "<PAL chain + verdict string>",
  "tag": "<series-tag>,series,supervised-only",
  "root": {
    "ref": "root",
    "title": "<Root item title>",
    "summary": "<One-paragraph description of the full program>"
  },
  "epics": [
    {"ref": "E1", "title": "<Epic title>", "phase": 1}
  ],
  "leaves": [
    {
      "ref": "L1",
      "parent": "E1",
      "title": "<Leaf title>",
      "disp": "BUILD|WIRE|HARDEN|DELETE|RETIRE|CONSOLIDATE|REBUILD",
      "targets": "<file:line optional>",
      "accept": "<acceptance criterion>"
    }
  ],
  "blocks": [
    ["L1", "L2"],
    ["L2", "L3"]
  ],
  "notes": "<Free-form notes about execution protocol>"
}
```

Key fields:
- `blocks`: array of `[blocker_ref, blocked_ref]` pairs — forms the BLOCKS DAG.
- `leaves[].disp`: disposition type (one of the enum above).
- `leaves[].accept`: acceptance criterion used at execution time.
- `epics`: optional phase grouping; leaves reference epics via `parent`.

---

## Verified Path Table

| Path | Status |
|------|--------|
| `docker/mcp-servers-source/conport/enhanced_server.py` | EXISTS |
| `docker/mcp-servers-source/conport/server.py` | EXISTS |
| `docker/mcp-servers-source/conport/conport_mcp_stdio.py` | EXISTS |
| `docker/mcp-servers-source/conport/schema.sql` | EXISTS |
| `docker/mcp-servers-source/conport/info_server.py` | EXISTS |
| `docker/mcp-servers-source/conport/Dockerfile` | EXISTS |
| `docker/mcp-servers-source/conport/migrations/` | EXISTS (7 files: 001–007 + README) |
| `docker/mcp-servers-source/conport/tests/` | EXISTS (test_instance_detector.py, test_worktree_routing.py) |
| `src/conport/memory_server.py` | EXISTS |
| `services/conport_kg/` | EXISTS (adhd_query_adapter.py, age_client.py, benchmark.py, orchestrator.py, queries/) |
| `services/dcp-readonly-facade/src/dcp_facade/conport.py` | EXISTS (conport adapter) |
| `services/dcp-readonly-facade/src/dcp_facade/tools.py` | EXISTS |
| `.claude/modules/cognitive-plane/conport-memory.md` | EXISTS |
| `docker/mcp-servers-source/conport/SURFACE_INVENTORY.md` | EXISTS |
| `docs/systems/conport/surface-equivalence-and-drift.md` | EXISTS |

**Notes on paths that differ from the task's suggested locations:**
- `SURFACE_INVENTORY.md` lives in `docker/mcp-servers-source/conport/` (NOT `docs/systems/conport/`), though a parallel copy exists at `docs/systems/conport/callable-surface-inventory.md`.
- `surface-equivalence-and-drift.md` exists at both `docs/systems/conport/` and `docs/03-reference/systems/conport/` — use `docs/systems/conport/surface-equivalence-and-drift.md` as the primary.
- No `src/conport/` files beyond `memory_server.py` — there is no additional `server.py` or `enhanced_server.py` there; those live under `docker/mcp-servers-source/conport/`.

---

## Naming Convention

**TP filename pattern** (from examining `task-packets/generated/`):

```
<SERIES-ID>-<NNN>-<slug>.json
```

Examples from existing series:
- `TP-DMX-ORCH-001.json`, `TP-DMX-ORCH-002.json` ... (zero-padded 3 digits)
- `TP-RTE-COSTPROFILE-E7-LADDERS-FAILOVER-001.json`
- `TP-DMX-COCKPIT-COMMAND-PALETTE-001.json`

For this series, use:
```
DMX-CONPORT-OPTIMAL-<NNN>-<slug>.json
```
e.g.:
```
DMX-CONPORT-OPTIMAL-101-surface-audit.json
DMX-CONPORT-OPTIMAL-102-schema-migration.json
```

The `id` field inside the JSON must match the filename (without `.json`):
```json
"id": "DMX-CONPORT-OPTIMAL-101-surface-audit"
```

Place files at: `task-packets/generated/DMX-CONPORT-OPTIMAL/<filename>.json`

---

## Schema Gotchas — What Trips Authors

1. **`additionalProperties: false` everywhere** — any field not in the spec (e.g. `notes`, `author`, `created_at`, `status`, `tags`) will fail schema validation. The spec only allows: `id, project, target, invariants, depends_on, repo_binding, series, execution, commit, pr, pal_chain, steps`.

2. **`pal_chain.steps` NOT `pal_chain.chain`** — the validate skill's Phase 3 code checks `packet.get('pal_chain', {}).get('chain', [])` (likely a legacy alias) but the actual schema property is `steps`. Write `"steps": [...]` inside `pal_chain`.

3. **`execution` is optional at root but `commit.allowlist` requires minItems: 1** — you cannot have an empty allowlist.

4. **`steps[i].validation` must be non-empty** — an empty array `[]` or missing field will FAIL step validation.

5. **gemini agent requires `pal_chain.enabled: true`** — enforced by schema `allOf`. Codex agent does NOT require `pal_chain` (it's optional for codex), but the AGENTS.md §5 Codex minimum chain is still expected for implementation work.

6. **`series.parent_tp_id` must be `string | null`** — never omit the field; use `null` for first-in-series.

7. **`commit.verify` is optional** — but per AGENTS.md §4 step 6, a jsonschema verify command should be included to prove validity at execution time.

8. **`execution.stacked_because`** — only include this field if you're stacking; if present, it must be a string. Do not add it unless needed (additionalProperties: false catches typos).

9. **No `status` field** — the spec has no `status` field. Status lives in the task-orchestrator, not the JSON packet.

10. **Proof glob in allowlist** — always include `"proof/<slug>/DMX-CONPORT-OPTIMAL-<NNN>-<slug>/**"` in `commit.allowlist` so the proof bundle files can be committed.
