# Dopemux Beta-Readiness — Dispatch Prompts (per tool)

Paste-ready prompts that open the orchestrator, pull the packets tagged for that tool, and run them under governance. Shared facts injected into each:

- **Repo:** `dopemux-mvp` · HEAD `755bf3846` · branch base `main` (cut a feature branch per packet)
- **Orchestrator:** task-orchestrator MCP, root item **`b5960763`** ("Dopemux Beta-Readiness")
- **Backlog + evidence:** `claudedocs/beta-readiness-2026-05-29/` → `01-SEQUENCED-BACKLOG.md` (fix per `BETA-<ID>`), `00-MASTER-REPORT.md` (path:line evidence), `02-REMOVE-CONSOLIDATE.md` (removals), `04-IMPLEMENTER-ASSIGNMENTS.md` (your packet list)
- **Wave order (hard):** Wave 0 → 1 → 2 → 3; `WRAP-00` before `WRAP-01..04`. Don't start a packet whose wave predecessors aren't merged.
- **Governance (AGENTS.md):** one branch + PR per packet; min PAL chain `analyze → planner → codereview → precommit`; proof bundle on completion; **never delete a `removal` item without a confirming diff first**.

How each tool finds its own packets: read `04-IMPLEMENTER-ASSIGNMENTS.md` → your `impl-<tag>` section (authoritative BETA-ID list). Resolve any ID to an orchestrator item with `query_items(operation="search", query="<BETA-ID>")` → use that `id` for `claim_item` / `advance_item`.

---

## 1 — Claude Code (Opus / Sonnet / Haiku)

> Run inside the dopemux repo (has the full MCP stack). Swap `impl-opus` for `impl-sonnet` / `impl-haiku` and launch that session on the matching model.

```
You are the `impl-opus` implementer for the Dopemux beta-readiness backlog (task-orchestrator root b5960763, HEAD 755bf3846).

1. Read claudedocs/beta-readiness-2026-05-29/04-IMPLEMENTER-ASSIGNMENTS.md → the `impl-opus` section. That is your packet list (BETA-IDs).
2. Work in WAVE ORDER (see 01-SEQUENCED-BACKLOG.md): only start a packet whose wave's predecessors are merged. Within a wave do CRIT/data-safety first.
3. For EACH packet:
   a. Resolve it: mcp__task-orchestrator__query_items(operation="search", query="<BETA-ID>") → take the item id → claim_item.
   b. git checkout -b packet/<BETA-ID> off main.
   c. Read the BETA-<ID> row in 01-SEQUENCED-BACKLOG.md and its evidence in 00-MASTER-REPORT.md (path:line). Implement the smallest correct change matching `fix`.
   d. Validate narrow-first (focused tests / the exact command in the fix). Run the PAL chain: pal/analyze → pal/planner → implement → pal/codereview → pal/precommit. For your security/architecture packets (SEC-01/02, WF-02, MCP-03, WRAP-00/04) add pal/thinkdeep + pal/challenge.
   e. Open a PR titled "<BETA-ID>: <title>". advance_item to review; manage_notes a proof bundle (files changed, validations PASS/FAIL/NOT_RUN, PR URL).
4. REMOVAL packets: produce the confirming diff and a grep proving zero importers BEFORE deleting. Stop if anything still references the target.
Drain your queue, then stop and report a one-line status per packet.
```

**Opus** takes: INSTALL-06, WF-02, SEC-01, SEC-02, MCP-03, UI-02, WRAP-00, WRAP-04 (think hard; these gate trust).
**Haiku** prompt is identical but the work is trivial — for INSTALL-02 the whole fix is two lines (`docker network create dopemux-network`). Skip pal/thinkdeep; keep codereview+precommit.

---

## 2 — Codex (5.5 / 5.3-codex / 5.4-mini)

> Codex CLI in the repo. Point each model at its tag.

```
You are Codex (model: gpt-5.3-codex) implementing the Dopemux beta-readiness packets tagged `impl-codex-53`.

Repo HEAD 755bf3846. Your packet list: claudedocs/beta-readiness-2026-05-29/04-IMPLEMENTER-ASSIGNMENTS.md → `impl-codex-53` section.
For EACH packet (respect wave order from 01-SEQUENCED-BACKLOG.md):
  1. Read the BETA-<ID> row in 01-SEQUENCED-BACKLOG.md + its evidence in 00-MASTER-REPORT.md (exact path:line).
  2. git checkout -b packet/<BETA-ID>; implement the minimal change in `fix`.
  3. Run the focused tests named in the fix (and `pytest -q <relevant path>`); do not broaden scope.
  4. Open one PR per packet titled "<BETA-ID>: <title>" with: what changed, the validation output, and residual risk.
If the task-orchestrator MCP is available, also: query_items(search "<BETA-ID>") → claim_item → advance_item with a proof note. Otherwise the PR is the record.
Hard rules: smallest correct change; no removal without a confirming diff; non-zero exit must surface (don't swallow).
```

- **5.3-codex** → CLI-01 (implement 5 `decisions` subcommands), CLI-03, TEST-06, CLI-07/08.
- **5.4-mini** (cheap, small) → INSTALL-07 (retry loop), SVC-01 (compose `deploy.resources.limits`), TEST-07/08.
- **5.5** (heavy net-new, owner-with-review) → WRAP-02 (Codex live wrapping) and WRAP-03 (Copilot live wrapping) — **blocked until WRAP-00 spec lands**; start from that spec, design the managed-agent launcher, ship behind a feature flag.

---

## 3 — Gemini + PAL (async PRs)

> Best for well-specified install/compose/config/docs/dead-code. Gemini writes the diff; PAL reviews. One PR per packet.

```
You are Gemini (with PAL tools) implementing the Dopemux beta-readiness packets tagged `impl-gemini-pal`.

Repo HEAD 755bf3846. Your packet list: claudedocs/beta-readiness-2026-05-29/04-IMPLEMENTER-ASSIGNMENTS.md → `impl-gemini-pal` section. These are well-specified and ship as async PRs.
For EACH packet (wave order per 01-SEQUENCED-BACKLOG.md):
  1. Read the BETA-<ID> row in 01-SEQUENCED-BACKLOG.md + evidence in 00-MASTER-REPORT.md (path:line).
  2. CODE/CONFIG packets (INSTALL-01/03/04/05/09, SEC-03, MCP-02, CLI-02/04, SVC-03/05/06): produce the minimal diff exactly per `fix`. Use your full-file context to keep edits surgical. Run pal/codereview on the diff before finalizing.
  3. DOC packets (DOCS-02/03/06, MCP-04, SVC-04): author the content. DOCS-02 = generate a real `dopemux` CLI reference from `dopemux --help` output (replace the chatx cheat-sheet entirely). Verify every command/port against compose.yml + the CLI, not the old docs.
  4. Open one PR per packet "<BETA-ID>: <title>" with the diff + your verification notes.
DO NOT attempt tasks needing an iterative local test-run-fix loop (those weren't assigned to you). If a packet turns out to need that, stop and flag it for reassignment rather than guessing.
Hard rules: smallest correct change; CLI-04 deletes Dummy* only from the PRODUCTION path (keep test fixtures); no behavior change beyond the stated fix.
```

---

## 4 — Agy (Antigravity) — the two big refactors

> Autonomous multi-file. Both are Wave 3 (post-beta) — don't start until Waves 0–2 are landing.

```
You are Antigravity (agy) handling the two largest Dopemux refactors, tagged `impl-agy`. Repo HEAD 755bf3846. These are post-beta — begin only once Waves 0–2 PRs are merging.

PACKET BETA-CLI-06 — split the 6337-line src/dopemux/cli.py monolith.
  - This is MECHANICAL extraction, behavior MUST stay identical. Move `start`'s routing/proxy/instance logic into src/dopemux/commands/start_*.py (the repo already uses commands/* modules). Delete the shadowed duplicate function flagged in 00-MASTER-REPORT.md.
  - After every extraction run the full test suite + `dopemux --help` and every subcommand `--help`; the command tree must be byte-identical. Open a PR with a before/after module map.

PACKET BETA-DOCS-DEDUP — repo-wide 760-file doc duplication (the `*-2.md`/`*-3.md` orphans from PR #226).
  - Build the duplicate set with `fdupes`/hash compare; confirm each dupe is wired into no live nav (`docs_index.yaml`, _index/_manifest, internal links) before deleting. Open a PR listing every file removed + the link-integrity check.
Hard rules: identical runtime behavior; no deletion without a no-importer/no-link proof; keep the canonical copy.
```

---

## Coordinator note (run this as a Claude Code pass)
After PRs land, reconcile the orchestrator so wave gates open correctly: for each merged `<BETA-ID>`, `query_items(search "<BETA-ID>") → advance_item(...complete...)`. When all of a wave's items are terminal, its `BLOCKS` edge releases the next wave. Re-run `BETA-WRAP-00` (Opus) early — it unblocks the whole agent-wrapping epic and is the one packet whose spec the audit couldn't finish.
