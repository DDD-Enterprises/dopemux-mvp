# J04 gates at 97b79962936da518888c12f3ff1ae8b6f0084eda

Recorded here because nothing outside this packet may change after the freeze. Amendment 05 defines the make test gate as no new failures against main at the merged base.

| Gate | Result |
|---|---|
| `make test` at the head | FAIL as a raw run: 8,832 passed, 29 failed, 36 skipped, 4 errors |
| `make test` at main 4cd889877 | 7,899 passed, 28 failed, 5 skipped, 5 errors |
| No new failures against main | PASS with one accepted exception |
| Whole 2A set in the services env | PASS: 2,131 passed, 1 deselected (test_16, fails on main too) |
| `git diff --check` | PASS |
| Change-contract preflight | PASS, max lane L3, model audit required |
| Docs hooks, including markdownlint | PASS |

Accepted exception (new on the branch): `tests/mcp/test_fleet_catalog_v2_runtime.py::test_live_catalog_files_are_untouched_by_this_packet`, Amendment 05.
Gone on the branch: `tests/security/test_rate_limiting.py::TestRateLimiting::test_no_rate_limit_on_health_endpoint`, an error that comes and goes between runs.
Failure lists: `J04_FAILURES_BRANCH.txt`, `J04_FAILURES_MAIN.txt`.
