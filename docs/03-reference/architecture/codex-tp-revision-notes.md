---
id: codex-tp-revision-notes
title: Codex Tp Revision Notes
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-22'
last_review: '2026-04-22'
next_review: '2026-07-21'
prelude: Codex Tp Revision Notes (reference) for dopemux documentation and developer workflows.
---

# Codex TP Revision Notes — Apply Before Execution

Use the previously generated TP series with these revisions applied before execution.

## Mandatory edits

1. Change any hard directive like **"merge adapter/proxy into gateway"** to:
   - **"internalize behind the gateway where parity, ownership clarity, and rollback exist"**

2. Treat proposed implementation roots such as:
   - `services/dopemux-agent-gateway/...`
   - `configs/agent-shims/...`
   - `tests/agent_gateway/...`

   as proposed target surfaces, not repo-proven locations. Codex must place them in repo-consistent locations after census and layout verification.

3. Add this invariant to all packets:
   - **"Gateway success is not authoritative success. Only an owning authority can emit a committed state event."**

4. Add this invariant where execution routing appears:
   - **"The gateway may coordinate execution handoff but does not own dopetask runtime truth."**

5. Add this Serena constraint where consolidation/deprecation is discussed:
   - **"Do not consolidate Serena-facing surfaces until runtime authority is frozen and duplicate exposure paths are classified."**

## Execution stance

- Treat the architecture as settled enough to begin bounded implementation.
- Treat exact file/module locations as subject to repo census and layout verification.
- Do not broaden scope beyond the existing TP series.
- Do not let gateway work become authority work.
