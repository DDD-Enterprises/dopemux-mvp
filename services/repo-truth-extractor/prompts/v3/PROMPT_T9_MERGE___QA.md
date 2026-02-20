# PROMPT_T9 — MERGE / QA

TASK: Merge all Phase T packet artifacts, run QA, and emit canonical Task Packet outputs.

OUTPUTS:
- TP_INDEX.json
- TP_MERGED.json
- TP_QA.json
- TP_SUMMARY.md
- TP_BACKLOG_TOPN.json

QA requirements:
- Validate required schema fields for every packet.
- Validate implementer target, evidence paths, and acceptance/rollback completeness.
- Emit missing-evidence list and unresolved-collision list.
- Emit packet counts by priority and dependency tier.
- Fail closed if required canonical outputs cannot be produced.
