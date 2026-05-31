# Git State

- worktree: `/Users/hue/code/dopemux-mvp/.worktrees/tp-dmx-merge-remediation-202`
- branch: `codex/tp-dmx-merge-remediation-202`
- base branch: `origin/codex/tp-dmx-steward-gate-201`
- base/head before TP202 commit: `eac0853f521041c5d52f0d40eddb4be84d66b424`
- TP202 implementation commit before proof metadata amend:
  `29bed2029a813e9c294273e6db36901fcd3ba13b`
- origin: `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- repo marker: `.dopetaskroot` present
- primary checkout dirty state: ignored; TP202 work ran in the dedicated worktree above

Intended staged files before commit:

```text
M  config/pr_merge_specialist/policy.yaml
M  docs/ops/steward-merge-gate.md
M  src/dopemux_pr_merge_specialist/queue_drain.py
M  task-packets/generated/TP-DMX-MERGE-REMEDIATION-202.json
A  tests/pr_merge_specialist/test_remediation_gate.py
?? proof/TP-DMX-MERGE-REMEDIATION-202/
```
