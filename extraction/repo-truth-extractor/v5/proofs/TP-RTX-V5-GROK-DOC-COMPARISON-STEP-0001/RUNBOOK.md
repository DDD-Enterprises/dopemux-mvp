---
title: "TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001 \u2014 Runbook"
type: how-to
status: active
prelude: Operator commands for the Grok comparison lane on v5 repo-truth-extractor.
tags:
- comparison-lane
- runbook
- grok
- v5
- operator
id: RUNBOOK
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-13'
last_review: '2026-03-13'
next_review: '2026-06-11'
---
# Runbook: Grok Comparison Lane

## ⚠️ Safety Note

**Never run `run_extraction_v5.py` directly in a live environment without understanding
the full cost implications.** Each run invokes provider APIs and may incur charges.
A single accidental run cost $10 in March 2026.

This runbook is reference documentation for operators who have already reviewed the cost
implications and have explicit authorization to run the extractor.

---

## Mode 1: Default Run (No Comparison)

Normal canonical run — unchanged behavior:

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --run-id FULL_RUN \
  --phase ALL
```

No `--compare-mode` flag = comparison disabled. Zero impact on behavior.

---

## Mode 2: Compare H9 Only

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --run-id COMPARE_H9 \
  --compare-mode additional \
  --compare-provider xai \
  --compare-model grok-4.20-beta \
  --compare-steps H9
```

**What happens:**
1. Canonical run for H9 proceeds normally
2. After canonical completes, comparison lane runs H9 partitions with `grok-4.20-beta`
3. Comparison outputs written to `runs/COMPARE_H9/H_home_entrypoints/raw/comparison/xai__grok-4.20-beta/`
4. Summary written to `runs/COMPARE_H9/H_home_entrypoints/COMPARE_SUMMARY_H9.json`
5. Canonical `PASS/FAIL` status is unaffected

---

## Mode 3: Compare Multiple Doc-Heavy Steps

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --run-id COMPARE_MULTI \
  --compare-mode additional \
  --compare-provider xai \
  --compare-model grok-4.20-beta \
  --compare-steps H9,A9,R9,S9
```

---

## Mode 4: Compare All Eligible Steps (use default allowlist)

Omit `--compare-steps` to use the full `COMPARISON_ELIGIBLE_STEPS` allowlist:

```bash
python services/repo-truth-extractor/run_extraction_v5.py \
  --run-id COMPARE_ALL_ELIGIBLE \
  --compare-mode additional \
  --compare-provider xai \
  --compare-model grok-4.20-beta
```

Current allowlist: `A9, B9, G9, H9, R9, S9, T9, W9, X9`

---

## Inspecting Comparison Summaries

### JSON summary (machine-readable)

```bash
cat runs/COMPARE_H9/H_home_entrypoints/COMPARE_SUMMARY_H9.json | python -m json.tool
```

### Markdown summary (human-readable)

```bash
cat runs/COMPARE_H9/H_home_entrypoints/COMPARE_SUMMARY_H9.md
```

### List all comparison outputs for a run

```bash
find runs/COMPARE_H9 -path "*/raw/comparison/*" -name "*.json" | sort
```

### Check for comparison failures

```bash
find runs/COMPARE_H9 -name "*.FAILED.*" | grep comparison
```

### View comparison artifact for a specific partition

```bash
cat runs/COMPARE_H9/H_home_entrypoints/raw/comparison/xai__grok-4.20-beta/H9__H_P0001.json \
  | python -m json.tool
```

---

## Verifying Non-Canonical Behavior

Confirm comparison artifacts are separate from canonical:

```bash
# These should NOT exist in canonical raw dir:
ls runs/COMPARE_H9/H_home_entrypoints/raw/ | grep comparison
# Expected: comparison/ (subdir)

# Canonical artifacts exist at top level:
ls runs/COMPARE_H9/H_home_entrypoints/raw/ | grep -v comparison
# Expected: H9__*.json files
```

---

## Eligible Steps Reference

Current `COMPARISON_ELIGIBLE_STEPS`:

```python
{"A9", "B9", "G9", "H9", "R9", "S9", "T9", "W9", "X9"}
```

To validate a step is eligible:

```bash
python3 -c "
import sys
sys.path.insert(0, 'services/repo-truth-extractor')
import importlib.util
spec = importlib.util.spec_from_file_location(
    'run_extraction_v5', 'services/repo-truth-extractor/run_extraction_v5.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
step = 'H9'
print(f'{step} eligible:', step in m.COMPARISON_ELIGIBLE_STEPS)
"
```

---

## Disabling Comparison Mid-Run (Resume)

If comparison was enabled but you want to resume without comparison:

Simply omit `--compare-mode`. Canonical resume proceeds normally.
Existing comparison artifacts are left in place (not deleted).

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ValueError: Comparison steps not in eligible set` | `--compare-steps` includes a non-eligible step | Check `COMPARISON_ELIGIBLE_STEPS` |
| `COMPARE_LANE_ERROR` in logs | Comparison lane raised an exception | Check `*.FAILED.txt` sidecars; canonical unaffected |
| No `COMPARE_SUMMARY_*` files | Comparison disabled or step not in allowlist | Verify `--compare-mode additional` and `--compare-steps` |
| `grok-4.20-beta` auth failure | XAI API key missing or invalid | Check `XAI_API_KEY` env var |
