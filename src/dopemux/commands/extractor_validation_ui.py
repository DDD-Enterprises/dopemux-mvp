from __future__ import annotations

import sys
import textwrap
from typing import Any, Dict, List

from dopemux.console import console

try:  # pragma: no cover - optional rich rendering
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except Exception:  # pragma: no cover - optional rich rendering
    Console = None
    Panel = None
    Table = None


_STAGE_ORDER = ("preflight", "provider_probe", "batch_pilot", "phase_slice", "full_phased")


class BatchValidationUI:
    def __init__(self, mode: str = "auto") -> None:
        requested = str(mode or "auto").strip().lower() or "auto"
        self.mode = requested if requested in {"auto", "rich", "plain"} else "auto"
        want_rich = self.mode == "rich" or (self.mode == "auto" and sys.stdout.isatty())
        self._console = Console(force_terminal=(self.mode == "rich")) if want_rich and Console is not None else None
        self._rich = self._console is not None and Panel is not None and Table is not None

    def emit(self, payload: Dict[str, Any]) -> None:
        if self._rich:
            self._emit_rich(payload)
        else:
            console.print(self._render_plain(payload))

    def _emit_rich(self, payload: Dict[str, Any]) -> None:
        assert self._console is not None and Panel is not None and Table is not None
        header = (
            f"[cyan][LIVE][/cyan] {payload.get('run_id')}"
            f"  stage={payload.get('stage')}"
            f"  status={str(payload.get('status') or '').upper()}"
            f"  spend=${float((payload.get('spend_ledger') or {}).get('total_estimated_upper_bound_usd', 0.0)):.2f}"
            f"  open_breakers={self._open_breaker_count(payload)}"
        )
        self._console.print(Panel(header, title="DOPemux v5 Validation", border_style="cyan"))

        rail = Table(title="Stage Rail")
        rail.add_column("Stage")
        rail.add_column("State")
        current = str(payload.get("stage") or "preflight")
        stage_decisions = payload.get("stage_decisions") or []
        decision_map = {
            str(row.get("stage")): str(row.get("status") or "pending")
            for row in stage_decisions
            if isinstance(row, dict)
        }
        for stage in _STAGE_ORDER:
            state = decision_map.get(stage, "current" if stage == current else "pending")
            rail.add_row(stage, state)
        self._console.print(rail)

        checkpoint = Table(title="Checkpoint")
        checkpoint.add_column("Field")
        checkpoint.add_column("Value")
        spend = payload.get("spend_ledger") or {}
        checkpoint.add_row("Promptset", str(payload.get("promptset_root") or ""))
        checkpoint.add_row("Routing", str(payload.get("routing_policy") or ""))
        launch_profile = payload.get("launch_profile") or {}
        checkpoint.add_row("Validator target", str(launch_profile.get("validator_target_policy") or payload.get("routing_policy") or ""))
        checkpoint.add_row("Consent", self._consent_state(payload))
        max_cost_val = payload.get("max_cost")
        max_str = f" / max ${float(max_cost_val):.2f}" if max_cost_val is not None else ""
        checkpoint.add_row("Spend", f"${float(spend.get('total_estimated_upper_bound_usd', 0.0)):.2f}{max_str}")
        checkpoint.add_row("Launch fingerprint", str(payload.get("launch_profile_fingerprint") or ""))
        checkpoint.add_row("Model map hash", str(launch_profile.get("promptset_model_map_sha256") or "unknown"))
        checkpoint.add_row("Safe to spend", self._safe_to_spend(payload))
        checkpoint.add_row("Why stopped spending", self._why_stopped(payload))
        self._console.print(checkpoint)

        blockers = payload.get("blockers") or []
        if blockers:
            blocker_table = Table(title="Blockers")
            blocker_table.add_column("Blocker")
            blocker_table.add_column("Next action")
            for blocker in blockers:
                blocker_table.add_row(str(blocker), self._next_action_for_blocker(str(blocker)))
            self._console.print(blocker_table)

    def _render_plain(self, payload: Dict[str, Any]) -> str:
        lines: List[str] = []
        spend = payload.get("spend_ledger") or {}
        lines.append(
            "[LIVE] "
            f"run={payload.get('run_id')} stage={payload.get('stage')} status={payload.get('status')} "
            f"spend=${float(spend.get('total_estimated_upper_bound_usd', 0.0)):.2f} "
            f"open_breakers={self._open_breaker_count(payload)}"
        )
        launch_profile = payload.get("launch_profile") or {}
        max_cost_val = payload.get("max_cost")
        max_str = f"{float(max_cost_val):.2f}" if max_cost_val is not None else "none"
        lines.append(
            f"promptset={payload.get('promptset_root')} routing_policy={payload.get('routing_policy')} "
            f"validator_target_policy={launch_profile.get('validator_target_policy') or payload.get('routing_policy')}"
        )
        lines.append(
            f"launch_profile_fingerprint={payload.get('launch_profile_fingerprint')} "
            f"model_map_sha256={launch_profile.get('promptset_model_map_sha256') or 'unknown'} "
            f"max_cost={max_str}"
        )
        lines.append(f"consent={self._consent_state(payload)}")
        lines.append("stage_rail=" + ", ".join(self._stage_rail(payload)))
        lines.append(f"safe_to_spend={self._safe_to_spend(payload)}")
        lines.append(f"why_stopped_spending={self._why_stopped(payload)}")
        blockers = payload.get("blockers") or []
        if blockers:
            lines.append("blockers:")
            for blocker in blockers:
                lines.append(f"- {blocker}")
                lines.append(f"  next_action: {self._next_action_for_blocker(str(blocker))}")
        return "\n".join(lines)

    def _stage_rail(self, payload: Dict[str, Any]) -> List[str]:
        stage_decisions = payload.get("stage_decisions") or []
        decision_map = {
            str(row.get("stage")): str(row.get("status") or "pending")
            for row in stage_decisions
            if isinstance(row, dict)
        }
        current = str(payload.get("stage") or "preflight")
        out: List[str] = []
        for stage in _STAGE_ORDER:
            state = decision_map.get(stage, "current" if stage == current else "pending")
            out.append(f"{stage}:{state}")
        return out

    def _open_breaker_count(self, payload: Dict[str, Any]) -> int:
        breaker = payload.get("breaker_state") or {}
        circuits = breaker.get("circuits") or {}
        return sum(1 for row in circuits.values() if isinstance(row, dict) and row.get("state") == "open")

    def _consent_state(self, payload: Dict[str, Any]) -> str:
        baseline = payload.get("baseline") or {}
        provider_env = baseline.get("provider_env") or {}
        live_ok = baseline.get("live_ok")
        present = sorted(key for key, meta in provider_env.items() if isinstance(meta, dict) and meta.get("present"))
        return f"live_ok={bool(live_ok)} keys={','.join(present) if present else 'none'}"

    def _why_stopped(self, payload: Dict[str, Any]) -> str:
        blockers = payload.get("blockers") or []
        return blockers[0] if blockers else "none"

    def _safe_to_spend(self, payload: Dict[str, Any]) -> str:
        blockers = payload.get("blockers") or []
        return "yes" if not blockers else "no"

    def _next_action_for_blocker(self, blocker: str) -> str:
        lowered = blocker.lower()
        if "prompt" in lowered:
            return "Fix the promptset root or required prompt files, then rerun preflight."
        if "auth" in lowered or "api key" in lowered or "provider" in lowered:
            return "Verify provider credentials and rerun provider preflight before spending."
        if "route" in lowered or "routing" in lowered:
            return "Inspect the resolved routing policy and required step routes before continuing."
        if "consent" in lowered or "spend" in lowered or "budget" in lowered:
            return "Confirm live consent and spend caps, then rerun the validation gate."
        if "artifact" in lowered or "phase" in lowered:
            return "Inspect the missing phase artifacts and rerun the affected phase or resume path."
        return textwrap.shorten(
            "Inspect the blocker evidence in the validation report, correct the underlying cause, then rerun the gate.",
            width=88,
            placeholder="…",
        )
