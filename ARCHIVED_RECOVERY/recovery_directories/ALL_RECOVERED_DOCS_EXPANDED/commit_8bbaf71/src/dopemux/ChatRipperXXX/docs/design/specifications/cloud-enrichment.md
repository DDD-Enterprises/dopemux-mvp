Title: Cloud Enrichment Spec
Status: Draft | Owner: XtractXact | Last Updated: 2025-09-02 PT

## Context & Purpose
This document defines the **cloud LLM enrichment** contract for ChatX/XtractXact. It specifies **what** gets sent to cloud, **what** comes back, and the **rules** that govern privacy, safety, determinism, and reproducibility. Cloud is **optional** and is only used after a local-first pass fails confidence gates.

## Non-Goals
- No unredacted text or attachments ever leave the device.
- No fine-grained sexual/fetish labels or explicit descriptors are sent to cloud.
- No cloud inference occurs without a passing **Policy Shield** preflight and explicit `--allow-cloud` flag.

## Field Visibility Matrix (authoritative)
| Field group | Cloud-visible | Local-only | Notes |
|---|---|---|---|
| Identifiers (`msg_id`, `cu_id`) | ✔ |  | Pseudonymized ids only |
| Coarse labels (`coarse_labels[]`) | ✔ |  | Broad, non-explicit themes |
| Fine labels (`fine_labels_local[]`) |  | ✔ | Never sent to cloud |
| Text windows (redacted) | ✔ |  | Must be pseudonymized, tokenized |
| Provenance, Shield, Merge | ✔ |  | Required for auditability |
| Token usage, latency | ✔ |  | For cost/ops analysis |
| Source hash | ✔ |  | Cache key/idempotency |
| Attachments (any) |  | ✔ | Prohibited to cloud |

## Orchestration (Hybrid Cascade)
1) **Pass A: Local** inference produces enrichment. If `confidence_llm ≥ τ` (default **0.7**), STOP.  
2) **Pass B: Cloud (optional)** only if **both**: (a) local confidence < τ **and** (b) `--allow-cloud` provided **and** (c) Policy Shield preflight passes coverage (≥ **0.995**; strict mode ≥ **0.999**).  
3) All cloud prompts use **redacted** windows (±2 turns) and **schema-locked** outputs.

## CLI Contracts (canonical)
```bash
chatx preflight cloud --input ./out/redacted/*.json --threshold 0.995 --hardfail-classes csam

chatx enrich messages --contact "<key>" --backend local|cloud|hybrid   --local-model "<id>" --tau 0.7 --allow-cloud   [--batch 100] [--context 2] [--max-out 800] [--no-hosted-retrieval]

chatx enrich units --contact "<key>" --backend local|cloud|hybrid   --local-model "<id>" --tau 0.7 --allow-cloud [--window turns:50]
```

## Message Enrichment Schema (cloud-aware; JSON)
```json
{
  "msg_id": "string",
  "speech_act": "ask|inform|promise|refuse|apologize|propose|meta",
  "intent": "string",
  "stance": "supportive|neutral|challenging",
  "tone": "string",
  "emotion_primary": "joy|anger|fear|sadness|disgust|surprise|neutral",
  "certainty": 0.0,
  "directness": 0.0,
  "boundary_signal": "none|set|test|violate|reinforce",
  "repair_attempt": false,
  "reply_to_consistent": true,
  "inferred_meaning": "string",
  "coarse_labels": ["string"],
  "fine_labels_local": ["string"],
  "influence_class": "string",
  "influence_score": 0.0,
  "relationship_structure": ["string"],
  "relationship_dynamic": ["string"],
  "map_refs": ["msg_id"],
  "notes": "string",
  "confidence_llm": 0.0,
  "source": "local|cloud",
  "provenance": {
    "schema_v": "1.0.0",
    "run_id": "uuid",
    "ts": "2025-08-16T12:00:00Z",
    "model_id": "string",
    "model_sha": "string",
    "provider": "local|openai|anthropic|other",
    "prompt_hash": "sha256",
    "source_hash": "sha256",
    "latency_ms": 0,
    "token_usage": {"input": 0, "output": 0, "total": 0},
    "cache_hit": false
  },
  "shield": {
    "preflight_coverage": 0.0,
    "strict": false,
    "hardfail_triggered": false,
    "nuance_level": "balanced|conservative|expressive",
    "placeholder_version": "string"
  },
  "merge": {
    "source_last_enrichment": "local|cloud",
    "reason": "low_confidence|validation_failed|manual|none"
  }
}
```

### Message JSON Schema (draft)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MessageEnrichment",
  "type": "object",
  "required": ["msg_id","speech_act","intent","map_refs","confidence_llm","source","provenance","shield","merge"],
  "properties": {
    "msg_id": {"type": "string"},
    "speech_act": {"type": "string","enum":["ask","inform","promise","refuse","apologize","propose","meta"]},
    "intent": {"type": "string"},
    "stance": {"type": "string","enum":["supportive","neutral","challenging"]},
    "tone": {"type": "string"},
    "emotion_primary": {"type": "string","enum":["joy","anger","fear","sadness","disgust","surprise","neutral"]},
    "certainty": {"type": "number","minimum": 0,"maximum": 1},
    "directness": {"type": "number","minimum": 0,"maximum": 1},
    "boundary_signal": {"type": "string","enum":["none","set","test","violate","reinforce"]},
    "repair_attempt": {"type": "boolean"},
    "reply_to_consistent": {"type": "boolean"},
    "inferred_meaning": {"type": "string","maxLength": 200},
    "coarse_labels": {"type": "array","items":{"type": "string"}},
    "fine_labels_local": {"type": "array","items":{"type": "string"}},
    "influence_class": {"type": "string"},
    "influence_score": {"type": "number","minimum": 0,"maximum": 1},
    "relationship_structure": {"type": "array","items":{"type": "string"}},
    "relationship_dynamic": {"type": "array","items":{"type": "string"}},
    "map_refs": {"type": "array","minItems": 1,"items":{"type": "string"}},
    "notes": {"type": "string","maxLength": 200},
    "confidence_llm": {"type": "number","minimum": 0,"maximum": 1},
    "source": {"type": "string","enum":["local","cloud"]},
    "provenance": {
      "type": "object",
      "required": ["schema_v","run_id","ts","model_id","provider","prompt_hash","source_hash","latency_ms","token_usage","cache_hit"],
      "properties": {
        "schema_v": {"type": "string"},
        "run_id": {"type": "string"},
        "ts": {"type": "string","format":"date-time"},
        "model_id": {"type": "string"},
        "model_sha": {"type": "string"},
        "provider": {"type": "string"},
        "prompt_hash": {"type": "string"},
        "source_hash": {"type": "string"},
        "latency_ms": {"type": "integer","minimum": 0},
        "token_usage": {
          "type": "object",
          "required": ["input","output","total"],
          "properties": {
            "input": {"type": "integer","minimum": 0},
            "output": {"type": "integer","minimum": 0},
            "total": {"type": "integer","minimum": 0}
          }
        },
        "cache_hit": {"type": "boolean"}
      }
    },
    "shield": {
      "type": "object",
      "required": ["preflight_coverage","strict","hardfail_triggered","nuance_level"],
      "properties": {
        "preflight_coverage": {"type": "number","minimum": 0,"maximum": 1},
        "strict": {"type": "boolean"},
        "hardfail_triggered": {"type": "boolean"},
        "nuance_level": {"type": "string","enum":["balanced","conservative","expressive"]},
        "placeholder_version": {"type": "string"}
      }
    },
    "merge": {
      "type": "object",
      "required": ["source_last_enrichment","reason"],
      "properties": {
        "source_last_enrichment": {"type": "string","enum":["local","cloud"]},
        "reason": {"type": "string","enum":["low_confidence","validation_failed","manual","none"]}
      }
    }
  },
  "additionalProperties": false
}
```

## CU Enrichment Schema (cloud-aware; JSON)
```json
{
  "cu_id": "string",
  "topic_label": "string",
  "vibe_trajectory": ["tone"],
  "escalation_curve": "low|spike|high|resolve",
  "coarse_labels": ["string"],
  "fine_labels_local": ["string"],
  "relationship_structure": ["string"],
  "relationship_dynamic": ["string"],
  "ledgers": {
    "boundary": [],
    "consent": [],
    "decisions": [],
    "commitments": []
  },
  "issue_refs": ["issue_id"],
  "evidence_index": ["msg_id"],
  "confidence_llm": 0.0,
  "source": "local|cloud",
  "provenance": { "schema_v": "1.0.0", "run_id": "uuid", "ts": "2025-08-16T12:00:00Z", "model_id": "string", "model_sha": "string", "provider": "local|openai|anthropic|other", "prompt_hash": "sha256", "source_hash": "sha256", "latency_ms": 0, "token_usage": {"input": 0, "output": 0, "total": 0}, "cache_hit": false },
  "shield": { "preflight_coverage": 0.0, "strict": false, "hardfail_triggered": false, "nuance_level": "balanced|conservative|expressive", "placeholder_version": "string" },
  "merge": { "source_last_enrichment": "local|cloud", "reason": "low_confidence|validation_failed|manual|none" }
}
```

### CU JSON Schema (draft)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CUEnrichment",
  "type": "object",
  "required": ["cu_id","topic_label","evidence_index","confidence_llm","source","provenance","shield","merge"],
  "properties": {
    "cu_id": {"type":"string"},
    "topic_label": {"type":"string"},
    "vibe_trajectory": {"type":"array","items":{"type":"string"}},
    "escalation_curve": {"type":"string","enum":["low","spike","high","resolve"]},
    "coarse_labels": {"type":"array","items":{"type":"string"}},
    "fine_labels_local": {"type":"array","items":{"type":"string"}},
    "relationship_structure": {"type":"array","items":{"type":"string"}},
    "relationship_dynamic": {"type":"array","items":{"type":"string"}},
    "ledgers": {
      "type":"object",
      "properties": {
        "boundary":{"type":"array"},
        "consent":{"type":"array"},
        "decisions":{"type":"array"},
        "commitments":{"type":"array"}
      }
    },
    "issue_refs": {"type":"array","items":{"type":"string"}},
    "evidence_index": {"type":"array","minItems":1,"items":{"type":"string"}},
    "confidence_llm": {"type":"number","minimum":0,"maximum":1},
    "source": {"type":"string","enum":["local","cloud"]},
    "provenance": {"type":"object"},
    "shield": {"type":"object"},
    "merge": {"type":"object"}
  },
  "additionalProperties": false
}
```

## Validation & QA
- **MUST** validate with the above JSON Schemas; reject on any enum or bounds violation.
- **MUST** include `map_refs` (message) or `evidence_index` (CU) tying every claim to source ids.
- **MUST** record `source`, `confidence_llm`, `provenance`, `shield`, and `merge` for every record.
- **SHOULD** sample 1–2% for manual audit; **MAY** widen context on automatic retry.

## Privacy & Safety
- **MUST** redact and pseudonymize before cloud; explicit terms replaced with opaque tokens `⟦TKN:<id8>⟧`.
- **MUST NOT** send `fine_labels_local` or any attachments to cloud.
- **MUST** log `preflight_coverage` and `strict` flags for every cloud call.

## Determinism, Caching, Idempotency
- Local inference runs with a fixed seed and streaming disabled.
- Cache keys include `(model_id, model_sha, prompt_hash, source_hash, schema_v)`; target ≥ 80% cache hit on reruns.
- Record `token_usage` and `latency_ms` for each run.

## Acceptance (Definition of Done)
- Redaction coverage ≥ **0.995** (or ≥ **0.999** strict) before any cloud call.
- Hybrid gate obeyed (`τ = 0.7`): if local `confidence_llm ≥ τ`, no cloud call occurs.
- All records are schema-valid, bounded, and contain evidence links.
- Field visibility matrix enforced by prompt/router tests.

## Prompt Skeleton (Cloud Pass)
- **System:** forensic annotator; follow schema exactly; cite `map_refs`/`evidence_index`; terse responses.
- **User content:** packed, redacted window (±2 turns), task, and JSON schema.
- **Params:** temperature ≤ 0.3; `max_output_tokens ≤ 800`.
