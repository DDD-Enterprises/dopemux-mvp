---
id: rte-audit-2026-05-22-hygiene-sweep
title: RTE Pre-Debut Audit — Repo Hygiene Sweep (F0b)
type: audit-artifact
phase: F0b
owner: claude
date: 2026-05-22
status: complete
---

# Repo Hygiene Sweep — F0b

**Audit branch:** `audit/rte-pre-debut-2026-05-22`
**Pre-sweep HEAD:** `aa97a331bcec37fbac747d1bdd125adc46426422` (post-F0a manifest)
**Working directory:** `/Users/hue/code/dopemux-mvp-audit-rte-debut`

## Scope decision

The user directed "extensive repo cleanup needs to happen first." Following an Explore-agent survey, candidates were grouped by risk. This sweep took the **conservative** subset only — items with **zero live references** in the codebase and clear leftover-scratch provenance. Higher-risk candidates (v3 code, `out/`, `proof/` artifacts, detached worktrees) were intentionally deferred.

## Deletions (this sweep)

### 1. Prior 55pro audit-assembly scratch (~1.3 MB, 27 files)

Removed from the audit branch:
- `audit_prep/` (24 files) — prompt bundles, reports, audit prep from the 2026-05-14 "55pro" effort
- `audit_inputs/` (3 files) — corresponding intake bundles

**Rationale:**
- Content is preserved on branch `codex/tp-dmx-rte-55pro-audit-assembly-001` (worktree at `/Users/hue/code/dopemux-mvp/.worktrees/tp-dmx-rte-55pro-audit-assembly-001`). F3 (promptset audit) can mine it from there.
- These directories were committed to main as scratch but are explicitly listed in the repo's exclusion policies:
  - `.pre-commit-config.yaml:119` — excluded from lints
  - `config/repo_hygiene/root_hygiene_policy.json:34–35` — declared as allowed root-clutter exception
  - `services/repo-truth-extractor/lib/prescan/models.py:48` — excluded by prescan walker
  - `task-packets/generated/TP-RTE-WALKER-006.json:104` — referenced as exclusion in walker hardening packet
- The walker exclusion remains defensive — if the dirs ever come back, they'll still be excluded. No runtime impact from deleting the contents.

### 2. Stale backup files (~40 KB, 5 files)

| Path | Reason |
|------|--------|
| `config/profiles/adhd-default.yaml.bak` | 0 live references; superseded `.yaml` exists |
| `config/profiles/python-ml.yaml.bak` | same |
| `config/profiles/web-dev.yaml.bak` | same |
| `docker/mcp-servers-source/conport/schema.sql.bak` | 0 live references; schema migrated |
| `services/dope-context/tests/test_mcp_server.py.bak` | 0 live references; current test file in place |

`grep -rln <basename> --include='*.py' --include='*.yaml' --include='*.json' --include='*.toml' --include='Makefile'` returned zero matches per file (excluding self-references).

**Total this sweep:** 32 files, ~1.34 MB removed.

## Intentionally NOT deleted

| Candidate | Size | Decision | Rationale |
|-----------|------|----------|-----------|
| `services/repo-truth-extractor/run_extraction_v3.py` + v3 test suite (~804 KB) | medium | **KEEP** | v3 is gated (PR #605) but still alive; deleting destroys the F1-CRIT-1/2 closure surface. Audit F2a will review the gate. Deprecation belongs to a future cleanup cycle. |
| `out/` (~2.5 MB) | mixed | **KEEP** | Mostly cockpit/authority series upload bundles, not RTE-specific. Out of audit scope. |
| `proof/` (~1.8 MB) | mixed | **KEEP** | Historical proof artifacts from prior TP closures (TP-CODEX-RTE-V5-*, TP-CONPORT-*). Removing them deletes audit evidence. F8 writes to `proof/repo-truth-extractor/audit-2026-05-22/` — that path remains clean. |
| 11 detached-HEAD git worktrees | n/a | **DEFER** | Worktree pruning affects the shared git dir at `/Users/hue/code/dopemux-mvp/`, not the audit branch alone. Separate cleanup pass; out of audit scope. |
| `.gitkeep` stubs under `docs/planes/pm/_evidence/` | <1 KB | **KEEP** | Trivially small; preserve as intentional placeholders until evidence packets land. |

## Verification

```
$ du -sh audit_prep audit_inputs 2>&1
du: audit_prep: No such file or directory
du: audit_inputs: No such file or directory

$ find . -name '*.bak' -path '*config/profiles*'
(none)

$ git status --short
D  audit_inputs/prompt3_refactored_seed.md
... (32 files total, all staged for commit)
```

## Exit criteria

- [x] Hygiene survey completed (Explore agent)
- [x] Per-candidate reference check (0 live refs for all items deleted)
- [x] Conservative deletion set applied
- [x] Higher-risk candidates explicitly deferred with rationale
- [x] Working tree state: 32 deletions staged

## Next

Commit, then mark F0b complete, then begin F1 (Drift Re-verification).
