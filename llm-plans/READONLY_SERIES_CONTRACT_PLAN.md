# Implementation Plan - TP-DSER-003: Read-Only Series Contract Support in Adapter Layer

## Objective
Add read-only series awareness to the `dopetask` adapter. The adapter will be able to load, validate, and normalize upstream series state (from `dopetask tp series status`) into a unified internal model.

## Key Files & Context
- **Models**: `src/dopemux_pr_merge_specialist/dopetask_series_models.py` (New)
- **Loader**: `src/dopemux_pr_merge_specialist/dopetask_series_loader.py` (New)
- **Mapper**: `src/dopemux_pr_merge_specialist/dopetask_status_mapper.py`
- **Adapter**: `src/dopemux_pr_merge_specialist/dopetask_adapter.py`
- **Deliverables**:
    - Normalized series result artifacts.
    - Fixture-backed tests for DAG and status validation.
    - `docs/integrations/dopetask/SERIES_READONLY_CONTRACT.md`

## Implementation Steps

### Phase 1: Models & Status Normalization
1.  **Define Enums**: Create `PacketStatus` and `SeriesStatus` enums in `dopetask_series_models.py`.
    - `PacketStatus`: `PLANNED`, `IN_PROGRESS`, `VALIDATED`, `FAILED`, `SKIPPED`, `UNKNOWN`.
    - `SeriesStatus`: `PLANNED`, `IN_PROGRESS`, `VALIDATED`, `FINALIZED`, `FAILED`, `UNKNOWN`.
2.  **Define Dataclasses**:
    - `DopetaskPacketRecord`: Represents a single TP in a series, including `depends_on` (list of IDs) and `is_final` flag.
    - `DopetaskSeriesIdentity`: `series_id`, `project_id`, `version`.
    - `DopetaskSeriesResult`: Aggregated result containing identity, status, and list of packet records.

### Phase 2: Series Loader & DAG Validation
1.  **Implement `DopetaskSeriesLoader`**:
    - Load JSON output from `dopetask tp series status`.
    - Validate required fields: `series_id`, `packets`, `status`.
    - **DAG Validation**: Ensure no cycles in `depends_on` edges and all references exist.
    - **Multiple Finals**: Handle cases where multiple packets are marked `is_final` (deterministic selection or error).
2.  **Update `DopetaskStatusMapper`**:
    - Add `map_series_status` and `map_packet_status` methods.
    - Implement governance aggregation: Aggregate `allowed_actions` across all packets in the series (intersection or union based on posture).

### Phase 3: Adapter Integration
1.  **Update `DopetaskAdapter`**:
    - Add `from_series_id(series_id: str, repo_path: Path)` entry point.
    - Integrate `DopetaskSeriesLoader` to build `DopetaskSeriesResult`.
    - Add `from_series_state_path(path: Path)` for explicit file loading.
2.  **Document No-Exec Boundary**: Add docstrings and comments explicitly stating that these methods are read-only.

## Verification & Testing
- **Unit Tests**:
    - `tests/unit/test_dopetask_series_loader.py`: Test valid/invalid JSON, cycle detection, missing dependencies.
    - `tests/unit/test_dopetask_series_status_mapper.py`: Test status normalization and governance aggregation.
    - `tests/unit/test_dopetask_series_adapter.py`: Test the full read-only series loading flow.
- **Fixture Verification**: Use the captured help outputs from TP-DSER-001 to ensure schema alignment.

## Alternatives Considered
- **Heuristic Discovery**: Rejected. Series IDs must be explicitly provided to avoid "filesystem wandering".
- **Dynamic Schema**: Rejected. We will stick to the 0.5.1 schema observed in the probe.
