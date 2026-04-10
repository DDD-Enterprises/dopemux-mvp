# Replay Branch Creation

- Packet: `TP-CODEX-RTE-MERGE-EXEC-001`
- Replay branch: `codex/rte-merge-exec-001`
- Base branch: `main`
- Merge-prep base guard: `f9c29499a2a1179b2dd77d81528492f47fcd55c9`
- Replay creation guard result: `BASE_OK`
- Actual branch creation source: current `main` tip at replay time
- Base commit: `e4bf2d148886cee0883c2afda5bdfd0a9591f840`
- Starting HEAD SHA: `e4bf2d148886cee0883c2afda5bdfd0a9591f840`
- Creation evidence: reflog entry `branch: Created from HEAD` at `2026-04-09 23:47:52 -0700`

## Commands

```bash
git merge-base --is-ancestor f9c29499a2a1179b2dd77d81528492f47fcd55c9 main && echo BASE_OK
git switch -c codex/rte-merge-exec-001
git reflog show codex/rte-merge-exec-001 --date=iso --format='%H%x09%gs%x09%cd'
```
