# Stage 4: Planner

**Plan:**

**Slice 1: Red-Lane Types/Rules & Schema**
- Create `schemas/dcp/dcp_red_lane_report.schema.json` based on the given JSON format.
- Create `src/dopemux/dcp/red_lane.py` with dataclasses/Pydantic models for Findings and Reports.
- Create `src/dopemux/dcp/red_lane_rules.py` with the definition of forbidden paths and text regexes.

**Slice 2: Scanner Logic**
- Create `src/dopemux/dcp/red_lane_scanner.py`.
- Implement `PathScanner` logic to detect forbidden edits.
- Implement `TextScanner` logic to regex match text in files, applying safe-listing for scanner definitions and test fixtures. Redact secrets.

**Slice 3: Artifact/Proof Scanning**
- Add logic to read TP-DCP-0003 and TP-DCP-0004 JSON files, checking `LIVE_WRITE_READY` status, merge seam status, reviewer validity, etc.
- Implement the fail-closed status logic (`CRITICAL` -> `BLOCKED`, `UNKNOWN` -> `UNKNOWN` or `BLOCKED`).

**Slice 4: Tests/Fixtures**
- Create `tests/dcp/fixtures/tp_dcp_0005_...` directories with mock files to trigger detections.
- Write `tests/dcp/test_dcp_0005_red_lane_scanner.py` matching all 30 test cases required by Section 17 of the prompt.

**Slice 5: Proof/Audit Artifacts**
- Generate `06_IMPLEMENTATION_SLICES.md` incrementally.
- Run `pytest` and `compileall`.
- Complete `07_SECAUDIT.md`, `08_CODEREVIEW.md`, `09_PRECOMMIT.md`, `10_FINAL_CHALLENGE.md`.
- Generate `proof/TP-DCP-0005/PROOF.json` and `AUDIT.md`.

**Decision:**
Plan mapped to requirements. Proceed to Stage 5: Challenge Plan.