---
id: dope-context-vector-profiles-and-migration
title: Vector profiles and collection migration
type: reference
owner: '@hu3mann'
last_review: 2026-07-26
next_review: 2026-10-24
author: '@hu3mann'
date: '2026-07-26'
prelude: Vector profiles and collection migration (reference) for dopemux documentation
  and developer workflows.
---
# Vector profiles and collection migration

## Canonical vector profiles

`services/dope-context/src/index_profile.py` is the single source of truth for
named-vector configuration. Every index and query path must consume these
profiles.

| Role | Model (default) | Endpoint | Index input | Query input |
|------|-----------------|----------|-------------|-------------|
| `code.content_vec` | contextual model (`voyage-context-4`) | `contextualized_embeddings` | document | query |
| `code.title_vec` | `voyage-code-3` | `embeddings` | document | query |
| `code.breadcrumb_vec` | `voyage-code-3` | `embeddings` | document | query |
| `docs.content_vec` | contextual model | `contextualized_embeddings` | document | query |
| `docs.title_vec` | contextual model | `contextualized_embeddings` | document | query |
| `docs.breadcrumb_vec` | contextual model | `contextualized_embeddings` | document | query |

Index and query share model, endpoint, dimension, and dtype. Only the Voyage
`input_type` (`document` vs `query`) may differ for the same model.

## Contextual model configuration

Preferred:

```bash
export DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL=voyage-context-4
```

Deprecated alias (accepted only when it does not conflict):

```bash
export DOPE_CONTEXT_DOC_EMBED_MODEL=voyage-context-4
```

Conflicting simultaneous values fail closed.

### Context-3 rollback (single variable)

```bash
export DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL=voyage-context-3
```

That one variable moves **all** contextual index and query paths together
(code `content_vec` and all docs vectors).
`DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3` no longer selects models.

## Collection identity

Versioned names:

```text
code_<workspace-hash>_<profile-digest>
docs_<workspace-hash>_<profile-digest>
```

The digest is the first 12 hex chars of a SHA-256 fingerprint over every
named-vector compatibility field (model, endpoint, dimension, dtype, chunker,
schema). Changing any field produces a new collection. Legacy unversioned
names (`code_<hash>`, `docs_<hash>`) are detected and reported but **never**
selected for new writes and **never** deleted automatically.

Local manifests under `~/.dope-context/snapshots/<hash>/` record active
collection + fingerprint for diagnostics. A versioned collection whose local
manifest disagrees with the derived profile fails closed before upsert.

## Tokenizer assets / egress

Exact token counts require Voyage/Hugging Face tokenizer assets. When download
or load fails:

- failure is memoized **once per model per process**
- subsequent texts use deterministic estimation (`token_count_exact=false`)
- blocked egress must not retry once per unique text

## Residual risks

- No live Voyage embedding benchmark was run in this packet.
- Existing legacy collections require operator-driven reindex into the active
  versioned collection; reads of old collections are not auto-routed.
- Deployment of the repaired image was intentionally **not** performed.
