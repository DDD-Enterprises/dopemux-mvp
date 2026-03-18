---
id: REQUIRED_TESTS_v0.1
title: Required Tests V0.1
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: Required Tests V0.1 (reference) for dopemux documentation and developer workflows.
---
# Required tests (v0.1)

## test_ids.py
- Same input -> same output every run
- Different namespaces -> different IDs
- IDs are URL/path safe

## test_timeutil.py
- Vancouver tz conversion deterministic
- Daypart mapping stable
- Operator time parsing never invents dates

## test_schema_validation.py
- Invalid JSON rejected
- Invalid enum rejected
- One repair attempt invoked once then fails

## test_rotation_active_filter.py
- supervisor ignores ads where position_on_site > 50

## test_set_immutability.py
- reorder creates new set_id, old set remains intact

## test_exposure_estimator.py
- given two observations and a weight profile, results are deterministic
