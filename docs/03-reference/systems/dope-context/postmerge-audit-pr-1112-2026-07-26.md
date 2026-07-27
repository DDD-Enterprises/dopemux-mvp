---
id: DOPE_CONTEXT_POSTMERGE_AUDIT_PR_1112_2026_07_26
title: Dope Context Postmerge Audit Pr 1112 2026 07 26
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Independent post-merge audit of PR 1112 recording the blocking vector
  compatibility, collection gate, and rollback findings with reproduction steps.
---
# Post-Merge Audit — PR #1112 (dope-context Voyage modernization)

## Verdict

`auditor_verdict: FAIL` · `operational_disposition: REPAIR_REQUIRED`

Repair packet: `task-packets/dope-context/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002.md`.

## Custody

| Field | Value |
|---|---|
| Merge commit | `4b42268775d1f94e26500c758128da3e11b151d5` (squash, single parent `603871f96a`) |
| PR head | `570b65a926de295d2e3d98b7776f420696d988d9` (not an ancestor of main) |
| Exact PR content | `603871f96a … 4b42268775` — 16 files, +2063 / −1056 |
| Main at audit time | `f4e91574a11e7f0e73d096b7b36def0230627727` |
| Post-merge drift | none on `services/dope-context`, `compose.yml`, `pyproject.toml`, `uv.lock` |

The PR's recorded `baseRefOid` (`70d81b23…`) is two commits behind the true merge
parent; diffing from it pulls in unrelated commits.

## Blocking findings

### F-001 — code `content_vec` index and query use different model families

`indexing_pipeline.py:283-289` embeds code content through
`ContextualizedEmbedder.embed_document(model="voyage-context-3")`, which
`resolve_context_model` rewrites to `voyage-context-4` on the
`contextualized_embeddings` endpoint. `server.py:1205-1209` embeds the content
query with `voyage-code-3` on the standard `embeddings` endpoint. Both produce
1024-dimensional vectors, so Qdrant stores and searches them without complaint.
`content_weight` dominates `SearchProfile.implementation()`.

Voyage documentation is silent on cross-family comparability; the only stated
compatibility concerns `input_type` variants of the same model.

Counter-evidence recorded for fairness: `voyage-code-3` and `voyage-context-4`
ship an identical tokenizer and vocabulary (both 151,665 entries; a mixed
code/CJK probe encodes to byte-identical ids). That constrains the input side
only and does not establish a shared output space, but the realistic outcome may
be partial degradation rather than noise. The defensible claim is "not proven
comparable".

Introduced by: pre-existing. PR #1112 changed which contextualized model is used,
not the mismatch itself.

### F-002 — model migration with no collection gate

`dense_search.py:129-137` returns as soon as a collection with the name exists,
validating nothing — not model, endpoint, dimension, dtype, chunker version, nor
the `index_fingerprint` this PR added. The fingerprints are written to docs
payloads and never read. The `voyage-context-3` → `voyage-context-4` default flip
therefore mixes vector generations inside an existing collection on the next
ordinary reindex.

Introduced by: PR #1112.

### F-003 — the documented rollback flag splits index from query

`docs_pipeline.py:233-239` indexes with `self.embedder.default_model`, so
`DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3` never applies to it. `server.py:1743` embeds
the query with a hard-coded `"voyage-context-3"` literal, so the flag does apply.
Setting the flag alone yields index `voyage-context-4` / query `voyage-context-3`.

The rollback that actually works is `DOPE_CONTEXT_DOC_EMBED_MODEL=voyage-context-3`,
which the PR does not document.

Introduced by: PR #1112.

## Non-blocking findings

| ID | Sev | Area | Summary |
|---|---|---|---|
| F-004 | HIGH | review-integrity | Both "resolved" review threads are unfixed: `token_count_exact=True` is still hard-coded at `voyage_embedder.py:286`, and `_existing_point_ids` still ignores `file_path`/`doc_id` |
| F-005 | HIGH | proof-content-integrity | `remaining_risks: []` and `findings: []` are false against five open items shipped in the same commit; report is evidence-free; independence unknown; valid signature attests to it |
| F-006 | HIGH | operational-risk | Tokenizer performs an undeclared `huggingface.co` fetch; the SDK never memoizes failures, so a blocked Hub costs one failed request per unique chunk |
| F-007 | HIGH | efficiency | Stale lookup moved inside the per-document loop: one full-collection scroll per document, was one per workspace |
| F-016 | HIGH | deployment-drift | The merged code is not deployed; the running container predates the merge and has no `model_registry` |
| F-017 | HIGH | mcp-budgeting | `search_code` can return zero results: only the content field is trimmed but the whole dict is measured, and `context` is unbounded |
| F-008 | MEDIUM | test-coverage | Nine MCP tool tests fail identically before and after the merge, so the paths carrying F-001/F-003 are untested |
| F-009 | MEDIUM | index-integrity | Fingerprints are written to docs payloads only; code payloads carry no provenance |
| F-010 | MEDIUM | dependency | The `voyageai>=0.5.0` constraint governs the image only; repo resolves 0.3.7, running container 0.4.1. `return_documents` exists in no SDK version |
| F-011 | MEDIUM | observability | Rerank failure returns input order with `tokens=0`, indistinguishable from success |
| F-012 | MEDIUM | resource | Unbounded caches returning embeddings by reference |
| F-013 | LOW | registry | `voyage-3-lite` request ceiling is 1M, should be 120K |
| F-014 | LOW | correctness | Reranker 8K per-query and 32K pair limits unenforced |
| F-015 | LOW | determinism | Point-ID determinism depends on a `workspace_id` one code path sets to `"default"` |

## What the PR got right

The registry is accurate against vendor documentation verified 2026-07-26: all
seven embedding prices, both reranker prices, every supported dimension set, all
32K per-input limits, the 1,000-input and 16K-chunk caps, the 1,000-document and
600K-token rerank caps, and the rerank billing formula
(`query × n_docs + Σ docs`). The only error is `voyage-3-lite` (F-013).

Deterministic UUIDv5 point IDs are collision-safe across directories and
workspaces. Upsert-before-delete genuinely preserves the last good index under
both embedding failure and Qdrant batch failure. Reindexing is idempotent and
shrinking documents drop their tail chunks correctly. Basename-only cleanup is
gone.

The MCP estimator's conservatism claim holds — measured against the real
`voyage-code-3` tokenizer it never under-counts (ASCII 1.00×, CJK 2.00×,
minified JSON 1.67×, emoji 1.33×).

The `SELECTIVE_REFRESH_REQUIRED` decision is correct and upheld. Upstream
`zilliztech/claude-context` at `6fc318b4` — the same head the merged audit
document inspected — has no contextualized-embedding support at all, no
three-vector schema, and no autonomous indexing. Replacement would delete
capability. Three upstream patterns remain worth backporting and are honestly
listed as open: gitignore negation matcher, canonical index root, deleted-file
reconciliation.

## Runtime state at audit time

- Target Qdrant holds zero collections
  (`curl -s http://localhost:6333/collections`).
- `mcp-dope-context` is healthy but was built 2026-06-20 and created 2026-07-01,
  both predating the merge; `model_registry` is absent from it.

F-002's hazard is therefore prospective, not realized. Deployment, not
re-indexing, is the gating event.

## Validation

| Check | Result |
|---|---|
| `compileall services/dope-context/src` | PASS |
| focused pytest (the PR's own claim) | PASS — 15 passed |
| full `services/dope-context/tests` | 9 failed, 34 passed, 1 skipped |
| same suite at pre-merge base `603871f` | identical 9 failures — pre-existing |
| docker build | PASS |
| container no-network import smoke | PASS — `voyageai 0.5.0` in image |
| `pre-commit run --files` (11 changed files) | PASS, but no Python linter hook is configured |
| proof signature (`ssh-keygen -Y verify`) | PASS — valid, signer registered |
| adversarial batteries A / B / C | 6 of 15, 2 of 6, 1 of 6 FAIL |

Not run: live Voyage requests, Qdrant mutation, and the empirical cross-model
comparability benchmark — all require billable calls or production data.

## Correction recorded

An earlier draft claimed a systemic proof-governance gap, on the grounds that the
schema `report_path` regex, `.validator_scope.json`, and the pre-commit hook all
exclude `proof/pr_merge/embedded-audit/**`. That claim is **withdrawn**. The
exclusion is deliberate: `local_audit_acceptance.py:186-197` documents that
`report_path` is intentionally not validated for locally-attested bundles because
the trusted CI emitter overrides it, and
`.github/workflows/embedded-audit.yml:269,344,396` confirm it writes a fresh
`PROOF.json`. Running `validate_audit_proof.py` against a `pr_merge` bundle is a
category error. F-005's content findings are unaffected.
