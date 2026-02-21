Goal: M6_RUNTIME_EXPORT_INDEX.json

Prompt:
- Task: write final runtime export index for Phase M.
- Include:
  - attempted exports
  - successful outputs
  - missing prerequisites
  - failures with reason codes
  - redaction rules applied
  - caps/truncation markers
- Include command strings used for verification where applicable.
- Hard rules:
  - No sensitive values.
  - No raw payload dumps.
