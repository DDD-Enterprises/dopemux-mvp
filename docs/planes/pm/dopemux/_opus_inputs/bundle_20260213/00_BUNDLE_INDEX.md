# Dopemux Opus Preflight Evidence Bundle Index

Generated: 2026-02-13
Bundle path: `docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/`
Comprehensive manifest: `docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/COMPREHENSIVE_SET.md`
Primary raw capture log: `tmp/opus_preflight_evidence_notes.md`

## Stop-condition check
- `compose.yml` present: PASS
- Event envelope implementation found: PASS
- ConPort write routes found: PASS

### Evidence
- `compose.yml:49`
```text
  postgres:
    image: apache/age:release_PG16_1.6.0
    container_name: dopemux-postgres-age
    restart: unless-stopped
    networks:
- dopemux-network
```
- `src/dopemux/memory/capture_client.py:323`
```text
def _emit_to_event_stream(event: dict[str, Any]) -> None:
    """Best-effort Redis stream fan-out for downstream consumers."""
    try:
        import redis  # type: ignore
    except Exception:
        LOGGER.debug("redis package unavailable; skipping event stream emit")
        return
```
- `docker/mcp-servers/conport/enhanced_server.py:245`
```text
        self.app.router.add_get('/api/context/{workspace_id}', self.get_context)
        self.app.router.add_post('/api/context/{workspace_id}', self.update_context)

        # Decision logging endpoints
        self.app.router.add_post('/api/decisions', self.log_decision)
        self.app.router.add_get('/api/decisions', self.get_decisions)
```

## Bundle files
- `00_BUNDLE_INDEX.md`
- `01_GLOBAL_SERVICE_INVENTORY.md`
- `02_TOPOLOGY_AND_STORES.md`
- `03_STORE_WRITE_OWNERSHIP_MATRIX.md`
- `04_EVENT_ENVELOPE_STREAMS_AND_SCHEMA.md`
- `05_CONPORT_AUTHORITY_SURFACES.md`
- `06_DOPE_MEMORY_PROMOTION_RETENTION_PROVENANCE.md`
- `07_PM_PLANE_BYPASS_AND_EXECUTION_SURFACES.md`
- `08_ADHD_COGNITIVE_PLANE_SURFACES.md`
- `09_SEARCH_PLANE_SURFACES.md`
- `10_DETERMINISM_LEAKS_AND_ENFORCEMENT_POINTS.md`
- `11_UNKNOWNs_AND_REQUIRED_EVIDENCE.md`
- `12_OPUS_PROMPTS_READY.md`
- `COMPREHENSIVE_SET.md`

## Phase 0 doc-gate result
Command run:
- `find docs scripts . -maxdepth 6 -type f \( -iname "*doc*gate*.py" -o -iname "doc_gate.py" -o -iname "*docs*gate*.py" \) 2>/dev/null | sort`
- `rg -n "Doc Gate Passed|Verifying docs|Headings and Frontmatter verified|doc_gate" -S docs scripts . || true`
- `python3 scripts/doc_gate.py`

Exit code: `0`

Last output:
```text
Verifying docs in docs/planes/pm/dopemux...
PASS: All required files exist.
PASS: Headings and Frontmatter verified.

SUCCESS: Doc Gate Passed. System Spec is valid.
```
