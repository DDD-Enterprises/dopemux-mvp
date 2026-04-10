from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Any

from ..models.entities import (
    Archetype,
    BenchmarkCase,
    BenchmarkCaseAttempt,
    BenchmarkCaseSet,
    BenchmarkRun,
    ContractSnapshot,
    ControlAnchorGroup,
    ControlDelta,
    EvidenceBundle,
    GovernanceDecision,
    ModelRecord,
    Profile,
    PromotionRecommendation,
    ProviderSurface,
    RetryPolicy,
    RouteRecord,
    ValidatorResult,
    ValidatorSuite,
)
from .hashing import stable_json_dumps
from .sqlite_bootstrap import bootstrap_catalog, connect_catalog


class BenchmarkCatalogRepo:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    @classmethod
    def from_root(cls, root: Path | None = None) -> "BenchmarkCatalogRepo":
        return cls(bootstrap_catalog(root))

    def _connect(self) -> sqlite3.Connection:
        return connect_catalog(self.db_path)

    def _execute(self, statement: str, params: tuple[Any, ...]) -> None:
        with self._connect() as conn:
            conn.execute(statement, params)
            conn.commit()

    def insert_provider_surface(self, record: ProviderSurface) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO provider_surface(
              surface_id, surface_class, provider_name, transport_kind, endpoint_ref,
              logging_posture, residency_posture, surface_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.surface_id,
                record.surface_class.value,
                record.provider_name,
                record.transport_kind,
                record.endpoint_ref,
                record.logging_posture,
                record.residency_posture,
                record.surface_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_model(self, record: ModelRecord) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO model(
              model_key, display_name, family, source_registry_ref, registry_class,
              lifecycle_status, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.model_key,
                record.display_name,
                record.family,
                record.source_registry_ref,
                record.registry_class,
                record.lifecycle_status,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_route(self, record: RouteRecord) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO route(
              route_id, surface_id, model_key, provider_model_id, api_key_ref, route_pin,
              strict_json_schema_declared, strict_passthrough_verified, route_hash, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.route_id,
                record.surface_id,
                record.model_key,
                record.provider_model_id,
                record.api_key_ref,
                record.route_pin,
                int(record.strict_json_schema_declared),
                int(record.strict_passthrough_verified),
                record.route_hash,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_contract_snapshot(self, record: ContractSnapshot) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO contract_snapshot(
              contract_snapshot_id, runtime_version, contract_version, strict_schema_expected,
              snapshot_hash, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.contract_snapshot_id,
                record.runtime_version,
                record.contract_version,
                int(record.strict_schema_expected),
                record.snapshot_hash,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_validator_suite(self, record: ValidatorSuite) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO validator_suite(
              validator_suite_id, strength_class, version_hash, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?)
            """,
            (
                record.validator_suite_id,
                record.strength_class,
                record.version_hash,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_control_anchor_group(self, record: ControlAnchorGroup) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO control_anchor_group(
              anchor_group_id, surface_class, archetype_id, required, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                record.anchor_group_id,
                record.surface_class.value,
                record.archetype_id,
                int(record.required),
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_archetype(self, record: Archetype) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO archetype(
              archetype_id, description, success_rubric_id, promotion_policy_id, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                record.archetype_id,
                record.description,
                record.success_rubric_id,
                record.promotion_policy_id,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_profile(self, record: Profile) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO profile(profile_id, is_production_profile, content_hash, record_json)
            VALUES(?, ?, ?, ?)
            """,
            (
                record.profile_id,
                int(record.is_production_profile),
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_retry_policy(self, record: RetryPolicy) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO retry_policy(
              retry_policy_id, max_hops, policy_hash, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?)
            """,
            (
                record.retry_policy_id,
                record.max_hops,
                record.policy_hash,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_benchmark_case(self, record: BenchmarkCase) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO benchmark_case(
              case_id, case_version, archetype_id, phase_or_step_family, validator_suite_id,
              contract_snapshot_id, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_id,
                record.case_version,
                record.archetype_id,
                record.phase_or_step_family,
                record.validator_suite_id,
                record.contract_snapshot_id,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_benchmark_case_set(self, record: BenchmarkCaseSet) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO benchmark_case_set(
              case_set_id, case_set_version, archetype_id, benchmark_stage,
              control_anchor_group_id, schedule_class, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_set_id,
                record.case_set_version,
                record.archetype_id,
                record.benchmark_stage,
                record.control_anchor_group_id,
                record.schedule_class,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_benchmark_run(self, record: BenchmarkRun) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO benchmark_run(
              benchmark_run_id, run_type, trigger_type, trigger_ref, git_commit,
              runtime_version, status, started_at, finished_at, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.benchmark_run_id,
                record.run_type,
                record.trigger_type,
                record.trigger_ref,
                record.git_commit,
                record.runtime_version,
                record.status,
                record.started_at,
                record.finished_at,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_evidence_bundle(self, record: EvidenceBundle) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO evidence_bundle(
              bundle_id, bundle_type, benchmark_run_id, root_path, manifest_hash,
              retention_class, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.bundle_id,
                record.bundle_type.value,
                record.benchmark_run_id,
                record.root_path,
                record.manifest_hash,
                record.retention_class,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_benchmark_case_attempt(self, record: BenchmarkCaseAttempt) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO benchmark_case_attempt(
              case_attempt_id, benchmark_run_id, case_id, case_version, case_set_id, archetype_id,
              phase_or_step_family, surface_class, surface_id, profile_id, route_id,
              control_anchor_group_id, runtime_version, contract_version, contract_snapshot_id,
              schema_id, strict_schema_expected, validator_suite_id, attempt_number, retry_policy_id,
              temperature_or_equivalent, max_tokens_or_budget, tool_mode, batch_mode, contract_gate_pass,
              contract_gate_strength, contract_fail_reason, validator_pass, task_success_score,
              output_artifact_ref, golden_eval_ref, control_delta_ref, evidence_bundle_id, timestamp_utc, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.case_attempt_id,
                record.benchmark_run_id,
                record.case_id,
                record.case_version,
                record.case_set_id,
                record.archetype_id,
                record.phase_or_step_family,
                record.surface_class.value,
                record.surface_id,
                record.profile_id,
                record.route_id,
                record.control_anchor_group_id,
                record.runtime_version,
                record.contract_version,
                record.contract_snapshot_id,
                record.schema_id,
                int(record.strict_schema_expected),
                record.validator_suite_id,
                record.attempt_number,
                record.retry_policy_id,
                record.temperature_or_equivalent,
                record.max_tokens_or_budget,
                record.tool_mode,
                record.batch_mode,
                int(record.contract_gate_pass),
                record.contract_gate_strength.value,
                record.contract_fail_reason,
                int(record.validator_pass),
                record.task_success_score,
                record.output_artifact_ref,
                record.golden_eval_ref,
                record.control_delta_ref,
                record.evidence_bundle_id,
                record.timestamp_utc,
                stable_json_dumps(payload),
            ),
        )

    def insert_validator_result(self, record: ValidatorResult) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO validator_result(
              validator_result_id, case_attempt_id, validator_suite_id, validator_name,
              passed, strength_class, failure_reason, details_ref, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.validator_result_id,
                record.case_attempt_id,
                record.validator_suite_id,
                record.validator_name,
                int(record.passed),
                record.strength_class,
                record.failure_reason,
                record.details_ref,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_control_delta(self, record: ControlDelta) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO control_delta(
              control_delta_id, candidate_attempt_id, anchor_attempt_id, metric_name,
              candidate_value, anchor_value, delta_value, delta_state, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.control_delta_id,
                record.candidate_attempt_id,
                record.anchor_attempt_id,
                record.metric_name,
                record.candidate_value,
                record.anchor_value,
                record.delta_value,
                record.delta_state,
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_promotion_recommendation(self, record: PromotionRecommendation) -> None:
        payload = record.to_dict()
        self._execute(
            """
            INSERT OR REPLACE INTO promotion_recommendation(
              recommendation_id, route_id, surface_id, archetype_id, profile_id,
              recommendation_state, requires_review, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.recommendation_id,
                record.route_id,
                record.surface_id,
                record.archetype_id,
                record.profile_id,
                record.recommendation_state.value,
                int(record.requires_review),
                record.content_hash,
                stable_json_dumps(payload),
            ),
        )

    def insert_governance_decision(self, record: GovernanceDecision) -> None:
        payload = record.to_dict()
        with self._connect() as conn:
            conn.execute(
            """
            INSERT INTO governance_decision(
              decision_id, recommendation_id, decision_type, decision_outcome, actor,
              timestamp, reason, supersedes_decision_id, content_hash, record_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.decision_id,
                record.recommendation_id,
                record.decision_type.value,
                record.decision_outcome.value,
                record.actor,
                record.timestamp,
                record.reason,
                record.supersedes_decision_id,
                record.content_hash,
                stable_json_dumps(payload),
            ),
            )
            conn.commit()

    def fetch_attempt(self, case_attempt_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("benchmark_case_attempt", "case_attempt_id", case_attempt_id)

    def fetch_bundle(self, bundle_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("evidence_bundle", "bundle_id", bundle_id)

    def fetch_contract_snapshot(self, contract_snapshot_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("contract_snapshot", "contract_snapshot_id", contract_snapshot_id)

    def fetch_validator_suite(self, validator_suite_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("validator_suite", "validator_suite_id", validator_suite_id)

    def fetch_provider_surface(self, surface_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("provider_surface", "surface_id", surface_id)

    def fetch_route(self, route_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("route", "route_id", route_id)

    def fetch_benchmark_case(self, case_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("benchmark_case", "case_id", case_id)

    def fetch_benchmark_case_set(self, case_set_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("benchmark_case_set", "case_set_id", case_set_id)

    def fetch_control_anchor_group(self, anchor_group_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("control_anchor_group", "anchor_group_id", anchor_group_id)

    def fetch_profile(self, profile_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("profile", "profile_id", profile_id)

    def list_profiles(self) -> list[dict[str, Any]]:
        return self._list_record_json("profile", "profile_id")

    def list_benchmark_cases(self) -> list[dict[str, Any]]:
        return self._list_record_json("benchmark_case", "case_id")

    def list_benchmark_case_sets(self) -> list[dict[str, Any]]:
        return self._list_record_json("benchmark_case_set", "case_set_id")

    def list_validator_suites(self) -> list[dict[str, Any]]:
        return self._list_record_json("validator_suite", "validator_suite_id")

    def fetch_benchmark_run(self, benchmark_run_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("benchmark_run", "benchmark_run_id", benchmark_run_id)

    def fetch_archetype(self, archetype_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("archetype", "archetype_id", archetype_id)

    def list_benchmark_runs(self) -> list[dict[str, Any]]:
        return self._list_record_json("benchmark_run", "started_at")

    def list_attempts(self, benchmark_run_id: str | None = None) -> list[dict[str, Any]]:
        if benchmark_run_id is None:
            return self._list_record_json("benchmark_case_attempt", "timestamp_utc")
        return self._list_record_json_where(
            "benchmark_case_attempt",
            "benchmark_run_id",
            benchmark_run_id,
            "timestamp_utc",
        )

    def list_validator_results(self, case_attempt_id: str | None = None) -> list[dict[str, Any]]:
        if case_attempt_id is None:
            return self._list_record_json("validator_result", "validator_result_id")
        return self._list_record_json_where(
            "validator_result",
            "case_attempt_id",
            case_attempt_id,
            "validator_result_id",
        )

    def list_control_deltas(
        self,
        candidate_attempt_id: str | None = None,
        anchor_attempt_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if candidate_attempt_id is not None:
            return self._list_record_json_where(
                "control_delta",
                "candidate_attempt_id",
                candidate_attempt_id,
                "metric_name",
            )
        if anchor_attempt_id is not None:
            return self._list_record_json_where(
                "control_delta",
                "anchor_attempt_id",
                anchor_attempt_id,
                "metric_name",
            )
        return self._list_record_json("control_delta", "control_delta_id")

    def fetch_promotion_recommendation(self, recommendation_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("promotion_recommendation", "recommendation_id", recommendation_id)

    def list_promotion_recommendations(self) -> list[dict[str, Any]]:
        return self._list_record_json("promotion_recommendation", "recommendation_id")

    def fetch_governance_decision(self, decision_id: str) -> dict[str, Any] | None:
        return self._fetch_record_json("governance_decision", "decision_id", decision_id)

    def list_governance_decisions(self, recommendation_id: str | None = None) -> list[dict[str, Any]]:
        if recommendation_id is None:
            return self._list_record_json("governance_decision", "timestamp")
        return self._list_record_json_where(
            "governance_decision",
            "recommendation_id",
            recommendation_id,
            "timestamp",
        )

    def _fetch_record_json(self, table: str, key_column: str, key_value: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT record_json FROM {table} WHERE {key_column} = ?",
                (key_value,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(str(row["record_json"]))

    def _list_record_json(self, table: str, order_column: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT record_json FROM {table} ORDER BY {order_column}"
            ).fetchall()
        return [json.loads(str(row["record_json"])) for row in rows]

    def _list_record_json_where(
        self,
        table: str,
        where_column: str,
        where_value: str,
        order_column: str,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT record_json FROM {table} WHERE {where_column} = ? ORDER BY {order_column}",
                (where_value,),
            ).fetchall()
        return [json.loads(str(row["record_json"])) for row in rows]

    def count_rows(self) -> dict[str, int]:
        table_names = [
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
        ]
        counts: dict[str, int] = {}
        with self._connect() as conn:
            for name in table_names:
                row = conn.execute(f"SELECT COUNT(*) AS row_count FROM {name}").fetchone()
                counts[name] = int(row["row_count"])
        return counts
