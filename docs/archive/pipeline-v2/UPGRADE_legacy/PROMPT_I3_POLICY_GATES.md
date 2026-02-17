# Prompt I3 (v2): LLM Policy Gates & Boundaries

**Outputs:** `LLM_POLICY_GATES.json`

---

## TASK

Produce ONE JSON file: `LLM_POLICY_GATES.json`.

## INPUT

- `LLM_INSTRUCTION_INDEX.json` from I1

## SCOPE

**Only files listed in LLM_INSTRUCTION_INDEX.json**

## LLM_POLICY_GATES.json

Extract atomic sentences containing **any** of:
- `MUST`, `MUST NOT`, `SHALL`, `REQUIRED`, `FORBIDDEN`
- `FAIL-CLOSED`, `NO INVENTION`, `DETERMINISTIC`, `AUDIT`
- `AUTHORITY`, `TRINITY`, `EVENTBUS`, `TASKX`, `MCP`, `HOOK`

For each policy statement:
- `policy_id`: `"policy:" + doc_id + ":" + line_range[0]`
- `doc_id`, `path`, `line_range`, `heading_path`
- `policy_type`: `claim|boundary` (use `boundary` if mentions authority/ownership/responsibility)
- `keywords_matched`: list of matched keywords
- `original_quote`: exact quote (cap 200 characters)
- `normalized_text`: lowercase, collapse whitespace only

**Example:**
```json
{
  "policy_id": "policy:doc:.claude/PRIMER.md:78",
  "doc_id": "doc:.claude/PRIMER.md",
  "path": ".claude/PRIMER.md",
  "line_range": [78, 80],
  "heading_path": "MCP Tools > Authority",
  "policy_type": "boundary",
  "keywords_matched": ["MUST", "AUTHORITY"],
  "original_quote": "MCP servers MUST be the authoritative source for their data domains.",
  "normalized_text": "mcp servers must be the authoritative source for their data domains"
}
```

## RULES

- **No deciding which policy wins**
- **Extract exact quotes only**
- **JSON only**, ASCII only
- **Deterministic sorting** by (doc_id, line_range[0])

## OUTPUT FORMAT

```json
{
  "artifact_type": "LLM_POLICY_GATES",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "WORKING_TREE",
  "policies": [...]
}
```
