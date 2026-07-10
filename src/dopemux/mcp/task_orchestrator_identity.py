"""Task Orchestrator fixed-port project identity probing (Packet 005).

Port :7890 listening is never proof of project ownership. Identity is proven
via HTTP /info, Docker labels, runtime registry, and wrapper metadata —
fail-closed on wrong-project or unknown for start.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence  # Mapping used by heuristics

DEFAULT_TO_PORT = 7890
METADATA_FILENAME = "task-orchestrator.identity.json"
SCHEMA_VERSION = "1.0"


@dataclass
class TOIdentity:
    service: str = "task-orchestrator"
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_root: Optional[str] = None
    worktree_root: Optional[str] = None
    project_hash: Optional[str] = None
    worktree_hash: Optional[str] = None
    instance_id: Optional[str] = None
    state_scope: str = "per-repo"
    runtime_scope: str = "project"
    port: int = DEFAULT_TO_PORT
    source: str = "unknown"  # http_info|docker_labels|registry|wrapper_metadata|unknown
    confidence: str = "UNKNOWN"  # HIGH|MEDIUM|LOW|UNKNOWN
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service": self.service,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "project_root": self.project_root,
            "worktree_root": self.worktree_root,
            "project_hash": self.project_hash,
            "worktree_hash": self.worktree_hash,
            "instance_id": self.instance_id,
            "state_scope": self.state_scope,
            "runtime_scope": self.runtime_scope,
            "port": self.port,
            "source": self.source,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
        }

    def has_project_proof(self) -> bool:
        return bool(self.project_root or self.project_id)


def _norm_path(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    try:
        return str(Path(value).expanduser().resolve())
    except Exception:  # noqa: BLE001
        return str(value).rstrip("/")


def _paths_equal(a: Optional[str], b: Optional[str]) -> bool:
    na, nb = _norm_path(a), _norm_path(b)
    if na is None or nb is None:
        return False
    return na == nb


def _ids_equal(a: Optional[str], b: Optional[str]) -> bool:
    if a is None or b is None:
        return False
    return str(a).strip().lower() == str(b).strip().lower()


def _normalize_project_id(value: Optional[str]) -> Optional[str]:
    """Deterministic project_id normalization for match_target.

    - lower-case
    - hyphen → underscore
    - strip a trailing generated hash suffix when the form is
      ``<slug>[-_]<hex8+>`` (e.g. ``dnh_crm-9a4e9aa8a329cdd5``)

    Does not strip arbitrary free-text suffixes.
    """
    if value is None or value == "":
        return None
    s = str(value).strip().lower().replace("-", "_")
    # slug + 8+ hex hash (worktree/project hash forms used by dopemux)
    m = re.match(r"^(.+)_([0-9a-f]{8,})$", s)
    if m:
        return m.group(1)
    return s


def _ids_match_normalized(a: Optional[str], b: Optional[str]) -> bool:
    na, nb = _normalize_project_id(a), _normalize_project_id(b)
    if na is None or nb is None:
        return False
    return na == nb


def _source_is_heuristic(source: Optional[str]) -> bool:
    s = (source or "").lower()
    if not s or s == "unknown":
        return True
    if s in {
        "container_heuristics",
        "name_slug",
        "data_path_heuristic",
        "container_name_heuristic",
        "port_only",
        "compose_metadata",
    }:
        return True
    return "heuristic" in s


def metadata_dir(instance_id: str, *, base: Optional[Path] = None) -> Path:
    root = base or (Path.home() / ".dopemux" / "mcp" / "runtime")
    return Path(root) / instance_id


def metadata_path(instance_id: str, *, base: Optional[Path] = None) -> Path:
    return metadata_dir(instance_id, base=base) / METADATA_FILENAME


def write_wrapper_metadata(
    identity: TOIdentity,
    *,
    base: Optional[Path] = None,
    dry_run: bool = False,
) -> Optional[Path]:
    """Write non-secret identity metadata. Returns path or None if dry_run/missing id."""
    if dry_run:
        return None
    instance_id = identity.instance_id or identity.worktree_hash or identity.project_hash
    if not instance_id:
        return None
    path = metadata_path(str(instance_id), base=base)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        **identity.to_dict(),
        "source": identity.source if identity.source != "unknown" else "wrapper_metadata",
    }
    # Do not overwrite another project's metadata
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing.get("project_root") and identity.project_root:
                if not _paths_equal(existing.get("project_root"), identity.project_root):
                    raise RuntimeError(
                        f"Refusing to overwrite TO metadata for other project at {path}"
                    )
        except (json.JSONDecodeError, OSError):
            pass
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def probe_wrapper_metadata(
    *,
    instance_id: Optional[str] = None,
    candidates: Optional[Sequence[str]] = None,
    base: Optional[Path] = None,
) -> Optional[TOIdentity]:
    ids: List[str] = []
    if instance_id:
        ids.append(str(instance_id))
    for c in candidates or []:
        if c and c not in ids:
            ids.append(str(c))
    for iid in ids:
        path = metadata_path(iid, base=base)
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        return TOIdentity(
            project_id=data.get("project_id"),
            workspace_id=data.get("workspace_id"),
            project_root=data.get("project_root"),
            worktree_root=data.get("worktree_root"),
            project_hash=data.get("project_hash"),
            worktree_hash=data.get("worktree_hash"),
            instance_id=data.get("instance_id") or iid,
            state_scope=str(data.get("state_scope") or "per-repo"),
            runtime_scope=str(data.get("runtime_scope") or "project"),
            port=int(data.get("port") or DEFAULT_TO_PORT),
            source="wrapper_metadata",
            confidence="HIGH" if data.get("project_root") else "MEDIUM",
            evidence=[str(path)],
        )
    return None


def probe_http_info(
    port: int = DEFAULT_TO_PORT,
    *,
    host: str = "127.0.0.1",
    timeout_s: float = 1.0,
    opener: Optional[Callable[[str], Any]] = None,
) -> Optional[TOIdentity]:
    """Best-effort HTTP identity probe.

    Upstream Kotlin Task Orchestrator does **not** expose generic REST ``/info``
    or ``/health`` (404). Those paths are only used when a FastAPI or other
    stack returns a JSON body with an ``identity`` object. 404/connection errors
    are non-fatal and return None (fall through to labels/metadata).
    """

    def _default_get(url: str) -> Any:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — localhost probe
            return json.loads(resp.read().decode("utf-8"))

    get = opener or _default_get
    for path in ("/info", "/health", "/mcp"):
        url = f"http://{host}:{int(port)}{path}"
        try:
            body = get(url)
        except urllib.error.HTTPError as exc:
            # 404 is expected for upstream jar — do not treat as failure
            if exc.code == 404:
                continue
            continue
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(body, dict):
            continue
        ident = body.get("identity") if isinstance(body.get("identity"), dict) else None
        if not ident and path == "/health":
            meta = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}
            ident = meta.get("identity") if isinstance(meta.get("identity"), dict) else None
        if not ident:
            continue
        return TOIdentity(
            project_id=ident.get("project_id"),
            workspace_id=ident.get("workspace_id"),
            project_root=ident.get("project_root"),
            worktree_root=ident.get("worktree_root"),
            project_hash=ident.get("project_hash"),
            worktree_hash=ident.get("worktree_hash"),
            instance_id=ident.get("instance_id"),
            state_scope=str(ident.get("state_scope") or "single_active_project"),
            runtime_scope=str(ident.get("runtime_scope") or "project"),
            port=int(port),
            source="http_info",
            confidence="HIGH" if ident.get("project_root") or ident.get("project_id") else "LOW",
            evidence=[url],
        )
    return None


def identity_from_container_heuristics(
    *,
    container_name: str,
    labels: Optional[Mapping[str, str]] = None,
    mounts: Optional[Sequence[Mapping[str, Any]]] = None,
    port: int = DEFAULT_TO_PORT,
    target_project_root: Optional[str] = None,
    target_project_id: Optional[str] = None,
) -> TOIdentity:
    """Infer TO identity from container name / data path / compose labels (006R).

    Upstream jar has no /info; wrapper names containers
    ``task-orchestrator-<state_id>`` and mounts project data under a hash path.
    """
    labels = labels or {}
    evidence = [container_name]
    project_root = labels.get("dopemux.project_root") or labels.get("com.dopemux.project_root")
    project_id = labels.get("dopemux.project_id") or labels.get("com.dopemux.project_id")
    instance_id = labels.get("dopemux.instance_id")
    name_l = (container_name or "").lower()

    # Name pattern: task-orchestrator-dnh_crm-9a4e9aa8a329cdd5
    if name_l.startswith("task-orchestrator-") and not instance_id:
        instance_id = container_name[len("task-orchestrator-") :]
        evidence.append(f"name_state_id={instance_id}")

    # Data mount under ~/.local/share/dopemux-mission-control/task-orchestrator/<id>
    if mounts:
        for m in mounts:
            src = str(m.get("Source") or m.get("source") or "")
            if "task-orchestrator" in src and instance_id and instance_id in src:
                evidence.append(f"data_mount={src}")
            if target_project_root and target_project_root.rstrip("/") in src:
                project_root = project_root or target_project_root
                evidence.append("mount_contains_target_root")

    # Slug match from name vs target
    if target_project_root and not project_root:
        slug = Path(target_project_root).name.lower().replace("-", "_")
        slug_compact = slug.replace("_", "")
        if slug in name_l or slug_compact in name_l.replace("_", "").replace("-", ""):
            project_root = target_project_root
            project_id = project_id or Path(target_project_root).name
            evidence.append(f"name_slug_match={slug}")

    conf = "MEDIUM" if project_root or instance_id else "LOW"
    if labels.get("dopemux.project_root"):
        conf = "HIGH"
    return TOIdentity(
        project_id=project_id or target_project_id,
        project_root=project_root,
        instance_id=instance_id,
        port=port,
        source="container_heuristics",
        confidence=conf,
        evidence=evidence,
        state_scope="single_active_project",
        runtime_scope="singleton",
    )


def identity_from_docker_labels(
    labels: Mapping[str, str],
    *,
    port: int = DEFAULT_TO_PORT,
    container_name: Optional[str] = None,
) -> TOIdentity:
    return TOIdentity(
        project_id=labels.get("dopemux.project_id") or labels.get("com.dopemux.project_id"),
        workspace_id=(
            labels.get("dopemux.workspace_id")
            or labels.get("com.dopemux.workspace_id")
            or labels.get("dopemux.worktree_root")
        ),
        project_root=labels.get("dopemux.project_root") or labels.get("com.dopemux.project_root"),
        worktree_root=labels.get("dopemux.worktree_root"),
        project_hash=labels.get("dopemux.project_hash"),
        worktree_hash=labels.get("dopemux.worktree_hash"),
        instance_id=labels.get("dopemux.instance_id"),
        port=port,
        source="docker_labels",
        confidence="HIGH" if labels.get("dopemux.project_root") else "MEDIUM",
        evidence=[container_name or "docker_labels"],
    )


def identity_from_registry_entry(
    entry: Mapping[str, Any],
    *,
    port: int = DEFAULT_TO_PORT,
) -> TOIdentity:
    return TOIdentity(
        project_id=entry.get("project_id"),
        workspace_id=entry.get("workspace_id") or entry.get("worktree_root"),
        project_root=entry.get("project_root"),
        worktree_root=entry.get("worktree_root"),
        project_hash=entry.get("project_hash"),
        worktree_hash=entry.get("worktree_hash"),
        instance_id=entry.get("instance_id"),
        port=int(entry.get("port") or port),
        source="registry",
        confidence="MEDIUM",
        evidence=[f"registry:{entry.get('instance_id') or entry.get('service')}"],
    )


def match_target(
    observed: Optional[TOIdentity],
    *,
    project_id: Optional[str],
    project_root: Optional[str],
) -> str:
    """Return OK | WRONG_PROJECT | UNKNOWN | CONFLICT.

    Fail-closed rules (006R2):
    - explicit root match + explicit ID match => OK
    - explicit root match + explicit ID mismatch => CONFLICT (never OK)
    - heuristic root + ID mismatch => CONFLICT/UNKNOWN (never OK)
    - ID comparison uses deterministic normalization (case/hyphen/hash-suffix)
    - heuristic evidence never outranks an explicit contradictory ID
    """
    if observed is None or not observed.has_project_proof():
        return "UNKNOWN"

    root_ok = (
        _paths_equal(observed.project_root, project_root)
        if observed.project_root and project_root
        else None
    )
    id_ok = (
        _ids_match_normalized(observed.project_id, project_id)
        if observed.project_id and project_id
        else None
    )
    heuristic = _source_is_heuristic(observed.source)

    if root_ok is True and id_ok is True:
        return "OK"
    if root_ok is True and id_ok is False:
        # Explicit (or heuristic) ID conflict must never become OK.
        return "CONFLICT"
    if root_ok is False and id_ok is True:
        return "CONFLICT"
    if root_ok is False and id_ok is False:
        return "WRONG_PROJECT"
    if root_ok is False and id_ok is None:
        return "WRONG_PROJECT"
    if id_ok is False and root_ok is None:
        return "WRONG_PROJECT"
    if root_ok is True and id_ok is None:
        # Root-only: OK only for explicit high-trust sources; heuristics stay UNKNOWN.
        if heuristic:
            return "UNKNOWN"
        return "OK"
    if id_ok is True and root_ok is None:
        return "UNKNOWN"  # id alone insufficient without root when target has root
    return "UNKNOWN"


def _sources_conflict(a: TOIdentity, b: TOIdentity) -> bool:
    if a.project_root and b.project_root and not _paths_equal(a.project_root, b.project_root):
        return True
    if a.project_id and b.project_id and not _ids_equal(a.project_id, b.project_id):
        return True
    return False


def merge_identity_sources(
    sources: Sequence[TOIdentity],
) -> tuple[Optional[TOIdentity], List[Dict[str, Any]]]:
    """Trust order is caller's list order. Conflict → (None, findings)."""
    findings: List[Dict[str, Any]] = []
    proven = [s for s in sources if s and s.has_project_proof()]
    if not proven:
        return (sources[0] if sources else None), findings
    primary = proven[0]
    for other in proven[1:]:
        if _sources_conflict(primary, other):
            findings.append(
                {
                    "code": "TASK_ORCHESTRATOR_RUNTIME_METADATA_CONFLICT",
                    "severity": "FAIL",
                    "message": (
                        f"TO identity conflict: {primary.source} vs {other.source}"
                    ),
                    "evidence": primary.evidence + other.evidence,
                    "primary": primary.to_dict(),
                    "other": other.to_dict(),
                }
            )
            return None, findings
    # Merge fill-missing fields from lower sources
    merged = TOIdentity(**{**primary.to_dict(), "evidence": list(primary.evidence)})
    for other in proven[1:]:
        for field_name in (
            "project_id",
            "workspace_id",
            "project_root",
            "worktree_root",
            "project_hash",
            "worktree_hash",
            "instance_id",
        ):
            if not getattr(merged, field_name) and getattr(other, field_name):
                setattr(merged, field_name, getattr(other, field_name))
        merged.evidence.extend(other.evidence)
    return merged, findings


@dataclass
class TOFixedPortEvaluation:
    """Result of evaluating fixed-port TO ownership for a target project."""

    port: int
    listening: bool
    match: str  # OK | WRONG_PROJECT | UNKNOWN | CONFLICT | FREE
    identity: Optional[TOIdentity]
    findings: List[Dict[str, Any]] = field(default_factory=list)
    start_allowed: bool = False
    start_block_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "port": self.port,
            "listening": self.listening,
            "match": self.match,
            "identity": self.identity.to_dict() if self.identity else None,
            "findings": list(self.findings),
            "start_allowed": self.start_allowed,
            "start_block_code": self.start_block_code,
        }


def evaluate_fixed_port_state(
    *,
    port: int = DEFAULT_TO_PORT,
    target_project_id: Optional[str],
    target_project_root: Optional[str],
    target_workspace_id: Optional[str] = None,
    target_instance_id: Optional[str] = None,
    target_worktree_hash: Optional[str] = None,
    listening: Optional[bool] = None,
    is_free_fn: Optional[Callable[[int], bool]] = None,
    http_identity: Optional[TOIdentity] = None,
    docker_identity: Optional[TOIdentity] = None,
    registry_identity: Optional[TOIdentity] = None,
    wrapper_identity: Optional[TOIdentity] = None,
    skip_http: bool = False,
    metadata_base: Optional[Path] = None,
    for_start: bool = False,
) -> TOFixedPortEvaluation:
    """Classify fixed-port TO state for doctor/start.

    ``listening`` if provided wins; else use ``is_free_fn`` (default socket probe).
    """
    findings: List[Dict[str, Any]] = []

    if listening is None:
        if is_free_fn is not None:
            listening = not is_free_fn(int(port))
        else:
            from .socket_probe import port_is_free

            listening = not port_is_free(int(port))

    if not listening:
        findings.append(
            {
                "code": "TASK_ORCHESTRATOR_FIXED_PORT_FREE",
                "severity": "INFO",
                "message": f"task-orchestrator fixed port :{port} is free",
                "service": "task-orchestrator",
            }
        )
        return TOFixedPortEvaluation(
            port=int(port),
            listening=False,
            match="FREE",
            identity=None,
            findings=findings,
            start_allowed=True,
            start_block_code=None,
        )

    findings.append(
        {
            "code": "TASK_ORCHESTRATOR_FIXED_PORT_OCCUPIED",
            "severity": "INFO",
            "message": f"task-orchestrator fixed port :{port} is occupied",
            "service": "task-orchestrator",
        }
    )

    sources: List[TOIdentity] = []
    if http_identity is not None:
        sources.append(http_identity)
    elif not skip_http:
        probed = probe_http_info(int(port))
        if probed:
            sources.append(probed)
            findings.append(
                {
                    "code": "TASK_ORCHESTRATOR_RUNTIME_METADATA_FOUND",
                    "severity": "INFO",
                    "message": "TO identity found via HTTP /info",
                    "service": "task-orchestrator",
                    "source": "http_info",
                }
            )
    if docker_identity is not None:
        sources.append(docker_identity)
    if registry_identity is not None:
        sources.append(registry_identity)

    # Wrapper metadata is disk-stale-capable and not tied to the live listener;
    # never treat it alone as proof of who owns :port (P1 fail-closed).
    has_live_proof = any(s.has_project_proof() for s in sources)
    wrapper: Optional[TOIdentity] = wrapper_identity
    if wrapper is None:
        wrapper = probe_wrapper_metadata(
            instance_id=target_instance_id,
            candidates=[c for c in (target_worktree_hash, target_project_id) if c],
            base=metadata_base,
        )
    if wrapper is not None and wrapper.has_project_proof():
        if has_live_proof:
            sources.append(wrapper)
            findings.append(
                {
                    "code": "TASK_ORCHESTRATOR_RUNTIME_METADATA_FOUND",
                    "severity": "INFO",
                    "message": "TO identity found via wrapper metadata (corroboration only)",
                    "service": "task-orchestrator",
                    "source": "wrapper_metadata",
                }
            )
        else:
            findings.append(
                {
                    "code": "TASK_ORCHESTRATOR_WRAPPER_METADATA_NOT_LIVE",
                    "severity": "WARN",
                    "message": (
                        "wrapper metadata present but not used as live ownership "
                        f"proof for occupied :{port} (HTTP/Docker identity unavailable)"
                    ),
                    "service": "task-orchestrator",
                    "source": "wrapper_metadata",
                    "evidence": list(wrapper.evidence),
                }
            )

    if not any(s.has_project_proof() for s in sources):
        findings.append(
            {
                "code": "TASK_ORCHESTRATOR_PROJECT_IDENTITY_UNKNOWN",
                "severity": "FAIL" if for_start else "UNKNOWN",
                "message": (
                    f"task-orchestrator on :{port} is listening but project ownership is unproven"
                ),
                "service": "task-orchestrator",
                "recommendation": "Do not treat port-alive as workflow authority; start is blocked until identity is proven.",
            }
        )
        findings.append(
            {
                "code": "TASK_ORCHESTRATOR_FIXED_PORT_OCCUPIED_UNKNOWN",
                "severity": "FAIL" if for_start else "WARN",
                "message": f"Occupied :{port} with unknown owner",
                "service": "task-orchestrator",
            }
        )
        findings.append(
            {
                "code": "TASK_ORCHESTRATOR_RUNTIME_METADATA_MISSING",
                "severity": "WARN",
                "message": "No TO identity metadata/labels/info with project fields",
                "service": "task-orchestrator",
            }
        )
        return TOFixedPortEvaluation(
            port=int(port),
            listening=True,
            match="UNKNOWN",
            identity=sources[0] if sources else None,
            findings=findings,
            start_allowed=False,
            start_block_code="TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER",
        )

    merged, conflict_findings = merge_identity_sources(sources)
    findings.extend(conflict_findings)
    if conflict_findings or merged is None:
        return TOFixedPortEvaluation(
            port=int(port),
            listening=True,
            match="CONFLICT",
            identity=None,
            findings=findings,
            start_allowed=False,
            start_block_code="TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER",
        )

    match = match_target(
        merged,
        project_id=target_project_id,
        project_root=target_project_root,
    )

    if match == "OK":
        findings.append(
            {
                "code": "TASK_ORCHESTRATOR_PROJECT_IDENTITY_OK",
                "severity": "INFO",
                "message": (
                    f"task-orchestrator on :{port} matches project "
                    f"{target_project_id or target_project_root}"
                ),
                "service": "task-orchestrator",
                "evidence": merged.evidence,
            }
        )
        findings.append(
            {
                "code": "TASK_ORCHESTRATOR_FIXED_PORT_OCCUPIED_SAME_PROJECT",
                "severity": "INFO",
                "message": f":{port} occupied by same project TO",
                "service": "task-orchestrator",
            }
        )
        return TOFixedPortEvaluation(
            port=int(port),
            listening=True,
            match="OK",
            identity=merged,
            findings=findings,
            start_allowed=True,
            start_block_code=None,
        )

    if match == "WRONG_PROJECT":
        findings.append(
            {
                "code": "TASK_ORCHESTRATOR_WRONG_PROJECT_RUNTIME",
                "severity": "FAIL",
                "message": (
                    f"task-orchestrator on :{port} belongs to another project "
                    f"(observed project_root={merged.project_root}, "
                    f"project_id={merged.project_id})"
                ),
                "service": "task-orchestrator",
                "evidence": merged.evidence,
            }
        )
        findings.append(
            {
                "code": "TASK_ORCHESTRATOR_FIXED_PORT_OCCUPIED_OTHER_PROJECT",
                "severity": "FAIL",
                "message": f":{port} occupied by other project TO",
                "service": "task-orchestrator",
            }
        )
        return TOFixedPortEvaluation(
            port=int(port),
            listening=True,
            match="WRONG_PROJECT",
            identity=merged,
            findings=findings,
            start_allowed=False,
            start_block_code="TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT",
        )

    if match == "CONFLICT":
        findings.append(
            {
                "code": "TASK_ORCHESTRATOR_RUNTIME_METADATA_CONFLICT",
                "severity": "FAIL",
                "message": "TO project_id matches but project_root differs from target",
                "service": "task-orchestrator",
                "evidence": merged.evidence,
            }
        )
        return TOFixedPortEvaluation(
            port=int(port),
            listening=True,
            match="CONFLICT",
            identity=merged,
            findings=findings,
            start_allowed=False,
            start_block_code="TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER",
        )

    # UNKNOWN
    findings.append(
        {
            "code": "TASK_ORCHESTRATOR_PROJECT_IDENTITY_UNKNOWN",
            "severity": "FAIL" if for_start else "UNKNOWN",
            "message": f"task-orchestrator on :{port} identity could not be matched to target",
            "service": "task-orchestrator",
            "evidence": merged.evidence,
        }
    )
    findings.append(
        {
            "code": "TASK_ORCHESTRATOR_FIXED_PORT_OCCUPIED_UNKNOWN",
            "severity": "FAIL" if for_start else "WARN",
            "message": f"Occupied :{port} ownership unknown relative to target",
            "service": "task-orchestrator",
        }
    )
    return TOFixedPortEvaluation(
        port=int(port),
        listening=True,
        match="UNKNOWN",
        identity=merged,
        findings=findings,
        start_allowed=False,
        start_block_code="TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER",
    )


def target_identity_from_view(
    *,
    project_id: Optional[str],
    project_root: Optional[str],
    workspace_id: Optional[str] = None,
    worktree_root: Optional[str] = None,
    project_hash: Optional[str] = None,
    worktree_hash: Optional[str] = None,
    instance_id: Optional[str] = None,
    port: int = DEFAULT_TO_PORT,
) -> TOIdentity:
    return TOIdentity(
        project_id=project_id,
        workspace_id=workspace_id or worktree_root,
        project_root=project_root,
        worktree_root=worktree_root or workspace_id,
        project_hash=project_hash,
        worktree_hash=worktree_hash,
        instance_id=instance_id or worktree_hash,
        port=port,
        source="target",
        confidence="HIGH",
        evidence=["target_identity"],
    )


def identity_env_exports(identity: TOIdentity) -> Dict[str, str]:
    """Env map for wrapper / docker -e."""
    out: Dict[str, str] = {
        "TASK_ORCHESTRATOR_STATE_SCOPE": "per-repo",
        "TASK_ORCHESTRATOR_RUNTIME_SCOPE": "project",
    }
    if identity.project_id:
        out["DOPEMUX_PROJECT_ID"] = str(identity.project_id)
    if identity.workspace_id:
        out["DOPEMUX_WORKSPACE_ID"] = str(identity.workspace_id)
    if identity.project_root:
        out["DOPEMUX_PROJECT_ROOT"] = str(identity.project_root)
        out["TASK_ORCHESTRATOR_PROJECT_ROOT"] = str(identity.project_root)
    if identity.worktree_root:
        out["DOPEMUX_WORKTREE_ROOT"] = str(identity.worktree_root)
        out["DOPEMUX_WORKSPACE_ROOT"] = str(identity.worktree_root)
    if identity.instance_id:
        out["DOPEMUX_INSTANCE_ID"] = str(identity.instance_id)
    return out
