# Auditor report for PR 1508

Verdict: PASS_WITH_RISKS.
Auditor: OpenCode 1.18.30, cheaper-inference, kimi-k3, session ses_e3c20cd30ffeJ7ug7vu0iAieM2.
Audited commit: 043cd1fd7f5f9f0e5956e543a0ea07fe78984a3f.
Base: c5a0ca34f53dd0f2d55e11139dff74828ab34ab5.
Diff sha256: dd4322730fac4b201318f5a65d52381d78baccdb4e708d089d39164fd714ecb2.

The skill text stops rebase, update-branch, delete-branch, admin bypass, auto-pilot, and queue-drain while a GitHub merge queue is active. It does not grant a draft merge, resolution of a still-true finding, or an enqueue of a head whose audit or steward check is not success.

Accepted risks:

- F1 MEDIUM: the skill does not give a command that detects whether the merge queue is active.
- F2 MEDIUM: outside an active queue, the per-head audit and steward gate is no longer restated in SKILL.md.
- F3 LOW: no command re-checks the current head SHA or queue state immediately before enqueue.
- F4 LOW: resolving a review thread is forbidden only when the finding is still true, and during a scan.
- F5 INFO: the example command uses the placeholder `<n>`.
- F6 INFO: operator authority is a reference to AGENTS.md §9, which is outside this diff.

The Python emitters in merge.py, queue_drain.py, and worktree.py are outside this diff and still issue rebase and delete-branch commands. The skill tells sessions not to run them while the queue is active.
