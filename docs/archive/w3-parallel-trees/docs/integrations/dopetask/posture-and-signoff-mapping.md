---
id: POSTURE_AND_SIGNOFF_MAPPING
title: Posture And Signoff Mapping
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Posture And Signoff Mapping (explanation) for dopemux documentation and developer
  workflows.
---
# Posture and Signoff Mapping

## Core Rule: No Flattening

The adapter NEVER flattens, promotes, or demotes posture values. Dopetask's governance
semantics are preserved exactly. The only transformation allowed is the derivation of
`summary.headline_state` — a display-only label that does NOT affect governance fields.

---

## Posture Mode Values

| Mode | Description |
|------|-------------|
| `GO_SUPERVISED_ONLY` | Apply is allowed but every action requires signoff |
| `ADVISORY_ONLY` | Engine provides recommendations only; no auto-apply |
| `LIVE_SAFE` | Low-risk auto-apply permitted; still monitored |
| `DEFER_ONLY` | All actions deferred; human must initiate |
| `GO_FULL_AUTO` | Full automation permitted within risk threshold |
| `HOLD` | All actions blocked; engine is frozen |
| `UNKNOWN` | Posture could not be determined from bundle |

---

## Signoff Derivation Table

| `posture.mode` | `signoff_required` | `advisory_only` | `defer_only` | `auto_apply_allowed` | `auto_apply_risk_threshold` |
|----------------|---------------------|-----------------|--------------|----------------------|-----------------------------|
| `GO_SUPERVISED_ONLY` | **true** | false | false | true | `LOW` |
| `ADVISORY_ONLY` | **true** | **true** | false | false | `LOW` |
| `LIVE_SAFE` | false | false | false | true | `MEDIUM` |
| `DEFER_ONLY` | false | false | **true** | false | `LOW` |
| `GO_FULL_AUTO` | false | false | false | true | `HIGH` |
| `HOLD` | false | false | false | false | `LOW` |
| `UNKNOWN` | false | false | false | false | `LOW` |

---

## Headline State Derivation (display only)

`summary.headline_state` is derived solely for operator UI. It does NOT modify posture.

| `posture.mode` | `headline_state` |
|----------------|-----------------|
| `GO_SUPERVISED_ONLY` | `SUPERVISED` |
| `ADVISORY_ONLY` | `SUPERVISED` |
| `HOLD` | `BLOCKED` |
| `DEFER_ONLY` | `DEFERRED` |
| `GO_FULL_AUTO` | `READY` |
| `LIVE_SAFE` | `READY` |
| `UNKNOWN` | `UNKNOWN` |

If `tp.status` is `FAILED` or `BLOCKED`, `headline_state` is overridden to `INCIDENT`
or `BLOCKED` respectively, regardless of posture.

---

## Governance Derivation

`governance.allowed_actions` and `governance.blocked_actions` are sourced from the bundle
when present. If absent, they are derived from posture:

| `posture.mode` | Default `allowed_actions` | Default `blocked_actions` |
|----------------|--------------------------|--------------------------|
| `GO_SUPERVISED_ONLY` | `["APPLY_FIX", "MISSION_SUMMARY"]` | `["HIGH_RISK_AUTO_APPLY"]` |
| `ADVISORY_ONLY` | `["MISSION_SUMMARY"]` | `["APPLY_FIX", "MERGE", "HIGH_RISK_AUTO_APPLY"]` |
| `LIVE_SAFE` | `["APPLY_FIX", "APPROVE", "MISSION_SUMMARY"]` | `["HIGH_RISK_AUTO_APPLY"]` |
| `DEFER_ONLY` | `["MISSION_SUMMARY"]` | `["APPLY_FIX", "MERGE", "APPROVE"]` |
| `GO_FULL_AUTO` | `["APPLY_FIX", "MERGE", "APPROVE", "MISSION_SUMMARY"]` | `[]` |
| `HOLD` | `[]` | `["APPLY_FIX", "MERGE", "APPROVE", "HIGH_RISK_AUTO_APPLY"]` |
| `UNKNOWN` | `[]` | `["APPLY_FIX", "MERGE", "APPROVE", "HIGH_RISK_AUTO_APPLY"]` |

---

## Next Action Derivation

`summary.next_action` is a single operator instruction, derived from posture + status:

| posture + status | `next_action` |
|------------------|---------------|
| `GO_SUPERVISED_ONLY` + any | `"Review engine output and apply approved fixes with signoff."` |
| `ADVISORY_ONLY` + any | `"Review advisory output. No automated action will be taken."` |
| `HOLD` + any | `"Engine is on HOLD. No actions permitted. Investigate blockers."` |
| `DEFER_ONLY` + any | `"All actions deferred. Human operator must initiate manually."` |
| `GO_FULL_AUTO` + VALIDATED | `"Automation ready. Engine will apply fixes within risk threshold."` |
| `LIVE_SAFE` + VALIDATED | `"Safe automation active. Monitor for unexpected changes."` |
| any + FAILED | `"Engine run failed. Review errors and relaunch with corrected context."` |
| any + BLOCKED | `"Engine blocked. Resolve blockers before proceeding."` |
| any + UNKNOWN | `"Status unknown. Verify bundle integrity and rerun."` |

If bundle contains `key_caveats`, they are appended to `next_action` as a note.

---

## No-Flatten Invariants

The following transformations are FORBIDDEN in the adapter:

- `GO_SUPERVISED_ONLY` → `READY` ❌
- `HOLD` → `BLOCKED` (in posture.mode) ❌ — only allowed in headline_state
- `signoff_required=True` → `False` ❌
- `defer_only=True` → `False` ❌
- `advisory_only=True` → `False` ❌
