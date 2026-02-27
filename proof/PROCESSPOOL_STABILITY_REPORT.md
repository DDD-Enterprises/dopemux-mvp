=== ProcessPool Stability Investigation ===

Current State:
- workers=1: PASS (252/252 files)
- workers=4: FAIL (21/252 files)

Observed Behavior:
- Different worker PIDs confirm ProcessPoolExecutor is working
- Only 21/252 files processed successfully
- Error: "Phase A failed: 'kind'" suggests missing field in worker output

Root Cause Hypothesis:
1. Worker function missing required fields in output
2. Exception handling not properly surfaced
3. Future results not fully collected
4. Race condition in file writing

Investigation Plan:
1. Add per-partition logging in worker function
2. Ensure all futures are awaited with exception handling
3. Count submitted vs completed partitions explicitly
4. Fix 'kind' field issue in worker output
5. Add validation for worker function outputs

Debugging Steps:
1. Add logging: "Worker {pid} START {partition_id}"
2. Add logging: "Worker {pid} END {partition_id} {status}"
3. Wrap future.result() in try/except with detailed error logging
4. Count futures submitted vs futures completed
5. Validate worker function returns all required fields
