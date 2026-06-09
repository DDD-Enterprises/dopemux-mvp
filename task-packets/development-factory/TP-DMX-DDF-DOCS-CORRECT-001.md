---
id: TP-DMX-DDF-DOCS-CORRECT-001
title: Correct Development Factory Docs Against Evidence-Gate Findings
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-06'
status: READY_FOR_REVIEW
prelude: Docs-only trust-repair packet. Corrects stale/incorrect claims in the Development Factory docs (TP-DMX-DDF-DOCS-001) against the verification results from TP-DMX-EVIDENCE-GATE-VERIFY-001.
---
# Task Packet: TP-DMX-DDF-DOCS-CORRECT-001 · Development Factory · Correct Docs Against Evidence-Gate Findings

════════════════════════════════════════════════════════════

## Objective

Correct the Development Factory documentation created by `TP-DMX-DDF-DOCS-001` so it reflects the verification results from `TP-DMX-EVIDENCE-GATE-VERIFY-001`. Docs-only trust repair before any further factory automation proceeds.

────────────────────────────────────────────────────────────

## Why This Packet Exists Now

`TP-DMX-EVIDENCE-GATE-VERIFY-001` (read-only, HEAD `8042f9f9f`) found materially stale or incorrect claims in the initial DDF docs:

- `monitoring-dashboard` port was documented as `1561`; real port is `8098` (line-number confusion).
- RTE S7 was framed as an always-PASS stub; implementation is present and wired at HEAD (`collect_truth_split` → `all_blockers`).
- RTE SP contracts were framed as missing; `SP_CONTRACT_MISSING` blocker is present at HEAD.
- DCP seam was framed as docs-only; executable `RedLaneScanner` exists (though unwired to CI/steward).
- `dope-memory` / `working-memory-assistant/main.py` was framed as an orphan safe to delete; it is imported by sibling modules.
- The build order assumed build-from-scratch where verify-and-close is correct.

Building automation on stale docs is the exact failure mode the evidence gate exists to prevent.

────────────────────────────────────────────────────────────

## Scope

IN (modify existing docs + create packet/proof):

* `docs/03-reference/development-factory/` (the 15 docs — modified as needed)
* `task-packets/development-factory/TP-DMX-DDF-DOCS-CORRECT-001.md`
* `proof/TP-DMX-DDF-DOCS-CORRECT-001/PROOF.json`
* `proof/TP-DMX-DDF-DOCS-CORRECT-001/SUMMARY.md`

OUT (do not touch):

* runtime code, schemas, `config/`, `.github/workflows/`
* Task-Orchestrator / Dopetask / ConPort / dope-memory / dope-context / dopecon-bridge state
* GitHub state, merge automation
* `queue_drain.py`, `scripts/batch_resolve_and_merge.py`

Do NOT create: `schemas/development-factory/`, `config/ai/model-routing.policy.yaml`, `task-packets/templates/EXECUTION_CAPSULE_TEMPLATE.md`.

────────────────────────────────────────────────────────────

## Invariants

* Docs-only packet. No runtime code, schema, or config touched.
* No service/task/proof-policy/GitHub state changed.
* No secrets printed.
* All corrections preserve uncertainty: verification was static (code read + `docker ps`), not a gate run. Corrections say "implementation present at HEAD, verify-not-assume" — never "fixed."
* `queue_drain.py` / `batch_resolve_and_merge.py` not touched, imported, or executed.

────────────────────────────────────────────────────────────

## Corrections Applied

1. **monitoring-dashboard:** `1561` → `8098` in `red-lines-and-stop-conditions.md` (register row + detail heading) and `open-questions.md` (VG-004). Noted latent (not running) + line-number-confusion provenance.
2. **RTE S7:** reframed in `red-lines-and-stop-conditions.md`, `autonomy-ladder.md`, `open-questions.md` (VG-005) from "always-PASS stub, must fix" → "implementation present at HEAD, verify-and-close (run against injected drift, confirm FAIL)."
3. **RTE SP contracts:** reframed in `red-lines-and-stop-conditions.md`, `open-questions.md` from "missing/ungated" → "verify `SP_CONTRACT_MISSING` blocks ungated SP."
4. **DCP seam:** `red-lines-and-stop-conditions.md` + `build-series.md` + `open-questions.md` (VG-007) note executable `RedLaneScanner` exists but is unwired to CI/steward → re-scope to "wire existing scanner." Hard-block on `queue_drain.py` / `batch_resolve_and_merge.py` preserved.
5. **dope-memory/WMA:** `architecture.md` + `open-questions.md` (VG-010) — `main.py` is imported by `trigger_manager.py`/`cache_manager.py`, NOT an orphan, NOT safe to delete.
6. **LIVE_WRITE_READY:** `autonomy-ladder.md` corrected — no schema defines it (prior "schema exists in schemas/dcp/" was wrong); tests forbid defining it; remains true L4+ blocker (VG-006).
7. **Build series:** `build-series.md` re-sequenced to verify-and-close-first order; added `TP-DMX-DCP-SEAM-LIFT-001` (last); preserved `TP-DMX-AGENT-AUTHORITY-001` as a LIVE_WRITE_READY prerequisite.
8. **Decision record:** added decisions — "docs are not source truth; patch before guiding agents" + "S7/SP/seam are verify-and-close."

────────────────────────────────────────────────────────────

## Exact Commands to Run

* `rg -n "1561|8098|S7|always-PASS|SP_CONTRACT|DCP-RED-MERGE-SEAM|RedLaneScanner|main.py|orphan|LIVE_WRITE_READY" docs/03-reference/development-factory`
* `find docs/03-reference/development-factory -maxdepth 1 -type f | sort`
* required-files existence check (python)
* `python -m json.tool proof/TP-DMX-DDF-DOCS-CORRECT-001/PROOF.json`
* `git status --porcelain` (untracked-aware)
* scope-escape grep: `git status --porcelain | rg "queue_drain|batch_resolve_and_merge|schemas/development-factory|config/ai|EXECUTION_CAPSULE_TEMPLATE"` → must be empty

────────────────────────────────────────────────────────────

## Acceptance Criteria

* All stale `monitoring-dashboard 1561` claims corrected to `8098`.
* S7 docs say verify-and-close, not build-from-scratch.
* SP docs say verify `SP_CONTRACT_MISSING`, not build-from-scratch.
* DCP seam docs say verify existing `RedLaneScanner` / wire into CI/steward, not docs-only.
* dope-memory/WMA `main.py` disposition corrected (not orphan).
* Build series order updated.
* Packet exists; proof JSON exists and validates; summary exists.
* No forbidden paths touched; final `git status --porcelain` limited to allowed docs/task/proof paths.

────────────────────────────────────────────────────────────

## Rollback

* `git checkout -- docs/03-reference/development-factory/` (revert doc edits)
* `rm -rf task-packets/development-factory/TP-DMX-DDF-DOCS-CORRECT-001.md proof/TP-DMX-DDF-DOCS-CORRECT-001/`

────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOP CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stop immediately if a correction requires: runtime code / schema / config changes, Task-Orchestrator or ConPort/dope-memory/dope-context/dopecon-bridge writes, Dopetask execution, GitHub mutation, touching `queue_drain.py` or `scripts/batch_resolve_and_merge.py`, or if evidence conflicts with the described corrections (escalate to supervisor). If stopped, return attempted steps, evidence collected, exact blocker, recommended next action.

## Next Recommended Packet

`TP-RTE-S7-DRIFT-FIX-001` (re-scoped to verify-and-close).
