from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .fingerprint import deterministic_generated_at
from .io import read_json
from .signals import compute_signals

PROFILE_SELECTION_FILENAME = "PROFILE_SELECTION.json"


@dataclass(frozen=True)
class ProfileRecord:
    profile_id: str
    version: str
    priority: int
    threshold: float
    payload: Dict[str, Any]


def _profile_sort_key(record: ProfileRecord) -> Tuple[int, str]:
    return (-int(record.priority), record.profile_id)


def _load_profile_file(path: Path) -> Dict[str, Any]:
    payload = read_json(path)
    if not payload:
        raise RuntimeError(f"Invalid profile JSON: {path}")
    return payload


def load_profiles(profiles_dir: Path) -> List[ProfileRecord]:
    rows: List[ProfileRecord] = []
    for path in sorted(profiles_dir.glob("P*.json")):
        payload = _load_profile_file(path)
        profile_id = str(payload.get("profile_id", "")).strip()
        if not profile_id:
            continue
        rows.append(
            ProfileRecord(
                profile_id=profile_id,
                version=str(payload.get("version", "1.0.0")),
                priority=int(payload.get("priority", 0)),
                threshold=float(payload.get("selection_threshold", 0.0)),
                payload=payload,
            )
        )
    rows.sort(key=lambda row: row.profile_id)
    return rows


def _profile_score(profile: ProfileRecord, signals: Dict[str, float]) -> Tuple[float, List[Dict[str, Any]]]:
    weights = profile.payload.get("match_weights") if isinstance(profile.payload.get("match_weights"), dict) else {}
    contributions: List[Dict[str, Any]] = []
    total = 0.0
    for signal_name in sorted(weights):
        weight = float(weights.get(signal_name, 0.0))
        signal_value = float(signals.get(signal_name, 0.0))
        contribution = weight * signal_value
        total += contribution
        contributions.append(
            {
                "signal": signal_name,
                "weight": weight,
                "signal_value": signal_value,
                "contribution": round(contribution, 6),
            }
        )
    contributions.sort(key=lambda row: (-float(row["contribution"]), str(row["signal"])))
    return total, contributions


def select_profile(
    *,
    run_id: str,
    root: Path,
    repo_fingerprint: Dict[str, Any],
    archetypes_payload: Dict[str, Any],
    profiles_dir: Path,
) -> Dict[str, Any]:
    profiles = load_profiles(profiles_dir)
    if not profiles:
        raise RuntimeError(f"No profiles found under {profiles_dir}")

    signals = compute_signals(repo_fingerprint, archetypes_payload)
    scored_rows: List[Dict[str, Any]] = []
    selected: ProfileRecord | None = None
    selected_score = -1e18

    for profile in profiles:
        score, contributions = _profile_score(profile, signals)
        passes_threshold = score >= profile.threshold
        row = {
            "profile_id": profile.profile_id,
            "version": profile.version,
            "priority": profile.priority,
            "selection_threshold": profile.threshold,
            "score": round(score, 6),
            "passes_threshold": passes_threshold,
            "top_contributions": contributions[:10],
        }
        scored_rows.append(row)

    scored_rows.sort(key=lambda row: (-float(row["score"]), -int(row["priority"]), str(row["profile_id"])))

    for row in scored_rows:
        if not row["passes_threshold"]:
            continue
        candidate = next((p for p in profiles if p.profile_id == row["profile_id"]), None)
        if candidate is None:
            continue
        score = float(row["score"])
        if selected is None:
            selected = candidate
            selected_score = score
            continue
        if score > selected_score:
            selected = candidate
            selected_score = score
        elif score == selected_score:
            if (candidate.priority, candidate.profile_id) > (selected.priority, selected.profile_id):
                selected = candidate
                selected_score = score

    fallback = next((p for p in profiles if p.profile_id == "P00_GENERIC"), profiles[0])
    if selected is None:
        selected = fallback

    selected_row = next(row for row in scored_rows if row["profile_id"] == selected.profile_id)

    return {
        "version": "PROFILE_SELECTION_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "selected_profile_id": selected.profile_id,
        "selected_profile_version": selected.version,
        "selected_profile_score": selected_row["score"],
        "selected_profile_priority": selected.priority,
        "signals": signals,
        "per_profile_scores": scored_rows,
        "top_contributing_signals": selected_row["top_contributions"],
        "selection_mode": "deterministic_weighted_rules",
    }


def load_selected_profile(selection_payload: Dict[str, Any], profiles_dir: Path) -> Dict[str, Any]:
    selected_id = str(selection_payload.get("selected_profile_id", "")).strip()
    if not selected_id:
        raise RuntimeError("Missing selected_profile_id in profile selection payload.")
    path = profiles_dir / f"{selected_id}.json"
    payload = read_json(path)
    if not payload:
        raise RuntimeError(f"Selected profile missing: {path}")
    return payload
