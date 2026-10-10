---
id: pm-plane-provenance-envelope
title: PM Plane Provenance Envelope
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-20'
next_review: '2026-06-18'
prelude: Reusable provenance contract for normalized and synthesized PM-plane reads.
---
# PM Plane Provenance Envelope

## Required fields

Each multi-plane PM read should preserve:

- `canonical_source`
- `canonical_ids`
- `supporting_sources`
- `lane_status`
- `canonicality`
- `derived_from`
- `timestamps`

## Canonicality values

- `canonical`
- `supporting`
- `derived`
- `indexed`
- `mirrored`

## Envelope rule

The provenance envelope exists to preserve source identity, not to collapse all inputs into a single implied authority.
