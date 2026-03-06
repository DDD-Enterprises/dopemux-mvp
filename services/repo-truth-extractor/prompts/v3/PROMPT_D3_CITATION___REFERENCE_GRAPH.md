OUTPUTS:
- DOC_CITATION_GRAPH.json

Hard rules:
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited line_range MUST use the line numbers shown in the provided excerpt.
- When emitting items[], every entry MUST include id, path, and line_range.
- Every evidence object MUST include repo-relative path, integer line_range, and exact excerpt.
- If a value cannot be grounded from the provided excerpt, return valid JSON with UNKNOWN or fail-closed placeholders; never invent line numbers.

Goal: DOC_CITATION_GRAPH.json

Prompt:
- Build graph edges:
  - doc A references doc B (links, filenames, "see also", explicit citations)
  - doc A references code path
  - doc A references service name/config name
- Output top referenced docs, hub docs, cross-plane edges.
```markdown

OUTPUTS:
	•	DOC_CITATION_GRAPH.json
```
