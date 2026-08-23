# Baseline test anomaly: test_doctor_placeholder_fails_closed

| Field | Value |
|---|---|
| Classification | **BASELINE_EXISTING** |
| Failure on #1188 | assert rc==2 got 0 |
| Failure on origin/main (`fb710ef405`) | assert rc==2 got 0 (identical) |
| Cause | #1187 restored real `config/pr_steward/policy.json`; doctor returns PASS |
| #1188 touches test? | **NO** |
| #1188 touches policy? | **NO** (policy not in PR delta) |
| Repair in #1188 | **FORBIDDEN** — separate follow-up debt |
