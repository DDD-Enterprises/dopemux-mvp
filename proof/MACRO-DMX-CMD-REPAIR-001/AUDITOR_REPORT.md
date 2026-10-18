# Auditor Report - MACRO-DMX-CMD-REPAIR-001

**Subject**: `fix/cmd-repair-001` @ `7c6cfc0370092c6076d227e7eaaf05203d379303` (base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`), frozen diff sha256 `ec458cc9...35e6`.
**Verdict**: `PASS_WITH_RISKS`. Tool `agy`, model recorded as generic `gemini` (ran `gemini-4-argon-high`).
**Route**: operator-approved packet-specific fallback. The exact model `gemini-3.1-pro-high` was not available, so exact-model evidence is unavailable.
**Containment**: sealed directory, diff-and-contract input only; stream has no tool steps; the auditor declared `tools_used: none`.
**History**: AUDIT-01 returned FAIL on the superseded head `70eb50363`; W06 repaired it. See `proof/MACRO-DMX-CMD-REPAIR-001/issuance/AUDIT-01/` and `AUDIT-02/`.
**Coordinator adjudication**: `proof/MACRO-DMX-CMD-REPAIR-001/issuance/AUDIT-02/ADJUDICATION.md`.

## Auditor response (verbatim)

```json
{
  "model_self_reported": "Gemini 4 Argon (High)",
  "tools_used": "none",
  "status": "PASS_WITH_RISKS",
  "questions": [
    {
      "id": "Q1",
      "verdict": "PASS",
      "evidence": "All 48 files in the diff match the declared workstreams with no unrelated or smuggled changes: 18 files in .claude/commands have W01 ConPort tool/argument updates (bootstrap.md, caveat.md, decision.md, doc-pull.md, dx/context.md, dx/implement.md, dx/next.md, followup.md, mem-query.md, mem-search.md, mem/save.md, mem/summarize.md, pattern.md, research-deep.md, research-report.md, runbook-update.md, scratch.md, search-decisions.md); 5 files have W03 script/tool removals or repoints (adr-new.md, doc-new.md, plan-tasks.md, plan.md, safe.md); 26 files have W02 single-line model frontmatter updates (3 of which—dx/context.md, dx/implement.md, dx/next.md—overlap with W01, giving 18 + 5 + 26 - 3 = 46 command files); 1 file in W05 (src/dopemux/mcp/fleet_catalog.py); and 1 new test file in W04/W06 (tests/arch/test_claude_command_references.py). Per-commit boundary isolation across the 6 individual commits is UNKNOWN from the squashed diff alone, but the net diff touches only the intended hunks."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "Every ConPort tool reference in the diff uses one of the 17 live SSE tool names and aligns with the stated signatures: (1) save_custom_data(workspace_id, category, key, value) in caveat.md:3, mem/save.md:3,8 (added missing workspace_id), and scratch.md:3; (2) get_custom_data(workspace_id, category=None, key=None) in bootstrap.md:5, caveat.md:14, mem-query.md:10-12, mem-search.md:8-9, and mem/summarize.md:8; (3) log_decision(workspace_id, topic, decision, rationale, tags=None) in decision.md:3-11 (replaced 'summary' with 'topic' and 'decision'), pattern.md:4 (added workspace_id, topic, decision), and runbook-update.md:4; (4) get_decisions(workspace_id=None, limit=10) in mem/summarize.md:8 and runbook-update.md:6; (5) search_content(workspace_id, query) in bootstrap.md:5,12, decision.md:17, doc-pull.md:5, mem-query.md:3-5 (renamed query_text->query, removed top_k), mem-search.md:7, pattern.md:6, runbook-update.md:6, and search-decisions.md:2 (added workspace_id, removed limit); (6) get_context(workspace_id) in dx/context.md:8,157, dx/next.md:8,102, and research-report.md:13; (7) update_context(workspace_id, context_data: dict) in dx/implement.md:129-131,281-283 and research-deep.md:14-16 (renamed patch_content->context_data); (8) get_progress(workspace_id, status=None, limit=20) in dx/implement.md:33,43-46 (renamed status_filter->status) and runbook-update.md:6; (9) update_progress(progress_id, updates: dict) in dx/implement.md:118-123,228-233 (removed unsupported workspace_id, wrapped status/description in updates dict); (10) log_progress(workspace_id, description, status, priority, linked_decision_id) in followup.md:3-9 (removed unsupported linked_item_type/linked_item_id) and runbook-update.md:4. No remaining reference in the diff uses search_content for custom_data/caveats. Note: in caveat.md and scratch.md, unchanged lines of the JSON block are outside the diff hunk (exact unchanged keys are UNKNOWN from diff alone), and whether any untouched .claude/commands/*.md file still has prose ConPort references is UNKNOWN from the diff alone."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "Semantic changes required by the narrower live SSE tool signatures are explicitly disclosed rather than silent, though three behavioral tradeoffs exist: (1) Server-side result limiting on search is lost because search_content(workspace_id, query) has no limit/top_k parameter; bootstrap.md:5,12, decision.md:17, doc-pull.md:5, mem-query.md:8, mem-search.md:12, pattern.md:6, runbook-update.md:6, and search-decisions.md:3 now instruct the model to read only the top 3-5 (or 5 or 10) results client-side after the full tool payload is returned. (2) Full-text query and server-side limit on custom_data (caveats, mem, scratch) are replaced by category-level retrieval via get_custom_data(workspace_id, category='caveats'|'mem'|'scratch') in bootstrap.md:5, caveat.md:14, mem-query.md:10-12, mem-search.md:8-9, and mem/summarize.md:8, which fetches all entries in the category unless an exact key is known. (3) In dx/implement.md:129-131,281-283 and research-deep.md:14-16, patch_content was renamed to context_data for update_context; whether the live server merges or replaces active context is UNKNOWN from the diff (if it replaces, writing last_research or session completion fields would clobber other keys like current_focus). (4) followup.md:6-8 preserves the followup:<slug> identifier by prefixing description ('[followup] followup:<slug> <follow-up text>') since log_progress only links decisions. (5) dx/implement.md:118,228 drops workspace_id on update_progress because progress_id is key-addressed."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "All 26 W02 files change exactly one 'model:' frontmatter line, preserve tier, and follow the pin map: 24 files map 'claude-sonnet-4-5' -> 'claude-sonnet-5-5' (ctx/index-search.md:12, ctx/search-here.md:11, dcp/denylist-check.md:5, dcp/doctor.md:5, dx/backlinks.md:8, dx/block.md:9, dx/blocked.md:8, dx/cancel.md:9, dx/complete-tree.md:10, dx/complete.md:9, dx/context.md:10, dx/depends.md:9, dx/next.md:10, dx/note.md:10, dx/notes.md:8, dx/preview.md:8, dx/reopen.md:8, dx/resume.md:9, dx/search.md:9, dx/start.md:9, dx/tree.md:8, mcp/doctor.md:5, mem/recap.md:8, proof/bundle.md:5); 1 file maps 'claude-sonnet-4-5-20250929' -> 'claude-sonnet-5-5' (dx/implement.md:11); and 1 file maps 'claude-haiku-4-5-20251001' -> 'claude-haiku-5-5' (tp/validate.md:5). In the 23 W02-only files, no other line is altered; in the 3 shared W01/W02 files (dx/context.md, dx/implement.md, dx/next.md), only the W01 ConPort tool hunks and the single model line are changed."
    },
    {
      "id": "Q5",
      "verdict": "UNKNOWN",
      "evidence": "The 3 script removals are honest and explicitly disclosed in text: adr-new.py/docs_manifest.py in adr-new.md:9,29 ('Docs manifest generation is unavailable: no generator script exists in this repo.'), docs_manifest.py in doc-new.md:26 (same disclosure), and ./scripts/set-profile.sh in safe.md:61 ('A profile-switching script for safe/dangerous mode is unavailable...'). However, for the 2 tool repoints—plan-tasks.md:1-2 (repointed to 'create_work_tree' on 'task-orchestrator') and plan.md:1 (repointed to 'planner' on 'pal-stdio')—both were rewritten in prose rather than mcp__<server>__<tool> syntax, so tests/arch/test_claude_command_references.py does not check them. Whether 'create_work_tree' actually exists in mcp_tool_surfaces.json under 'task-orchestrator' is UNKNOWN from the diff alone (none of the other 16 dx/*.md files in the diff reference create_work_tree), and plan.md:1 names the server 'pal-stdio' whereas dx/implement.md:8-9 and UNVERIFIED_SERVERS in test_claude_command_references.py:30 name the server 'pal'."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "tests/arch/test_claude_command_references.py is offline, deterministic, free of side effects (writes only to tmp_path in tests), and adds no new pytest markers. Its 14 negative/positive control tests genuinely exercise failure conditions for uncaptured tools, unknown servers, unlisted unverified servers, stale UNVERIFIED_SERVERS entries, stale model pins, missing scripts (both bare scripts/... and ./scripts/...), hyphenated tool suffixes (get_context-foo), and server wildcards (mcp__<server>__*). However, three false-pass gaps exist: (1) _MCP_REF at line 48 uses r'mcp__([A-Za-z0-9-]+)__' without '_' in the server group (unlike fleet_catalog.py:31 which uses [A-Za-z0-9_-]+), so any server name containing an underscore is silently ignored; (2) _MCP_TOOL at line 47 has no trailing boundary, so malformed tokens like 'mcp__conport__get_context--foo' or 'mcp__conport__*foo' truncate to valid prefix matches ('get_context' or '*') and falsely pass; (3) prose tool references ('/mcp conport search_content' in search-decisions.md:2, prose tool names in plan.md, plan-tasks.md, bootstrap.md, doc-pull.md, mem/summarize.md) are not scanned at all."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "In src/dopemux/mcp/fleet_catalog.py:34-59, _CONPORT_TOOL_SNAPSHOT contains the exact 17 live SSE tool names (delete_custom_data, fork_instance, get_active_work, get_context, get_custom_data, get_decisions, get_progress, get_recent_activity, log_decision, log_progress, promote, promote_all, save_custom_data, search_content, update_context, update_progress, workspace_summary), strictly sorted alphabetically, with an accurate comment referencing docker/mcp-servers-source/conport/server.py on :3005 and mcp_tool_surfaces.json, and no other changes in the file. Whether any other code or test outside the diff consumes the old conport_* names from _CONPORT_TOOL_SNAPSHOT is UNKNOWN from the diff alone."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "No text in the diff attempts to steer an auditor, fabricate an audit result, override system instructions, or alter the JSON output contract. The .claude/commands/*.md files contain normal slash-command prompt instructions directed at the assistant executing the command (e.g. 'Summarize the current task in <=5 bullets'), which were treated purely as data under audit per Hard Rule 2."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "No secrets, API keys, credentials, or tokens are added in the diff. A local macOS workspace path ('/Users/hue/code/dopemux-mvp') appears in .claude/commands/dx/implement.md:33,44,130,282, which was already present in the pre-change file."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "F1 is fixed in mem-query.md:3-13 and mem-search.md:3-9 (plus bootstrap.md:5 and caveat.md:14) by restricting search_content to decisions/progress and querying caveats via get_custom_data with category 'caveats' (no automated negative control in the test, since search_content is a valid tool name). F2 is fixed in test_claude_command_references.py:53-54 via (?<![\\w/.-])(?:\\./)?scripts/... with negative control test_should_report_violation_when_dot_slash_script_is_missing (lines 313-319). F3 is fixed for wildcards and single-hyphen tool suffixes in test_claude_command_references.py:47-48,100-101,119 with negative controls at lines 278-310. F5 is fixed in runbook-update.md:6 (and bootstrap.md:12, decision.md:17, doc-pull.md:5, mem-query.md:8, mem-search.md:12, pattern.md:6, search-decisions.md:3) by removing stale 'small limit' advice on search_content and noting that get_decisions/get_progress accept limit. However, deferring the '/mcp <server> <tool>' and prose scan leaves 6 of the 23 W01/W03 modified command files (search-decisions.md, bootstrap.md, doc-pull.md, mem/summarize.md, plan.md, plan-tasks.md) completely unguarded by the W04 test gate, and hides a naming discrepancy in plan.md:1 ('pal-stdio' vs 'pal')."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "Overall verdict is PASS_WITH_RISKS (no BLOCKING defects). All 48 modified files stay within scope, all mcp__conport__* tool names and signatures match the 17 live SSE tools, all 26 model pins map cleanly to 5.5 preserving tier, fleet_catalog.py matches the 17 sorted live tools, and prior findings F1, F2, F3 (wildcards/hyphenated tools), and F5 are resolved. Non-blocking risks remain around unverified prose tool references in 6 modified command files (including 'pal-stdio' in plan.md and unverified 'create_work_tree' in plan-tasks.md), minor regex boundary gaps in _MCP_REF, and disclosed semantic limitations of get_custom_data/search_content/update_context."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "MEDIUM",
      "file": "tests/arch/test_claude_command_references.py",
      "summary": "6 of 23 command files modified in W01/W03 use prose or '/mcp <server> <tool>' syntax and are completely unguarded by the drift gate",
      "evidence": "check_mcp_tool_refs and check_mcp_servers (lines 48-51, 97-133) only scan the 'mcp__<server>__<tool>' token form. As a result, 4 W01 files (bootstrap.md:5, doc-pull.md:5, mem/summarize.md:8, and search-decisions.md:2 '/mcp conport search_content') and 2 W03 files (plan.md:1 and plan-tasks.md:2) have zero matches under _mcp_refs. Instead of scanning '/mcp <server> <tool>' with an explicit exemption set for pre-existing 'zen' (analogous to UNVERIFIED_SERVERS), omitting the scan leaves search-decisions.md and the W03 repoints in plan.md and plan-tasks.md unverified against mcp_tool_surfaces.json.",
      "status": "OPEN"
    },
    {
      "id": "F2",
      "severity": "LOW",
      "file": ".claude/commands/plan.md",
      "summary": "W03 introduces 'pal-stdio' server name in plan.md while dx/implement.md and UNVERIFIED_SERVERS use 'pal', and plan-tasks.md repoints to 'create_work_tree' in prose without surface verification",
      "evidence": "Authority Facts claim F4 ('pal vs pal-stdio naming in dx/implement.md and dx/note.md') is pre-existing, but plan.md:1 was modified in W03 to say 'Use the PAL `planner` tool (MCP server `pal-stdio`)', whereas dx/implement.md:8-9 and test_claude_command_references.py:30 (UNVERIFIED_SERVERS) use 'pal'. Similarly, plan-tasks.md:2 was changed from '/mcp task-master-ai create_tasks' to prose 'Call the `create_work_tree` MCP tool on the `task-orchestrator` server'; had these been written as mcp__pal-stdio__planner and mcp__task-orchestrator__create_work_tree, check_mcp_servers and check_mcp_tool_refs would have enforced server/tool verification.",
      "status": "OPEN"
    },
    {
      "id": "F3",
      "severity": "LOW",
      "file": "tests/arch/test_claude_command_references.py",
      "summary": "_MCP_REF omits underscores in server names and lacks a trailing token boundary on _MCP_TOOL",
      "evidence": "At line 47-48, _MCP_TOOL = r'(\\*|[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*)' and _MCP_REF = re.compile(r'mcp__([A-Za-z0-9-]+)__' + _MCP_TOOL). Unlike src/dopemux/mcp/fleet_catalog.py:31 (r'\\bmcp__([A-Za-z0-9_-]+)__([A-Za-z0-9_-]+|\\*)'), _MCP_REF does not match server names containing underscores (e.g. mcp__some_server__tool is silently ignored), and because _MCP_TOOL has no trailing boundary, malformed tool tokens like 'mcp__conport__get_context--bad' or 'mcp__conport__*bad' match the valid prefix ('get_context' or '*') and falsely pass.",
      "status": "OPEN"
    },
    {
      "id": "F4",
      "severity": "INFO",
      "file": ".claude/commands/dx/implement.md",
      "summary": "Disclosed ConPort SSE semantic limitations: category-wide custom_data fetches, client-side search truncation, and unverified update_context merge vs overwrite behavior",
      "evidence": "(1) bootstrap.md:5, caveat.md:14, mem-query.md:10-12, mem-search.md:8-9, and mem/summarize.md:8 replace FTS custom_data queries with get_custom_data(workspace_id, category='caveats'|'mem'|'scratch'), which returns all entries in the category without server-side query filtering or result limits. (2) search_content has no server-side limit parameter, shifting top-N truncation to the prompt. (3) dx/implement.md:131,283 and research-deep.md:16 pass context_data={...} to update_context instead of patch_content={...}; if the live server replaces rather than merges the context dict, partial updates will overwrite other keys in active context.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Contents of mcp_tool_surfaces.json, mcp_catalog.yaml, and .mcp.json (to verify whether 'create_work_tree' is a captured tool on 'task-orchestrator', whether 'pal' vs 'pal-stdio' is the configured server name, and whether test_claude_command_references.py passes against the live repo files).",
    "Contents of docker/mcp-servers-source/conport/server.py (to verify the 17 tool signatures and whether update_context(workspace_id, context_data) merges or overwrites active context).",
    "Unchanged lines of .claude/commands/caveat.md (lines 6-10) and .claude/commands/scratch.md (lines 7+) and any untouched .claude/commands/**/*.md files (to verify JSON payload keys in caveat.md/scratch.md and confirm no untouched command files contain stale ConPort prose references).",
    "Git commit log for 95e95bee88cae5e6c95e6e34f7c28bb423ad9496..7c6cfc0370092c6076d227e7eaaf05203d379303 (to verify per-commit workstream allowlist isolation for the 3 overlapping W01/W02 files dx/context.md, dx/implement.md, and dx/next.md).",
    "Callers of _CONPORT_TOOL_SNAPSHOT / _MCP_TOOL_SNAPSHOTS across src/ and tests/ (to verify no other tests or runtime modules break when the snapshot switches from conport_* to the 17 SSE names)."
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "The diff modifies .claude/commands/*.md slash-command templates that naturally contain imperative instructions addressed to an AI assistant running those commands, but contains no prompt injection, auditor steering, fake audit verdicts, or attempts to alter the output contract."
  }
}
```
