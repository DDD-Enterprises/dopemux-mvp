# Adapter registry policy — 0007A

- `mutation_adapters_enabled: false` (const)
- Every adapter `enabled_for_mutation: false`
- `derives_only: true` for all listed future adapters
- Runtime `active_mutation_adapter_ids()` always `[]`
- Does not enable authenticated_operator or any mutation path
