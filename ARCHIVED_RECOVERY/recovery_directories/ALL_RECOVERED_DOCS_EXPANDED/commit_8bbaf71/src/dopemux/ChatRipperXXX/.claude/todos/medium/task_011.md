## Task: Benchmarking suite for quality, performance, and memory
- **ID**: 20250906-185622
- **Priority**: Medium
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [6], [7], [8], [9], [10]

### Description
Create a reproducible benchmarking CLI to compare SOTA models vs baseline on domain datasets, measuring accuracy, latency, throughput, and memory.

### Implementation Details
Implementation:
- CLI: chatripper-bench with subcommands: quality, perf, mem
- Datasets: local corpus hooks (privacy-first) + optional MTEB tasks if allowed; input via path
- Metrics:
  - Quality: nDCG@k/MRR on retrieval pairs; cosine similarity distributions
  - Perf: p50/p95 latency per 1/8/32 batch; tokens/sec where applicable
  - Memory: peak RSS (psutil), CUDA reserved/allocated (torch.cuda.memory_stats)
- Compare providers: stella vs cohere vs legacy; export JSON and Markdown reports
- Benchmark harness pseudocode:
async def bench_provider(provider, dataset):
  t0=time.perf_counter(); embs=await provider.embed(dataset.texts)
  dt=time.perf_counter()-t0
  mem = get_mem();
  return {"latency": dt/len(dataset), "throughput": len(dataset)/dt, "mem": mem}
- Plotting optional (saving CSV/JSON is sufficient for CI artifacts)
- Add CI job to run small smoke benchmark to detect regressions


### Test Strategy
- Use synthetic dataset with known neighbors to validate metric math
- Run small sample bench in CI and assert no worse than baseline thresholds (configurable)
- Manual large-run instructions documented; ensure repeatability across runs (seeded shuffling)
- Validate memory probes work on CPU/GPU machines (skip CUDA probes if not available)

### Migration Notes
- Originally Task ID: 11
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: medium
- Status mapping: pending
- Dependencies: [6, 7, 8, 9, 10]

### Related Files
- Original: .taskmaster/tasks/tasks.json
