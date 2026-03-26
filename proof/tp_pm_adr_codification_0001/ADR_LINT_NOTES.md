# ADR Lint Notes

## Validation commands

```bash
python3 scripts/docs_validator.py
python3 scripts/docs_frontmatter_guard.py \
  docs/90-adr/adr-index.md \
  docs/90-adr/adr-pm-plane-authority-boundaries.md \
  docs/90-adr/adr-dopecon-bridge-narrowing-to-adapter-only-role.md \
  docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md \
  docs/90-adr/adr-conport-as-decision-progress-and-context-authority.md \
  docs/90-adr/adr-dope-memory-as-chronicle-memory-authority.md \
  docs/90-adr/adr-task-orchestrator-as-workflow-authority.md \
  docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md \
  docs/90-adr/adr-serena-as-technical-context-plane.md \
  docs/90-adr/adr-dope-context-as-search-and-retrieval-plane.md
python3 scripts/check_root_hygiene.py
```

## Result

- All codified ADR files have valid frontmatter.
- The ADR index renders cleanly and references the full PM-plane ADR spine.
- Cross-links were normalized in the ADR set.
- No canvas artifacts, duplicate fragments, or truncated sections remain in the codified files.

## Notes

- `docs_validator.py` still reports pre-existing, non-blocking warnings in unrelated documentation outside this packet.
- Five ADRs that had previously been absent from the repo were populated from user-supplied source text rather than inferred reconstruction.
