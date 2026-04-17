from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class RunContext:
    run_id: str
    source: str
    latest_file: Path
    latest_written: bool


@dataclass(frozen=True)
class OutputLayout:
    extraction_root: Path
    runs_root: Path
    latest_run_file: Path
    doctor_root: Path


def _default_output_layout(repo_root: Path, extraction_root_rel: Path) -> OutputLayout:
    extraction_root = (repo_root / extraction_root_rel).resolve()
    return OutputLayout(
        extraction_root=extraction_root,
        runs_root=(extraction_root / "runs").resolve(),
        latest_run_file=(extraction_root / "latest_run_id.txt").resolve(),
        doctor_root=(extraction_root / "doctor").resolve(),
    )


def configure_output_layout(
    repo_root: Path,
    output_root: Optional[str],
    *,
    extraction_root_rel: Path,
) -> OutputLayout:
    if output_root:
        extraction_root = Path(output_root).expanduser().resolve()
        return OutputLayout(
            extraction_root=extraction_root,
            runs_root=(extraction_root / "runs").resolve(),
            latest_run_file=(extraction_root / "latest_run_id.txt").resolve(),
            doctor_root=(extraction_root / "doctor").resolve(),
        )
    return _default_output_layout(repo_root, extraction_root_rel)


def current_output_layout(
    repo_root: Path,
    *,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
) -> OutputLayout:
    return active_output_layout or _default_output_layout(repo_root, extraction_root_rel)


def current_extraction_root(
    repo_root: Path,
    *,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
) -> Path:
    return current_output_layout(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    ).extraction_root


def current_runs_root(
    repo_root: Path,
    *,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
) -> Path:
    return current_output_layout(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    ).runs_root


def current_doctor_root(
    repo_root: Path,
    *,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
) -> Path:
    return current_output_layout(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    ).doctor_root


def latest_run_id_path(
    repo_root: Path,
    *,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
) -> Path:
    return current_output_layout(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    ).latest_run_file


def load_run_id(
    repo_root: Path,
    *,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
) -> Optional[str]:
    id_file = latest_run_id_path(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    )
    if not id_file.exists():
        return None
    run_id = id_file.read_text(encoding="utf-8").strip()
    return run_id or None


def validate_existing_run_dir(
    repo_root: Path,
    run_id: str,
    *,
    allow_create_if_missing: bool,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
) -> None:
    candidate = current_runs_root(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    ) / run_id
    if not candidate.exists():
        if allow_create_if_missing:
            candidate.mkdir(parents=True, exist_ok=True)
            return
        raise FileNotFoundError(f"Run directory {candidate} does not exist.")
    if not candidate.is_dir():
        raise NotADirectoryError(f"Path {candidate} is not a directory.")


def generate_run_id(
    repo_root: Path,
    *,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
) -> str:
    base = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    runs_root = current_runs_root(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    )
    runs_root.mkdir(parents=True, exist_ok=True)
    candidate = runs_root / base
    suffix = 1
    while candidate.exists():
        candidate = runs_root / f"{base}_{suffix:02d}"
        suffix += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate.name


def persist_latest_run_id(
    repo_root: Path,
    run_id: str,
    *,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
) -> None:
    id_file = latest_run_id_path(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    )
    id_file.parent.mkdir(parents=True, exist_ok=True)
    id_file.write_text(run_id + "\n", encoding="utf-8")


def resolve_run_context(
    repo_root: Path,
    args: Any,
    *,
    allow_create_if_missing: bool,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
    logger: Any,
) -> RunContext:
    latest_file = latest_run_id_path(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    )
    run_id_source = "generated"
    resume_requested = bool(getattr(args, "resume", False))

    if args.run_id:
        run_id = args.run_id
        validate_existing_run_dir(
            repo_root,
            run_id,
            allow_create_if_missing=allow_create_if_missing,
            extraction_root_rel=extraction_root_rel,
            active_output_layout=active_output_layout,
        )
        run_id_source = "explicit"
    elif resume_requested:
        latest = load_run_id(
            repo_root,
            extraction_root_rel=extraction_root_rel,
            active_output_layout=active_output_layout,
        )
        if latest:
            latest_dir = current_runs_root(
                repo_root,
                extraction_root_rel=extraction_root_rel,
                active_output_layout=active_output_layout,
            ) / latest
            if latest_dir.exists() and latest_dir.is_dir():
                run_id = latest
                run_id_source = "latest_run_id"
            else:
                raise FileNotFoundError(
                    "Resume requested but latest_run_id.txt points to missing run "
                    f"directory {latest_dir}."
                )
        else:
            raise FileNotFoundError(
                f"Resume requested but no latest run id exists at {latest_file}."
            )
    else:
        run_id = generate_run_id(
            repo_root,
            extraction_root_rel=extraction_root_rel,
            active_output_layout=active_output_layout,
        )

    write_latest = not args.no_write_latest and (
        not args.dry_run or args.write_latest_even_on_dry_run
    )
    if write_latest:
        persist_latest_run_id(
            repo_root,
            run_id,
            extraction_root_rel=extraction_root_rel,
            active_output_layout=active_output_layout,
        )
    return RunContext(
        run_id=run_id,
        source=run_id_source,
        latest_file=latest_file,
        latest_written=write_latest,
    )


def get_run_dirs(
    repo_root: Path,
    run_id: str,
    *,
    extraction_root_rel: Path,
    active_output_layout: Optional[OutputLayout],
    legacy_phase_dir_aliases: Dict[str, str],
    phase_dir_names: Dict[str, str],
    phases: Iterable[str],
) -> Dict[str, Path]:
    base = current_runs_root(
        repo_root,
        extraction_root_rel=extraction_root_rel,
        active_output_layout=active_output_layout,
    ) / run_id
    if not base.exists():
        raise FileNotFoundError(f"Run directory {base} does not exist.")
    for legacy_name, canonical_name in legacy_phase_dir_aliases.items():
        legacy_path = base / legacy_name
        canonical_path = base / canonical_name
        if legacy_path.exists():
            if canonical_path.exists():
                raise RuntimeError(
                    f"Run directory has both canonical and legacy phase folders: {canonical_path} and {legacy_path}. "
                    f"Keep only canonical {canonical_name}."
                )
            raise RuntimeError(
                f"Legacy phase folder detected: {legacy_path}. Rename it to canonical {canonical_path} before running."
            )

    dirs: Dict[str, Path] = {"root": base, "inputs": base / "00_inputs"}
    for phase, suffix in phase_dir_names.items():
        dirs[phase] = base / suffix

    dirs["inputs"].mkdir(parents=True, exist_ok=True)
    for phase in phases:
        phase_dir = dirs[str(phase)]
        (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)
        (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
        (phase_dir / "norm").mkdir(parents=True, exist_ok=True)
        (phase_dir / "qa").mkdir(parents=True, exist_ok=True)
    return dirs
