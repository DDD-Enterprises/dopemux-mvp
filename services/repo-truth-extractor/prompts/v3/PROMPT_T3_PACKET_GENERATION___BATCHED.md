# PROMPT_T3 — PACKET GENERATION / BATCHED

TASK: Generate implementation-ready Task Packets in deterministic batches from R and X norm artifacts.

OUTPUTS:
- TP_BATCHED_PACKETS.partX.md
- TP_BATCH_INDEX.json

Rules:
- Emit packets in stable order by priority, then `tp_id`.
- Each packet must include: objective, scope in/out, invariants, plan, exact commands, acceptance criteria, rollback, stop conditions.
- Each packet must include a commit plan and explicit acceptance gates.
- Every load-bearing claim must cite `authority_inputs` paths.
- If output exceeds context, split into `.partX` artifacts and include full index references in `TP_BATCH_INDEX.json`.
