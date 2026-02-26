Goal:
- merged: DOC_INDEX.json, DOC_CONTRACT_CLAIMS.json, DOC_SUPERSESSION.json, DOC_TOPIC_CLUSTERS.json, DUPLICATE_DRIFT_REPORT.json
- optional alternate duplicate artifact: DOC_RECENCY_DUPLICATE_REPORT.json
- QA: DOC_COVERAGE_REPORT.json

Prompt:
- Merge all part files.
- Dedup rules:
  - prefer newer timestamps when same doc appears in multiple buckets
  - preserve both if content differs materially
- Coverage gates:
  - all docs indexed
  - no pending partitions
  - all CAP_NOTICES resolved or explicitly waived
  - citation graph present

```markdown

OUTPUTS:
	•	DOC_CONTRACT_CLAIMS.json
	•	DOC_COVERAGE_REPORT.json
	•	DOC_INDEX.json
	•	DOC_RECENCY_DUPLICATE_REPORT.json
	•	DOC_SUPERSESSION.json
	•	DOC_TOPIC_CLUSTERS.json
	•	DUPLICATE_DRIFT_REPORT.json
```
