---
id: gpt-facade-read-only-boundary-v1
title: "GPT Facade Read-Only Boundary V1"
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-08-27'
last_review: '2026-08-27'
next_review: '2026-09-27'
status: accepted
prelude: Freeze exact six-tool ChatGPT facade inventory as read-only evidence access over opaque targets.
---

# GPT Facade Read-Only Boundary V1

Current P0 facade inventory is exactly six tools:

1. `list_targets`
2. `get_target_capabilities`
3. `get_target_repo_state_snapshot`
4. `list_target_proof_bundles`
5. `fetch_target_proof_bundle`
6. `get_target_runtime_receipt`

Targets remain opaque and consent-bound. Resolution and ownership evidence must
fail closed before backend access. Returned snapshots, proof bundles, and runtime
receipts are evidence; they do not grant PM, workflow, canonical memory,
repository, task, merge, provider, or activation authority.

Forbidden surface includes arbitrary path/URL/token targets, backend lifecycle,
writes, provider execution, task transitions, repository mutation, audit
judgment, merge, and activation. A seventh tool requires a separate accepted
contract change and deterministic inventory update.
