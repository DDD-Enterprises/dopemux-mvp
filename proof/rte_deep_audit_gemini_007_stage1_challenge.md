# RTE Deep Audit Stage 1: PAL Challenge

**Model:** `grok-4.1-fast-reasoning`

## Challenge Assessment
The authority map claiming `run_extraction_v5.py` is the terminal authority was **successfully challenged and qualified**. 

### Key Contradictions Identified
- **v4 Wrapper Complexity:** The discovery that `run_extraction_v4.py` is an active wrapper for `v5` complicates the "terminal authority" claim. An operator invoking `v4` triggers a dual-authority state where `v4` dictates the schema/contracts and `v5` provides the execution logic.
- **Shadow Authority Persistence:** `run_extraction_v3.py` is not just "legacy"; it is an un-gated execution path that persists in the primary service folder. It represents a "Shadow Authority" that could be accidentally invoked, bypassing the v25 validator.
- **Brittle Versioning:** The hard-coded `v5` strings in `dopemux/cli.py` and `rte_config.py` create a circular dependency where changing the runner requires changing the CLI and the config simultaneously, increasing technical debt.
- **CLI vs direct execution:** The CLI performs argument transformation (Click options to subprocess list). Direct execution of `run_extraction_v5.py` is possible and safe (due to internal environment checks), but results in a degraded operator experience (loss of branded UI/progress).

## Final Qualified Verdict
Authority is **Execution-Canonical in v5** but **Contract-Fragmented**. The system relies on version-suffixed filenames as a proxy for actual version control, which is an architectural anti-pattern.
