from __future__ import annotations

import json
import logging
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from output_safety import sanitize_payload_for_output
from phases import PHASES
from rte_config import TELEMETRY_DIRNAME, TERMINAL_TIMELINE_FILENAME

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.table import Table
    from rich.text import Text
except Exception:  # pragma: no cover - optional rich rendering
    Console = None  # type: ignore[assignment]
    Panel = None  # type: ignore[assignment]
    Progress = None  # type: ignore[assignment]
    SpinnerColumn = None  # type: ignore[assignment]
    BarColumn = None  # type: ignore[assignment]
    MofNCompleteColumn = None  # type: ignore[assignment]
    TimeElapsedColumn = None  # type: ignore[assignment]
    TextColumn = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    Text = None  # type: ignore[assignment]


AppendJsonl = Callable[[Path, Dict[str, Any]], None]
DEFAULT_ROUTING_POLICY = "balanced_openrouter"
EXTRACTOR_COMPONENT_NAME = "repo_truth_extractor"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_trace_id() -> str:
    return uuid.uuid4().hex


def _new_span_id() -> str:
    return uuid.uuid4().hex[:16]


def _clean_event_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {
            str(key): _clean_event_value(subvalue)
            for key, subvalue in value.items()
            if subvalue is not None
        }
    if isinstance(value, (list, tuple)):
        return [_clean_event_value(item) for item in value if item is not None]
    return str(value)


@dataclass(frozen=True)
class UiConfig:
    mode: str = "auto"  # auto|rich|plain
    quiet: bool = False
    jsonl_events: bool = False


class UI:
    def __init__(
        self,
        cfg: UiConfig,
        run_root: Path,
        run_id: str,
        *,
        append_jsonl: AppendJsonl,
        now_iso_fn: Callable[[], str] = now_iso,
        new_trace_id: Callable[[], str] = _new_trace_id,
        new_span_id: Callable[[], str] = _new_span_id,
        component_name: str = EXTRACTOR_COMPONENT_NAME,
        readonly: bool = False,
    ):
        self.cfg = cfg
        self.run_root = run_root
        self.run_id = run_id
        self._append_jsonl = append_jsonl
        self._now_iso = now_iso_fn
        self._new_trace_id = new_trace_id
        self._new_span_id = new_span_id
        self._component_name = component_name
        # F-59: readonly UIs back introspection commands (--status, etc.) that
        # must never materialise a run directory or write telemetry as a
        # side effect of merely reporting on a run.
        self._readonly = bool(readonly)
        self._stdout_is_tty = sys.stdout.isatty()
        self._console: Optional[Any] = None
        self._progress: Optional[Any] = None
        self._task_id: Optional[int] = None
        self._progress_total = 0
        self._rich = False

        requested = cfg.mode
        want_rich = requested == "rich" or (requested == "auto" and self._stdout_is_tty)
        if want_rich and Console is not None and Progress is not None:
            self._console = Console(force_terminal=(requested == "rich"))
            self._rich = True

        import threading as _threading
        self._active_partitions: Dict[str, Dict[str, Any]] = {}
        self._partitions_lock = _threading.Lock()
        self._timeline_path: Path = (
            run_root / TELEMETRY_DIRNAME / TERMINAL_TIMELINE_FILENAME
        )
        self._events_path: Optional[Path] = None
        if cfg.jsonl_events:
            self._events_path = run_root / "events.jsonl"

    def _emit_event(self, payload: Dict[str, Any]) -> None:
        if self._readonly:
            # Never touch disk on a readonly/introspection path (F-59):
            # writing the timeline JSONL would mkdir the run directory tree
            # even though no run was ever started.
            return
        row = sanitize_payload_for_output(dict(payload))
        row.setdefault("ts", self._now_iso())
        row.setdefault("component", self._component_name)
        row.setdefault("event_type", str(row.get("type") or "event"))
        row.setdefault("run_id", self.run_id)
        row.setdefault("run_root", str(self.run_root.resolve()))
        try:
            self._append_jsonl(self._timeline_path, row)
            if self._events_path is not None:
                self._append_jsonl(self._events_path, row)
        except Exception:
            # UI event persistence must never alter execution flow.
            return

    def make_trace_context(
        self,
        *,
        phase: str,
        step_id: str,
        partition_id: Optional[str] = None,
        parent_trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> Dict[str, str]:
        trace_id = str(parent_trace_id or "").strip() or self._new_trace_id()
        context = {
            "trace_id": trace_id,
            "span_id": self._new_span_id(),
        }
        if parent_span_id:
            context["parent_span_id"] = str(parent_span_id)
        context["phase"] = phase
        context["step_id"] = step_id
        if partition_id:
            context["partition_id"] = partition_id
        return context

    def llm_request_event(
        self,
        *,
        phase: str,
        step_id: str,
        status: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str] = None,
        partition_id: Optional[str] = None,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        route: Optional[str] = None,
        routing_policy: Optional[str] = None,
        attempt: Optional[int] = None,
        hop: Optional[int] = None,
        latency_ms: Optional[int] = None,
        status_code: Optional[int] = None,
        failure_type: Optional[str] = None,
        finish_reason: Optional[str] = None,
        request_payload_bytes: Optional[int] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        reasoning_tokens: Optional[int] = None,
        cached_tokens: Optional[int] = None,
        estimated_cost_usd: Optional[float] = None,
        actual_cost_usd: Optional[float] = None,
        upstream_request_id: Optional[str] = None,
        upstream_generation_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload: Dict[str, Any] = {
            "type": f"llm_request_{status}",
            "event_type": f"llm_request_{status}",
            "phase": phase,
            "step": step_id,
            "partition_id": partition_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "provider": provider,
            "model_id": model_id,
            "route": route,
            "routing_policy": routing_policy,
            "attempt": attempt,
            "hop": hop,
            "latency_ms": latency_ms,
            "status": status,
            "status_code": status_code,
            "failure_type": failure_type,
            "finish_reason": finish_reason,
            "request_payload_bytes": request_payload_bytes,
            "tokens_prompt": prompt_tokens,
            "tokens_completion": completion_tokens,
            "tokens_reasoning": reasoning_tokens,
            "tokens_cached": cached_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "actual_cost_usd": actual_cost_usd,
            "upstream_request_id": upstream_request_id,
            "upstream_generation_id": upstream_generation_id,
            "batch_id": batch_id,
        }
        if extra:
            payload.update(_clean_event_value(extra))
        self._emit_event({k: v for k, v in payload.items() if v is not None})

    def spend_ledger_event(
        self,
        *,
        phase: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str] = None,
        prompt_tokens: int,
        completion_tokens: int,
        estimated_cost_usd: Optional[float] = None,
        partition_id: Optional[str] = None,
        step_id: Optional[str] = None,
    ) -> None:
        self._emit_event(
            {
                "type": "spend_ledger_accumulate",
                "event_type": "spend_ledger_accumulate",
                "phase": phase,
                "step": step_id,
                "partition_id": partition_id,
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
                "tokens_prompt": int(prompt_tokens),
                "tokens_completion": int(completion_tokens),
                "estimated_cost_usd": estimated_cost_usd,
            }
        )

    def _print_plain(self, line: str) -> None:
        print(line, flush=True)

    def _summary_line(self, line: str) -> None:
        if self._rich and self._console is not None:
            self._console.print(line)
        else:
            self._print_plain(line)

    def _status_style(self, status: str) -> str:
        token = str(status or "").strip().upper()
        if token in {"PASS", "OK", "SUCCESS"}:
            return "bold green"
        if token in {"FAIL", "ERROR"}:
            return "bold red"
        if token in {"IN_PROGRESS", "RUNNING"}:
            return "bold yellow"
        return "bold cyan"

    def _ratio_bar(self, ok: int, total: int, width: int = 24) -> str:
        if total <= 0:
            return "[" + ("." * width) + "] 0.0%"
        ratio = max(0.0, min(1.0, float(ok) / float(total)))
        filled = int(round(ratio * width))
        bar = "#" * filled + "." * (width - filled)
        return f"[{bar}] {ratio * 100.0:5.1f}%"

    def _provider_color(self, provider: str) -> str:
        """Return Rich color for a provider name."""
        mapping = {
            "openai": "bold green",
            "anthropic": "bold magenta",
            "gemini": "bold blue",
            "xai": "bold yellow",
            "openrouter": "bold cyan",
            "mistral": "bold orange3",
        }
        return mapping.get(str(provider).lower(), "bold white")

    def partition_start_event(
        self,
        phase: str,
        step_id: str,
        partition_id: str,
        provider: str,
        model_id: str,
    ) -> None:
        """Record that a partition has started LLM execution on a specific provider/model."""
        import time as _time
        entry = {
            "phase": phase,
            "step_id": step_id,
            "provider": provider,
            "model_id": model_id,
            "start_ts": _time.monotonic(),
            "attempt": 1,
            "status": "running",
        }
        with self._partitions_lock:
            self._active_partitions[partition_id] = entry
        self._emit_event({
            "type": "partition_start",
            "phase": phase,
            "step": step_id,
            "partition_id": partition_id,
            "provider": provider,
            "model_id": model_id,
        })
        if self.cfg.quiet:
            return
        color = self._provider_color(provider)
        if self._rich and self._console is not None:
            self._console.print(
                f"  [{color}]▶ {phase}:{step_id} {partition_id}[/{color}]"
                f" [dim]→ {provider}/{model_id}[/dim]"
            )
        else:
            self._print_plain(
                f"PARTITION_START phase={phase} step={step_id} partition={partition_id} "
                f"provider={provider} model={model_id}"
            )

    def retry_event(
        self,
        phase: str,
        step_id: str,
        partition_id: str,
        attempt: int,
        max_attempts: int,
        provider: str,
        model_id: str,
        status_code: Optional[int],
        failure_type: Optional[str],
        delay_seconds: float,
    ) -> None:
        """Show a live retry notification for a partition."""
        with self._partitions_lock:
            entry = self._active_partitions.get(partition_id)
            if entry:
                entry["attempt"] = attempt
                entry["status"] = "retry"
        self._emit_event({
            "type": "partition_retry",
            "phase": phase,
            "step": step_id,
            "partition_id": partition_id,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "provider": provider,
            "model_id": model_id,
            "status_code": status_code,
            "failure_type": failure_type,
            "delay_seconds": delay_seconds,
        })
        if self.cfg.quiet:
            return
        status_str = str(status_code) if status_code else "-"
        failure_str = str(failure_type or "-")
        if self._rich and self._console is not None:
            self._console.print(
                f"  [bold orange3]⟳ RETRY[/bold orange3] "
                f"[dim]{phase}:{step_id} {partition_id}[/dim] "
                f"attempt=[bold yellow]{attempt}/{max_attempts}[/bold yellow] "
                f"[{self._provider_color(provider)}]{provider}/{model_id}[/{self._provider_color(provider)}] "
                f"status=[bold red]{status_str}[/bold red] "
                f"reason=[italic red]{failure_str}[/italic red] "
                f"wait=[bold]{delay_seconds:.1f}s[/bold]"
            )
        else:
            self._print_plain(
                f"PARTITION_RETRY phase={phase} step={step_id} partition={partition_id} "
                f"attempt={attempt}/{max_attempts} provider={provider} model={model_id} "
                f"status_code={status_str} failure_type={failure_str} delay={delay_seconds:.1f}s"
            )

    def step_progress_stop(self) -> None:
        if self._progress is not None:
            self._progress.stop()
            self._progress = None
            self._task_id = None
            self._progress_total = 0

    def phase_start(
        self,
        phase: str,
        phase_dir: Path,
        inventory: int,
        partitions: int,
        provider: str,
        model_id: str,
        workers: int,
        flags: str,
        routing_policy: str = DEFAULT_ROUTING_POLICY,
        tier_defaults: Optional[Dict[str, str]] = None,
    ) -> None:
        self._emit_event(
            {
                "type": "phase_start",
                "phase": phase,
                "phase_dir": str(phase_dir.resolve()),
                "inventory": inventory,
                "partitions": partitions,
                "provider": provider,
                "model_id": model_id,
                "workers": workers,
                "flags": flags,
                "routing_policy": routing_policy,
                "tier_defaults": dict(tier_defaults or {}),
            }
        )
        if self.cfg.quiet:
            return
        if (
            self._rich
            and self._console is not None
            and Panel is not None
            and Text is not None
        ):
            body = Text()
            body.append(f"run={self.run_id}\n", style="bold")
            body.append(f"phase={phase}  workers={workers}\n")
            body.append(f"inventory={inventory}  partitions={partitions}\n", style="cyan")
            body.append(f"provider={provider}  model={model_id}\n", style="magenta")
            body.append(f"routing_policy={routing_policy}\n", style="yellow")
            body.append(
                "status_chips=PASS[green] WARN[yellow] FAIL[red] RUNNING[cyan]\n",
                style="dim",
            )
            if tier_defaults:
                body.append(
                    f"tier_defaults={json.dumps(tier_defaults, sort_keys=True)}\n"
                )
            body.append(f"flags={flags}\n")
            body.append(f"phase_dir={phase_dir.resolve()}", style="dim")
            self._console.print(
                Panel(
                    body,
                    title=f"[bold cyan]Phase {phase} Start[/bold cyan]",
                    border_style="cyan",
                    expand=False,
                )
            )
            return
        self._print_plain(
            (
                f"PHASE_START phase={phase} run_id={self.run_id} phase_dir={phase_dir.resolve()} "
                f"inventory={inventory} partitions={partitions} provider={provider} model={model_id} "
                f"workers={workers} routing_policy={routing_policy} "
                f"tier_defaults={json.dumps(tier_defaults or {}, sort_keys=True)} flags={flags}"
            )
        )
        self._print_plain(
            (
                f"PHASE_PLAN phase={phase} lanes={json.dumps(tier_defaults or {}, sort_keys=True)} "
                "status_chips=PASS:green,WARN:yellow,FAIL:red,RUNNING:cyan"
            )
        )

    def phase_inputs_provenance(
        self,
        phase: str,
        inventory_meta: Dict[str, Any],
        partitions_meta: Dict[str, Any],
    ) -> None:
        self._emit_event(
            {
                "type": "phase_inputs_provenance",
                "phase": phase,
                "inventory": inventory_meta,
                "partitions": partitions_meta,
            }
        )
        if self.cfg.quiet:
            return
        inv_size = int(inventory_meta.get("size", 0))
        part_size = int(partitions_meta.get("size", 0))
        if self._rich and self._console is not None:
            self._console.print(
                f"inputs_written phase={phase} inventory_bytes={inv_size} partitions_bytes={part_size}"
            )
            return
        self._print_plain(
            f"PHASE_INPUTS phase={phase} inventory_bytes={inv_size} partitions_bytes={part_size}"
        )

    def step_start(
        self,
        phase: str,
        step_id: str,
        prompt_path: Path,
        outputs: Tuple[str, ...],
        partitions_total: int,
        provider: str,
        model_id: str,
        step_tier: str = "extract",
        routing_policy: str = DEFAULT_ROUTING_POLICY,
    ) -> None:
        self._emit_event(
            {
                "type": "step_start",
                "phase": phase,
                "step": step_id,
                "prompt": str(prompt_path.resolve()),
                "outputs": list(outputs),
                "partitions_total": partitions_total,
                "provider": provider,
                "model_id": model_id,
                "step_tier": step_tier,
                "routing_policy": routing_policy,
            }
        )
        if self.cfg.quiet:
            return
        if self._rich and self._console is not None and TextColumn is not None:
            self.step_progress_stop()
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TextColumn(
                    "ok={task.fields[ok]} fail={task.fields[failed]} skip={task.fields[skipped]} "
                    "retry={task.fields[retried]} esc={task.fields[escalated]} "
                    "repair={task.fields[repair]} sidefill={task.fields[sidefill]} "
                    "soft_gate={task.fields[soft_gate]}"
                ),
                console=self._console,
                transient=True,
            )
            self._progress.start()
            self._progress_total = max(0, int(partitions_total))
            total = max(1, self._progress_total)
            self._task_id = self._progress.add_task(
                f"{phase}:{step_id} [{step_tier}] {provider}/{model_id}",
                total=total,
                ok=0,
                failed=0,
                skipped=0,
                retried=0,
                escalated=0,
                repair=0,
                sidefill=0,
                soft_gate=0,
            )
            return
        self._print_plain(
            (
                f"STEP_START phase={phase} step={step_id} partitions={partitions_total} "
                f"prompt={prompt_path.name} outputs={list(outputs)} tier={step_tier} "
                f"provider={provider} model={model_id} routing_policy={routing_policy}"
            )
        )

    def escalation_event(
        self,
        phase: str,
        step_id: str,
        partition_id: str,
        reason: str,
        from_route: str,
        to_route: str,
        hop: int,
    ) -> None:
        self._emit_event(
            {
                "type": "escalation",
                "phase": phase,
                "step": step_id,
                "partition_id": partition_id,
                "reason": reason,
                "from_route": from_route,
                "to_route": to_route,
                "hop": hop,
            }
        )
        if self.cfg.quiet:
            return
        if self._rich and self._console is not None:
            self._console.print(
                f"  [bold yellow]🔀 ESCALATE[/bold yellow] "
                f"[dim]{phase}:{step_id} {partition_id}[/dim] "
                f"hop=[bold]{hop}[/bold] "
                f"[bold red]{from_route}[/bold red] [bold]→[/bold] "
                f"[bold cyan]{to_route}[/bold cyan] "
                f"reason=[italic yellow]{reason}[/italic yellow]"
            )
            return
        self._summary_line(
            f"ESCALATE phase={phase} step={step_id} partition={partition_id} "
            f"reason={reason} from={from_route} to={to_route} hop={hop}"
        )

    def batch_event(
        self,
        phase: str,
        step_id: str,
        status: str,
        provider: str,
        details: str = "",
    ) -> None:
        self._emit_event(
            {
                "type": "batch",
                "phase": phase,
                "step": step_id,
                "status": status,
                "provider": provider,
                "details": details,
            }
        )
        if self.cfg.quiet:
            return
        suffix = f" {details}" if details else ""
        self._summary_line(
            f"BATCH phase={phase} step={step_id} status={status} provider={provider}{suffix}"
        )

    def partition_result(
        self,
        phase: str,
        step_id: str,
        completed: int,
        total: int,
        ok: int,
        failed: int,
        skipped: int,
        retried: int,
        escalated: int = 0,
        repair: int = 0,
        sidefill: int = 0,
        soft_gate: int = 0,
    ) -> None:
        self._emit_event(
            {
                "type": "partition_result",
                "phase": phase,
                "step": step_id,
                "completed": completed,
                "total": total,
                "ok": ok,
                "failed": failed,
                "skipped": skipped,
                "retried": retried,
                "escalated": escalated,
                "repair": repair,
                "sidefill": sidefill,
                "soft_gate": soft_gate,
            }
        )
        if self.cfg.quiet:
            return
        if self._rich and self._progress is not None and self._task_id is not None:
            bounded_total = max(1, total)
            self._progress.update(self._task_id, total=bounded_total)
            self._progress.update(
                self._task_id,
                completed=min(completed, bounded_total),
                ok=ok,
                failed=failed,
                skipped=skipped,
                retried=retried,
                escalated=escalated,
                repair=repair,
                sidefill=sidefill,
                soft_gate=soft_gate,
            )

    def step_heartbeat(
        self,
        *,
        phase: str,
        step_id: str,
        completed: int,
        total: int,
        ok: int,
        failed: int,
        skipped: int,
        retried: int,
        escalated: int,
        repair: int,
        sidefill: int,
        soft_gate: int,
    ) -> None:
        ratio_bar = self._ratio_bar(ok, max(1, completed - skipped))
        self._emit_event(
            {
                "type": "step_heartbeat",
                "phase": phase,
                "step": step_id,
                "completed": int(completed),
                "total": int(total),
                "ok": int(ok),
                "failed": int(failed),
                "skipped": int(skipped),
                "retried": int(retried),
                "escalated": int(escalated),
                "repair": int(repair),
                "sidefill": int(sidefill),
                "soft_gate": int(soft_gate),
                "ratio_bar": ratio_bar,
            }
        )
        if self.cfg.quiet:
            return
        line = (
            f"STEP_HEARTBEAT phase={phase} step={step_id} completed={completed}/{total} "
            f"ok={ok} failed={failed} skipped={skipped} retry={retried} "
            f"escalated={escalated} repair={repair} sidefill={sidefill} soft_gate={soft_gate} "
            f"ratio={ratio_bar}"
        )
        if self._rich and self._console is not None:
            self._console.print(f"[bold cyan]{line}[/bold cyan]")
            return
        self._summary_line(line)

    def failure_spotlight(
        self,
        *,
        phase: str,
        step_id: str,
        partition_id: str,
        failure_class: str,
        reason: str,
        route: str,
        artifact_name: Optional[str] = None,
        item_key: Optional[str] = None,
        item_id: Optional[str] = None,
        item_path: Optional[str] = None,
        retry_trace: Optional[List[Dict[str, Any]]] = None,
        mode: str = "full",
    ) -> None:
        event_payload = {
            "type": "step_failure_spotlight",
            "phase": phase,
            "step": step_id,
            "partition_id": partition_id,
            "failure_class": str(failure_class or "").strip(),
            "reason": str(reason or "").strip(),
            "route": str(route or "").strip(),
            "artifact_name": str(artifact_name or "").strip() or None,
            "item_key": str(item_key or "").strip() or None,
            "item_id": str(item_id or "").strip() or None,
            "item_path": str(item_path or "").strip() or None,
            "retry_trace": retry_trace or [],
            "mode": str(mode or "full").strip().lower(),
        }
        self._emit_event(event_payload)
        line = (
            f"STEP_FAILURE phase={phase} step={step_id} partition={partition_id} "
            f"class={failure_class or '-'} reason={reason or '-'} route={route or '-'} "
            f"artifact={artifact_name or '-'} key={item_key or '-'} item_id={item_id or '-'} "
            f"item_path={item_path or '-'} mode={event_payload['mode']}"
        )
        if self._rich and self._console is not None:
            style = "bold red" if event_payload["mode"] == "full" else "red"
            self._console.print(f"[{style}]{line}[/{style}]")
            # If retry trace is available on the event payload, dump it
            retry_trace = event_payload.get("retry_trace")
            if isinstance(retry_trace, list) and len(retry_trace) > 1:
                self._console.print(
                    f"    [dim]retry trace ({len(retry_trace)} attempts):[/dim]"
                )
                for i, tr in enumerate(retry_trace, start=1):
                    sc = tr.get("status_code", "-")
                    ft = tr.get("failure_type", "-")
                    ds = tr.get("delay_seconds")
                    delay_str = f" → wait {ds:.1f}s" if ds is not None else ""
                    self._console.print(
                        f"    [dim]  [{i}] status={sc} type=[italic red]{ft}[/italic red]{delay_str}[/dim]"
                    )
            return
        self._summary_line(line)

    def soft_gate_event(
        self,
        *,
        phase: str,
        step_id: str,
        status: str,
        attempted_llm_partitions: int,
        resume_success_skips: int,
        deterministic_input_skips: int,
        n_total: int,
        fail_rate: float,
        failed_partitions: int,
        action: str,
        fallback_route: Optional[str] = None,
        remaining_failed: Optional[int] = None,
    ) -> None:
        status_token = str(status or "").strip().lower()
        event_type_map = {
            "triggered": "soft_gate_triggered",
            "fallback_started": "strict_fallback_batch_started",
            "fallback_done": "strict_fallback_batch_done",
        }
        event_type = event_type_map.get(status_token)
        if event_type is None:
            logging.getLogger(__name__).warning(
                "soft_gate_event: unknown status %r for phase=%s step=%s; emitting soft_gate_triggered",
                status_token,
                phase,
                step_id,
            )
            event_type = "soft_gate_triggered"
        payload = {
            "type": event_type,
            "phase": phase,
            "step": step_id,
            "status": status_token,
            "attempted_llm_partitions": int(attempted_llm_partitions),
            "resume_success_skips": int(resume_success_skips),
            "deterministic_input_skips": int(deterministic_input_skips),
            "n_total": int(n_total),
            "fail_rate": float(fail_rate),
            "failed_partitions": int(failed_partitions),
            "action": str(action or "").strip(),
            "fallback_route": str(fallback_route or "").strip() or None,
            "remaining_failed": (
                int(remaining_failed)
                if remaining_failed is not None
                else None
            ),
        }
        self._emit_event(payload)
        line = (
            f"SOFT_GATE phase={phase} step={step_id} status={status_token} action={action} "
            f"attempted={attempted_llm_partitions} resume_skips={resume_success_skips} "
            f"input_skips={deterministic_input_skips} n_total={n_total} fail_rate={fail_rate:.4f} "
            f"failed={failed_partitions} fallback={fallback_route or '-'} "
            f"remaining_failed={remaining_failed if remaining_failed is not None else '-'}"
        )
        if self._rich and self._console is not None:
            self._console.print(f"[bold yellow]{line}[/bold yellow]")
            return
        self._summary_line(line)

    def step_top_failures(
        self,
        *,
        phase: str,
        step_id: str,
        failure_histogram: Dict[str, int],
        limit: int = 3,
    ) -> None:
        ordered = sorted(
            (
                (str(key), int(value))
                for key, value in (failure_histogram or {}).items()
                if int(value) > 0
            ),
            key=lambda row: (-row[1], row[0]),
        )[: max(1, int(limit))]
        self._emit_event(
            {
                "type": "step_top_failures",
                "phase": phase,
                "step": step_id,
                "top_failures": [
                    {"failure_class": name, "count": count} for name, count in ordered
                ],
            }
        )
        if not ordered:
            return
        rendered = ",".join(f"{name}:{count}" for name, count in ordered)
        self._summary_line(
            f"STEP_TOP_FAILURES phase={phase} step={step_id} top={rendered}"
        )

    def run_dashboard_snapshot(
        self, payload: Dict[str, Any], source: str = "phase"
    ) -> None:
        summary = payload.get("summary") if isinstance(payload, dict) else {}
        self._emit_event(
            {
                "type": "run_dashboard_snapshot",
                "source": source,
                "summary": dict(summary) if isinstance(summary, dict) else {},
            }
        )
        if self.cfg.quiet:
            return
        if not isinstance(summary, dict):
            summary = {}
        line = (
            f"RUN_DASHBOARD source={source} PASS={int(summary.get('PASS', 0))} "
            f"FAIL={int(summary.get('FAIL', 0))} IN_PROGRESS={int(summary.get('IN_PROGRESS', 0))} "
            f"NOT_STARTED={int(summary.get('NOT_STARTED', 0))}"
        )
        if self._rich and self._console is not None:
            self._console.print(f"[bold cyan]{line}[/bold cyan]")
            return
        self._summary_line(line)

    def step_done(
        self,
        phase: str,
        step_id: str,
        partitions_total: int,
        ok: int,
        failed: int,
        retries: int,
        skipped: int,
        elapsed_ms: int,
        norm_written: int,
        qa_file: str,
        hop_distribution: Optional[Dict[str, int]] = None,
        escalated_partitions: int = 0,
        execution_mode_counts: Optional[Dict[str, int]] = None,
        final_route_counts: Optional[Dict[str, int]] = None,
        repair_invocations: int = 0,
        repair_successes: int = 0,
        sidefill_invocations: int = 0,
        sidefill_dropped_rows: int = 0,
        soft_gate_invocations: int = 0,
        failure_histogram: Optional[Dict[str, int]] = None,
    ) -> None:
        self.step_progress_stop()
        processed_partitions = max(0, int(partitions_total) - int(skipped))
        throughput_per_min = (
            (float(processed_partitions) * 60000.0) / float(max(1, elapsed_ms))
            if processed_partitions > 0
            else 0.0
        )
        self._emit_event(
            {
                "type": "step_done",
                "phase": phase,
                "step": step_id,
                "partitions_total": partitions_total,
                "ok": ok,
                "failed": failed,
                "retries": retries,
                "skipped": skipped,
                "elapsed_ms": elapsed_ms,
                "norm_written": norm_written,
                "qa_file": qa_file,
                "hop_distribution": dict(hop_distribution or {}),
                "escalated_partitions": int(escalated_partitions),
                "execution_mode_counts": dict(execution_mode_counts or {}),
                "final_route_counts": dict(final_route_counts or {}),
                "repair_invocations": int(repair_invocations),
                "repair_successes": int(repair_successes),
                "sidefill_invocations": int(sidefill_invocations),
                "sidefill_dropped_rows": int(sidefill_dropped_rows),
                "soft_gate_invocations": int(soft_gate_invocations),
                "throughput_partitions_per_min": round(throughput_per_min, 3),
            }
        )
        self._summary_line(
            (
                f"STEP_DONE phase={phase} step={step_id} ok={ok} failed={failed} "
                f"retries={retries} skipped={skipped} elapsed_ms={elapsed_ms} "
                f"norm_written={norm_written} qa_file={qa_file} "
                f"throughput_partitions_per_min={throughput_per_min:.2f} "
                f"hops={json.dumps(hop_distribution or {}, sort_keys=True)} "
                f"escalated={escalated_partitions} "
                f"repair_invocations={int(repair_invocations)} "
                f"repair_successes={int(repair_successes)} "
                f"sidefill_invocations={int(sidefill_invocations)} "
                f"sidefill_dropped_rows={int(sidefill_dropped_rows)} "
                f"soft_gate_invocations={int(soft_gate_invocations)} "
                f"exec_mode={json.dumps(execution_mode_counts or {}, sort_keys=True)} "
                f"routes={json.dumps(final_route_counts or {}, sort_keys=True)}"
            )
        )
        if self._rich and self._console is not None:
            self._console.print(
                f"[bold cyan]STEP_METRICS[/bold cyan] {phase}:{step_id} "
                f"{self._ratio_bar(ok, max(0, partitions_total - skipped))} "
                f"elapsed={elapsed_ms}ms escalated={escalated_partitions} "
                f"throughput={throughput_per_min:.2f}/min"
            )
        self.step_top_failures(
            phase=phase,
            step_id=step_id,
            failure_histogram=(failure_histogram or {}),
            limit=3,
        )

    def phase_done(
        self,
        phase: str,
        status: str,
        raw_ok: int,
        raw_failed: int,
        raw_total: int,
        norm_count: int,
        qa_count: int,
        phase_dir: Path,
    ) -> None:
        self.step_progress_stop()
        self._emit_event(
            {
                "type": "phase_done",
                "phase": phase,
                "status": status,
                "raw_ok": raw_ok,
                "raw_failed": raw_failed,
                "raw_total": raw_total,
                "norm_count": norm_count,
                "qa_count": qa_count,
                "phase_dir": str(phase_dir.resolve()),
            }
        )
        self._summary_line(
            (
                f"PHASE_DONE phase={phase} status={status} raw_ok={raw_ok} raw_failed={raw_failed} "
                f"raw_total={raw_total} norm={norm_count} qa={qa_count} phase_dir={phase_dir.resolve()}"
            )
        )
        if self._rich and self._console is not None:
            self._console.print(
                f"[{self._status_style(status)}]PHASE {phase} {status}[/{self._status_style(status)}] "
                f"{self._ratio_bar(raw_ok, raw_total)} norm={norm_count} qa={qa_count}"
            )

    def verify_result(
        self,
        phase: str,
        status: str,
        counts: Dict[str, Any],
        reasons: List[str],
        phase_dir: Path,
    ) -> None:
        self._emit_event(
            {
                "type": "verify_result",
                "phase": phase,
                "status": status,
                "counts": counts,
                "reasons": reasons,
                "phase_dir": str(phase_dir.resolve()),
            }
        )

    def status_table(self, payload: Dict[str, Any], clear: bool = False) -> None:
        self._emit_event({"type": "status_snapshot", "payload": payload})
        if self._rich and Table is not None and self._console is not None:
            if clear:
                self._console.clear()
            summary = payload.get("summary", {})
            self._console.print(
                (
                    f"run={payload.get('run_id')} run_dir={payload.get('run_dir')} "
                    f"PASS={summary.get('PASS', 0)} FAIL={summary.get('FAIL', 0)} "
                    f"IN_PROGRESS={summary.get('IN_PROGRESS', 0)} NOT_STARTED={summary.get('NOT_STARTED', 0)}"
                )
            )
            table = Table(show_header=True, header_style="bold")
            table.add_column("Phase")
            table.add_column("Status")
            table.add_column("Inputs")
            table.add_column("Raw (ok/failed/total)")
            table.add_column("Norm")
            table.add_column("QA")
            table.add_column("Last Modified (UTC)")
            table.add_column("Phase Dir")
            for phase in PHASES:
                row = payload.get("phases", {}).get(phase, {})
                status_value = str(row.get("status", "UNKNOWN"))
                row_style = None
                if status_value == "PASS":
                    row_style = "green"
                elif status_value == "FAIL":
                    row_style = "red"
                elif status_value == "IN_PROGRESS":
                    row_style = "yellow"
                table.add_row(
                    phase,
                    status_value,
                    str(row.get("inputs_count", 0)),
                    f"{row.get('raw_ok', 0)}/{row.get('raw_failed_sidecars', 0)}/{row.get('raw_total', 0)}",
                    str(row.get("norm_count", 0)),
                    str(row.get("qa_count", 0)),
                    str(row.get("last_modified") or "-"),
                    str(row.get("phase_dir") or "-"),
                    style=row_style,
                )
            self._console.print(table)
            return

        if clear and self._stdout_is_tty:
            self._print_plain("\033[2J\033[H")
        summary = payload.get("summary", {})
        self._print_plain(
            (
                f"run={payload.get('run_id')} run_dir={payload.get('run_dir')} "
                f"PASS={summary.get('PASS', 0)} FAIL={summary.get('FAIL', 0)} "
                f"IN_PROGRESS={summary.get('IN_PROGRESS', 0)} NOT_STARTED={summary.get('NOT_STARTED', 0)}"
            )
        )
        self._print_plain(
            "phase status inputs raw_ok raw_failed raw_total norm qa last_modified_utc phase_dir"
        )
        for phase in PHASES:
            row = payload.get("phases", {}).get(phase, {})
            self._print_plain(
                (
                    f"{phase} {row.get('status', 'UNKNOWN')} {row.get('inputs_count', 0)} "
                    f"{row.get('raw_ok', 0)} {row.get('raw_failed_sidecars', 0)} {row.get('raw_total', 0)} "
                    f"{row.get('norm_count', 0)} {row.get('qa_count', 0)} {row.get('last_modified') or '-'} "
                    f"{row.get('phase_dir') or '-'}"
                )
            )
