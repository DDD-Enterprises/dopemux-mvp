# Independent L2 audit — PR #1420, dopemux-mvp

You are the **sole final independent auditor**. The implementer was Claude Code. One call; be adversarial and check claims against primary files.

## 0. Custody
Repository under audit: `/Users/hue/code/dopemux-mvp/.worktrees/untrack-hook-caches`. Your working directory is an empty scratch directory, so run every git command as `git -C /Users/hue/code/dopemux-mvp/.worktrees/untrack-hook-caches …`. Your sandbox can't write to the repository.
`git rev-parse HEAD` must print exactly `d7bb1e1462a6d0233b3d97beac7fbe43055a6d0e`; otherwise return `NEEDS_SUPERVISOR` / `CUSTODY_MISMATCH`. Base (merge-base with main): `e47602a192e5dd245ba0264decbd5e51b269b44e`. Use `git diff e47602a192e5dd245ba0264decbd5e51b269b44e..d7bb1e1462a6d0233b3d97beac7fbe43055a6d0e`. **Do not create or modify any file in the mounted worktree** (run anything under `/tmp`). If you cannot run tools, set `TOOL_ACCESS=NONE`.

## 1. What this PR is
One commit, three paths:
- `.claude/.dopemux-advisor-cache.json`: removed from the index (`git rm --cached`; the file stays on disk).
- `.claude/.untracked-work-probe-cache.json`: removed from the index the same way.
- `.gitignore`: two lines added beside the other per-hook caches (`.gitignore:416-424`), so both paths are ignored.

Claim: both files are hook-written runtime caches committed by accident in #1273 (`6aeb25001`). Hooks rewrite them every session, so every checkout shows them modified.

## 2. Challenge each point — UPHELD / DISPUTED / UNVERIFIABLE with evidence
1. **Writers.** `.claude/hooks/untracked_work_probe.py` (around lines 21-26) is the only in-repo writer of `.untracked-work-probe-cache.json`. `.dopemux-advisor-cache.json` has **no** in-repo writer; it comes from a user-global hook outside the repo. Verify with `git grep` over the whole tree, excluding `proof/`.
2. **No readers depend on the file being tracked.** No code, test, CI workflow (`.github/`), script or config reads either file from the committed tree, or expects it present in a fresh checkout. Search `.github/workflows`, `scripts/`, `src/`, `services/`, `tests/`, `.claude/`, `.codex/`, `config/`. Mentions under `proof/` are historical diff records; confirm they are not consumed by any validator that would break when the paths disappear (e.g. `scripts/audit/`, `scripts/governance/`, proof validators that re-hash referenced paths on HEAD).
3. **Probe still behaves.** `untracked_work_probe.py` keeps working when its cache is ignored: it creates or overwrites the file and does not require it to be tracked. Its own cache write no longer counts as untracked work, because `git status --porcelain` excludes ignored files by default; check how the probe enumerates changes.
4. **Ignore rules are exact and narrow.** The two new `.gitignore` lines match only these two files: `git check-ignore -v` resolves each to `.gitignore:423`/`:424`. They don't hide other tracked or intended-tracked content, and no negation pattern elsewhere re-includes them.
5. **Scope and safety.** Only those three paths change. No secrets or machine-specific values are added, and the deleted blobs contain only cache data (inspect them with `git show e47602a192e5dd245ba0264decbd5e51b269b44e:.claude/.dopemux-advisor-cache.json` and likewise for the other file). Note the downstream effect: a checkout where either file is locally modified must `git checkout -- <file>` before pulling, which the PR body states. Is anything else at risk?

## 3. Output format
```
TOOL_ACCESS=<FULL|PARTIAL|NONE>
CUSTODY=<MATCH|MISMATCH>  head=<sha>
VERDICT=<PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR>
POINTS:
  1: <UPHELD|DISPUTED|UNVERIFIABLE> — <evidence>
  ... (1-5)
FINDINGS:
  - id: F-01
    severity: <CRITICAL|HIGH|MEDIUM|LOW|INFO>
    blocking: <true|false>
    title: ...
    body: ...
REMAINING_RISKS:
  - ...
```
