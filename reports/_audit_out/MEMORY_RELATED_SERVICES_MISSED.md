# Memory-Related Services Missed (2026-02-07)

Source of truth checked: `services/registry.yaml`

## Registry-mapped memory/context services
- `dope-memory` -> `services/working-memory-assistant`
- `dope-query` -> `services/conport`

## Additional memory-adjacent service dirs captured in separate file set
These were harvested into the separate archive because they are memory/context/intelligence/session related by name and were not covered by the strict registry mapping above.

- `services/claude_brain`
- `services/conport_kg_ui`
- `services/dope-context`
- `services/dopecon-bridge`
- `services/dopemux-gpt-researcher`
- `services/intelligence`
- `services/session-intelligence`
- `services/session-manager`
- `services/session_intelligence`

## Artifacts
- Main memory harvest archive: `reports/dopemux-memory-harvest-20260207-152636.zip`
- Missed-services archive: `reports/dopemux-memory-missed-services-20260207-152636.zip`
- Main manifest: `_audit_out/memory_harvest_manifest_20260207-152636.txt`
- Missed manifest: `_audit_out/memory_missed_services_manifest_20260207-152636.txt`
