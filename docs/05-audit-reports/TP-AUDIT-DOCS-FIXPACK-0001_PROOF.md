---
id: TP-AUDIT-DOCS-FIXPACK-0001_PROOF
title: Tp Audit Docs Fixpack 0001 Proof
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-02'
last_review: '2026-03-02'
next_review: '2026-05-31'
prelude: Tp Audit Docs Fixpack 0001 Proof (reference) for dopemux documentation and
  developer workflows.
---
# TP-AUDIT-DOCS-FIXPACK-0001_PROOF.md
**Title:** ConPort Diátaxis Docs FixPack Proof Bundle
**Date:** 2026-02-26
**Status:** ❌ NOT VERIFIED IN THIS ARTIFACT (requires operator command outputs)

This file is a **fail-closed proof bundle template**. It contains the exact commands that must be run and the exact places to paste the output.
Nothing in this document is “assumed true” until the corresponding output is pasted under each command.

---

## 0) Repo Context

### Command
```bash
pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
```

### Output
```text
PASTE OUTPUT HERE
```

---

## 1) MCP stdio endpoint verification (fail-closed)

### Command
```bash
echo '{"tool":"test","input":{}}' | uvx --from context-portal-mcp conport-mcp 2>&1 | head -100
```

### Output
```text
PASTE OUTPUT HERE (including any errors)
```

### Result
- [ ] VERIFIED (command runs and returns a valid response)
- [ ] UNVERIFIED (command fails; error captured above)

---

## 2) Status banner compliance

### Requirement
Every audited doc must begin with:

```md
**Status**: Current | Partial | Planned
**Last Verified**: 2026-02-26
```

### Commands
```bash
# Count status banners found
rg -n "^\*\*Status\*\*:" docs | wc -l

# Count markdown files under docs
find docs -name "*.md" -type f | wc -l

# Show first 40 banner hits (spot-check)
rg -n "^\*\*Status\*\*:" docs | head -40
```

### Output
```text
PASTE OUTPUT HERE
```

### Result
- [ ] PASS (banner count matches audited doc count)
- [ ] FAIL

---

## 3) Doc size compliance (<= 800 lines each)

### Commands
```bash
# List offenders (must be empty to PASS)
find docs -name "*.md" -type f -exec wc -l {} + | awk '$1 > 800 {print $2, "EXCEEDS", $1, "lines"}'

# Optional: show top 30 largest docs (for diagnostics)
find docs -name "*.md" -type f -exec wc -l {} + | sort -nr | head -30
```

### Output
```text
PASTE OUTPUT HERE
```

### Result
- [ ] PASS (no output from the EXCEEDS command)
- [ ] FAIL

---

## 4) Final audit gates

### Commands
```bash
# Working tree state (should be clean OR changes are intentional and ready to commit)
git status --porcelain

# ConPort REST health (if running)
curl -s http://localhost:3004/health | jq -r .status

# Claude hook presence checks (adjust paths if your config differs)
rg -n "UserPromptSubmit" .claude/settings.json | wc -l || true
rg -n "SessionStart" .claude/settings.json | wc -l || true
```

### Output
```text
PASTE OUTPUT HERE
```

### Result
- [ ] PASS
- [ ] FAIL

---

## 5) Before/After summaries

### Before (baseline) – paste from prior audit
- Docs >800 lines: `__ / __`
- Missing status banners: `__ / __`
- MCP stdio: VERIFIED / UNVERIFIED

### After (this FixPack)
- Docs >800 lines: `__ / __`
- Missing status banners: `__ / __`
- MCP stdio: VERIFIED / UNVERIFIED

---

## 6) Conclusion (fail-closed)

**Overall Audit Status:** ☐ PASS ☐ FAIL

### Notes
- If overall status is PASS, include the commit hash of the final state and (optionally) tag the proof bundle with the repo version.
- If overall status is FAIL, list remaining blockers and the exact next commands to resolve them.
