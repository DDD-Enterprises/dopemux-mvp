# Benchmark Dependency Graph

## Decision Flow

```mermaid
flowchart TD
  A["SPLIT-001\nlane contract split"] --> B["DMB-001\ndirect-model evidence"]
  A --> C["R1C\nbenchmark-owned dry-run route proof"]
  B --> D["PRICE-001\npricing truth layer"]
  C --> E["R1D\nlive readiness and live admissibility gate"]
  B --> F["PROFILE-SYNTH-001\nreview-first synthesis"]
  D --> F
  C --> F
  E --> G["R1 restart decision"]
  F --> H["profile/routing review packets"]
  G --> I["campaign restart truth"]
```

## Authority Surfaces

```mermaid
flowchart LR
  SEL["campaigns/selection.py"] --> OWN["benchmark_route_ownership_smoke.py"]
  SEL --> LIVE["benchmark_live_route_readiness_smoke.py"]
  OWN --> ADMIT["campaigns/admissibility.py"]
  LIVE --> ADMIT
  LIVE --> EXEC["orchestration/attempt_executor.py"]
  EXEC --> STORE["storage/sqlite_repo.py"]
  STORE --> REPORT["reporting/*"]
  DMB["direct_model/runner.py"] --> PRICE["pricing/coverage.py"]
  PRICE --> SYN["synthesis/profile_synth.py"]
  GOV["synthesis/governance_pipeline.py"] --> SYN
  SYN --> REVIEW["review_packets.py"]
```

## Practical Dependency Notes

- `SPLIT-001` is the contract prerequisite. Without lane separation, later proofs would collapse evidence classes.
- `DMB-001` is upstream admission evidence only. It does not prove runtime-route truth.
- `PRICE-001` upgrades cost truth enough to block unsafe cost claims and enable partial advisory synthesis.
- `R1C` is the structural proof that owned dry-run route distinctness exists.
- `R1D` is the operational gate for restarting R1. It can block restart even when `R1C` passes.
- `PROFILE-SYNTH-001` depends on direct-model, pricing, and runtime-route/governance evidence, but remains advisory-only by design.

## Current Critical Path

1. `SPLIT-001` established lane separation.
2. `R1C` proved dry-run owned-lane distinctness.
3. `R1D` failed live readiness in this environment.
4. Therefore the current blocker is operational provider readiness, not benchmark architecture.

## Current Non-Critical But Important Path

1. `DMB-001` established direct-model evidence.
2. `PRICE-001` improved pricing truth and blocker propagation.
3. `PROFILE-SYNTH-001` created reviewable profile/routing proposals.
4. Dynamic profile updates remain intentionally blocked because runtime-route truth and pricing truth are still incomplete across the full active universe.
