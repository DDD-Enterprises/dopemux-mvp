---
id: repo-truth-extractor-reference
title: Repo Truth Extractor Reference
type: reference
owner: '@hu3mann'
date: '2026-05-26'
last_review: '2026-05-26'
next_review: '2026-08-24'
author: '@hu3mann'
prelude: Repo Truth Extractor Reference (reference) for dopemux documentation and
  developer workflows.
---
# Repo Truth Extractor Reference

## Print Config Cost Profile Contract

`services/repo-truth-extractor/run_extraction_v5.py --print-config` emits
the resolved cost profile as a top-level `cost_profile` string.

The field is the canonical operator-visible cost-profile selector. Its value
matches `--cost-profile` after legacy-name normalization. When no profile is
provided, the value is `value-default`.

During the compatibility window, legacy routing surfaces remain present:

- `cli.routing_policy` reports the routing policy derived from the resolved
  profile.
- `route_readiness_summary.target_policy` reports the same derived routing
  policy for existing readiness consumers.

Consumers should prefer top-level `cost_profile` for profile identity and treat
the routing-policy fields as compatibility metadata.
