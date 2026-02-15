## D4: Merge + Normalize + Coverage QA (global)

Output files
	•	DOC_INDEX.json
	•	DOC_CLAIMS.json
	•	DOC_BOUNDARIES.json
	•	DOC_SUPERSESSION.json
	•	DOC_INTERFACES.json
	•	DOC_WORKFLOWS.json
	•	DOC_DECISIONS.json
	•	DOC_GLOSSARY.json
	•	DOC_COVERAGE_REPORT.json

ROLE: Mechanical normalizer. No reasoning. JSON only. ASCII only.

INPUTS:
- all DOC_INDEX.*.json
- all DOC_CLAIMS.*.json
- all DOC_BOUNDARIES.*.json
- all DOC_SUPERSESSION.*.json
- all DOC_INTERFACES.*.json
- all DOC_WORKFLOWS.*.json
- all DOC_DECISIONS.*.json
- all DOC_GLOSSARY.*.json
- DOC_INVENTORY.json
- DOC_CITATION_GRAPH.json

MERGE RULES:
- concatenate items per artifact type
- dedupe items by (path, line_range, hash(original_quote or block_text or excerpt))
- stable sort by path asc then line_range start asc

OUTPUT unified JSON artifacts listed above.

QA OUTPUT: DOC_COVERAGE_REPORT.json
Must include:
- total_docs (from DOC_INVENTORY)
- docs_processed (count docs appearing in any merged artifact)
- docs_with_claims
- docs_with_interfaces
- docs_with_workflows
- docs_with_decisions
- docs_missing_all (docs that appear in DOC_INVENTORY but not in any merged artifact)
- archive_counts and evidence_counts

RULES:
- no interpretation
- JSON only
