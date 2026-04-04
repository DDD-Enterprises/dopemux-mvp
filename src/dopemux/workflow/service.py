"""Persistence and orchestration helpers for Dopemux workflow runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.error import URLError
from urllib.request import urlopen

from .models import (
    DEFAULT_COMPLETION_TOKEN,
    WorkflowPhase,
    WorkflowState,
    WorkflowStatus,
    WorkflowTask,
    parse_workflow_checkpoint,
    utc_now_iso,
    validate_phase_entry,
)


_IGNORED_BRIEF_NAMES = {
    "readme.md",
    "index.md",
    "status.md",
    "template_task_packet.md",
    "checklist.md",
}


@dataclass(frozen=True)
class WorkspaceContext:
    """Resolved paths for the current workflow execution context."""

    family_root: Path
    active_workspace: Path
    instance_id: str


class WorkflowKernel:
    """Create, resolve, and mutate workflow runs stored in `.dopemux/workflows`."""

    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = (cwd or Path.cwd()).resolve()
        self.context = self.discover_workspace_context(self.cwd)

    @staticmethod
    def _git_output(args: List[str], cwd: Path) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None

        if result.returncode != 0:
            return None
        return result.stdout.strip() or None

    @classmethod
    def discover_workspace_context(cls, cwd: Path) -> WorkspaceContext:
        """Resolve the workflow storage root and active workspace."""
        active_workspace = Path(
            os.environ.get("DOPEMUX_WORKSPACE_ROOT")
            or cls._git_output(["rev-parse", "--show-toplevel"], cwd)
            or cwd
        ).resolve()

        if os.environ.get("DOPEMUX_WORKSPACE_ROOT"):
            return WorkspaceContext(
                family_root=active_workspace,
                active_workspace=active_workspace,
                instance_id=os.environ.get("DOPEMUX_INSTANCE_ID") or "A"
            )

        family_root = active_workspace
        env_main_repo = os.environ.get("DOPEMUX_MAIN_REPO")
        if env_main_repo:
            family_root = Path(env_main_repo).resolve()
        else:
            common_dir = cls._git_output(["rev-parse", "--git-common-dir"], cwd)
            if common_dir:
                common_path = Path(common_dir)
                if not common_path.is_absolute():
                    common_path = (active_workspace / common_path).resolve()
                if common_path.name == ".git":
                    family_root = common_path.parent.resolve()

        instance_id = os.environ.get("DOPEMUX_INSTANCE_ID") or "A"
        return WorkspaceContext(
            family_root=family_root,
            active_workspace=active_workspace,
            instance_id=instance_id,
        )

    @property
    def store_root(self) -> Path:
        root = self.context.family_root / ".dopemux" / "workflows"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def workflow_dir(self, workflow_id: str) -> Path:
        path = self.store_root / workflow_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def state_path(self, workflow_id: str) -> Path:
        return self.workflow_dir(workflow_id) / "state.json"

    @staticmethod
    def _safe_write_json(path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            delete=False,
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
        ) as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            tmp_path = Path(handle.name)
        tmp_path.replace(path)

    @staticmethod
    def _slugify(value: str) -> str:
        lowered = value.strip().lower()
        if not lowered:
            return "workflow"
        return re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")[:48] or "workflow"

    def list_states(self) -> List[WorkflowState]:
        states: List[WorkflowState] = []
        for state_path in self.store_root.glob("*/state.json"):
            try:
                payload = json.loads(state_path.read_text(encoding="utf-8"))
                states.append(WorkflowState.from_dict(payload))
            except (json.JSONDecodeError, OSError, KeyError, ValueError, TypeError):
                continue
        return states

    def save(self, state: WorkflowState) -> WorkflowState:
        state.updated_at = utc_now_iso()
        self._safe_write_json(self.state_path(state.workflow_id), state.to_dict())
        return state

    def load(self, workflow_id: str) -> WorkflowState:
        payload = json.loads(self.state_path(workflow_id).read_text(encoding="utf-8"))
        return WorkflowState.from_dict(payload)

    def create_or_resume(self, *, prompt: Optional[str] = None, force_new: bool = False, **kwargs) -> WorkflowState:
        """Create a new workflow or resume the active one."""
        existing = self.resolve(kwargs.get("workflow_id"))
        if existing and existing.status == WorkflowStatus.ACTIVE and not force_new:
            return existing
        state = self.init_workflow(prompt=prompt, force_new=force_new)
        for k, v in kwargs.items():
            if hasattr(state, k):
                setattr(state, k, v)
        return self.save(state)

    def resolve(self, workflow_id: Optional[str] = None) -> Optional[WorkflowState]:
        """Resolve a workflow by id or by current cwd ancestry and instance."""
        if workflow_id:
            path = self.state_path(workflow_id)
            if path.exists():
                return self.load(workflow_id)
            return None

        best: Optional[Tuple[int, str, WorkflowState]] = None
        current_path = self.cwd.resolve()
        for state in self.list_states():
            score = 0
            workspace_root = Path(state.workspace_root).resolve()
            family_root = Path(state.workspace_family_root or state.workspace_root).resolve()
            active_workspace = Path(state.active_workspace or state.workspace_root).resolve()

            if current_path == active_workspace or current_path.is_relative_to(active_workspace):
                score += 50
            elif current_path == family_root or current_path.is_relative_to(family_root):
                score += 25
            elif current_path == workspace_root or current_path.is_relative_to(workspace_root):
                score += 15

            if state.instance_id == self.context.instance_id:
                score += 100
            if state.status == WorkflowStatus.ACTIVE:
                score += 10

            recency = state.updated_at
            if best is None or (score, recency) > (best[0], best[1]):
                best = (score, recency, state)

        return best[2] if best and best[0] > 0 else None

    def _discover_brief_artifact(self) -> Tuple[Optional[str], Optional[Path]]:
        candidates: List[Path] = []
        patterns = [
            "task-packets/**/*.md",
            "docs/task-packets/**/*.md",
            "docs/**/task-packets/**/*.md",
        ]
        for pattern in patterns:
            candidates.extend(self.context.family_root.glob(pattern))

        candidates = [
            path for path in candidates
            if path.is_file() and path.name.lower() not in _IGNORED_BRIEF_NAMES
        ]
        if not candidates:
            return None, None

        latest = max(candidates, key=lambda item: item.stat().st_mtime)
        return "task-packet", latest

    def _create_local_brief(self, workflow_dir: Path, prompt: Optional[str]) -> Path:
        brief_path = workflow_dir / "brief.md"
        title = ((prompt or "").strip()).splitlines()[0] if ((prompt or "").strip()) else "Internal Workflow Brief"
        content = "\n".join(
            [
                "---",
                f"id: {self._slugify(title)}",
                f"title: {title}",
                "type: brief",
                "prelude: Automatic local workflow brief.",
                "---",
                "# ━━━◆ Ø ◆━━━",
                "",
                f"# {title}",
                "",
                "## Summary",
                ((prompt or "").strip()) or "Local workflow brief created because no task packet or external brief was detected.",
                "",
                "## Source",
                "- Origin: local workflow kit",
                "- Authority: temporary local brief until PM authority is available",
                "",
                "## Next Step",
                "- Move into `breakdown` with explicit local task mirrors.",
                "",
            ]
        )
        brief_path.write_text(content, encoding="utf-8")
        return brief_path

    @staticmethod
    def _parse_title_from_brief(path: Path, fallback: str) -> str:
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("#"):
                    return line.lstrip("#").strip() or fallback
        except OSError:
            pass
        return fallback

    def probe_pm_authority(self) -> Dict[str, Any]:
        """Best-effort task-orchestrator availability probe."""
        base_url = os.environ.get("DOPEMUX_WORKFLOW_API_URL", "http://localhost:8000").rstrip("/")
        for candidate in ("/health", "/api/health"):
            try:
                with urlopen(f"{base_url}{candidate}", timeout=2) as response:
                    if 200 <= getattr(response, "status", 200) < 300:
                        return {
                            "authority": "task-orchestrator",
                            "reachable": True,
                            "url": base_url,
                            "health_path": candidate,
                        }
            except URLError:
                continue
            except Exception:
                continue
        return {
            "authority": "local-mirror",
            "reachable": False,
            "url": base_url,
        }

    def _create_initial_task(self, workflow_dir: Path, *, title: str, summary: str, authority: str, source_artifact: Optional[Path]) -> WorkflowTask:
        task_id = "task-001"
        artifact_dir = workflow_dir / "tasks" / task_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return WorkflowTask(
            task_id=task_id,
            title=title,
            summary=summary,
            authority=authority,
            source_artifact=str(source_artifact) if source_artifact else None,
            artifact_dir=str(artifact_dir),
        )

    def init_workflow(
        self,
        *,
        prompt: Optional[str],
        mode: str = "manager",
        max_iterations: int = 0,
        max_minutes: int = 0,
        completion_token: str = DEFAULT_COMPLETION_TOKEN,
        force_new: bool = False,
    ) -> WorkflowState:
        existing = self.resolve()
        if existing and existing.status == WorkflowStatus.ACTIVE and not force_new:
            return existing

        slug_source = prompt or self.cwd.name or "workflow"
        workflow_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{self._slugify(slug_source)}"
        workflow_dir = self.workflow_dir(workflow_id)
        brief_source, brief_path = self._discover_brief_artifact()
        if brief_path is None:
            brief_path = self._create_local_brief(workflow_dir, prompt)
            brief_source = "local-brief"

        pm_probe = self.probe_pm_authority()
        title = self._parse_title_from_brief(brief_path, "Workflow Task")
        task = self._create_initial_task(
            workflow_dir,
            title=title,
            summary=((prompt or "").strip()) or f"Execute workflow for {title}",
            authority=pm_probe["authority"],
            source_artifact=brief_path,
        )

        now = utc_now_iso()
        state = WorkflowState(
            workflow_id=workflow_id,
            workspace_root=str(self.context.family_root),
            instance_id=self.context.instance_id,
            mode=mode,
            phase=WorkflowPhase.BRIEF,
            current_task_id=task.task_id,
            iteration=0,
            max_iterations=max_iterations,
            max_minutes=max_minutes,
            completion_token=completion_token or DEFAULT_COMPLETION_TOKEN,
            started_at=now,
            updated_at=now,
            status=WorkflowStatus.ACTIVE,
            active_workspace=str(self.context.active_workspace),
            workspace_family_root=str(self.context.family_root),
            brief_source=brief_source,
            brief_path=str(brief_path),
            pm_authority=pm_probe["authority"],
            pm_reachable=bool(pm_probe["reachable"]),
            tasks=[task],
        )
        state.record_history(
            event="workflow.init",
            message="Workflow initialized.",
            details={
                "brief_source": brief_source,
                "brief_path": str(brief_path),
                "pm_authority": pm_probe["authority"],
                "pm_reachable": pm_probe["reachable"],
            },
        )
        return self.save(state)

    def resume(self, workflow_id: Optional[str] = None) -> Optional[WorkflowState]:
        state = self.resolve(workflow_id)
        if not state:
            return None
        state.active_workspace = str(self.context.active_workspace)
        if state.instance_id != self.context.instance_id:
            state.record_history(
                event="workflow.rebind",
                message=f"Workflow rebound from instance {state.instance_id} to {self.context.instance_id}.",
                details={
                    "previous_instance_id": state.instance_id,
                    "new_instance_id": self.context.instance_id,
                },
            )
            state.instance_id = self.context.instance_id
        state.status = WorkflowStatus.ACTIVE
        return self.save(state)

    def cancel(self, workflow_id: Optional[str] = None) -> Optional[WorkflowState]:
        state = self.resolve(workflow_id)
        if not state:
            return None
        state.status = WorkflowStatus.CANCELLED
        state.record_history(event="workflow.cancel", message="Workflow cancelled.")
        return self.save(state)

    def record_tool_event(
        self,
        state: WorkflowState,
        *,
        event_name: str,
        tool_name: Optional[str],
        status: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> WorkflowState:
        state.record_history(
            event=f"tool.{event_name.lower()}",
            message=f"{tool_name or 'unknown tool'} {status}",
            details=payload or {},
        )
        return self.save(state)

    def apply_response_text(self, state: WorkflowState, response_text: str) -> WorkflowState:
        checkpoint = parse_workflow_checkpoint(response_text)
        if checkpoint:
            state.add_checkpoint(checkpoint)
            current_task = state.current_task()
            if current_task and checkpoint.status.value in {"complete", "approved"} and checkpoint.phase in {
                WorkflowPhase.REFACTOR,
                WorkflowPhase.COMPLETE,
            }:
                current_task.status = "done"
            return self.save(state)
        if state.completion_token and state.completion_token in response_text:
            state.status = WorkflowStatus.COMPLETE
            state.phase = WorkflowPhase.COMPLETE
            state.record_history(
                event="workflow.complete",
                message="Completion token observed in model response.",
            )
            return self.save(state)
        return state

    def inspection(self, state: WorkflowState) -> Dict[str, Any]:
        task = state.current_task()
        gate_failures = validate_phase_entry(state, state.phase)
        task_presence = {}
        if task:
            from .models import task_artifact_presence
            task_presence = task_artifact_presence(task)
        return {
            "workflow_id": state.workflow_id,
            "phase": state.phase.value,
            "status": state.status.value,
            "workspace_root": state.workspace_root,
            "active_workspace": state.active_workspace,
            "current_task_id": state.current_task_id,
            "task_title": task.title if task else None,
            "task_status": task.status if task else None,
            "pm_authority": state.pm_authority,
            "pm_reachable": state.pm_reachable,
            "brief_path": state.brief_path,
            "gate_failures": gate_failures,
            "required_artifacts": task_presence,
            "history_count": len(state.history),
            "checkpoint_count": len(state.checkpoints),
        }
