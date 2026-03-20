---
id: PHASE0_WORKUNIT_MAP
title: Phase0 Workunit Map
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-02'
last_review: '2026-03-02'
next_review: '2026-05-31'
prelude: Phase0 Workunit Map (reference) for dopemux documentation and developer workflows.
---
# Phase 0 Work Unit Boundary Map

## Executor Location
- **File**: `services/repo-truth-extractor/run_extraction_v3.py`
- **Line**: 6986
- **Function**: `executor.submit(_run_one_partition, partition)`

## Work Unit Structure
- **Function**: `_run_one_partition(partition: Dict[str, Any]) -> PartitionExecResult`
- **Args Shape**: `{'id': str, ...partition_data...}`
- **Payload Example**: `{'id': 'A0', 'files': [...], 'config': {...}}`

## Execution Flow
1. **Executor Creation**: `ThreadPoolExecutor(max_workers=workers)`
2. **Task Submission**: `executor.submit(_run_one_partition, partition)`
3. **Future Processing**: `for future in as_completed(future_map)`
4. **Result Aggregation**: `results_by_partition[partition_id] = future.result()`

## Key Components
- **Worker Pool**: ThreadPoolExecutor with configurable max_workers
- **Work Unit**: Individual partition processing
- **Result Handling**: Per-partition JSON output files
- **Error Handling**: Try/catch with FAILED.txt sidecar files

## Code Context
```python
# Lines 6985-6987 in run_extraction_v3.py
with ThreadPoolExecutor(max_workers=workers) as executor:
    future_map = {executor.submit(_run_one_partition, partition): partition for partition in ordered_partitions}
    for future in as_completed(future_map):
        partition = future_map[future]
        partition_id = str(partition["id"])
        # ... result processing ...
```

## Partition Function Signature
```python
def _run_one_partition(partition: Dict[str, Any]) -> PartitionExecResult:
    partition_id = str(partition["id"])
    # Creates output files:
    # - {step_id}__{partition_id}.json (success)
    # - {step_id}__{partition_id}.FAILED.txt (failure)
    # - {step_id}__{partition_id}.TRACE.md (trace)
```

## Validation Status
- ✅ Executor location identified
- ✅ Work unit function identified
- ✅ Payload structure documented
- ✅ Execution flow mapped
- ⏳ Serialization testing pending
- ⏳ Determinism validation pending
