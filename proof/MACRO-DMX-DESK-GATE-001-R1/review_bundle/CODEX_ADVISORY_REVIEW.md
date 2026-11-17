# Codex advisory review of 508a0418b (superseded head) — FAIL

Advisory only. `AGENTS.md` forbids Codex as the formal auditor; this record is kept so the failed review and the repair are not lost. The verbatim report is not stored in this bundle (it was returned in the supervisor session; Codex thread `01a1e285-5a0e-78b2-ad09-b7b2de6e0034`). What follows is the supervisor's summary of it.

- Route: Codex companion task, read-only sandbox, model and effort not reported (UNKNOWN). Operator-selected ("Use Codex").
- Subject: `508a0418ba985fed2c1557b28c6ec5f3a115b051`, base `365f70ce2edc907d14356d82d2843104dbdaa434`.
- Status: `FAIL`. Pytest was `NOT_RUN` in its sandbox (no writable temp directory).

| Finding | Severity | Location | Summary | Disposition |
|---|---|---|---|---|
| F1 | medium | `src/dopemux/claude/dispatch_gate.py:50` | On git lookup failure the client fell back to the worktree folder name and could report GO for the wrong project (violates I03). | Repaired in `bce53a90e`: returns UNKNOWN without running the gate; git wait bounded by the check timeout. |
| F2 | medium | `src/dopemux/claude/native_hooks.py:413` | Raw gate output was placed in session context, unbounded and multi-line. | Repaired in `bce53a90e` (message reduced to one printable line, 200 chars) and `79799cade` (hook uses fixed wording; no gate text). |
| F3 | low | `src/dopemux/claude/native_hooks.py:84` | One new E501. | Repaired in `79799cade`; flake8 count back to the base 76. |

The operator authorised the repair round in chat ("Yes, repair"). The repaired head `79799cade` was then frozen and audited by the formal route (see `../AUDITOR_REPORT.md`).
