## D3: Citation / Reference Graph (global)

Output file
	•	DOC_CITATION_GRAPH.json

ROLE: Mechanical reference extractor. No reasoning. JSON only. ASCII only.

TARGET: docs/**/*.md and docs/**/*.txt

Extract:
- markdown links [text](target)
- plain references to other docs (paths containing "docs/" or ending in ".md")
- phrases: "see", "refer to", "linked", "as described in"

For each edge:
- from_path
- to_target (exact string)
- context_quote <= 12 words
- line_range

Output DOC_CITATION_GRAPH.json with stable ordering by from_path then line_range.
