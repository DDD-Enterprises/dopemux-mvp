# Dopemux Execution Plan

**Plan posture:** `PLAN_ONLY`
**Execution mode:** repo-bound, TP-driven, evidence-gated
**First objective:** prove runtime authority before touching architecture docs or agent automation, because otherwise we’d be automating confusion with better formatting. 🧨

The plan follows the repo’s own constraints: runtime code/config/tests outrank docs; contradictions must stay visible; bridges, shims, mirrors, and retrieval outputs must not become authority; and non-trivial work requires a strict Task Packet with repo binding, series binding, worktree verification, validations, PR state, and proof. 

---

# 1. Control board

```json
{
  "items": [
    {
      "rank": 1,
      "series": "SERIES-DMX-AUTHORITY-001",
      "goal": "Prove runtime authority and stop the biggest drift from lying to operators."
    },
    {
      "rank": 2,
      "series": "SERIES-DMX-DOC-REPAIR-001",
      "goal": "Repair docs only after runtime facts are verified."
    },
    {
      "rank": 3,
      "series": "SERIES-DMX-AGENT-OPS-001",
      "goal": "Create deterministic multi-agent execution rails after authority is stable."
    }
  ],
  "more_count": 3,
  "next_token": "SERIES-DMX-VALIDATION-001"
}
```

---

# 2. Hard order of operations

## Phase 0 — Preflight and worktree setup

**Goal:** create a safe execution lane before any edits.

| Step | Action                                 | Validation                                            | Stop condition                  |
| ---: | -------------------------------------- | ----------------------------------------------------- | ------------------------------- |
|  0.1 | Create dedicated worktree from `main`. | Worktree path is not the primary checkout.            | Existing unrelated worktree.    |
|  0.2 | Verify repo identity.                  | `.dopetaskroot` exists; origin matches `dopemux-mvp`. | Marker missing or wrong origin. |
|  0.3 | Verify branch.                         | Branch matches TP series.                             | Branch mismatch.                |
|  0.4 | Snapshot current state.                | `git status --short` captured.                        | Dirty unexpected state.         |

**Commands:**

```bash
git worktree add ../dopemux-authority-001 -b audit/runtime-authority-verifier main
cd ../dopemux-authority-001

git rev-parse --show-toplevel
test -e .dopetaskroot
git branch --show-current
git remote -v
git status --short
```

Why this comes first: the repo rules require fresh dedicated worktrees and explicit repo identity checks before implementation. Humanity invented footguns, then invented worktrees to reload them safely. 

---

## Phase 1 — Runtime authority verification

**Goal:** create an executable verifier that turns “docs say” into “repo proves.”

| TP                            | Type                   | Target                                | Why now                                                                               | Validation                                                                         |
| ----------------------------- | ---------------------- | ------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `TP-DMX-RUNTIME-VERIFY-001`   | `RUNTIME_VERIFY`       | Runtime authority manifest + verifier | Generated pointer docs explicitly do not replace code/config inspection.              | Static verifier reports known drift deterministically.                             |
| `TP-DMX-TASKORCH-RUNTIME-001` | `RUNTIME_VERIFY`       | task-orchestrator runtime and port    | Runtime packaging, Docker target, and port authority are contradictory.               | Docker/app target and port contract are single-valued or explicitly `CONFLICTING`. |
| `TP-DMX-CONPORT-AUTH-001`     | `AUTHORITY_RESOLUTION` | ConPort deployed authority            | `src/conport/memory_server.py` and Docker ConPort both look active in different docs. | One deployed runtime chosen by evidence, or conflict remains blocked.              |

**Evidence:** The architecture docs define Dopemux as a composed multi-system workspace, not one unified platform, and require preserving split authority and drift.  Task-orchestrator specifically has unresolved packaging and port drift.  ConPort has a direct conflict between the truth scope’s `src/conport/memory_server.py` authority and the system doc’s Docker-packaged `enhanced_server.py` runtime.  

---

## Phase 2 — PM, bridge, and memory boundary locks

**Goal:** prevent writes from silently going to the wrong authority.

| TP                            | Type                    | Target                                    | Why now                                                                                    | Validation                                                                            |
| ----------------------------- | ----------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `TP-DMX-PM-PORTS-001`         | `RUNTIME_VERIFY`        | PM endpoint and writer consistency tests  | PM writes are split across Leantime, task-orchestrator, ConPort, and dope-memory receipts. | Tests prove metadata, workflow, progress/decision, and receipt paths route correctly. |
| `TP-DMX-BRIDGE-WRITER-001`    | `DOC_RECONCILE` + tests | Bridge route-to-writer matrix             | DopeconBridge exposes PM/ConPort-like routes but must not become authority.                | Every write-like route names upstream canonical writer.                               |
| `TP-DMX-MEMORY-TRANSPORT-001` | `RUNTIME_VERIFY`        | dope-memory `3020` vs legacy `8096` drift | Active dope-memory runtime is `3020`; stale WMA surfaces still exist.                      | Stale adapter calls are fixed, deprecated, or blocked.                                |

**Evidence:** PM authority is explicitly split by concern: Leantime metadata, task-orchestrator workflow transitions, ConPort decisions/progress/context, and dope-memory historical receipts.  DopeconBridge is adapter/proxy/event transport, not PM, workflow, decision, or progress authority.  dope-memory’s active runtime is `services/working-memory-assistant/dope_memory_main.py` on `3020`, while older `8096` WMA assumptions remain stale. 

---

## Phase 3 — Documentation repair

**Goal:** make docs usable by agents without letting docs outrank runtime.

| TP                          | Type                 | Target                                       | Depends on                     | Validation                                                       |
| --------------------------- | -------------------- | -------------------------------------------- | ------------------------------ | ---------------------------------------------------------------- |
| `TP-DMX-DOC-TRUST-001`      | `DOC_CREATE`         | `DOC_TRUST_MAP.md`, `DOCS_VS_REPO_DIFF.md`   | Runtime verifier               | Every primary doc has trust level and drift status.              |
| `TP-DMX-DOC-BOUNDARIES-001` | `DOC_RECONCILE`      | `SYSTEM_BOUNDARIES`, `PM_PLANE`, system docs | Runtime + PM/bridge/memory TPs | No unqualified false authority claims remain.                    |
| `TP-DMX-UPLOAD-REFRESH-001` | `UPLOAD_SET_REFRESH` | ChatGPT Project upload set                   | Doc repair                     | Top-40 upload manifest regenerated; unsafe files still excluded. |

**Evidence:** The source map says generated docs are advisory and exact source contents remain authoritative.  The current ChatGPT upload set is a curated top-40 snapshot, useful for seeding but not permanent truth.  The drift summary also records secret-pattern-skipped optional docs, so unsafe docs must be redacted before being promoted. 

---

## Phase 4 — Multi-agent rails

**Goal:** only after authority and docs are repaired, create deterministic agent workflows.

| TP                         | Type                         | Target                       | Depends on     | Validation                                                      |
| -------------------------- | ---------------------------- | ---------------------------- | -------------- | --------------------------------------------------------------- |
| `TP-DMX-AGENTS-CREATE-001` | `AGENT_INSTRUCTION_CREATE`   | `.github/agents/*.agent.md`  | Doc trust map  | Planner/reviewer are read-only; implementer/testgen are scoped. |
| `TP-DMX-PROOF-GATE-001`    | `RUNBOOK_CREATE` + validator | Proof and handoff validators | Proof contract | Proof bundle fixtures pass/fail correctly.                      |
| `TP-DMX-CODEX-RUNBOOK-001` | `RUNBOOK_CREATE`             | Codex implementation runbook | Agent specs    | Codex flow maps to TP, worktree, proof, PR.                     |

**Evidence:** GitHub Copilot agent instructions require Markdown agent files with YAML frontmatter and tool scoping; the local instructions also emphasize handoffs, least privilege, and specific agent roles.  Proof bundles and handoffs have explicit required fields, status values, artifacts, warnings, blockers, and chain-of-custody requirements.  

---

## Phase 5 — Runtime validation and governance closure

**Goal:** turn the repaired system into a repeatable operating loop.

| TP                        | Type             | Target                        | Depends on         | Validation                                                                          |
| ------------------------- | ---------------- | ----------------------------- | ------------------ | ----------------------------------------------------------------------------------- |
| `TP-DMX-VALIDATION-001`   | `RUNTIME_VERIFY` | End-to-end validation runbook | Prior phases       | CLI, compose, service health, PM write, memory write, retrieval smoke all captured. |
| `TP-DMX-PROOF-BUNDLE-001` | `RUNBOOK_CREATE` | Proof bundle generation       | Validation runbook | Manifest, warnings, blockers, artifacts, chain of custody.                          |
| `TP-DMX-OPERATOR-UX-001`  | `DOC_CREATE`     | Operator workflow guide       | Proof bundle       | Approval/error states map to Telegram Topics and Top-3 summaries.                   |

---

# 3. Critical dependency graph

```text
SERIES-DMX-AUTHORITY-001
  ├─ TP-DMX-RUNTIME-VERIFY-001
  ├─ TP-DMX-TASKORCH-RUNTIME-001
  ├─ TP-DMX-CONPORT-AUTH-001
  └─ TP-DMX-PM-PORTS-001

SERIES-DMX-BOUNDARY-001
  ├─ TP-DMX-BRIDGE-WRITER-001
  └─ TP-DMX-MEMORY-TRANSPORT-001

SERIES-DMX-DOC-REPAIR-001
  ├─ TP-DMX-DOC-TRUST-001
  ├─ TP-DMX-DOC-BOUNDARIES-001
  └─ TP-DMX-UPLOAD-REFRESH-001

SERIES-DMX-AGENT-OPS-001
  ├─ TP-DMX-AGENTS-CREATE-001
  ├─ TP-DMX-PROOF-GATE-001
  └─ TP-DMX-CODEX-RUNBOOK-001

SERIES-DMX-VALIDATION-001
  ├─ TP-DMX-VALIDATION-001
  ├─ TP-DMX-PROOF-BUNDLE-001
  └─ TP-DMX-OPERATOR-UX-001
```

**Do not start `SERIES-DMX-AGENT-OPS-001` before `SERIES-DMX-DOC-REPAIR-001`.** Agents trained on wrong docs become extremely confident little goblins. 🧌

---

# 4. First executable series

## Series

```json
{
  "series_id": "SERIES-DMX-AUTHORITY-001",
  "base_branch": "main",
  "worktree": "../dopemux-authority-001",
  "purpose": "Establish runtime authority before doc repair or agent automation",
  "final_state": "runtime verifier exists; task-orchestrator and ConPort conflicts are verified or blocked; PM endpoint tests exist"
}
```

## Acceptance criteria

| Criterion                          | Required proof                                                                 |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| Runtime authority manifest exists  | Manifest file, test output, verifier output                                    |
| Task-orchestrator conflict handled | Docker/app/port evidence captured; config fixed or explicitly blocked          |
| ConPort conflict handled           | Deployed/runtime evidence captured; docs patched only after proof              |
| PM endpoints tested                | Unit/static tests prove canonical writer routing                               |
| No authority inflation             | Bridge, mirror, shim, retrieval, and adapter surfaces remain non-authoritative |
| PR opened                          | PR URL recorded                                                                |
| Worktree lifecycle closed          | Worktree removed or cleanup blocker reported                                   |

---

# 5. Ready TP 1 — runtime authority verifier

```json
{
  "id": "TP-DMX-RUNTIME-VERIFY-001",
  "project": "dopemux",
  "target": "RUNTIME_VERIFY: add deterministic runtime authority manifest and verifier",
  "invariants": [
    "Runtime code/config/tests outrank docs",
    "Generated pointer docs do not replace runtime inspection",
    "Bridge, proxy, mirror, retrieval, and shim surfaces must not be promoted to authority"
  ],
  "depends_on": [],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "SERIES-DMX-AUTHORITY-001",
    "base_branch": "main",
    "parent_tp_id": null,
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "audit/runtime-authority-verifier"
  },
  "commit": {
    "message": "Add deterministic runtime authority verifier",
    "allowlist": [
      "config/runtime_authority_manifest.json",
      "scripts/verify_runtime_authority.py",
      "tests/unit/test_runtime_authority_manifest.py",
      "docs/03-reference/governance/runtime-authority-verification.md"
    ],
    "verify": [
      "python -m json.tool config/runtime_authority_manifest.json",
      "python -m pytest -q tests/unit/test_runtime_authority_manifest.py",
      "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static"
    ]
  },
  "pr": {
    "title": "Add deterministic runtime authority verifier",
    "body": "Adds a static verifier and manifest for runtime authority pointers, known conflicts, and non-authority surfaces.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Create runtime_authority_manifest.json for dopemux, dopetask, task-orchestrator, ConPort, dope-memory, dope-context, dopecon-bridge, ADHD Engine, and Repo Truth Extractor.",
      "requirements": [
        "Mark known conflicts explicitly",
        "Mark unresolved surfaces UNKNOWN",
        "Do not infer authority from directory names"
      ],
      "commands": [
        "python -m json.tool config/runtime_authority_manifest.json"
      ],
      "expected_files": [
        "config/runtime_authority_manifest.json"
      ],
      "validation": [
        "Manifest parses as JSON",
        "Every system entry declares authority_status and validation_mode"
      ],
      "context_files": [
        "RULES.md",
        "ARCHITECTURE.md",
        "TRUTH_GAPS.md",
        "RUNTIME_AUTHORITY_POINTERS.md"
      ]
    },
    {
      "id": "S2",
      "task": "Implement static verifier for required paths, conflict markers, stale ports, wrapper drift, and non-authority surfaces.",
      "requirements": [
        "Stable output ordering",
        "No network calls in static mode",
        "Unexpected missing required paths fail nonzero"
      ],
      "commands": [
        "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static"
      ],
      "expected_files": [
        "scripts/verify_runtime_authority.py"
      ],
      "validation": [
        "Known conflicts are reported deterministically",
        "Unexpected authority drift fails nonzero"
      ],
      "context_files": [
        "SYSTEM_TaskOrchestrator.md",
        "SYSTEM_ConPort.md",
        "SYSTEM_DopeMemory.md"
      ]
    },
    {
      "id": "S3",
      "task": "Add tests and reference docs for the verifier.",
      "requirements": [
        "Tests must not require Docker",
        "Docs must state that verifier supports but does not replace runtime execution"
      ],
      "commands": [
        "python -m pytest -q tests/unit/test_runtime_authority_manifest.py"
      ],
      "expected_files": [
        "tests/unit/test_runtime_authority_manifest.py",
        "docs/03-reference/governance/runtime-authority-verification.md"
      ],
      "validation": [
        "Unit tests pass",
        "Docs include known limitations, failure states, and proof expectations"
      ],
      "context_files": [
        "PAL_EXECUTION_RULES.md",
        "proof-contract.md"
      ]
    }
  ]
}
```

---

# 6. Ready TP 2 — task-orchestrator runtime

```json
{
  "id": "TP-DMX-TASKORCH-RUNTIME-001",
  "project": "dopemux",
  "target": "RUNTIME_VERIFY: reconcile task-orchestrator runtime entrypoint and port authority",
  "invariants": [
    "Task-orchestrator owns workflow transitions and workflow views only",
    "Task-orchestrator must not own passive PM metadata",
    "No local task-orchestrator PM database may be introduced in this packet"
  ],
  "depends_on": [
    "TP-DMX-RUNTIME-VERIFY-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "SERIES-DMX-AUTHORITY-001",
    "base_branch": "main",
    "parent_tp_id": "TP-DMX-RUNTIME-VERIFY-001",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "fix/task-orchestrator-runtime"
  },
  "commit": {
    "message": "Reconcile task-orchestrator runtime entrypoint and port",
    "allowlist": [
      "services/task-orchestrator/Dockerfile",
      "services/task-orchestrator/app/main.py",
      "services/task-orchestrator/task_orchestrator/app.py",
      "compose.yml",
      "docker/compose.core.yml",
      "services/registry.yaml",
      "tests/unit/test_task_orchestrator_runtime_config.py",
      "SYSTEM_TaskOrchestrator.md",
      "docs/03-reference/systems/system-boundaries.md"
    ],
    "verify": [
      "python -m pytest -q tests/unit/test_task_orchestrator_runtime_config.py",
      "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --system task-orchestrator --check static"
    ]
  },
  "pr": {
    "title": "Reconcile task-orchestrator runtime entrypoint and port",
    "body": "Aligns task-orchestrator runtime entrypoint and port references or marks unresolved runtime authority explicitly with tests and docs.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "thinkdeep",
      "challenge",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Trace task-orchestrator runtime launch paths and port references across Dockerfile, compose files, registry, app code, adapters, tests, and docs.",
      "requirements": [
        "Read-only step",
        "Classify each path as active, legacy, conflicting, or UNKNOWN"
      ],
      "commands": [
        "rg -n \"task_orchestrator\\.app|app/main|3014|8000|task-orchestrator\" services/task-orchestrator compose.yml docker/compose.core.yml services/registry.yaml src tests docs -S"
      ],
      "validation": [
        "Evidence list names every conflicting task-orchestrator path",
        "No file modifications occur in S1"
      ],
      "context_files": [
        "SYSTEM_TaskOrchestrator.md",
        "PM_PLANE.md",
        "TRUTH_GAPS.md"
      ]
    },
    {
      "id": "S2",
      "task": "Apply the smallest safe runtime alignment or mark the conflict fail-closed if evidence is insufficient.",
      "requirements": [
        "Do not alter PM authority split",
        "Do not make bridge or Leantime workflow authority",
        "Do not add broad refactors"
      ],
      "commands": [
        "python -m pytest -q tests/unit/test_task_orchestrator_runtime_config.py"
      ],
      "expected_files": [
        "services/task-orchestrator/Dockerfile",
        "tests/unit/test_task_orchestrator_runtime_config.py"
      ],
      "validation": [
        "Test proves Docker target does not point at unsupported hard-failing module",
        "Port expectation is explicit and single-valued or marked CONFLICTING"
      ],
      "context_files": [
        "SYSTEM_TaskOrchestrator.md"
      ]
    },
    {
      "id": "S3",
      "task": "Patch task-orchestrator and boundary docs to reflect verified or still-conflicting runtime state.",
      "requirements": [
        "Preserve unresolved truth as CONFLICTING or UNKNOWN",
        "Do not claim completion without validation evidence"
      ],
      "commands": [
        "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --system task-orchestrator --check static"
      ],
      "expected_files": [
        "SYSTEM_TaskOrchestrator.md",
        "docs/03-reference/systems/system-boundaries.md"
      ],
      "validation": [
        "Docs no longer contain contradictory unqualified task-orchestrator runtime claims",
        "Verifier output is captured for proof bundle"
      ],
      "context_files": [
        "RULES.md",
        "docs/03-reference/systems/system-boundaries.md"
      ]
    }
  ]
}
```

---

# 7. Ready TP 3 — ConPort authority audit

```json
{
  "id": "TP-DMX-CONPORT-AUTH-001",
  "project": "dopemux",
  "target": "AUTHORITY_RESOLUTION: resolve or explicitly preserve ConPort runtime authority conflict",
  "invariants": [
    "ConPort owns only implemented structured context, decision, progress, custom-data, and relationship-query surfaces",
    "ConPort does not own passive PM metadata, workflow legality, dope-memory chronicle, or dope-context retrieval",
    "DopeconBridge proxy routes must not become ConPort authority"
  ],
  "depends_on": [
    "TP-DMX-RUNTIME-VERIFY-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "SERIES-DMX-AUTHORITY-001",
    "base_branch": "main",
    "parent_tp_id": "TP-DMX-RUNTIME-VERIFY-001",
    "final_packet": false
  },
  "execution": {
    "agent": "gemini",
    "branch": "audit/conport-runtime-authority"
  },
  "commit": {
    "message": "Add ConPort runtime authority audit",
    "allowlist": [
      "docs/03-reference/governance/conport-runtime-authority-audit.md",
      "SYSTEM_ConPort.md",
      "TRUTH_CANONICALS.md",
      "TRUTH_SCOPE.md"
    ],
    "verify": [
      "test -f docs/03-reference/governance/conport-runtime-authority-audit.md",
      "rg -n \"CONFLICTING|UNKNOWN|enhanced_server|memory_server|3004|3005|4004\" docs/03-reference/governance/conport-runtime-authority-audit.md SYSTEM_ConPort.md TRUTH_CANONICALS.md TRUTH_SCOPE.md"
    ]
  },
  "pr": {
    "title": "Audit ConPort runtime authority conflict",
    "body": "Adds a ConPort authority audit and updates docs only where runtime evidence supports the change.",
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
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Compare ConPort authority claims across truth docs, system docs, Docker sources, src runtime, compose, registry, clients, and PM plane.",
      "requirements": [
        "Read-only step",
        "Separate OBSERVED, CONFLICTING, UNKNOWN, and RECOMMENDED",
        "Do not choose a runtime without evidence"
      ],
      "commands": [
        "rg -n \"ConPort|conport|enhanced_server|memory_server|3004|3005|4004|/api/decisions|/api/progress|/api/context\" . -S"
      ],
      "validation": [
        "Audit evidence lists Docker ConPort and src/conport candidates",
        "Every claim is classified"
      ],
      "context_files": [
        "TRUTH_SCOPE.md",
        "TRUTH_CANONICALS.md",
        "SYSTEM_ConPort.md",
        "PM_PLANE.md"
      ]
    },
    {
      "id": "S2",
      "task": "Write a ConPort runtime authority audit document with exact unresolved facts and runtime proof needed.",
      "requirements": [
        "No code edits",
        "Do not erase historical conflict",
        "Do not treat bridge routes as authority"
      ],
      "expected_files": [
        "docs/03-reference/governance/conport-runtime-authority-audit.md"
      ],
      "validation": [
        "Audit names primary candidate runtime, alternate candidate runtime, ports, storage, API surfaces, and confidence",
        "Audit contains explicit next validation command list"
      ],
      "context_files": [
        "SYSTEM_DopeconBridge.md",
        "TRUTH_GAPS.md"
      ]
    },
    {
      "id": "S3",
      "task": "Patch ConPort docs only where the audit proves a stronger statement; otherwise mark conflict as CONFLICTING.",
      "requirements": [
        "No unqualified canonicality claim without runtime evidence",
        "Preserve UNKNOWN where deployment proof is absent"
      ],
      "commands": [
        "rg -n \"CONFLICTING|UNKNOWN|enhanced_server|memory_server|3004|3005|4004\" docs/03-reference/governance/conport-runtime-authority-audit.md SYSTEM_ConPort.md TRUTH_CANONICALS.md TRUTH_SCOPE.md"
      ],
      "expected_files": [
        "SYSTEM_ConPort.md",
        "TRUTH_CANONICALS.md",
        "TRUTH_SCOPE.md"
      ],
      "validation": [
        "Docs reflect either verified deployed authority or explicit unresolved conflict",
        "No bridge, adapter, or retrieval surface is promoted to authority"
      ],
      "context_files": [
        "RULES.md",
        "SYSTEM_ConPort.md"
      ]
    }
  ]
}
```

---

# 8. Workstream backlog after first series

| Rank | Packet                        | Workstream | Why                                                                 | Validation                                                     |
| ---: | ----------------------------- | ---------- | ------------------------------------------------------------------- | -------------------------------------------------------------- |
|    4 | `TP-DMX-PM-PORTS-001`         | PM         | PM endpoint splits can break canonical writer routing.              | Unit/static tests for writer destinations.                     |
|    5 | `TP-DMX-BRIDGE-WRITER-001`    | Bridge     | Proxy routes look authoritative. Tiny UI tragedy waiting to happen. | Route-to-upstream-writer table and tests.                      |
|    6 | `TP-DMX-MEMORY-TRANSPORT-001` | Memory     | `3020` active vs `8096` legacy drift.                               | Adapter/port audit and stale-call prevention.                  |
|    7 | `TP-DMX-DOC-TRUST-001`        | Docs       | Agents need doc reliability map.                                    | Every doc classified with trust status.                        |
|    8 | `TP-DMX-DOC-BOUNDARIES-001`   | Docs       | Boundary docs must not encode stale runtime claims.                 | Diff review against verifier output.                           |
|    9 | `TP-DMX-AGENTS-CREATE-001`    | Agents     | Planner/implementer/reviewer/testgen roles need hard boundaries.    | `.github/agents/*.agent.md` validates and follows tool limits. |
|   10 | `TP-DMX-PROOF-GATE-001`       | Governance | Proof contracts need enforcement, not vibes.                        | Proof fixtures pass/fail correctly.                            |

---

# 9. Human decisions needed

| Decision        | Needed before                   | Options                                                                       | Recommendation                                                                        |
| --------------- | ------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| TaskX naming    | Kernel command doc/code cleanup | Preserve TaskX alias or move operator language to dopetask-first              | Keep `taskx` shim, move docs/operator language to dopetask-first after wrapper tests. |
| ConPort runtime | PM endpoint finalization        | Docker `enhanced_server.py` primary, `src/conport` primary, or explicit split | Let runtime/compose evidence decide; do not decide from docs.                         |
| Agent authority | Agent automation                | Treat existing agent families as runtime authorities or helpers               | Treat as helpers only until separate authority audit.                                 |
| Unsafe docs     | Upload refresh                  | Exclude forever, redact, or inspect locally only                              | Redact and scan twice before upload.                                                  |
| PR batching     | First execution series          | One PR per TP or one PR for authority series                                  | One PR per TP for P0 runtime work; don’t bundle blast radius like a maniac.           |

---

# 10. Proof bundle required per TP

Every executed packet must return:

| Proof field        | Required content                         |
| ------------------ | ---------------------------------------- |
| `slices_completed` | Step IDs completed                       |
| `validations`      | Commands, outputs, exit codes            |
| `diff_stat`        | `git diff --stat`                        |
| `diff`             | Full relevant diff or artifact path      |
| `risks`            | Residual risks, not “none” unless proven |
| `warnings`         | Non-blocking drift                       |
| `blockers`         | Blocking facts                           |
| `worktree_path`    | Absolute path                            |
| `branch`           | Verified branch                          |
| `repo_identity`    | Marker/origin result                     |
| `pr_url`           | Required after PR creation               |
| `cleanup_status`   | Worktree removed or blocker stated       |

Proof is mandatory because the repo’s proof contract requires substantive runs to emit evidence, manifests, blockers/warnings, and handoff bundles when control passes across skills. 

---

# 11. Stop conditions

Stop immediately if any of these happen:

| Stop condition                                            | Reason                                     |
| --------------------------------------------------------- | ------------------------------------------ |
| `.dopetaskroot` missing                                   | Wrong repo or unsafe checkout.             |
| Worktree is primary checkout                              | Violates execution discipline.             |
| Branch does not match TP                                  | Cross-series mutation risk.                |
| Runtime evidence contradicts planned target               | Re-plan; do not patch around it.           |
| Required file outside allowlist is needed                 | TP scope must be revised before edits.     |
| Secret-pattern file is needed                             | Redaction workflow first.                  |
| Bridge/mirror/retrieval starts being treated as canonical | Architecture violation.                    |
| Tests require unavailable external service                | Mark validation blocked, do not fake pass. |

---

# 12. Final operating cadence

## Per packet

```text
preflight
  -> analyze
  -> planner
  -> challenge
  -> implement slice
  -> validate slice
  -> diff inspect
  -> codereview
  -> precommit
  -> proof bundle
  -> PR
  -> handoff
```

## Per series

```text
create dedicated worktree
  -> run packets in dependency order
  -> update index / proof state
  -> open PRs
  -> capture residual risks
  -> remove worktree or report cleanup blocker
```

## Per ChatGPT supervisor pass

```json
{
  "items": [
    "Top 3 current packets",
    "Top 3 blockers",
    "Top 3 next validations"
  ],
  "more_count": "remaining backlog count",
  "next_token": "next packet or backlog cursor"
}
```

That is the actual plan: **prove authority, repair runtime drift, repair docs, then automate agents**. Anything else is just giving a confused system more keyboards.

