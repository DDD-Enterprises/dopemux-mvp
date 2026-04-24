# RTE Pre-Run Hygiene Stage 1 Boundary Model

Date: 2026-04-23
Packet: `DMX-RTE-PRE-RUN-HYGIENE-GEMINI-001`
Repo: `/Users/hue/code/dopemux-mvp`
Branch: `audit/rte-pre-run-hygiene-gemini-001`

## Authority Used

- Runtime/code:
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/rte_config.py`
  - `services/repo-truth-extractor/rte_output_layout.py`
  - `services/repo-truth-extractor/reporting.py`
- Repo operator docs:
  - `AGENTS.md`
  - `PROJECT.md`
  - `ARCHITECTURE.md`
- Derived truth docs:
  - `docs/03-reference/truth/truth-canonicals.md`
  - `docs/03-reference/truth/truth-gaps.md`
  - `docs/03-reference/truth/truth-scope.md`
  - `docs/03-reference/systems/system-boundaries.md`
  - `docs/03-reference/planes/pm/pm-plane.md`

## PAL Toolchain

- Requested by packet:
  - `analyze:gpt-4.1`
  - `thinkdeep:gemini-3-pro-preview`
  - `challenge:grok-4.1-fast-reasoning`
- Executed:
  - `analyze:gpt-4.1`
  - `thinkdeep:gemini-2.5-pro`
  - `challenge` tool invocation recorded separately
- Gaps:
  - `tracer` is not available in the current PAL toolset.
  - `gemini-3-pro-preview` was unavailable from provider keys, so `gemini-2.5-pro` was used as the closest available Gemini reasoning fallback.
  - The `challenge` tool returns a structured reassessment prompt, not a provider-signed verdict; it is recorded as process pressure-testing, not as an external arbitration result.

## Boundary Decision

Preservation-first is required.

Observed RTE runtime/reporting code makes the following paths operator-visible evidence surfaces, not generic clutter:

- `extraction/repo-truth-extractor/v5/runs/`
- `extraction/repo-truth-extractor/v5/doctor/`
- `extraction/repo-truth-extractor/v5/latest_run_id.txt`
- linked proof and resume artifacts referenced by reporting code

Observed repo-truth docs also require contradictions and split authority to remain visible. That means hygiene cannot rewrite, relocate, or normalize the following classes.

## Do-Not-Touch Classes

- Canonical runtime code under `src/`, `services/`, and runtime wrappers under `scripts/`
- Tests and validation surfaces under `tests/`
- Compose, registry, and routing/config surfaces
- `docs/03-reference/truth/*`
- derived boundary docs used by this packet
- existing extraction evidence under `extraction/doctor/`, `extraction/v4/doctor/`, `extraction/repo-truth-extractor/v5/doctor/`, `extraction/repo-truth-extractor/v5/runs/`, and `latest_run_id.txt` pointers
- existing proof and audit artifacts under `proof/` and `reports/`
- ambiguous hidden local trees that may still encode operator evidence or drift, including `.claude/`, `.dopemux/`, and `.conport/`

## Candidate Low-Authority Hygiene Classes

These were classified as eligible for physical cleanup only because they have no plausible canonical truth role:

- `.DS_Store`
- `__pycache__/`
- `*.pyc`
- `*.pyo`
- editor swap files such as `*.swp`

## Out Of Scope

- architecture cleanup
- truth normalization
- deleting ignored trees merely because they are large
- rewriting docs to remove contradictions before extraction

## Stage 1 Verdict

- Safe for direct mutation:
  - transient OS/editor/cache artifacts only
- Safe only for bounded run-input exclusion, not deletion:
  - `.claude/`
  - `.dopemux/`
  - `.conport/`
  - `.venv/`
  - `build/`
  - `node_modules/`
  - historical or heavy ignored local state not proven canonical for the first pass
- Unsafe for cleanup:
  - `proof/`
  - `reports/`
  - extraction doctor/latest/runs evidence
  - truth docs and split-authority evidence
