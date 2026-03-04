OUTPUTS:
- DOC_INDEX.partX.json
- DOC_CONTRACT_CLAIMS.partX.json
- DOC_BOUNDARIES.partX.json
- DOC_SUPERSESSION.partX.json
- CAP_NOTICES.partX.json

Hard rules:
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited line_range MUST use the line numbers shown in the provided excerpt.
- Every items[] entry MUST include id, path, and line_range.
- Every evidence object MUST include repo-relative path, integer line_range, and exact excerpt.
- If a value cannot be grounded from the provided excerpt, return valid JSON with UNKNOWN or fail-closed placeholders; never invent line numbers.

Goal (per partition):
- DOC_INDEX.partX.json
- DOC_CONTRACT_CLAIMS.partX.json
- DOC_BOUNDARIES.partX.json
- DOC_SUPERSESSION.partX.json
- CAP_NOTICES.partX.json (what didn't fit, what needs D2)

Prompt:
- Extract only "normative" and "boundary" statements:
  - MUST/SHALL/DO NOT, invariants, failure modes, interfaces, "authority" language
  - plane boundaries and what enforces them (even if just planned)
  - supersession markers: ACTIVE/DEPRECATED, version headers, timestamps, "supersedes"
- Cite everything: file + line_range + short quote.
```markdown

OUTPUTS:
	•	DOC_INDEX.partX.json
	•	DOC_CONTRACT_CLAIMS.partX.json
	•	DOC_BOUNDARIES.partX.json
	•	DOC_SUPERSESSION.partX.json
	•	CAP_NOTICES.partX.json
```
