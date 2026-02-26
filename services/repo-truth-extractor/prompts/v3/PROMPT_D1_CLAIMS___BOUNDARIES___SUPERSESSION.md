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
