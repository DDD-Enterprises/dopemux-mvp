---
description: "Validate a Task Packet against dopetask-canonical-spec.json + AGENTS.md §5 constraints; emit pass/fail table and proof-bundle status"
arguments: "<TP-ID-or-path> [--strict] [--proof]"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
model: "claude-haiku-4-5-20251001"
---

# /tp:validate — Task Packet Validator

Fast mechanical validation of a Task Packet against repo governance. Checks schema
compliance, AGENTS.md §5 rules, and (optionally) proof-bundle status. Designed to run
before PR filing or packet handoff.

Use `--strict` to treat WARN as FAIL. Use `--proof` to also check the proof bundle.

---

## Phase 1 — Locate the Packet

Parse `$ARGUMENTS`:

- `--strict` → WARN counts as FAIL
- `--proof` → run Phase 4 (proof-bundle check)
- First non-flag positional → TP-ID or path (e.g. `TP-DCP-MCP-RO-0007` or
  `task-packets/TP-DCP-MCP-RO-0007.json`)

**Locate the packet file:**

```bash
# If given a direct path, use it
# If given a bare TP-ID, search:
find task-packets -name "<TP-ID>.json" -o -name "<TP-ID>.md" 2>/dev/null | head -1
find task-packets/generated -name "<TP-ID>.json" 2>/dev/null | head -1
```

If the packet is a `.md` file, note that JSON schema validation cannot run — skip
Phase 2 schema check and proceed with Phase 3 manual checks only.

If not found → FAIL immediately:
```
❌ Packet not found: <TP-ID>
Searched: task-packets/, task-packets/generated/
```

---

## Phase 2 — Schema Validation

Validate the JSON packet against `dopetask-canonical-spec.json`:

```bash
python3 -c "
import json, sys
from pathlib import Path

spec_path = Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json')
packet_path = Path('<PACKET-PATH>')

spec = json.loads(spec_path.read_text())
packet = json.loads(packet_path.read_text())

# Required root fields
required = spec.get('required', [])
missing = [f for f in required if f not in packet]

# Undeclared fields (not in spec properties)
declared = set(spec.get('properties', {}).keys())
extra = [f for f in packet if f not in declared]

# Step validation
steps = packet.get('steps', [])
step_req = ['id', 'task', 'validation']
step_errors = []
for i, step in enumerate(steps):
    missing_step = [f for f in step_req if f not in step or not step[f]]
    if missing_step:
        step_errors.append(f'step[{i}] missing/empty: {missing_step}')

print(json.dumps({'missing_root': missing, 'extra_fields': extra, 'step_errors': step_errors}))
"
```

Report:
- **PASS** — no missing required fields, no undeclared fields, no step errors
- **FAIL** — any missing required field or step error
- **WARN** — extra/undeclared fields (tolerated unless `--strict`)

---

## Phase 3 — AGENTS.md §5 Constraint Checks

Read the packet JSON and check each rule from AGENTS.md §5:

**3a — Gemini/PAL coupling**: If `execution.agent == "gemini"`, then
`pal_chain.enabled` must be `true`.

```python
agent = packet.get('execution', {}).get('agent', '')
pal_enabled = packet.get('pal_chain', {}).get('enabled', False)
if agent == 'gemini' and not pal_enabled:
    FAIL: 'AGENTS.md §5: execution.agent=gemini requires pal_chain.enabled=true'
```

**3b — Repo-bound**: `repo_binding` must be present and non-empty.

**3c — Series-bound**: `series` must be present and non-empty.

**3d — Commit-sized**: `commit` must be a dict or non-empty string (not null,
not `"UNKNOWN"`). WARN if `commit == "UNKNOWN"` (not yet assigned).

**3e — PAL chain present**: If `pal_chain.enabled = true`, the chain sequence must
be non-empty. Minimum expected: `analyze`, `planner`, `codereview`, `precommit`.

```python
if pal_chain_enabled:
    chain = packet.get('pal_chain', {}).get('chain', [])
    if len(chain) < 4:
        WARN: 'PAL chain has fewer than 4 stages (minimum: analyze, planner, codereview, precommit)'
    for stage in ['analyze', 'planner', 'codereview', 'precommit']:
        if stage not in chain:
            WARN: f'PAL chain missing expected stage: {stage}'
```

**3f — Steps non-empty**: `steps` must be a non-empty list.

**3g — Validation non-empty**: Every step's `validation` field must be a non-empty
string or non-empty list. (Already checked in Phase 2 step validation.)

---

## Phase 4 — Proof Bundle Check (only with `--proof`)

Check whether a proof bundle exists and is git-tracked:

```bash
# Existence
ls proof/<TP-ID>/ 2>/dev/null

# TRACK-tier files (from TP-DMX-PROOF-TRACKING-POLICY-001)
TRACK_TIER="PROOF.json SUMMARY.md AUDIT.md MERGE_READINESS.json VALIDATION.md CMD_SUMMARY.md MODEL_ROUTING.json MANIFEST.json"
for f in $TRACK_TIER; do
  git ls-files --error-unmatch "proof/<TP-ID>/$f" 2>/dev/null && echo "tracked: $f" || echo "not-tracked: $f"
done

# Gitignore status for PROOF.json
git check-ignore -q "proof/<TP-ID>/PROOF.json" && echo "gitignored: PROOF.json" || echo "not-gitignored: PROOF.json"
```

Report:
- **PASS** — proof dir exists, PROOF.json is tracked
- **WARN** — proof dir exists but PROOF.json gitignored (needs `git add -f`)
- **NOT_RUN** — proof dir does not exist (expected pre-implementation)

---

## Phase 5 — Report

Emit a structured pass/fail table:

```
Task Packet: <TP-ID>
File: <path>
─────────────────────────────────────────────────────
Check                                Result   Detail
─────────────────────────────────────────────────────
Schema: required fields              PASS     8/8 present
Schema: undeclared fields            PASS     none
Schema: step validation              PASS     N steps clean
Constraint: gemini→pal_chain         PASS     (not gemini)
Constraint: repo_binding             PASS
Constraint: series                   PASS
Constraint: commit                   WARN     value="UNKNOWN" (not yet assigned)
Constraint: steps non-empty          PASS     N steps
PAL chain stages                     PASS     analyze→planner→codereview→precommit
Proof bundle                         NOT_RUN  --proof not passed
─────────────────────────────────────────────────────
Verdict: ✅ PASS (1 WARN)
```

**Verdict rules:**
- `✅ PASS` — all checks PASS (WARNs allowed unless `--strict`)
- `⚠️ PASS WITH WARNINGS` — PASS + 1+ WARNs (only without `--strict`)
- `❌ FAIL` — any FAIL, or any WARN when `--strict`

---

## Error Handling

- `dopetask-canonical-spec.json` not found → skip Phase 2 schema check with NOT_RUN
- Packet is valid JSON but not a dict → FAIL with parse note
- Any Python error in validation → report exact error, mark that check as FAIL
- Proof dir not accessible → Phase 4 NOT_RUN with note

---

## Notes for Claude

- This command is **read-only** — never modifies the packet or proof files.
- Model: `claude-haiku-4-5-20251001` — mechanical validation, no judgment needed.
- The schema path `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` is
  authoritative; do not restate the schema rules inline.
- `commit: "UNKNOWN"` is a WARN (not yet assigned), not a FAIL — packets are often
  created before a commit SHA is known.
- For `.md` packets (not JSON), report schema check as NOT_RUN and proceed with
  manual checks where possible.
