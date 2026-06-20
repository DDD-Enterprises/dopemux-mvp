# Claude Code Automation Implementation Plan

> **DEFERRED** — validation tree only. Do not execute until supervisor approves phase 1 TP.

**Spec:** `claudedocs/spec-claude-code-automation-design-2026-06-16.md`  
**Design basis:** `proof/TP-DMX-CLAUDE-AUTO-VALIDATION-001/`

---

## Task 1: Template skill — task-packet

**Files:**
- Create: `src/dopemux/templates/init/.claude/skills/task-packet/SKILL.md`

**Steps:**
1. Copy TaskX workflow from adOps `CLAUDE.md` + dopemux `AGENTS.md` §5
2. Add `$ARGUMENTS` for TP path
3. Require Implementer Report with raw command outputs

**Verify:** `test -f src/dopemux/templates/init/.claude/skills/task-packet/SKILL.md`

---

## Task 2: Template skill — project-conventions

**Files:**
- Create: `src/dopemux/templates/init/.claude/skills/project-conventions/SKILL.md`

**Steps:**
1. Frontmatter: `user-invocable: false`
2. Document pytest/ruff/mypy commands as placeholders `{{TEST_CMD}}`

**Verify:** YAML frontmatter valid

---

## Task 3: Template skill — verify-gates

**Files:**
- Create: `src/dopemux/templates/init/.claude/skills/verify-gates/SKILL.md`

**Steps:**
1. `disable-model-invocation: true`
2. List CI-equivalent commands with PASS/FAIL/NOT_RUN buckets

**Verify:** Skill parseable by Claude Code

---

## Task 4: Template skill — pal-routing

**Files:**
- Create: `src/dopemux/templates/init/.claude/skills/pal-routing/SKILL.md`

**Steps:** Use routing table from spec §8

---

## Task 5: Child hook snippet

**Files:**
- Create: `src/dopemux/templates/init/.claude/settings.json.hook-snippet.json`

**Steps:**
1. PreToolUse block for `.env`, `uv.lock`
2. Document merge instructions in `INSTALL.md`

**Verify:** JSON valid; no conflict with platform `native_hooks.py` pattern (child repos use their own settings or merge)

---

## Task 6: Wire pal_validation.json routes

**Files:**
- Modify: `pal_validation.json`

**Steps:**
1. Add routes for automation catalog validation
2. Link to `proof/TP-DMX-CLAUDE-AUTO-VALIDATION-001/VALIDATION_MATRIX.md`

---

## Task 7: Docs update

**Files:**
- Modify: `INSTALL.md` or `QUICK_START.md`

**Steps:** Add "Claude automation templates" section

**Verify:** `python scripts/docs_validator.py` if applicable

---

## Task 8: adOps pilot (phase 2 — separate TP)

**Files:** adOps `.claude/skills/*` (via worktree init)

**Steps:**
1. `dopemux mcp init` in adOps
2. Copy templates
3. Proof bundle `TP-ADOPS-CLAUDE-AUTO-PILOT-001`

---

## Commit strategy

One commit per task. Push after each. Proof bundle per TP series.