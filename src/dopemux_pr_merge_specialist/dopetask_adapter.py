"""DopetaskAdapter — top-level coordinator for consuming Dopetask proof bundles."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .dopetask_archive_resolver import DopetaskArchiveResolver
from .dopetask_bundle_loader import BundleSchemaError, DopetaskBundleLoader
from .dopetask_series_loader import DopetaskSeriesLoader, SeriesSchemaError
from .dopetask_series_models import DopetaskSeriesResult
    ) -> None:
        self.loader = loader
        self.mapper = mapper
        self.launcher = launcher
        self.repo = repo
        self.worktree = worktree or str(Path.cwd())
        self._archive_resolver = archive_resolver or DopetaskArchiveResolver()
        self._compat_mode = compat_mode or DopetaskCompatibilityMode()
        self.series_loader = series_loader or DopetaskSeriesLoader()
    def from_bundle_path(self, bundle_path: Path) -> DopetaskAdapterResult:
        """Build a normalized result from an existing bundle file."""
        errors: list[str] = []
        warnings: list[str] = []

        try:
            bundle = self.loader.load(bundle_path)
        except BundleSchemaError as exc:
            return self._error_result(str(exc), str(bundle_path))
        except Exception as exc:  # noqa: BLE001
            return self._error_result(str(exc), str(bundle_path))

        proof_ref = self.loader.extract_proof_ref(bundle, bundle_path)

        return self._build_result(
            bundle=bundle,
            proof_ref=proof_ref,
            bundle_path=Path(bundle_path),
            loaded_from_hint="bundle",
            errors=errors,
            warnings=warnings,
        )

    def from_tp_id(
        self,
        tp_id: str,
        context: dict | None = None,
    ) -> DopetaskAdapterResult:
        """Build a normalized result by TP ID.

        If a launcher is configured, launches the engine and uses the resulting bundle.
        Otherwise, finds an existing bundle in loader.bundle_root.
        """
        ctx = context or {}
        errors: list[str] = []
        warnings: list[str] = []
        loaded_from_hint = "bundle"

        if self.launcher is not None:
            trace = self.launcher.launch(tp_id, ctx)
            if not trace.success:
                return self._error_result(
                    trace.error or "Launch failed", f"tp_id={tp_id}"
                )
            bundle_path = Path(trace.bundle_path)
            loaded_from_hint = "launch"
        else:
            bundle_path = self.loader.find_bundle(tp_id)
            if bundle_path is None:
                return self._error_result(
                    f"No bundle found for tp_id={tp_id!r} in {self.loader.bundle_root}",
                    f"tp_id={tp_id}",
                )

        try:
            bundle = self.loader.load(bundle_path)
        except BundleSchemaError as exc:
            return self._error_result(str(exc), str(bundle_path))
        except Exception as exc:  # noqa: BLE001
            return self._error_result(str(exc), str(bundle_path))

        proof_ref = self.loader.extract_proof_ref(bundle, bundle_path)

        return self._build_result(
            bundle=bundle,
            proof_ref=proof_ref,
            bundle_path=bundle_path,
            loaded_from_hint=loaded_from_hint,
            errors=errors,
            warnings=warnings,
        )

    def emit_adapter_artifacts(
        self,
        result: DopetaskAdapterResult,
        out_dir: Path,
    ) -> None:
        """Write ADAPTER_RESULT.json to out_dir."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        data = _result_to_dict(result)
        (out_dir / "ADAPTER_RESULT.json").write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _build_result(
        self,
        bundle: dict,
        proof_ref: DopetaskProofRef,
        bundle_path: Path,
        loaded_from_hint: str,
        errors: list[str],
        warnings: list[str],
    ) -> DopetaskAdapterResult:
        """Assemble DopetaskAdapterResult from bundle data and mapped states."""

        # --- Step 1: Compatibility check ---
        compat_result = self._compat_mode.check(bundle)
        bundle = compat_result.normalized  # use normalized bundle from here on
        warnings = list(warnings) + list(compat_result.warnings)

        # --- Step 2: Determine loaded_from label ---
        if loaded_from_hint == "launch":
            final_loaded_from = "launch"
        elif compat_result.is_canonical:
            final_loaded_from = "canonical_bundle"
        else:
            final_loaded_from = "compatibility_manifest"

        # --- Step 3: Archive resolution ---
        archive_res = self._archive_resolver.resolve(
            bundle_path, proof_ref.supporting_artifacts
        )

        # Update proof_ref fields with resolved values
        # (proof_ref is a dataclass — rebuild a corrected version)
        from dataclasses import replace as dc_replace

        proof_ref = dc_replace(
            proof_ref,
            archive_path=(
                archive_res.archive_path
                if archive_res.archive_expected
                else proof_ref.archive_path
            ),
            archive_present=archive_res.archive_present,
        )

        if archive_res.archive_expected and not archive_res.archive_present:
            warnings.append(archive_res.note)

        # --- Step 4: Status table logic ---
        # | errors | is_canonical | arc_expected | arc_present | adapter_status |
        # |--------|-------------|--------------|-------------|----------------|
        # | yes    | any         | any          | any         | ERROR          |
        # | no     | True        | False        | any         | READY          |
        # | no     | True        | True         | True        | READY          |
        # | no     | True        | True         | False       | DEGRADED       |
        # | no     | False       | any          | any         | DEGRADED       |

        if errors:
            adapter_status = "ERROR"
        elif not compat_result.is_canonical:
            adapter_status = "DEGRADED"
        elif archive_res.archive_expected and not archive_res.archive_present:
            adapter_status = "DEGRADED"
        else:
            adapter_status = "READY"

        # --- Step 5: Build output objects ---
        raw_posture = bundle.get("posture") or bundle.get("manifest", {}).get(
            "posture", "UNKNOWN"
        )
        raw_status = bundle.get("status", "UNKNOWN")

        posture_obj = self.mapper.derive_posture_obj(raw_posture)
        governance = self.mapper.derive_governance(raw_status, raw_posture, bundle)

        summary_raw = bundle.get("summary", {})
        if isinstance(summary_raw, str):
            summary_raw = {}
        key_findings = bundle.get("key_findings", summary_raw.get("key_findings", []))
        key_caveats = bundle.get("key_caveats", summary_raw.get("key_caveats", []))

        headline = self.mapper.derive_headline_state(raw_posture, raw_status)
        next_action = self.mapper.derive_next_action(
            raw_status, raw_posture, key_caveats
        )

        tp_id = bundle.get("tp_id") or bundle.get("pr_id", "UNKNOWN")
        run_id = bundle.get("run_id") or bundle.get("cycle_id", "UNKNOWN")

        # Determine lane from proof path
        bundle_path_str = proof_ref.bundle_path
        lane = "unknown"
        for candidate in ("closed_loop", "patch", "fusion"):
            if candidate in bundle_path_str:
                lane = candidate
                break

        tp = DopetaskTPIdentity(
            id=tp_id,
            family="flight_deck",
            lane=lane,
            title=bundle.get("title", tp_id.upper().replace("-", "_")),
            status=self.mapper.map_status(raw_status),
            run_id=str(run_id),
        )

        target = DopetaskTarget(
            repo=self.repo,
            worktree=self.worktree,
            ref=bundle.get("ref", ""),
            pr_number=bundle.get("pr_number"),
            case_id=bundle.get("case_id"),
        )

        summary = DopetaskSummary(
            result=(
                summary_raw.get("result", "") if isinstance(summary_raw, dict) else ""
            ),
            next_action=next_action,
            headline_state=headline,
            confidence=(
                summary_raw.get("confidence", "UNKNOWN")
                if isinstance(summary_raw, dict)
                else "UNKNOWN"
            ),
            risk=(
                summary_raw.get("risk", "UNKNOWN")
                if isinstance(summary_raw, dict)
                else "UNKNOWN"
            ),
            key_findings=list(key_findings),
            key_caveats=list(key_caveats),
        )

        recommended_panel = self.mapper.derive_recommended_panel(raw_posture)
        operator_view = DopetaskOperatorView(
            open_first=proof_ref.bundle_path,
            open_second=proof_ref.archive_path,
            recommended_panel=recommended_panel,
            artifact_priority=["bundle", "supporting_artifacts", "archive"],
        )

        integration = DopetaskIntegration(
            loaded_from=final_loaded_from,
            adapter_status=adapter_status,
            errors=errors,
            warnings=warnings,
            compatibility_mode=not compat_result.is_canonical,
            archive_expected=archive_res.archive_expected,
        )

        return DopetaskAdapterResult(
            source="dopetask",
            schema_version="1.0",
            tp=tp,
            target=target,
            posture=posture_obj,
            summary=summary,
            proof=proof_ref,
            governance=governance,
            operator_view=operator_view,
            integration=integration,
            computed_at=utc_now(),
        )

    def _error_result(self, error: str, source_hint: str) -> DopetaskAdapterResult:
        """Build a minimal ERROR result when loading fails."""
        dummy_tp = DopetaskTPIdentity(
            id="UNKNOWN",
            family="flight_deck",
            lane="unknown",
            title="UNKNOWN",
            status="UNKNOWN",
            run_id="UNKNOWN",
        )
        dummy_target = DopetaskTarget(
            repo=self.repo,
            worktree=self.worktree,
            ref="",
            pr_number=None,
            case_id=None,
        )
        dummy_posture = DopetaskPosture(
            mode="UNKNOWN",
            advisory_only=False,
            signoff_required=False,
            defer_only=False,
            auto_apply_allowed=False,
            auto_apply_risk_threshold="LOW",
        )
        dummy_summary = DopetaskSummary(
            result="Error loading bundle.",
            next_action="Status unknown. Verify bundle integrity and rerun.",
            headline_state="UNKNOWN",
            confidence="UNKNOWN",
            risk="UNKNOWN",
            key_findings=[],
            key_caveats=[],
        )
        dummy_proof = DopetaskProofRef(
            bundle_path=source_hint,
            bundle_present=False,
            archive_path=None,
            archive_present=False,
            supporting_artifacts=[],
        )
        dummy_gov = DopetaskGovernance(
            allowed_actions=[],
            blocked_actions=["APPLY_FIX", "MERGE", "APPROVE"],
            signoff={"required": False, "owner": "", "reason": ""},
        )
        dummy_op = DopetaskOperatorView(
            open_first=source_hint,
            open_second=None,
            recommended_panel="detail",
            artifact_priority=["bundle", "supporting_artifacts", "archive"],
        )
        integration = DopetaskIntegration(
            loaded_from="bundle",
            adapter_status="ERROR",
            errors=[error],
            warnings=[],
            compatibility_mode=False,
            archive_expected=False,
        )
        return DopetaskAdapterResult(
            source="dopetask",
            schema_version="1.0",
            tp=dummy_tp,
            target=dummy_target,
            posture=dummy_posture,
            summary=dummy_summary,
            proof=dummy_proof,
            governance=dummy_gov,
            operator_view=dummy_op,
            integration=integration,
            computed_at=utc_now(),
        )


def _result_to_dict(result: DopetaskAdapterResult) -> dict:
    """Convert DopetaskAdapterResult to a JSON-serializable dict."""
    return asdict(result)
