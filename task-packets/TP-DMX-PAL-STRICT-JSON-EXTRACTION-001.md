# Task Packet: TP-DMX-PAL-STRICT-JSON-EXTRACTION-001

## Goal

Harden `scripts/audit/pal_clink_runner.py::parse_audit_json_object` so model audit stdout is accepted only as:

1. a direct full-output JSON object, or
2. exactly one full-output fenced JSON object with deterministic line structure.

Reject multi-fence and oversized inputs explicitly. Never invent PASS/READY from rejected text.

## Policy

### Size bound

`MAX_AUDIT_OUTPUT_BYTES = 1_048_576` (1 MiB UTF-8). Measured before strip, splitlines, or `json.loads`. Applies to direct stdout and nested tool-content strings via the same parser.

### One-fence line structure

After outer whitespace trim, if output starts with a fence:

- first line exactly `` ``` `` or `` ```json ``
- final line exactly `` ``` ``
- no interior line may be an exact fence opener or closer
- parse interior as JSON object only

No brace scraping. No conversational wrappers.

## Out of scope

- Marking PR ready, merging, or closing any PR
- Cherry-picks from PR 1171
- Force push / history rewrite

## Repair context

Draft PR #1181 repair via `TP-DMX-PAL-STRICT-JSON-EXTRACTION-REPAIR-001R`.
