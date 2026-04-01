from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence

if __package__ in {None, ""}:
    service_root = Path(__file__).resolve().parents[1]
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))
    import run_extraction_v5 as runner  # type: ignore[import-not-found]
    from fl_int.fl_int_paths import ensure_fl_int_dirs
    from s_int.schema_validate import load_schema, validate_payload_or_raise
else:
    import run_extraction_v5 as runner  # type: ignore[import-not-found]
    from .fl_int_paths import ensure_fl_int_dirs
    from s_int.schema_validate import load_schema, validate_payload_or_raise


REQUIRED_PHASE_IDS = ("D", "C", "R")
OPTIONAL_PHASE_IDS = ("X",)


def _line_number_text(text: str) -> str:
    return "\n".join(f"{line_no:04d}: {line}" for line_no, line in enumerate(text.splitlines(), start=1))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_payload(path: Path) -> Dict[str, Any]:
    artifact_name = path.name
    source_path = str(path.resolve())
    if path.suffix.lower() == ".json":
        return {
            "artifact_name": artifact_name,
            "kind": "json",
            "source_path": source_path,
            "payload": _load_json(path),
        }
    text = path.read_text(encoding="utf-8")
    return {
        "artifact_name": artifact_name,
        "kind": "markdown",
        "source_path": source_path,
        "content": _line_number_text(text),
    }


def _load_phase_artifacts(norm_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(norm_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".json", ".md"}:
            continue
        rows.append(_artifact_payload(path))
    return rows


def _phase_payload(run_root: Path, phase_id: str) -> Optional[Dict[str, Any]]:
    norm_dir = run_root / runner.PHASE_DIR_NAMES[phase_id] / "norm"
    if not norm_dir.exists():
        return None
    artifacts = _load_phase_artifacts(norm_dir)
    return {
        "phase_id": phase_id,
        "norm_dir": str(norm_dir.resolve()),
        "artifact_count": len(artifacts),
        "artifact_names": [row["artifact_name"] for row in artifacts],
        "artifacts": artifacts,
    }


def collect_input_payload(run_root: Path) -> Dict[str, Any]:
    resolved_run_root = run_root.resolve()
    if not resolved_run_root.exists():
        raise ValueError(f"Run root does not exist: {resolved_run_root}")

    phases: Dict[str, Dict[str, Any]] = {}
    available_phase_ids: List[str] = []
    missing_required_phase_ids: List[str] = []
    for phase_id in REQUIRED_PHASE_IDS + OPTIONAL_PHASE_IDS:
        payload = _phase_payload(resolved_run_root, phase_id)
        if payload is None:
            if phase_id in REQUIRED_PHASE_IDS:
                missing_required_phase_ids.append(phase_id)
            continue
        phases[phase_id] = payload
        available_phase_ids.append(phase_id)

    if missing_required_phase_ids:
        missing = ", ".join(missing_required_phase_ids)
        raise ValueError(f"Run root is missing required norm directories for phases: {missing}")

    return {
        "schema_version": "FL_INT_INPUT_V1",
        "run_id": resolved_run_root.name,
        "run_root": str(resolved_run_root),
        "required_phase_ids": list(REQUIRED_PHASE_IDS),
        "optional_phase_ids": list(OPTIONAL_PHASE_IDS),
        "available_phase_ids": sorted(available_phase_ids),
        "missing_required_phase_ids": sorted(missing_required_phase_ids),
        "phases": phases,
    }


def collect_input_bundle(run_root: Path, out_root: Optional[Path] = None) -> Dict[str, Any]:
    dirs = ensure_fl_int_dirs(run_root, out_root=out_root)
    payload = collect_input_payload(run_root)
    schema = load_schema(Path(__file__).resolve().parent / "schema_input.json")
    validate_payload_or_raise(payload, schema, label="FL_INT_INPUT")

    dirs["raw"].mkdir(parents=True, exist_ok=True)
    for phase_id, phase_payload in sorted(payload["phases"].items()):
        (dirs["raw"] / f"{phase_id}_NORM_ARTIFACTS.json").write_text(
            json.dumps(phase_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    dirs["input"].write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser("FL_INT input collector")
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--out-root", default="")
    args = parser.parse_args(argv)
    run_root = Path(args.run_root).resolve()
    out_root = Path(args.out_root).resolve() if str(args.out_root).strip() else None
    collect_input_bundle(run_root, out_root=out_root)
    output_root = out_root if out_root is not None else run_root / "postprocess" / "fl_int_v1"
    print(json.dumps({"status": "OK", "output": str(output_root.resolve())}))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
