---
id: 05_promotion_redaction
title: 05_Promotion_Redaction
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: 05_Promotion_Redaction (explanation) for dopemux documentation and developer
  workflows.
---
# Dope-Memory v1 — Promotion + Redaction

## Redaction Philosophy
Fail closed. If in doubt, strip or drop sensitive fields rather than persist.

Redaction occurs twice:
1) Ingestion redaction (before raw_activity_events)
2) Promotion redaction (before work_log_entries)

## Redaction Inputs

### Denylist path prefixes (examples)
Any payload field containing paths matching these prefixes must be removed or path-hashed:
- ".env"
- "secrets/"
- "secret/"
- "keys/"
- ".ssh/"
- "id_rsa"
- "id_ed25519"
- "credentials"
- "config/credentials"
- "private/"
- "certs/private"
- ".aws/credentials"
- ".npmrc"
- ".pypirc"

### Sensitive key names (case-insensitive)
Drop fields when key name matches:
- "password"
- "passwd"
- "pwd"
- "secret"
- "api_key"
- "apikey"
- "token"
- "access_token"
- "refresh_token"
- "authorization"
- "cookie"
- "set-cookie"
- "private_key"
- "ssh_key"
- "client_secret"
- "session"
- "bearer"
- "jwt"
- "signature"

### Pattern detectors (regex)
These patterns must be replaced with "[REDACTED]" when found in strings.

1) AWS Access Key ID
```
\b(A3T|AKIA|ASIA|AGPA|AIDA|AROA|ANPA|ANVA|ASCA)[A-Z0-9]{16}\b
```

1) AWS Secret Access Key (heuristic: 40 base64-ish)
```
(?i)\baws(.{0,20})?(secret|access).{0,20}([A-Za-z0-9/+=]{40})\b
```

1) Generic Bearer token
```
(?i)\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b
```

1) JWT (three base64url parts)
```
\beyJ[A-Za-z0-9\-_]+?\.[A-Za-z0-9\-_]+?\.[A-Za-z0-9\-_]+?\b
```

1) Private key blocks
```
-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----[\s\S]+?-----END (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----
```

1) GitHub tokens (classic + fine-grained)
```
\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b
\bgithub_pat_[A-Za-z0-9_]{80,}\b
```

1) Slack tokens
```
\bxox[baprs]-[A-Za-z0-9-]{10,}\b
```

1) OpenAI keys (legacy-style)
```
\bsk-[A-Za-z0-9]{20,}\b
```

1) Generic API key assignment patterns
```
(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*["']?([A-Za-z0-9\-._~+/]{12,})["']?\b
```

## Redaction Output Rules
- Replace matched secrets with "[REDACTED]"
- For denied paths:
- if path appears in linked_files, store:
    `{ "path_hash": "sha256(path)", "action": "...", "note": "denied_path" }`
- do not store raw path

- Hard size cap:
- payload_json and details_json must be <= 64KB after redaction
- if larger, truncate and add:
    `{"truncated": true, "original_size": N}`

## Promotion Rules (Phase 1 Deterministic)
Events eligible for promotion must meet minimum required data fields.

### 1) decision.logged
- requires: decision_id, title, choice OR rationale
- produces:
- category = "planning" (or "architecture" if tags contain "arch")
- entry_type = "decision"
- outcome = "success"
- importance_score = max(7, inferred_importance)
- summary = "Decided: {title} -> {choice}"
- reasoning = rationale (redacted)
- linked_decisions = [decision_id]
- linked_files = affected_files (paths redacted by denylist)

### 2) task.failed / task.blocked
- requires: task_id, title OR error.message
- produces:
- category = "debugging" if failed/blocked else "implementation"
- entry_type = "blocker" for blocked; "error" for failed
- outcome = "failed" or "blocked"
- importance_score = 7
- summary = "Task {failed|blocked}: {title}"
- details = {task_id, error_kind, message, service, ci_job} redacted

### 3) task.completed
- requires: task_id, title
- produces:
- category = "implementation"
- entry_type = "milestone"
- outcome = "success"
- importance_score = 5
- summary = "Completed: {title}"

### 4) error.encountered
- requires: message
- produces:
- category = "debugging"
- entry_type = "error"
- outcome = "in_progress"
- importance_score = 6
- summary = "Error: {error_kind or message_headline}"

### 5) workflow.phase_changed
- requires: from_phase, to_phase
- produces:
- category = "planning" if to_phase is planning else to_phase-derived
- entry_type = "workflow_transition"
- outcome = "success"
- importance_score = 5
- summary = "Phase: {from_phase} -> {to_phase}"

### 6) manual.memory_store
- requires: category, entry_type, summary
- produces:
- category/entry_type from payload
- importance_score from payload (default 6)
- summary from payload
- details from payload (redacted)

## Tag Extraction (Deterministic)
- If event.data.tags exists and is a list of strings: use it (after ASCII normalize)
- Else infer tags from:
- decision title keywords (snake_case)
- service field (service:xyz)
- phase field (phase:implementation)
- Cap tags to 12 max; stable order:
- explicit tags first in given order
- then inferred tags sorted lexicographically

## Importance Score Rules (Phase 1)
No LLM scoring in Phase 1.
Deterministic mapping:
- decision.logged: 7
- task.failed: 7
- task.blocked: 7
- error.encountered: 6
- task.completed: 5
- workflow.phase_changed: 5
- manual.memory_store: payload.importance_score else 6
