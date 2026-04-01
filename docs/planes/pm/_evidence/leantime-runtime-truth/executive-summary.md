---
id: leantime_runtime_truth_executive_summary
title: Leantime Runtime Truth Executive Summary
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Short supervisor-facing summary of current Leantime runtime truth in this repository.
---
# Leantime - Executive Summary

- Leantime is still the correct PM operational system of record.
- The primary proved integration seam here is JSON-RPC over `/api/jsonrpc` with `x-api-key`.
- dopecon-bridge translates normalized PM requests into Leantime ticket operations.
- Workflow-significant changes are deliberately blocked from being treated as Leantime-owned decisions.
- The main evidence limit is that this repo proves the adapter layer, not the upstream Leantime internals.
