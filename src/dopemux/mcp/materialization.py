"""Generic atomic runner-session materialization (P1 fleet control plane).

Writes caller-supplied file payloads atomically into an explicit output
root, never a shared/global runner config location, and emits a
PROVENANCE_ONLY receipt. Runner-specific rendering (which files, in which
format) stays P7's job -- this module only knows how to write a set of
bytes atomically and prove what it wrote; it never decides content. See
``schemas/mcp/runner-materialization-receipt.schema.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

SCHEMA_VERSION = "dopemux.mcp.runner-materialization-receipt.v1"
AUTHORITY = "PROVENANCE_ONLY"
RUNNER_FAMILIES = ("claude", "codex", "opencode", "gemini", "copilot")

CURRENT_LINK_NAME = "current"
GENERATIONS_DIRNAME = "generations"


class MaterializationError(RuntimeError):
    """Raised when a plan targets a forbidden root, is malformed, or a
    generation write fails. On any failure the previous complete generation
    (if any) is left untouched -- see ``materialize_atomic``."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def known_shared_global_config_roots(home: Optional[Path] = None) -> Tuple[Path, ...]:
    """Best-effort, non-exhaustive list of shared/global runner config
    locations this materializer must never write into. ``home`` is
    injectable for tests; production callers omit it (``Path.home()``)."""

    base = home if home is not None else Path.home()
    return (
        (base / ".claude.json").resolve(),
        (base / ".claude").resolve(),
        (base / ".codex").resolve(),
        (base / ".config" / "opencode").resolve(),
        (base / ".gemini").resolve(),
        (base / ".config" / "github-copilot").resolve(),
    )


def _paths_overlap(a: Path, b: Path) -> bool:
    try:
        a.relative_to(b)
        return True
    except ValueError:
        pass
    try:
        b.relative_to(a)
        return True
    except ValueError:
        pass
    return a == b


def _reject_if_shared_global(output_root: Path, *, home: Optional[Path] = None) -> None:
    resolved = output_root.resolve()
    for forbidden in known_shared_global_config_roots(home):
        if _paths_overlap(resolved, forbidden):
            raise MaterializationError(
                f"output_root {resolved} overlaps a known shared/global runner "
                f"config location ({forbidden}); materialization is confined to "
                "an explicit caller-supplied session/output directory"
            )


@dataclass(frozen=True)
class MaterializationPlan:
    output_root: Path
    files: Dict[str, bytes]  # relative path -> content
    project_id: str
    workspace_id: str
    instance_id: str
    registry_generation: int
    runner_family: str
    profile: str
    catalog_digest: str  # 64 lowercase hex, caller-computed over the source catalog
    lease_refs: Tuple[str, ...] = ()
    strict_mode: bool = False
    inherited_surface_status: str = "UNKNOWN"  # KNOWN | UNKNOWN


@dataclass(frozen=True)
class MaterializationReceipt:
    materialization_id: str
    project_id: str
    workspace_id: str
    instance_id: str
    registry_generation: int
    runner_family: str
    profile: str
    catalog_digest: str
    rendered_config_digest: str
    lease_refs: Tuple[str, ...]
    generated_at: str
    strict_mode: bool
    inherited_surface_status: str
    generation_dir: Path

    def to_schema_dict(self) -> Dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "authority": AUTHORITY,
            "materialization_id": self.materialization_id,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "instance_id": self.instance_id,
            "registry_generation": self.registry_generation,
            "runner_family": self.runner_family,
            "profile": self.profile,
            "catalog_digest": self.catalog_digest,
            "rendered_config_digest": self.rendered_config_digest,
            "lease_refs": list(self.lease_refs),
            "generated_at": self.generated_at,
            "shared_global_config_mutated": False,
            "strict_mode": self.strict_mode,
            "inherited_surface_status": self.inherited_surface_status,
        }


def _validate_plan(plan: MaterializationPlan) -> None:
    if plan.runner_family not in RUNNER_FAMILIES:
        raise MaterializationError(f"unknown runner_family: {plan.runner_family!r}")
    if plan.inherited_surface_status not in ("KNOWN", "UNKNOWN"):
        raise MaterializationError(
            f"unknown inherited_surface_status: {plan.inherited_surface_status!r}"
        )
    if plan.strict_mode and plan.inherited_surface_status != "KNOWN":
        raise MaterializationError(
            "strict_mode=True requires inherited_surface_status=KNOWN"
        )
    if not plan.files:
        raise MaterializationError("plan.files must not be empty")
    for rel_path in plan.files:
        candidate = Path(rel_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise MaterializationError(f"unsafe relative file path in plan: {rel_path!r}")


def _rendered_config_digest(files: Dict[str, bytes]) -> str:
    """Deterministic digest over the full file set: sorted relative paths,
    each paired with its content, so any change to any file's path or bytes
    changes the digest."""

    hasher = hashlib.sha256()
    for rel_path in sorted(files):
        hasher.update(rel_path.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(files[rel_path])
        hasher.update(b"\0")
    return hasher.hexdigest()


def _fsync_file(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def materialize_atomic(
    plan: MaterializationPlan, *, home: Optional[Path] = None
) -> MaterializationReceipt:
    """Write ``plan.files`` atomically as a new generation under
    ``plan.output_root``, then atomically flip the ``current`` symlink.

    Every file is staged into a temp sibling directory, fsynced, then the
    whole directory is renamed into place in one filesystem operation before
    ``current`` is repointed -- so a failure at any point during staging
    leaves the prior generation (if any) and ``current`` completely
    untouched. Never writes into a shared/global runner config root.
    """

    _validate_plan(plan)
    output_root = Path(plan.output_root)
    _reject_if_shared_global(output_root, home=home)

    output_root.mkdir(parents=True, exist_ok=True)
    generations_dir = output_root / GENERATIONS_DIRNAME
    generations_dir.mkdir(parents=True, exist_ok=True)

    materialization_id = f"mat_{uuid.uuid4().hex}"
    gen_name = f"gen-{uuid.uuid4().hex}"
    staging_dir = output_root / f".staging-{uuid.uuid4().hex}"
    final_gen_dir = generations_dir / gen_name

    rendered_config_digest = _rendered_config_digest(plan.files)
    generated_at = _utc_now()
    receipt = MaterializationReceipt(
        materialization_id=materialization_id,
        project_id=plan.project_id,
        workspace_id=plan.workspace_id,
        instance_id=plan.instance_id,
        registry_generation=plan.registry_generation,
        runner_family=plan.runner_family,
        profile=plan.profile,
        catalog_digest=plan.catalog_digest,
        rendered_config_digest=rendered_config_digest,
        lease_refs=tuple(plan.lease_refs),
        generated_at=generated_at,
        strict_mode=plan.strict_mode,
        inherited_surface_status=plan.inherited_surface_status,
        generation_dir=final_gen_dir,
    )

    try:
        staging_dir.mkdir(parents=True, exist_ok=False)
        for rel_path, content in plan.files.items():
            dest = staging_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            _fsync_file(dest)
        (staging_dir / "receipt.json").write_text(
            json.dumps(receipt.to_schema_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _fsync_file(staging_dir / "receipt.json")
        _fsync_dir(staging_dir)

        os.rename(staging_dir, final_gen_dir)
        _fsync_dir(generations_dir)

        _flip_current_symlink(output_root, final_gen_dir)
    except Exception as exc:
        shutil.rmtree(staging_dir, ignore_errors=True)
        if final_gen_dir.exists() and not _current_points_at(output_root, final_gen_dir):
            shutil.rmtree(final_gen_dir, ignore_errors=True)
        raise MaterializationError(f"materialization failed, no generation promoted: {exc}") from exc

    return receipt


def _current_points_at(output_root: Path, gen_dir: Path) -> bool:
    current = output_root / CURRENT_LINK_NAME
    if not current.is_symlink():
        return False
    try:
        return current.resolve() == gen_dir.resolve()
    except OSError:
        return False


def _flip_current_symlink(output_root: Path, gen_dir: Path) -> None:
    current = output_root / CURRENT_LINK_NAME
    tmp_link = output_root / f".current-{uuid.uuid4().hex}"
    tmp_link.symlink_to(gen_dir, target_is_directory=True)
    os.replace(tmp_link, current)


def read_current_receipt(output_root: Path) -> Optional[Dict[str, object]]:
    """Read-only: the receipt of whatever generation ``current`` points at,
    or ``None`` if nothing has been materialized yet."""

    current = Path(output_root) / CURRENT_LINK_NAME
    receipt_path = current / "receipt.json"
    if not receipt_path.exists():
        return None
    return json.loads(receipt_path.read_text(encoding="utf-8"))
