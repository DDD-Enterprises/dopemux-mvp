# AUDITOR REPORT — PR #1420 L2 embedded audit (TP-DMX-PR1420-L2-AUDIT-001)

- **Auditor**: grok CLI 1.0.46, `grok-4.5` (`--effort high`), `--sandbox workspace` with cwd set to an empty scratch dir, so it could not write to the repo; edit and web tools disallowed
- **Implementer**: Claude Code (Anthropic Claude). The runner and model family differ from the auditor's.
- **Audited head**: `d7bb1e1462a6d0233b3d97beac7fbe43055a6d0e` · **Base**: `e47602a192e5dd245ba0264decbd5e51b269b44e` (main after #1412)
- **Verdict**: **PASS_WITH_RISKS**: 0 blocking findings, F-01 LOW, F-02 INFO
- **Observed identity**: grok session `01a11bd0-6669-78c3-b741-7b2447924f12` `summary.json` records `current_model_id=grok-4.5` and `reasoning_effort=high`
- **Raw output**: `review_bundle/AUDIT_OUTPUT_RAW.json`. Prompt: `review_bundle/AUDIT_INPUT.md`. Invocation: `review_bundle/AUDIT_INVOCATION.txt`

## Auditor return (verbatim)

```
TOOL_ACCESS=FULL
CUSTODY=MATCH  head=d7bb1e1462a6d0233b3d97beac7fbe43055a6d0e
VERDICT=PASS_WITH_RISKS
POINTS:
  1: UPHELD — `git grep` over HEAD excluding `proof/` finds only `.claude/hooks/untracked_work_probe.py:21` (`_CACHE_FILENAME = ".untracked-work-probe-cache.json"`) plus the new `.gitignore` lines for the probe cache; `_cache_path` / `_save_probe_marker` (`path.write_text`) are the in-repo writer. Zero in-repo hits for `dopemux-advisor-cache` / `advisor_cache` outside `.gitignore:424`. Outside-repo corroboration (not required by the grep gate): `~/.claude/hooks/dopemux_mcp_advisor.py` defines `_CACHE_FILENAME = ".dopemux-advisor-cache.json"` and `_save_cache` → `p.write_text(...)`. Accidental add in `6aeb25001` (#1273) confirmed via `git log --diff-filter=A` and `git diff --name-status 6aeb25001^..6aeb25001` (`A` for both caches).
  2: UPHELD — Scoped search of `.github/workflows`, `scripts/`, `src/`, `services/`, `tests/`, `.claude/`, `.codex/`, `config/` shows no reader that requires either path tracked or present in a fresh checkout. The only non-proof code hit is the probe hook’s own cache filename. Mentions under `proof/**` are narrative worktree-noise notes (`stash_check`, auditor residual notes, `AUDIT_CUSTODY.json`); no `checksums.sha256` or other hash manifest lists these paths. `scripts/audit/` and `scripts/governance/` validators bind proof packet paths / ADR inventories / embedded-audit heads — they do not re-hash these cache paths. `scripts/` has zero references to either filename. CI workflows have zero hits.
  3: UPHELD — Hook creates the cache via `_save_probe_marker` (`mkdir` + `write_text`) and treats missing/unreadable cache as “not yet probed” (`_already_probed` → `False` on exception). Detection goes through `dopemux.untracked_work` → `UncommittedChangeDetector.check_changes()` which runs `git status --porcelain` with no `--ignored`. Live check on this worktree: default `git status --porcelain` omits both paths; `git status --porcelain --ignored` shows `!!` for both. After ignore, the probe’s own write cannot appear as untracked/modified work.
  4: UPHELD — `git check-ignore -v` resolves `.claude/.untracked-work-probe-cache.json` → `.gitignore:423` and `.claude/.dopemux-advisor-cache.json` → `.gitignore:424`. Patterns are exact path literals beside the other per-hook caches (416–422). `!.claude/` negations only re-include `CLAUDE.md`, `statusline.sh`, `modules/`, `templates/` — none re-include these two files. Index at HEAD contains neither path (`git ls-files` empty; `cat-file -e HEAD:.claude/...` → exists on disk, not in HEAD).
  5: UPHELD — `git diff --name-status e47602a1..d7bb1e14` is exactly three paths (`D` ×2 caches, `M` `.gitignore` +2 lines). No secrets added. Deleted blobs are cache JSON only: probe = `{session_id, written_at}`; advisor = port/env snapshot with local absolute paths under `/Users/hue/code/dopemux-mvp` and instance id `dcd6` — machine-local cache data, no API keys/tokens (secretish scan negative). Files remain on disk and show as ignored (`!!`), consistent with `git rm --cached` + ignore. Disclosed pull friction is real; nothing else in-repo depends on these blobs remaining tracked.

FINDINGS:
  - id: F-01
    severity: LOW
    blocking: false
    title: Pull/merge friction on dirty local copies of the former tracked caches
    body: Any worktree that still has a locally modified copy of either file relative to the pre-PR blob must restore or otherwise clear that path before the deletion can apply cleanly (`git checkout -- <file>` as the PR states). This repo is worktree-heavy, so operators may hit this once per dirty worktree. Expected consequence of untracking; disclosed; does not break runtime hooks.
  - id: F-02
    severity: INFO
    blocking: false
    title: Historical #1273 blobs retain machine-local path/port snapshot
    body: Untracking stops further churn and removes the files from HEAD, but blob `1091cae16…` (advisor cache) remains reachable from `6aeb25001` history with local absolute paths and instance ports. Out of scope for this PR; no secret material observed in the blobs.

REMAINING_RISKS:
  - One-time checkout/pull conflict on worktrees where either cache is still dirty against the old tracked blob (F-01).
  - Advisor writer lives outside the repo (`~/.claude/hooks/dopemux_mcp_advisor.py`); in-repo grep cannot police future renames of that global hook, but ignore of the exact path still covers the current writer.
  - Git history still contains the accidental #1273 cache blobs (F-02); purge would be a separate history-rewrite decision.

DELEGATION: none — sole independent L2 auditor contract; cost-first child delegation not used.
```

## Disposition

- **F-01 (LOW, non-blocking)**: ACCEPTED_RISK. This is the expected one-time cost of untracking, and the PR body discloses it: a checkout whose copy of either file is still modified must run `git checkout -- <file>` before pulling.
- **F-02 (INFO, non-blocking)**: ACCEPTED_RISK. The #1273 blobs hold machine-local paths, ports and an instance id, but no secret material. Removing them from history would be a separate history-rewrite decision and is out of scope.
