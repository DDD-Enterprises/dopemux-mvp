# CCAR-002R Changed Files

## Allowlisted R1 delta (relative to a22699fc9834c77017ac88e482a6c94fdd319bda)

### Packet
- `task-packets/CCAR-002R.md` (new)
- `task-packets/CCAR-002R.json` (new)

### Implementation
- `scripts/commandcode_router/build_normalized_catalog.py` (portability + determinism)
- `tests/commandcode_router/test_normalized_catalog.py` (dual-worktree + relative-path gates)
- `config/commandcode/normalized_agent_persona_catalog.yaml` (regenerated)

### Implementation proof
- `proof/CCAR-002/**` (evidence refresh; audit remains SKIPPED pending R2)

## Allowlisted R3 delta (CCAR-002R-A2, relative to 1cb80e40f0f818389307aedeb14aaaceaa3e8ed1)

### Packet
- `task-packets/CCAR-002R-A2.md` (new)
- `task-packets/CCAR-002R-A2.json` (new)

### Implementation
- `scripts/commandcode_router/build_normalized_catalog.py` (`_scan_model_ids` non-capturing/full-match fix)
- `tests/commandcode_router/test_normalized_catalog.py` (`test_generation_idempotent` check-before-regenerate reorder; new `TestScanModelIds`)
- `config/commandcode/normalized_agent_persona_catalog.yaml` (regenerated; `generated_at` only)

### Implementation proof
- `proof/CCAR-002/SOURCE_MANIFEST.json` (removed absolute `worktree` path)
- `proof/CCAR-002/NORMALIZATION_REPORT.md` (real timestamp; R3 repair notes)
- `proof/CCAR-002/CHANGED_FILES.md`, `proof/CCAR-002/COMMAND_LOG.md`, `proof/CCAR-002/PROOF.json` (evidence refresh)

## Source surfaces (must be byte-identical)
- `.claude/agents/**` — unchanged
- `.claude/personas/**` — unchanged
- `.github/agents/**` — unchanged
- `src/dopemux/personas/**` — unchanged
