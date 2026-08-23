# Stage 2: Thinkdeep

**False-Positive Handling:**
The scanner will use regex matching for forbidden calls and imports. Since `rg` might flag scanner rules (e.g., `queue_drain` appearing in the rule definition), the scanner must be able to ignore its own definitions and explicitly flagged test fixtures. A `path_scope` or `allowed_contexts` rule definition can mitigate this.

**Test Fixture Exemptions:**
We must create test fixtures like `tp_dcp_0005_clean/` and `tp_dcp_0005_forbidden_path/`. The scanner will check if the path being scanned is within a known test fixture directory to avoid triggering on valid test setups.

**Secret Redaction:**
If a scanner detects a secret or token pattern, the reported `match` and `evidence` must not include the actual secret text. We will redact the output using a masking function (e.g., replace with `***REDACTED***`).

**Fail-Closed Logic:**
If any check produces an `UNKNOWN` or `CONFLICTING` status for a required gate, the final report status cannot be `PASS`. It must be `UNKNOWN`, `CONFLICTING`, or `BLOCKED`. A `BLOCKER` or `CRITICAL` severity makes the report `BLOCKED`.

**Schema Convention Risk:**
The schema directory uses `snake_case.schema.json`. I will use `dcp_red_lane_report.schema.json` to match this convention, mitigating this risk.

**Authority-Boundary Drift Risk:**
The scanner must not make network calls or execute processes (e.g., `subprocess`). It reads files locally and produces a `DCP_RED_LANE_REPORT` JSON. It only scans evidence; it does not enforce the block itself at runtime—it produces a report that `PR Steward` will use.

**Scanner-as-Authority Risk:**
The scanner report explicitly states it is a derived guard report (`"implementation": "local"`), and the inputs show what was scanned. Source artifacts remain the authority.

**Decision & Next Action:**
Proceed to Stage 3: Challenge Understanding.
