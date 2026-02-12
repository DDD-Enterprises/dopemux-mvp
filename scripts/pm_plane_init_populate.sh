#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

# Safety: ensure target folder exists
test -d "docs/planes/pm" || { echo "Missing docs/planes/pm"; exit 1; }

write() {
  local path="$1"
  shift
  mkdir -p "$(dirname "$path")"
  cat > "$path"
  echo "WROTE: $path"
}

write "docs/planes/pm/README.md" <<'EOF'
# PM Plane

Purpose: Evidence-first audit, minimal redesign, and task-packet implementation of the Dopemux PM / Task-Management plane.

This plane is governed by strict phases. Do not skip phases.

## Non-negotiables
- No fabrication. If not evidenced, mark UNKNOWN or MISSING.
- Evidence-first. Every architectural claim must cite:
  - file path + line range, or
  - command output, or
  - explicit absence (0 hits + command).
- Current state > historical docs.
- Task Packets are law for code changes.
- ADHD-first. Default outputs are minimal; progressive disclosure only.
- Trinity boundaries: PM must not become a shadow Dope-Memory or DopeQuery store.

## How to run
1) Run Phase 0 evidence capture:
   - See: docs/planes/pm/_evidence/PM-INV-00.commands.txt
   - Paste outputs into: docs/planes/pm/_evidence/PM-INV-00.outputs/
2) Write Phase 0 deliverables:
   - docs/planes/pm/PM_PLANE_INVENTORY.md
   - docs/planes/pm/PM_PLANE_GAPS.md
3) Only after Phase 0 stop conditions clear:
   - Phase 1: PM_FRICTION_MAP.md
   - Phase 2: PM_ADHD_REQUIREMENTS.md + PM_OUTPUT_BOUNDARIES.md
   - Phase 3: PM_ARCHITECTURE.md + ADR-PM-### set
   - Phase 4: implementation via Task Packets
   - Phase 5: PM_WORKFLOWS_DERIVED.md (derived only)

## Phase 0 stop condition
If any PM-critical service is missing or non-functional, stop after documenting it in PM_PLANE_GAPS.md.
Do not proceed to Phase 1.

## Deliverables
- Phase 0:
  - PM_PLANE_INVENTORY.md
  - PM_PLANE_GAPS.md
- Phase 1:
  - PM_FRICTION_MAP.md
  - SIGNAL_VS_NOISE_ANALYSIS.md (create when Phase 1 begins)
- Phase 2:
  - PM_ADHD_REQUIREMENTS.md
  - PM_OUTPUT_BOUNDARIES.md
- Phase 3:
  - PM_ARCHITECTURE.md
  - ADR-PM-### set
- Phase 4:
  - Task Packets A/B/C
- Phase 5:
  - PM_WORKFLOWS_DERIVED.md
  - PM_PRESETS.md (optional)
EOF

write "docs/planes/pm/PM_PLANE_INVENTORY.md" <<'EOF'
# PM Plane Inventory (Phase 0)

Status: DRAFT (evidence-first)

## Scope
Phase 0 only. Inventory and reality check. No design.

## Evidence bundle pointers
- Evidence outputs folder:
  - docs/planes/pm/_evidence/PM-INV-00.outputs/
- Command list:
  - docs/planes/pm/_evidence/PM-INV-00.commands.txt

## Observed components (Verified)
Fill this section only with evidence references.

| Component | Location | Purpose (Observed) | Entry points | Storage | Task model | States | Integrations | Tests | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| task-orchestrator | services/task-orchestrator/ | TBD | TBD | TBD | TBD | TBD | TBD | TBD | path:line |
| taskmaster | services/taskmaster/ | TBD | TBD | TBD | TBD | TBD | TBD | TBD | path:line |
| dopemux CLI | src/dopemux/cli.py | TBD | CLI | TBD | TBD | TBD | TBD | TBD | path:line |
| event bus | src/dopemux/event_bus.py (or equivalent) | TBD | API | TBD | N/A | N/A | producers/consumers | TBD | path:line |
| leantime installer | installers/leantime/ | TBD | scripts | TBD | TBD | TBD | sync/bridge | TBD | path:line |

## Task lifecycle inventory (Verified)
Document task lifecycle and status transitions for each task system.

| System | Canonical task object name | Status/state representation | Transition function(s) | Idempotency strategy | Evidence |
|---|---|---|---|---|---|
| task-orchestrator | TBD | TBD | TBD | TBD | path:line |
| taskmaster | TBD | TBD | TBD | TBD | path:line |

## Event producers/consumers (Verified)
List PM-relevant event types and streams.

| Producer | Consumer | Stream/topic | Event types | Payload shape | Determinism risks | Evidence |
|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | path:line |

## Cross-plane wiring (Verified)
Document explicit integration touchpoints (only if evidenced).

| PM component | Memory/Chronicle | DopeQuery/ConPort | ADHD Engine | Notes | Evidence |
|---|---|---|---|---|---|
| task-orchestrator | TBD | TBD | TBD | TBD | path:line |
| taskmaster | TBD | TBD | TBD | TBD | path:line |

## Unknown or Missing (Phase 0)
Everything here must include what evidence is missing and how to get it.

| Question | Why it matters | How to resolve (exact file/command) |
|---|---|---|
| What is the PM canonical status source (Leantime vs internal)? | prevents drift | inspect docs/90-adr/* + installers/leantime + task-orchestrator sync code |
| Are decisions linked to tasks in a canonical store? | traceability | search for conport/dopequery references in task services |
| Does event bus persist PM events? | determinism | inspect event bus adapter implementation |
EOF

write "docs/planes/pm/PM_PLANE_GAPS.md" <<'EOF'
# PM Plane Gaps (Phase 0)

Status: DRAFT (evidence-first)

## Severity rubric
- P0: prevents PM plane from functioning or makes state untrustworthy
- P1: causes persistent friction or drift, but system still runs
- P2: quality/UX issue, not correctness critical
- P3: nice-to-have or cleanup

## Stop condition
If any P0 is present, stop after documenting it. Do not proceed to Phase 1.

## Gaps table
| Severity | Gap | Impact | Where observed | Evidence | Proposed next step (Phase 0 only) |
|---|---|---|---|---|---|
| P0 | rg missing in operator env | audit workflow breaks | operator shell | command output | install rg or lock grep fallback |
| TBD | TBD | TBD | TBD | path:line or output | TBD |

## Explicit absences (important)
Use this section to record searches that returned 0 hits.

| Expectation | Search command | Result | Why it matters |
|---|---|---|---|
| decision linkage fields exist | rg/grep query | 0 hits | traceability gap |
| PM CLI commands exist | rg/grep query | 0 hits | discoverability gap |
EOF

write "docs/planes/pm/PM_FRICTION_MAP.md" <<'EOF'
# PM Friction Map (Phase 1)

Status: PLACEHOLDER

Do not fill until Phase 0 stop conditions are cleared.

Phase 1 goal: find where PM breaks cognition/flow.
Focus: creation friction, state drift, duplicate representations, missing decision linkage.

Required sections:
- Friction points (Observed, with evidence)
- "Forces user to remember" map
- Signal vs noise classification (ADHD-first)
EOF

write "docs/planes/pm/PM_ADHD_REQUIREMENTS.md" <<'EOF'
# PM ADHD Requirements (Phase 2)

Status: PLACEHOLDER

Do not fill until Phase 0 stop conditions are cleared.

Phase 2 goal: define what PM must do for neurodivergent users without violating Trinity boundaries.

Required sections:
- ADHD failure modes (Observed from workflow + inferred from constraints)
- Required PM signals (minimal)
- Suppressed signals (noise by default)
- Proactive surfacing rules (gated by focus state)
EOF

write "docs/planes/pm/PM_OUTPUT_BOUNDARIES.md" <<'EOF'
# PM Output Boundaries (Phase 2)

Status: PLACEHOLDER

Do not fill until Phase 0 stop conditions are cleared.

Define output rules:
- Default minimal (Top-3 unless explicitly requested)
- Progressive disclosure path (what expands when user asks)
- Split of signals across planes:
  - PM plane vs Dope-Memory chronicle vs DopeQuery decisions vs Search
- "Never by default" list (noise, duplicates, or trust risks)
EOF

write "docs/planes/pm/PM_ARCHITECTURE.md" <<'EOF'
# PM Architecture (Phase 3)

Status: PLACEHOLDER

Do not fill until Phase 0 and Phase 1-2 are complete.

Phase 3 goal: minimal, correct redesign based on evidence.

Required sections:
- Canonical task object contract
- Lifecycle + transitions (deterministic)
- What is stored vs derived vs mirrored
- Event taxonomy for PM (only if required)
- Idempotency strategy
- Integration contracts:
  - Dope-Memory chronicle
  - DopeQuery/ConPort decisions
  - ADHD engine focus gating
- Acceptance tests (must be runnable locally and in CI)
EOF

write "docs/planes/pm/PM_WORKFLOWS_DERIVED.md" <<'EOF'
# PM Workflows (Derived, Phase 5)

Status: PLACEHOLDER

Do not fill until Phase 4 implementation exists.

Rules:
- Workflows are derived from reality, not imposed.
- Presets may exist but are optional.
- Recovery patterns are mandatory to document.
EOF

write "docs/planes/pm/_evidence/README.md" <<'EOF'
# PM Plane Evidence Bundles

This folder stores raw, verbatim evidence captured during PM Plane phases.

## Naming convention
- Bundle name: PM-INV-00, PM-INV-01, PM-FRIC-01, etc.
- Outputs live under:
  - docs/planes/pm/_evidence/<BUNDLE>.outputs/

## Rules
- Store verbatim command outputs only.
- Do not summarize inside outputs.
- If output is large, split into numbered files:
  - 01_baseline.txt
  - 02_search.txt
  - 03_task_orchestrator_models.txt
  - etc.

## What counts as evidence
- file excerpts with line ranges (preferred)
- command output with exact command shown
- explicit absence: 0 hits + command

## Quarantine
quarantine/** is excluded by default to prevent stale session artifacts from polluting evidence.
Include it only when explicitly investigating provenance drift.
EOF

write "docs/planes/pm/_evidence/PM-INV-00.commands.txt" <<'EOF'
PM-INV-00: Phase 0 Evidence Capture Commands
Run from repo root. Capture outputs verbatim into PM-INV-00.outputs/.

Tooling:
- Preferred: rg (ripgrep)
- Fallback: grep -rnE
Exclude: .git/** and quarantine/** by default.

0) Baseline snapshot
- git rev-parse HEAD
- git status --porcelain

1) Service inventory
- ls -la services
- find services -maxdepth 2 -type f -name "Dockerfile" -o -name "pyproject.toml" -o -name "package.json"

2) PM surface scan (rg preferred)
- rg -n --hidden --glob '!.git/**' --glob '!quarantine/**' "task[-_ ]orchestrator|taskmaster|leantime|workflow|state transition|kanban|backlog|todo|triage|milestone|sprint" .
Fallback:
- grep -rnE --exclude-dir=.git --exclude-dir=quarantine "task[-_ ]orchestrator|taskmaster|leantime|workflow|state transition|kanban|backlog|todo|triage|milestone|sprint" .

3) Task state + lifecycle scan
- rg -n --hidden --glob '!.git/**' --glob '!quarantine/**' "Enum|Status|State|Transition|lifecycle" services/task-orchestrator services/taskmaster src/dopemux
Fallback:
- grep -rnE --exclude-dir=.git --exclude-dir=quarantine "Enum|Status|State|Transition|lifecycle" services/task-orchestrator services/taskmaster src/dopemux

4) Event bus scan
- rg -n --hidden --glob '!.git/**' --glob '!quarantine/**' "event_bus|EventBus|activity\.events\.v1|memory\.derived\.v1|xadd|xread|stream|publish|subscribe" services src/dopemux
Fallback:
- grep -rnE --exclude-dir=.git --exclude-dir=quarantine "event_bus|EventBus|activity\.events\.v1|memory\.derived\.v1|xadd|xread|stream|publish|subscribe" services src/dopemux

5) ConPort/DopeQuery decision linkage scan (explicit absence allowed)
- rg -n --hidden --glob '!.git/**' --glob '!quarantine/**' "conport|dopequery|decision|rationale|link_conport" services/task-orchestrator services/taskmaster src/dopemux
Fallback:
- grep -rnE --exclude-dir=.git --exclude-dir=quarantine "conport|dopequery|decision|rationale|link_conport" services/task-orchestrator services/taskmaster src/dopemux

6) Tests inventory (PM-related)
- find . -maxdepth 4 -type d \( -name "tests" -o -name "__tests__" \)
- rg -n --hidden --glob '!.git/**' --glob '!quarantine/**' "task|workflow|state|transition|leantime|orchestrator|pm" tests services/*/tests
Fallback:
- grep -rnE --exclude-dir=.git --exclude-dir=quarantine "task|workflow|state|transition|leantime|orchestrator|pm" tests services/*/tests
EOF

echo "Done."
