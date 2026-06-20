# 04 — Challenge · TP-DMX-CLAUDE-AUTO-VALIDATION-001

Statements challenged with evidence-first counter-analysis.

## C1: "We need packet-scope-guard hook in MVP"

**Challenge:** Requires active task packet state file, allowlist parser, and PreToolUse on every edit — high complexity, easy false positives.

**Verdict:** **DEFER to phase 2.** MVP relies on task-packet skill (explicit invocation) + orchestrator enforcement hooks already live. Scope guard needs `ACTIVE_TP.json` convention — not standardized across child repos yet.

## C2: "Auto-pytest on every Python edit"

**Challenge:** adOps has 206 tests + 85% cov gate; full suite on each edit is prohibitive. CI already runs `uv run pytest -q`.

**Verdict:** **DEFER** platform-wide. **CONDITIONAL** child template: module-scoped `pytest path/to/test_module.py -q` only when test file exists. Never run full suite in PostToolUse.

## C3: "Playwright MCP for adOps"

**Challenge:** adOps uses Playwright as Python library for scraping (`src/adops/scrape/`), not browser UI testing.

**Verdict:** **DEFER.** context7 for Playwright docs is sufficient. Playwright MCP adds container overhead without matching use case.

## C4: "Duplicate /dx:next as a new skill"

**Challenge:** 18 dx commands already cover orchestrator workflow; duplication causes drift vs `surface_manifest.json`.

**Verdict:** **REJECT.** Use pal-routing Claude-only skill that maps intent → existing `/dx:*` or PAL tool. Never reimplement orchestrator surface.

## C5: "Implement all automations in one PR"

**Challenge:** design-dcp-mcp-skills-hooks used independent slices; AGENTS.md requires proof per TP.

**Verdict:** **REJECT.** Phased rollout: (1) templates + docs, (2) child-repo pilot on adOps, (3) optional hooks/plugins.

## Summary

| Item | Decision |
|------|----------|
| packet-scope-guard | DEFER phase 2 |
| auto-pytest PostToolUse | DEFER / module-scoped only |
| Playwright MCP | DEFER |
| New dx duplicates | REJECT |
| Big-bang impl | REJECT |