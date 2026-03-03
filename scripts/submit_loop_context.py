                    out_failed_json=out_failed_json,
                    exc=exc,
                )
            _ui_record_result(results_by_partition[partition_id])
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {executor.submit(_run_one_partition, partition): partition for partition in ordered_partitions}
            for future in as_completed(future_map):
                partition = future_map[future]
                partition_id = str(partition["id"])
                out_json = raw_dir / f"{step_id}__{partition_id}.json"
                out_failed = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
                out_failed_json = raw_dir / f"{step_id}__{partition_id}.FAILED.json"
                try:
                    results_by_partition[partition_id] = future.result()
                except Exception as exc:
