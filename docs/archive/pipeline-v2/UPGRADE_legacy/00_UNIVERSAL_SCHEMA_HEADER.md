---
id: 00_UNIVERSAL_SCHEMA_HEADER
title: 00 Universal Schema Header
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: 00 Universal Schema Header (explanation) for dopemux documentation and developer
  workflows.
---
# Universal Output Schema (include at top of every Flash run)

**Paste this header at the top of every Gemini Flash job:**

---

**ROLE:** Mechanical extractor (no reasoning, no opinions, no arbitration).

**INPUTS:** repo working tree and specified baselines only.

**OUTPUT:** JSON only. ASCII only. No markdown.

## UNIVERSAL ITEM SCHEMA

Every extracted item MUST be an object with:

```json
{
  "id": "<deterministic string id>",
  "domain": "<one of the allowed domains>",
  "name": "<command/tool/event/table/symbol/etc>",
  "path": "<repo-relative path>",
  "line_range": [start_line, end_line],
  "symbol": "<python symbol if applicable, else empty string>",
  "kind": "<type label: file|service|cli_command|api_route|mcp_tool|hook|event_emitter|event_consumer|db_table|db_index|db_trigger|migration|model|config_loader|env_var|risk|doc_claim|doc_workflow|doc_boundary>",
  "strings": ["<flags/help/event names/keywords>"],
  "excerpt": ["<=2 lines", "<=2 lines"],
  "source_artifact": "<input name, eg WORKING_TREE or dopemux-mvp-llm-20260206-074421.zip or DOC_CORPUS>",
  "confidence": "high|medium|low",
  "missing_fields": []
}
```

## ALLOWED DOMAINS

```
doc_meta, doc_claim, doc_workflow, doc_boundary,
code_service, code_entrypoint, code_cli, code_api, code_mcp, code_hook,
code_event_emitter, code_event_consumer,
code_db, code_model, code_env,
risk_determinism, risk_concurrency, risk_idempotency, risk_secrets,
drift_pair
```

## HARD RULES

- Never invent line numbers. If you cannot determine line_range, set confidence=low and include missing_fields=["line_range"].
- Never describe purpose/meaning. **Forbidden words:** "means", "likely", "should", "correct", "wrong", "best", "problem", "bug".
- Always sort outputs deterministically by (domain, path, line_range[0], name).
- Cap lists per file when huge: max 200 items per file; keep earliest occurrences.

## ID RULE

```
id = domain + ":" + path + ":" + line_range[0] + ":" + name
```

No hashing, no UUIDs, no timestamps. This makes reruns stable.

## CAP RULE

If a single file yields >200 items, keep the first 200 by line order and add a summary item:

```json
{
  "domain": "doc_meta",
  "kind": "cap_notice",
  "name": "cap_reached",
  "strings": ["kept:200", "dropped:<n>"]
}
```

---

This makes your normalize stage painless.
