# CLAUDE.md Prune Pass — Removal Accountability Audit

**Date**: 2026-06-07
**Question audited**: "It seems excessive — what was actually removed?"
**Method**: 8 Sonnet auditors, each instructed to be skeptical/pro-restoration, classifying every removed block and **verifying every "duplicate" claim by opening the cited canonical file**. Plus mechanical byte-diff proofs.
**Verdict**: **Not excessive.** ~97% of removed content was relocation, verified duplication, dead snapshots, not-wired pseudo-code, or generic filler. The audit found a small set of genuine gaps (~40 lines of real behavioral content + a few stub tool-name omissions), now restored — see §4.

---

## 1. Headline accounting

Total removed across the whole pass (global always-loaded + in-repo lazy modules): **~4,450 lines**.

| Category | ~Lines | Lost? |
|---|---:|---|
| **Relocated** to `MCP_*_REFERENCE.md` (byte-identical supersets) | 1,930 | No — full originals on disk |
| **Relocated** to canonical (`custom-commands.md`, MCP stubs, CLAUDE.md, MODE_Orchestration) | 1,233 | No — verified present in canonical |
| **Verified duplicate** of a cited canonical | 318 | No — confirmed by opening canonical |
| **Not-wired bash pseudo-code** (DETECT_ATTENTION_STATE, ADAPT_FOR_*, etc.) | 498 | No — behavioral rules kept as prose |
| **Dead status/timeline snapshots** (Implementation Status, Day-1/Day-2 timeline) | 60 | No — frozen project state |
| **Generic filler** (SOLID/DRY prose, TOCs, how-to-write-a-shell-script) | 286 | No — generic SWE / navigation |
| **Flagged as unique-lost by auditors** | ~125 | Mostly trivial — see §3 |

The 1,930-line MCP-manual figure was **mechanically proven**: each `MCP_X_REFERENCE.md`, with its 8-line header stripped, is `diff`-identical to the pre-prune original. Zero bytes lost.

---

## 2. Per-scope verdicts

| Scope | Before→After | Verdict | Real issues |
|---|---|---|---|
| `PRINCIPLES.md` (deleted) | 60→0 | ✅ safe | SOLID O/C/L/I/D, DRY — generic, in model weights |
| `FLAGS.md` + `RULES.md` strip | 572→343 | ✅ safe-minor | MCP Tool Preference **confirmed intact**; lost a 5-line flag-order list |
| `ADHD_FEATURES.md` + `GOVERNANCE` | 560→388 | ⚠️ safe-minor | **NOTABLE: PAL behavioral mandates lost + pointer was wrong** |
| 5 MODE files | 335→147 | ✅ safe-minor | All "Behavioral Changes" kept; lost 🔧 and `:` symbols |
| consolidate `integration.md` | 598→107 | ✅ safe | 4-category map, 15-agent table, why-table all survive |
| consolidate `workflows.md` | 933→160 | ⚠️ safe-minor | Lost ADHD doc-frontmatter schema (its canonical was archived) |
| consolidate `adhd-patterns.md` | 701→98 | ⚠️ safe-minor | **Lost: attention-conditioned task ordering + 7±2 list cap** |
| 6 MCP stubs (completeness) | n/a | ⚠️ safe-minor | **Stubs omit some real tool names** (delete tools, find_relationships) |

No scope returned `over-cut-recommend-restore`. The big reduction holds up.

---

## 3. Genuine losses found (skeptical audit)

### Restored (behavior-changing, gone from all reachable files) — see §4
1. **NOTABLE — GOVERNANCE PAL per-tool behavioral mandates.** The doctrinal one-liners (`tracer`: don't patch orchestration from intuition; `planner`: required before multi-file/schema/migration/infra/arch changes; `challenge`: assume first-pass incomplete; `consensus`: never silently choose easiest; `precommit`: tests passing ≠ correctness) were cut, and my replacement pointer "lives in `MCP_PAL.md`" was **factually wrong** — those mandates are *not* in MCP_PAL.md or its reference. This is a correctness bug I introduced.
2. **MINOR — ConPort stub** omitted 4 delete tools (`delete_decision_by_id`, `delete_progress_by_id`, `delete_system_pattern_by_id`, `delete_custom_data`). A model wouldn't know they exist.
3. **MINOR — Serena stub** omitted `get_symbols_overview`, `find_referencing_symbols`, `find_relationships`, `get_linked_items` (real navigation/graph tools).
4. **MINOR — DopeContext stub** omitted `stop_autonomous_docs_indexing` (asymmetry).
5. **MINOR — adhd-patterns** lost two real behavioral rules: attention-conditioned **task ordering** (scattered→quick-wins-first, hyperfocus→hardest-first) and the **7±2 working-memory list cap** (distinct from the 1/3/5 option cap).

### Flagged but NOT restored (trivial / recoverable / aspirational)
- SOLID O/C/L/I/D + DRY (PRINCIPLES) — generic OOP in model weights; no Dopemux behavioral delta.
- Flag-application order 5-line list (FLAGS) — derivable from surviving Flag Priority Rules.
- 🔧 / `:` symbols (Token Efficiency) — shorthand notation only.
- Completion-streak ConPort schema (adhd) — flavor; recoverable from main-branch.
- `pal/challenge` "on user disagreements" trigger — PAL stub's "avoid reflexive agreement" captures the spirit.
- `is_revision`/`branch_from_step` planner params — in `MCP_PAL_REFERENCE.md`.
- ADHD doc-frontmatter schema (`cognitive_load`/`attention_state`/`reading_time`) — its canonical (`documentation-standards.md`) was archived *independently* of this pass; `doc-new.md` already uses stripped frontmatter, so the convention was effectively dead. Noted, not restored.
- Serena `filter_by_focus`/`suggest_next_step` — aspirational ADHD tools on the unproven attention-state pipeline; intentionally not promoted.

---

## 4. Fixes applied

| Fix | File | Type |
|---|---|---|
| Restore condensed PAL behavioral mandates + correct the pointer | `~/.claude/GOVERNANCE_PRINCIPLES.md` | global (live) |
| Add 4 ConPort delete tools to stub | `~/.claude/MCP_ConPort.md` | global (live) |
| Add 4 Serena nav/graph tools to stub | `~/.claude/MCP_Serena.md` | global (live) |
| Add `stop_autonomous_docs_indexing` | `~/.claude/MCP_DopeContext.md` | global (live) |
| Restore task-ordering + 7±2 working-memory rules | `.claude/modules/shared/adhd-patterns.md` | in-repo (committed) |

All restorations are additive and kept terse (stubs stay thin; total ~+25 lines).

---

## 5. Recoverability map

Nothing is irreversibly gone:
- **MCP manual detail** → `~/.claude/MCP_*_REFERENCE.md` (on disk, lazy-loaded).
- **Global Tier-A removals** → `~/.claude/backups/2026-06-06-claude-md-audit/prune-pass/`.
- **In-repo consolidation** → `git show fa862cfa5:<path>` (pre-consolidation) and the un-consolidated `adhd-patterns.md` still on `main`.
- **Deleted strays / archive** → `ARCHIVED_RECOVERY/` kept on disk; strays in git history.

---

## 6. Conclusion

The ~66% always-loaded reduction (4,295→1,447 lines) and the ~1,867-line module consolidation were **justified, not excessive**. The dominant categories were relocation-to-reference and verified duplication, not loss. The audit earned its keep by catching one correctness bug (the inaccurate PAL pointer) and four minor stub/behavioral gaps, all now fixed. Residual trivial losses are generic knowledge in model weights or recoverable from backups/references.
