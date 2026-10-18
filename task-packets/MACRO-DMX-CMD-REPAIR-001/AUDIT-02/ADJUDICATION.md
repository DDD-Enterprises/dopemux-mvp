# AUDIT-02 — Final audit record and coordinator adjudication

**Authority**: NONE. **Subject**: `fix/cmd-repair-001` head `7c6cfc0370092c6076d227e7eaaf05203d379303` (frozen diff sha256 `ec458cc90e56166dc36203a95a881132562ba1356b3f30a7900c9d2d6d4135e6`, 46,151 bytes; base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`; 6 commits, 48 files).
**Auditor verdict**: `PASS_WITH_RISKS` (0 BLOCKING, 0 HIGH, 1 MEDIUM, 2 LOW, 1 INFO). Q1–Q4, Q6–Q11 PASS; Q5 UNKNOWN (resolved below).
**Supersedes** AUDIT-01 (FAIL on head `70eb50363`). AUDIT-01 is retained as history. The packet allows one final audit per frozen subject; the earlier FAIL was on a different, superseded subject and its repair was operator-authorized.

## Route

- **Operator approval**: operator chat, "Approve a packet-specific fallback auditor for MACRO-DMX-CMD-REPAIR-001: agy --model gemini-4-argon-high, input limited to the frozen diff ... no repo mount, no secrets, recorded as auditor_model gemini with a note that exact-model evidence is unavailable". Repair authorization: the "Authorize W06 ... then one fresh final audit with the same approved fallback" button text.
- **Tool and model**: `auditor_tool: agy`; `auditor_model: gemini` (generic). The init event echoed `gemini-4-argon-high`; the model self-reported "Gemini 4 Argon (High)". **Exact-model evidence (`gemini-3.1-pro-high`) is unavailable**: it is absent from `agy models` (v1.3.6). The provider-attested identity is UNKNOWN.
- **Invocation**: `INVOCATION.txt`. A sealed directory outside the repo holds only `AUDIT_PROMPT.txt` (sha256 `94992742…af74`) and `frozen.diff`. Flags: `--sandbox --disable-slash-commands --output-format stream-json`. No repo mount.
- **Pre-send checks**: the diff was scanned for secrets (none).
- **Run**: 2026-10-18 ~12:33–12:37 local, 252.6 s, 1 turn, `SUCCESS`. Tokens: 34,655 in, 25,102 out, 19,692 thinking.
- **Containment (structural)**: 1,170 stream events: `init` ×1, `step_update` ×1,168 (one `user_input`, 1,167 `agent_response`), `result` ×1. **No tool step**, and the auditor declared `tools_used: none`. Global MCP servers were reachable but unused.
- **Independence**: a different model family from the Claude implementers (class DIFFERENT_FAMILY). Residual: the auditor saw the prior-audit summary in the contract, by design, to check closure; it was told to judge the head on its own merits.

## Findings and adjudication

| ID | Auditor sev | Adjudication | Evidence / disposition |
|---|---|---|---|
| F1 | MEDIUM | **CONFIRMED, accepted as a disclosed limitation.** The `/mcp <server> <tool>` prose form and prose tool names are not scanned, so `search-decisions.md`, `bootstrap.md`, `doc-pull.md`, `mem/summarize.md`, `plan.md` and `plan-tasks.md` rely on review rather than the gate. Deferred because the scan would flag `zen.md` and `zen-continue.md` (`/mcp zen execute_workflow`), which reference a nonexistent `zen` server. Fixing them needs files outside every allowlist. | Test-module comment; supervisor ruling R1 (W06). **Follow-up packet needed**: retire or repoint the two `zen` commands, then add the prose scan. |
| F2 | LOW | **PARTLY RESOLVED.** `create_work_tree` is a captured `task-orchestrator` tool (`mcp_tool_surfaces.json:263`). The `pal-stdio` (plan.md) vs `pal` (`dx/implement.md`, `dx/note.md`) naming inconsistency is real and pre-existing. | The same item is on the issuance record's out-of-scope list. |
| F3 | LOW | **CONFIRMED, narrow.** `_MCP_REF` misses server names with underscores and lacks a trailing token boundary, so `get_context--bad` and `*bad` truncate to a valid prefix. The only underscore server in the repo is `MCP_DOCKER`, which no command references. | Ran the regex on the three inputs. Low impact; can ride the follow-up. |
| F4 | INFO | **DISCLOSED.** Category-wide `get_custom_data` fetches, client-side result truncation, and `update_context` merge-vs-replace UNKNOWN. | The residual risks in the `PROOF.json`. |
| Q5 | UNKNOWN | **RESOLVED.** `create_work_tree` exists (F2). The three script removals are disclosed in the command text. | |
| Q10 | PASS | Prior findings closed: **F1 (AUDIT-01)** fixed in `mem-search.md` and `mem-query.md`; **F2** fixed (`./scripts/` negative control); **F3** fixed for wildcards and hyphenated suffixes; **F5** fixed. | Matches the coordinator's own verification. |

## Disposition

- **No BLOCKING or HIGH finding.** The verdict `PASS_WITH_RISKS` is accepted as the single final-audit result for this subject.
- **No further repair.** The residual items are disclosed limitations or follow-ups, and a change would invalidate this audit.
- **Not claimed**: this audit is not an Audit Broker certification. The exact-model requirement of the embedded-audit docs is unmet and the fallback was operator-approved, so PR Steward may treat the proof as non-READY. That decision stays with the operator and PR Steward.
