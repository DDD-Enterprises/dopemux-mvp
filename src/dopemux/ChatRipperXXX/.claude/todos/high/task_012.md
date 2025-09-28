## Task: Integration tests, optimization pass, and documentation
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11]

### Description
Execute comprehensive integration tests with existing pipeline, optimize memory/speed for large models, finalize documentation and deployment guides.

### Implementation Details
Implementation:
- Integration tests:
  - End-to-end: ingest -> embed (cache on/off) -> store -> retrieve (multi-vector) -> results
  - Feature flags: allow_cloud off/on; fallback chains; hot-swap during workload
  - Error handling: assert ProblemDetails shapes for network/model/db errors
- Memory/speed optimization for local Stella:
  - Enable torch.inference_mode(), torch.set_grad_enabled(False)
  - Prefer FP16 on GPU; try 4-bit via bitsandbytes when VRAM constrained
  - Batch sizing auto-tuner: find largest batch that fits (catch CUDA OOM and reduce)
  - Use device_map='auto' if model supports
- Documentation:
  - docs/setup.md: prerequisites, GPU/CPU paths
  - docs/models.md: configuring Stella-1.5B-v5 (HF repo id), Cohere v3.0 models, flags
  - docs/migration.md: legacy -> multi-vector schema; index creation scripts; fallback behavior
  - docs/benchmarking.md: how to run and interpret
  - docs/ops.md: env vars, feature flags, hot-swap, monitoring/logging
- CI updates: parallelize tests, coverage collection, artifact upload for bench outputs
- Backward compatibility validation: ensure legacy embeddings remain queryable until migration completes


### Test Strategy
- Achieve >=90% coverage: unit + integration; coverage report enforced by CI
- Performance regression tests compare against stored baselines; fail if >X% slower (configurable)
- Memory tests: ensure no leaks across multiple embed cycles (track RSS/CUDA)
- Documentation link check and examples runnable end-to-end

### Migration Notes
- Originally Task ID: 12
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

### Related Files
- Original: .taskmaster/tasks/tasks.json
