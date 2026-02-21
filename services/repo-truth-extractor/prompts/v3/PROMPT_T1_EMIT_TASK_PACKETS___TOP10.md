MODE: Arbitration output only. Do not implement code.
EVIDENCE REQUIRED: Every load-bearing claim must map to authority input paths.
OUTPUT: Markdown packets plus JSON index.
STABLE ORDER: Sort packets by priority, then tp_id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase T1: Emit Task Packets (Top 10)

Outputs:
- TP_PACKETS_TOP10.partX.md
- TP_PACKET_IMPLEMENTATION_INDEX.json

Prompt:
ROLE: GPT-5.2 (arbitration).
Inputs:
- TP_BACKLOG_TOPN.json
- R norm artifact paths referenced by each backlog item

Action:
Generate complete Task Packet markdowns for the top 10 items in the backlog.
Each packet must be implementation-ready for Codex Desktop and must not relitigate truth.

Required packet header block (exact keys):
- Implementer: Codex Desktop (GPT-5.3-Codex)
- Authority Inputs: <list of R/X norm artifact paths>
- Forbidden: re-run extraction; reinterpret truth without new evidence
- Required Proofs: git diff --stat, tests run, acceptance checks, rollback verification

Required sections per packet:
- Objective
- Scope (IN / OUT)
- Invariants
- Plan
- Exact commands
- Acceptance criteria
- Rollback
- Stop conditions

Required schema keys for TP_PACKET_IMPLEMENTATION_INDEX.json:
- run_id
- generated_at
- packet_count
- packets (array)
- packets[].tp_id
- packets[].title
- packets[].implementer_target
- packets[].authority_inputs
- packets[].packet_markdown_locator
