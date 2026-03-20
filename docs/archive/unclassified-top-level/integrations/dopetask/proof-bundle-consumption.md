---
id: PROOF_BUNDLE_CONSUMPTION
title: Proof Bundle Consumption
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Proof Bundle Consumption (explanation) for dopemux documentation and developer
  workflows.
---
# Proof Bundle Consumption

## Overview

`DopetaskBundleLoader` is responsible for finding, loading, and validating proof bundles
emitted by Dopetask flight-deck engines. It provides a stable interface over the variable
naming conventions used by different engine lanes.

---

## Bundle Discovery

Given a `bundle_root` directory and a `tp_id`, the loader searches in order:

1. `{bundle_root}/TP-{tp_id}_PROOF_BUNDLE.json` — canonical bundle name
2. `{bundle_root}/*MANIFEST.json` — manifest fallback (closed_loop lane)
3. `{bundle_root}/*BUNDLE.json` — generic bundle fallback

The first match wins. If no file is found, `find_bundle()` returns `None`.

Example for `TP-PRMS-052`:
```
bundle_root = proof/pr_merge/flight_deck/closed_loop/
→ looks for: TP-PRMS-052_PROOF_BUNDLE.json
→ fallback:  CLOSED_LOOP_MANIFEST.json   ← found
```

---

## Required Fields

A valid bundle must contain all of the following top-level keys:

```
tp_id | pr_id      — task packet or PR identifier (one is required)
status              — TP lifecycle status string
summary             — dict with result/next_action/confidence/risk
acceptance_checks   — list of check dicts
validation          — dict with outcome/gates
artifacts           — list of artifact file names
manifest            — dict with generator/cycle_id/posture
```

If any required field is missing, `BundleSchemaError` is raised with a message listing
all missing fields. The adapter sets `integration.adapter_status = "ERROR"` and
`integration.errors` contains the exception message.

---

## Optional Fields

These fields are read if present; their absence does not cause an error:

| Field | Used for | Default if absent |
|-------|----------|-------------------|
| `posture` | posture.mode | `"UNKNOWN"` |
| `next_tactic` | summary.next_action hint | derived from posture |
| `allowed_actions` | governance.allowed_actions | `[]` |
| `blocked_actions` | governance.blocked_actions | `[]` |
| `key_findings` | summary.key_findings | `[]` |
| `key_caveats` | summary.key_caveats | `[]` |
| `run_id` | tp.run_id | `"UNKNOWN"` |

---

## Proof Ref Extraction

`extract_proof_ref(bundle, bundle_path)` builds a `DopetaskProofRef` by:

1. Setting `bundle_path` = the path of the loaded file (stringified)
2. Setting `bundle_present` = `True` (it was loaded successfully)
3. Deriving `archive_path` by replacing bundle filename with `{lane}.zip`
   (e.g. `closed_loop/CLOSED_LOOP_MANIFEST.json` → `closed_loop.zip` in parent dir)
4. Setting `archive_present` = `True` if derived archive exists on disk
5. Collecting `supporting_artifacts` from `bundle["artifacts"]` list

---

## Fail Behavior

| Condition | Behavior |
|-----------|----------|
| File not found | `find_bundle()` returns `None`; caller decides |
| Invalid JSON | `json.JSONDecodeError` propagates; adapter catches and sets ERROR |
| Missing required field | `BundleSchemaError` raised; adapter catches and sets ERROR |
| Missing archive | `archive_present=False`, `warnings` list updated, status stays READY |
| Unknown posture value | Mapped to `"UNKNOWN"`, warning added |
| Unknown status value | Mapped to `"UNKNOWN"`, warning added |

---

## Direct Load API

```python
from pathlib import Path
from dopemux_pr_merge_specialist.dopetask_bundle_loader import DopetaskBundleLoader

loader = DopetaskBundleLoader(Path("proof/pr_merge/flight_deck/closed_loop"))

# Find by TP ID
path = loader.find_bundle("TP-PRMS-052")  # → Path or None

# Load and validate
bundle = loader.load(path)  # → dict, raises BundleSchemaError if invalid

# Extract proof ref
proof_ref = loader.extract_proof_ref(bundle, path)
```
