# Implementation report — TP-DOPECONTEXT-VOYAGE4-REPAIR-0002

## Design selected for code content_vec

Behavior-preserving correctness repair: index and query both use the configured
contextual model on the `contextualized_embeddings` endpoint. Query uses a
single chunk with auto-chunking disabled and extracts exactly one vector.

Title/breadcrumb remain `voyage-code-3` / `embeddings`.

## Collection migration

New writes use `code_<ws>_<digest>` / `docs_<ws>_<digest>`. Legacy unversioned
collections are reported only. Manifest mismatch fails closed. No automatic
deletion or rewrite of existing collections.

## Rollback

```bash
DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL=voyage-context-3
```

## Findings disposition

| ID | Disposition |
|----|-------------|
| F-001 | REPAIRED |
| F-002 | REPAIRED |
| F-003 | REPAIRED |
| F-004 | REPAIRED |
| F-006 | REPAIRED |
| F-007 | REPAIRED |
| F-008 | REPAIRED |
| F-009 | REPAIRED |
| F-010 | REPAIRED |
| F-011 | REPAIRED |
| F-012 | REPAIRED |
| F-013 | REPAIRED |
| F-014 | REPAIRED |
| F-015 | REPAIRED |
| F-017 | REPAIRED |
| F-005 withdrawn proof regex | OUT_OF_SCOPE |

## Residual risks

- No live Voyage billable benchmark.
- Operator must reindex into versioned collections; legacy not auto-read.
- Embedded audit must be independent (not same implementer session).
- Deployment NOT_RUN.
