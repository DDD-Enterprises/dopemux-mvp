# CCAR-002R R1 Changed Files

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

## Source surfaces (must be byte-identical)
- `.claude/agents/**` — unchanged
- `.claude/personas/**` — unchanged
- `.github/agents/**` — unchanged
- `src/dopemux/personas/**` — unchanged
