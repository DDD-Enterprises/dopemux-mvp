Goal:
- merged: DOC_INDEX.json, DOC_CONTRACT_CLAIMS.json, DOC_BOUNDARIES.json, DOC_SUPERSESSION.json, DOC_INTERFACES.json, DOC_WORKFLOWS.json, DOC_DECISIONS.json, DOC_GLOSSARY.json
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