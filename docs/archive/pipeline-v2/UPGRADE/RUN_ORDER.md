---
id: RUN_ORDER
title: Run Order
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Run Order (explanation) for dopemux documentation and developer workflows.
---
# Quick Reference: Run Order & Output Mapping

## Sequential Run Order

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: CODE EXTRACTION (Prompts A-F)                     │
└─────────────────────────────────────────────────────────────┘

1️⃣  PROMPT A → STRUCTURE_MAP.json
              SERVICE_MAP.json
              ENTRYPOINTS.json

2️⃣  PROMPT B → CLI_SURFACE.json
              API_SURFACE.json
              MCP_SURFACE.json
              HOOKS_SURFACE.json

3️⃣  PROMPT C → EVENT_EMITTERS.json
              EVENT_CONSUMERS.json
              EVENT_ENVELOPE_FIELDS.json

4️⃣  PROMPT D → DB_SURFACE.json
              MIGRATIONS.json
              DAO_SURFACE.json

5️⃣  PROMPT E → ENV_VARS.json
              CONFIG_LOADERS.json
              SECRETS_RISK_LOCATIONS.json

6️⃣  PROMPT F → DETERMINISM_RISKS.json

┌─────────────────────────────────────────────────────────────┐
│ Phase 2: DOCS EXTRACTION (Phased Pipeline D0-CL)           │
└─────────────────────────────────────────────────────────────┘

7️⃣  PROMPT D0 → DOC_INVENTORY.json
               DOC_PARTITIONS.json
               DOC_TODO_QUEUE.json

8️⃣  PROMPT D1 → (Per partition, 17 runs)
               DOC_INDEX.partNN.json
               DOC_CLAIMS.partNN.json
               DOC_BOUNDARIES.partNN.json
               DOC_SUPERSESSION.partNN.json
               CAP_NOTICES.partNN.json

9️⃣  PROMPT D2 → (For CAP_NOTICES only, ~8 runs)
               DOC_INTERFACES.partNN.json
               DOC_WORKFLOWS.partNN.json
               DOC_DECISIONS.partNN.json
               DOC_GLOSSARY.partNN.json

🔟 PROMPT D3 → DOC_CITATION_GRAPH.json

1️⃣1️⃣ PROMPT M1 → (Merged docs artifacts)
               DOC_INDEX.json
               DOC_CLAIMS.json
               DOC_BOUNDARIES.json
               DOC_SUPERSESSION.json
               DOC_INTERFACES.json
               DOC_WORKFLOWS.json
               DOC_DECISIONS.json
               DOC_GLOSSARY.json

1️⃣2️⃣ PROMPT QA → DOC_COVERAGE_REPORT.json

1️⃣3️⃣ PROMPT CL → DOC_TOPIC_CLUSTERS.json
```

> **Note:** For doc extraction, see `PHASED_PIPELINE_GUIDE.md` for detailed execution instructions.

4️⃣  PROMPT D → DB_SURFACE.json
              MIGRATIONS.json
              DAO_SURFACE.json

5️⃣  PROMPT E → ENV_VARS.json
              CONFIG_LOADERS.json
              SECRETS_RISK_LOCATIONS.json

6️⃣  PROMPT F → DETERMINISM_RISKS.json

┌─────────────────────────────────────────────────────────────┐
│ Phase 2: DOCS EXTRACTION (Prompt G)                        │
└─────────────────────────────────────────────────────────────┘

7️⃣  PROMPT G → DOC_INDEX.json
              DOC_CLAIMS.json
              DOC_BOUNDARIES.json
              DOC_WORKFLOWS.json
              DOC_SUPERSESSION.json
              DOC_GLOSSARY.json
```

## Domain Mapping

| Prompt | Domains Extracted                                          |
| ------ | ---------------------------------------------------------- |
| A      | `code_service`, `code_entrypoint`, `doc_meta`              |
| B      | `code_cli`, `code_api`, `code_mcp`, `code_hook`            |
| C      | `code_event_emitter`, `code_event_consumer`, `code_model`  |
| D      | `code_db` (tables, indexes, triggers, migrations, DAOs)    |
| E      | `code_env`, `risk_secrets`                                 |
| F      | `risk_determinism`, `risk_concurrency`, `risk_idempotency` |
| G      | `doc_meta`, `doc_claim`, `doc_boundary`, `doc_workflow`    |

## Total Artifacts: 23 JSON files

### Code Artifacts (17):
- STRUCTURE_MAP.json
- SERVICE_MAP.json
- ENTRYPOINTS.json
- CLI_SURFACE.json
- API_SURFACE.json
- MCP_SURFACE.json
- HOOKS_SURFACE.json
- EVENT_EMITTERS.json
- EVENT_CONSUMERS.json
- EVENT_ENVELOPE_FIELDS.json
- DB_SURFACE.json
- MIGRATIONS.json
- DAO_SURFACE.json
- ENV_VARS.json
- CONFIG_LOADERS.json
- SECRETS_RISK_LOCATIONS.json
- DETERMINISM_RISKS.json

### Doc Artifacts (6):
- DOC_INDEX.json
- DOC_CLAIMS.json
- DOC_BOUNDARIES.json
- DOC_WORKFLOWS.json
- DOC_SUPERSESSION.json
- DOC_GLOSSARY.json

## Parallel Execution Strategy

If running in parallel, group by independence:

**Batch 1 (independent):**
- Prompt A (structure)
- Prompt B (interfaces)
- Prompt E (env/config)

**Batch 2 (depends on structure awareness):**
- Prompt C (events)
- Prompt D (db)
- Prompt F (risks)

**Batch 3 (docs - can run anytime):**
- Prompt G (docs)

## Estimated Token Usage (per prompt)

| Prompt | Input Tokens | Output Tokens | Total |
| ------ | ------------ | ------------- | ----- |
| A      | ~50K         | ~20K          | ~70K  |
| B      | ~40K         | ~15K          | ~55K  |
| C      | ~30K         | ~10K          | ~40K  |
| D      | ~35K         | ~12K          | ~47K  |
| E      | ~25K         | ~8K           | ~33K  |
| F      | ~30K         | ~10K          | ~40K  |
| G      | ~200K        | ~50K          | ~250K |

**Total:** ~535K tokens (all prompts)

## Validation Checklist

After each prompt run, verify:
- ✅ Output is valid JSON
- ✅ All items have `id`, `domain`, `name`, `path`, `line_range`
- ✅ No forbidden words in any field
- ✅ Items sorted by `(domain, path, line_range[0], name)`
- ✅ IDs follow format: `domain:path:line:name`
- ✅ `confidence` field present
- ✅ `missing_fields` array present (even if empty)
