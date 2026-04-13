from __future__ import annotations


SCHEMA_VERSION = "benchmark_catalog_v2"
SCHEMA_USER_VERSION = 2


DDL_STATEMENTS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version TEXT PRIMARY KEY,
      applied_at_utc TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS catalog_meta (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS provider_surface (
      surface_id TEXT PRIMARY KEY,
      surface_class TEXT NOT NULL,
      provider_name TEXT NOT NULL,
      transport_kind TEXT NOT NULL,
      endpoint_ref TEXT NOT NULL,
      logging_posture TEXT NOT NULL,
      residency_posture TEXT NOT NULL,
      surface_hash TEXT NOT NULL,
      record_json TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS model (
      model_key TEXT PRIMARY KEY,
      display_name TEXT NOT NULL,
      family TEXT NOT NULL,
      candidate_type TEXT NOT NULL,
      source_registry_ref TEXT NOT NULL,
      registry_class TEXT NOT NULL,
      lifecycle_status TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS route (
      route_id TEXT PRIMARY KEY,
      surface_id TEXT NOT NULL,
      model_key TEXT NOT NULL,
      candidate_type TEXT NOT NULL,
      provider_model_id TEXT NOT NULL,
      api_key_ref TEXT NOT NULL,
      route_pin TEXT NOT NULL,
      strict_json_schema_declared INTEGER NOT NULL,
      strict_passthrough_verified INTEGER NOT NULL,
      route_hash TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL,
      FOREIGN KEY(surface_id) REFERENCES provider_surface(surface_id),
      FOREIGN KEY(model_key) REFERENCES model(model_key)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS contract_snapshot (
      contract_snapshot_id TEXT PRIMARY KEY,
      runtime_version TEXT NOT NULL,
      contract_version TEXT NOT NULL,
      strict_schema_expected INTEGER NOT NULL,
      snapshot_hash TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS validator_suite (
      validator_suite_id TEXT PRIMARY KEY,
      strength_class TEXT NOT NULL,
      version_hash TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS control_anchor_group (
      anchor_group_id TEXT PRIMARY KEY,
      surface_class TEXT NOT NULL,
      archetype_id TEXT NOT NULL,
      required INTEGER NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS archetype (
      archetype_id TEXT PRIMARY KEY,
      description TEXT NOT NULL,
      success_rubric_id TEXT NOT NULL,
      promotion_policy_id TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS profile (
      profile_id TEXT PRIMARY KEY,
      candidate_type TEXT NOT NULL,
      is_production_profile INTEGER NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS retry_policy (
      retry_policy_id TEXT PRIMARY KEY,
      max_hops INTEGER NOT NULL,
      policy_hash TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS benchmark_case (
      case_id TEXT PRIMARY KEY,
      case_version INTEGER NOT NULL,
      benchmark_mode TEXT NOT NULL,
      candidate_type TEXT NOT NULL,
      execution_family TEXT NOT NULL,
      archetype_id TEXT NOT NULL,
      phase_or_step_family TEXT NOT NULL,
      validator_suite_id TEXT NOT NULL,
      contract_snapshot_id TEXT NOT NULL,
      route_distinctness_required INTEGER NOT NULL,
      pricing_relevant INTEGER NOT NULL,
      governance_relevant INTEGER NOT NULL,
      governance_blockers_apply_directly INTEGER NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL,
      FOREIGN KEY(archetype_id) REFERENCES archetype(archetype_id),
      FOREIGN KEY(validator_suite_id) REFERENCES validator_suite(validator_suite_id),
      FOREIGN KEY(contract_snapshot_id) REFERENCES contract_snapshot(contract_snapshot_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS benchmark_case_set (
      case_set_id TEXT PRIMARY KEY,
      case_set_version INTEGER NOT NULL,
      archetype_id TEXT NOT NULL,
      benchmark_stage TEXT NOT NULL,
      control_anchor_group_id TEXT,
      schedule_class TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL,
      FOREIGN KEY(archetype_id) REFERENCES archetype(archetype_id),
      FOREIGN KEY(control_anchor_group_id) REFERENCES control_anchor_group(anchor_group_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS benchmark_run (
      benchmark_run_id TEXT PRIMARY KEY,
      run_type TEXT NOT NULL,
      trigger_type TEXT NOT NULL,
      trigger_ref TEXT NOT NULL,
      git_commit TEXT NOT NULL,
      runtime_version TEXT NOT NULL,
      status TEXT NOT NULL,
      started_at TEXT NOT NULL,
      finished_at TEXT,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence_bundle (
      bundle_id TEXT PRIMARY KEY,
      bundle_type TEXT NOT NULL,
      benchmark_run_id TEXT NOT NULL,
      root_path TEXT NOT NULL UNIQUE,
      manifest_hash TEXT NOT NULL,
      retention_class TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL,
      FOREIGN KEY(benchmark_run_id) REFERENCES benchmark_run(benchmark_run_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS benchmark_case_attempt (
      case_attempt_id TEXT PRIMARY KEY,
      benchmark_run_id TEXT NOT NULL,
      case_id TEXT NOT NULL,
      case_version INTEGER NOT NULL,
      case_set_id TEXT NOT NULL,
      benchmark_mode TEXT NOT NULL,
      candidate_type TEXT NOT NULL,
      execution_family TEXT NOT NULL,
      archetype_id TEXT NOT NULL,
      phase_or_step_family TEXT NOT NULL,
      surface_class TEXT NOT NULL,
      surface_id TEXT NOT NULL,
      profile_id TEXT,
      route_id TEXT,
      control_anchor_group_id TEXT,
      runtime_version TEXT NOT NULL,
      contract_version TEXT NOT NULL,
      contract_snapshot_id TEXT NOT NULL,
      schema_id TEXT NOT NULL,
      strict_schema_expected INTEGER NOT NULL,
      validator_suite_id TEXT NOT NULL,
      attempt_number INTEGER NOT NULL,
      retry_policy_id TEXT NOT NULL,
      temperature_or_equivalent REAL NOT NULL,
      max_tokens_or_budget INTEGER NOT NULL,
      tool_mode TEXT NOT NULL,
      batch_mode TEXT NOT NULL,
      route_distinctness_required INTEGER NOT NULL,
      pricing_relevant INTEGER NOT NULL,
      governance_relevant INTEGER NOT NULL,
      governance_blockers_apply_directly INTEGER NOT NULL,
      contract_gate_pass INTEGER NOT NULL,
      contract_gate_strength TEXT NOT NULL,
      contract_fail_reason TEXT,
      validator_pass INTEGER NOT NULL,
      task_success_score REAL NOT NULL,
      output_artifact_ref TEXT NOT NULL,
      golden_eval_ref TEXT NOT NULL,
      control_delta_ref TEXT NOT NULL,
      evidence_bundle_id TEXT NOT NULL UNIQUE,
      timestamp_utc TEXT NOT NULL,
      record_json TEXT NOT NULL,
      FOREIGN KEY(benchmark_run_id) REFERENCES benchmark_run(benchmark_run_id),
      FOREIGN KEY(case_id) REFERENCES benchmark_case(case_id),
      FOREIGN KEY(case_set_id) REFERENCES benchmark_case_set(case_set_id),
      FOREIGN KEY(archetype_id) REFERENCES archetype(archetype_id),
      FOREIGN KEY(surface_id) REFERENCES provider_surface(surface_id),
      FOREIGN KEY(profile_id) REFERENCES profile(profile_id),
      FOREIGN KEY(route_id) REFERENCES route(route_id),
      FOREIGN KEY(control_anchor_group_id) REFERENCES control_anchor_group(anchor_group_id),
      FOREIGN KEY(contract_snapshot_id) REFERENCES contract_snapshot(contract_snapshot_id),
      FOREIGN KEY(validator_suite_id) REFERENCES validator_suite(validator_suite_id),
      FOREIGN KEY(retry_policy_id) REFERENCES retry_policy(retry_policy_id),
      FOREIGN KEY(evidence_bundle_id) REFERENCES evidence_bundle(bundle_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS validator_result (
      validator_result_id TEXT PRIMARY KEY,
      case_attempt_id TEXT NOT NULL,
      validator_suite_id TEXT NOT NULL,
      validator_name TEXT NOT NULL,
      passed INTEGER NOT NULL,
      strength_class TEXT NOT NULL,
      failure_reason TEXT,
      details_ref TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL,
      FOREIGN KEY(case_attempt_id) REFERENCES benchmark_case_attempt(case_attempt_id),
      FOREIGN KEY(validator_suite_id) REFERENCES validator_suite(validator_suite_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS control_delta (
      control_delta_id TEXT PRIMARY KEY,
      candidate_attempt_id TEXT NOT NULL,
      anchor_attempt_id TEXT NOT NULL,
      metric_name TEXT NOT NULL,
      candidate_value REAL NOT NULL,
      anchor_value REAL NOT NULL,
      delta_value REAL NOT NULL,
      delta_state TEXT NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL,
      FOREIGN KEY(candidate_attempt_id) REFERENCES benchmark_case_attempt(case_attempt_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS promotion_recommendation (
      recommendation_id TEXT PRIMARY KEY,
      benchmark_mode TEXT NOT NULL,
      candidate_type TEXT NOT NULL,
      route_id TEXT NOT NULL,
      surface_id TEXT NOT NULL,
      archetype_id TEXT NOT NULL,
      profile_id TEXT NOT NULL,
      recommendation_state TEXT NOT NULL,
      requires_review INTEGER NOT NULL,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL,
      FOREIGN KEY(route_id) REFERENCES route(route_id),
      FOREIGN KEY(surface_id) REFERENCES provider_surface(surface_id),
      FOREIGN KEY(archetype_id) REFERENCES archetype(archetype_id),
      FOREIGN KEY(profile_id) REFERENCES profile(profile_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS governance_decision (
      decision_id TEXT PRIMARY KEY,
      recommendation_id TEXT NOT NULL,
      decision_type TEXT NOT NULL,
      decision_outcome TEXT NOT NULL,
      actor TEXT NOT NULL,
      timestamp TEXT NOT NULL,
      reason TEXT NOT NULL,
      supersedes_decision_id TEXT,
      content_hash TEXT NOT NULL,
      record_json TEXT NOT NULL,
      FOREIGN KEY(recommendation_id) REFERENCES promotion_recommendation(recommendation_id)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_evidence_bundle_run ON evidence_bundle(benchmark_run_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempt_run ON benchmark_case_attempt(benchmark_run_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempt_case_set ON benchmark_case_attempt(case_set_id);",
]


EXPECTED_TABLES = {
    "schema_migrations",
    "catalog_meta",
    "provider_surface",
    "model",
    "route",
    "contract_snapshot",
    "validator_suite",
    "control_anchor_group",
    "archetype",
    "profile",
    "retry_policy",
    "benchmark_case",
    "benchmark_case_set",
    "benchmark_run",
    "evidence_bundle",
    "benchmark_case_attempt",
    "validator_result",
    "control_delta",
    "promotion_recommendation",
    "governance_decision",
}


REQUIRED_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "model": [
        ("candidate_type", "TEXT NOT NULL DEFAULT 'model_candidate'"),
    ],
    "route": [
        ("candidate_type", "TEXT NOT NULL DEFAULT 'route_candidate'"),
    ],
    "profile": [
        ("candidate_type", "TEXT NOT NULL DEFAULT 'profile_candidate'"),
    ],
    "benchmark_case": [
        ("benchmark_mode", "TEXT NOT NULL DEFAULT 'runtime_route'"),
        ("candidate_type", "TEXT NOT NULL DEFAULT 'route_candidate'"),
        ("execution_family", "TEXT NOT NULL DEFAULT 'runtime_integrated_execution'"),
        ("route_distinctness_required", "INTEGER NOT NULL DEFAULT 0"),
        ("pricing_relevant", "INTEGER NOT NULL DEFAULT 0"),
        ("governance_relevant", "INTEGER NOT NULL DEFAULT 1"),
        ("governance_blockers_apply_directly", "INTEGER NOT NULL DEFAULT 1"),
    ],
    "benchmark_case_attempt": [
        ("benchmark_mode", "TEXT NOT NULL DEFAULT 'runtime_route'"),
        ("candidate_type", "TEXT NOT NULL DEFAULT 'route_candidate'"),
        ("execution_family", "TEXT NOT NULL DEFAULT 'runtime_integrated_execution'"),
        ("route_distinctness_required", "INTEGER NOT NULL DEFAULT 0"),
        ("pricing_relevant", "INTEGER NOT NULL DEFAULT 0"),
        ("governance_relevant", "INTEGER NOT NULL DEFAULT 1"),
        ("governance_blockers_apply_directly", "INTEGER NOT NULL DEFAULT 1"),
    ],
    "promotion_recommendation": [
        ("benchmark_mode", "TEXT NOT NULL DEFAULT 'runtime_route'"),
        ("candidate_type", "TEXT NOT NULL DEFAULT 'route_candidate'"),
    ],
}
