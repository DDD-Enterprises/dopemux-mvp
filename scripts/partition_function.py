"""Legacy ProcessPool partition-function snippet.

This file was introduced as a partial reference fragment, not as a runnable
module. Keep the original snippet inert so repository-wide compile checks do not
fail while preserving the historical text for audit review.
"""

LEGACY_PARTITION_FUNCTION_SNIPPET = r'''
    def _run_one_partition(partition: Dict[str, Any]) -> PartitionExecResult:
        partition_id = str(partition["id"])
        out_json = raw_dir / f"{step_id}__{partition_id}.json"
        out_failed = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
        out_failed_json = raw_dir / f"{step_id}__{partition_id}.FAILED.json"
        out_trace = raw_dir / f"{step_id}__{partition_id}.TRACE.md"
        logs: List[Tuple[str, str]] = []
        write_ops: List[Dict[str, Any]] = []

        if cfg.resume:
            decision = compute_resume_decision(
                success_json_path=out_json,
                raw_dir=raw_dir,
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                expected_artifact_names=output_artifacts,
            )
'''
