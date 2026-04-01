from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Iterable, List, Tuple


F0_CAPS = {
    "max_total_chars": 100000,
    "max_chunks": 60,
    "max_chunk_chars": 4000,
    "batch_target_chars": 20000,
}

L0_CAPS = {
    "max_total_chars": 120000,
    "max_units_per_family": 80,
    "max_unit_chars": 3000,
    "batch_target_chars": 30000,
}

KEYWORD_WEIGHTS: Tuple[Tuple[int, Tuple[str, ...]], ...] = (
    (3, ("architecture", "system", "design", "workflow", "integration")),
    (2, ("policy", "authority", "control", "memory", "context", "ledger")),
    (1, ("feature", "capability", "module", "runtime")),
    (-2, ("changelog", "audit", "status", "report", "logs")),
)

PRESERVE_TERMS = ("authority", "pm", "policy", "governance")
HEADING_RE = re.compile(r"^(?P<line>\d{4}): (?P<hashes>#{1,6})\s*(?P<title>.*)$")
LINE_PREFIX_RE = re.compile(r"^\d{4}: ?")


def _json_text(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _keyword_score(text: str) -> int:
    lowered = _normalized_text(text)
    score = 0
    for weight, words in KEYWORD_WEIGHTS:
        for word in words:
            if re.search(rf"\b{re.escape(word)}\b", lowered):
                score += weight
    return score


def _preserve_guardrail(text: str) -> bool:
    lowered = _normalized_text(text)
    for term in PRESERVE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            return True
    return False


def _hash_fingerprint(*parts: str) -> str:
    digest = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def _coerce_line_range(value: Any) -> List[int]:
    if isinstance(value, list) and len(value) >= 2:
        start = int(value[0])
        end = int(value[1])
        return [start, end]
    if isinstance(value, list) and len(value) == 1:
        line = int(value[0])
        return [line, line]
    return [0, 0]


def _line_range_from_text(text: str) -> List[int]:
    line_numbers: List[int] = []
    for line in text.splitlines():
        prefix = line.split(":", 1)[0]
        if prefix.isdigit():
            line_numbers.append(int(prefix))
    if not line_numbers:
        return [0, 0]
    return [line_numbers[0], line_numbers[-1]]


def _truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[TRUNCATED]..."


def _sort_line_range(value: Any) -> Tuple[int, int]:
    line_range = _coerce_line_range(value)
    return (line_range[0], line_range[1])


def _batched(records: List[Dict[str, Any]], *, target_chars: int, prefix: str) -> List[Dict[str, Any]]:
    batches: List[Dict[str, Any]] = []
    current: List[Dict[str, Any]] = []
    current_chars = 0
    batch_index = 0
    for row in records:
        row_chars = int(row.get("char_count") or 0)
        if current and current_chars + row_chars > target_chars:
            batch_id = f"{prefix}_{batch_index:03d}"
            batches.append(
                {
                    "batch_id": batch_id,
                    "selected_ids": [item["chunk_id"] for item in current],
                    "total_chars": current_chars,
                }
            )
            batch_index += 1
            current = []
            current_chars = 0
        current.append(row)
        current_chars += row_chars
    if current or not batches:
        batch_id = f"{prefix}_{batch_index:03d}"
        batches.append(
            {
                "batch_id": batch_id,
                "selected_ids": [item["chunk_id"] for item in current],
                "total_chars": current_chars,
            }
        )
    return batches


def _split_markdown_sections(content: str) -> List[Dict[str, Any]]:
    lines = content.splitlines()
    sections: List[Dict[str, Any]] = []
    current_title = "preamble"
    current_lines: List[str] = []
    current_start = 0
    current_end = 0

    def flush() -> None:
        nonlocal current_lines, current_start, current_end, current_title
        if not current_lines:
            return
        sections.append(
            {
                "section_key": current_title,
                "content": "\n".join(current_lines).strip(),
                "line_range": [current_start, current_end],
            }
        )
        current_lines = []

    for raw_line in lines:
        match = HEADING_RE.match(raw_line)
        line_no = int(raw_line.split(":", 1)[0]) if ":" in raw_line and raw_line.split(":", 1)[0].isdigit() else 0
        if match:
            flush()
            title = LINE_PREFIX_RE.sub("", raw_line).strip().lower() or "untitled"
            current_title = title
            current_lines = [raw_line]
            current_start = line_no
            current_end = line_no
            continue
        if not current_lines:
            current_start = line_no
            current_title = "preamble"
        current_lines.append(raw_line)
        if line_no:
            current_end = line_no
    flush()
    return [row for row in sections if row["content"]]


def _window_section(section: Dict[str, Any], *, max_chunk_chars: int) -> List[Dict[str, Any]]:
    content = str(section.get("content") or "")
    if len(content) <= max_chunk_chars:
        return [dict(section, chunk_ordinal=0, char_count=len(content))]
    windows: List[Dict[str, Any]] = []
    current_lines: List[str] = []
    current_chars = 0
    chunk_index = 0
    for line in content.splitlines():
        additional = len(line) + (1 if current_lines else 0)
        if current_lines and current_chars + additional > max_chunk_chars:
            chunk_text = "\n".join(current_lines).strip()
            windows.append(
                {
                    "section_key": section["section_key"],
                    "content": chunk_text,
                    "line_range": _line_range_from_text(chunk_text),
                    "chunk_ordinal": chunk_index,
                    "char_count": len(chunk_text),
                }
            )
            chunk_index += 1
            current_lines = []
            current_chars = 0
        current_lines.append(line)
        current_chars += additional
    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        windows.append(
            {
                "section_key": section["section_key"],
                "content": chunk_text,
                "line_range": _line_range_from_text(chunk_text),
                "chunk_ordinal": chunk_index,
                "char_count": len(chunk_text),
            }
        )
    return windows


def _markdown_chunks(artifact: Dict[str, Any], *, max_chunk_chars: int) -> List[Dict[str, Any]]:
    content = str(artifact.get("content") or "").strip()
    if not content:
        return []
    rows: List[Dict[str, Any]] = []
    for section in _split_markdown_sections(content):
        rows.extend(_window_section(section, max_chunk_chars=max_chunk_chars))
    chunks: List[Dict[str, Any]] = []
    for row in rows:
        content_text = str(row["content"])
        chunks.append(
            {
                "source_artifact": artifact["artifact_name"],
                "source_path": artifact["source_path"],
                "path": artifact["source_path"],
                "line_range": row["line_range"],
                "section_key": row["section_key"],
                "chunk_ordinal": row["chunk_ordinal"],
                "kind": "markdown",
                "content": content_text,
                "char_count": len(content_text),
            }
        )
    return chunks


def _json_chunks(artifact: Dict[str, Any], *, max_chunk_chars: int) -> List[Dict[str, Any]]:
    payload = artifact.get("payload")
    items: Optional[List[Any]] = None
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        maybe_items = payload.get("items")
        if isinstance(maybe_items, list):
            items = maybe_items

    rows: List[Dict[str, Any]] = []
    if items is not None:
        for index, item in enumerate(items):
            item_dict = item if isinstance(item, dict) else {"value": item}
            text = _truncate_text(_json_text(item_dict), max_chunk_chars)
            rows.append(
                {
                    "source_artifact": artifact["artifact_name"],
                    "source_path": artifact["source_path"],
                    "path": str(item_dict.get("path") or artifact["source_path"]),
                    "line_range": _coerce_line_range(item_dict.get("line_range")),
                    "section_key": str(item_dict.get("id") or f"item_{index:04d}"),
                    "chunk_ordinal": 0,
                    "kind": "json",
                    "content": text,
                    "char_count": len(text),
                }
            )
        return rows
    if not isinstance(payload, dict):
        return []
    text = _truncate_text(_json_text(payload), max_chunk_chars)
    rows.append(
        {
            "source_artifact": artifact["artifact_name"],
            "source_path": artifact["source_path"],
            "path": artifact["source_path"],
            "line_range": [0, 0],
            "section_key": "artifact",
            "chunk_ordinal": 0,
            "kind": "json",
            "content": text,
            "char_count": len(text),
        }
    )
    return rows


def _candidate_chunks(artifacts: Iterable[Dict[str, Any]], *, max_chunk_chars: int) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    unique: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    dropped = {"empty": 0, "duplicate": 0}
    for artifact in artifacts:
        kind = str(artifact.get("kind") or "").strip().lower()
        if kind == "markdown":
            rows = _markdown_chunks(artifact, max_chunk_chars=max_chunk_chars)
        elif kind == "json":
            rows = _json_chunks(artifact, max_chunk_chars=max_chunk_chars)
        else:
            rows = []
        for row in rows:
            content = str(row.get("content") or "").strip()
            if not content:
                dropped["empty"] += 1
                continue
            norm = _normalized_text(content)
            dedupe_key = (row["source_path"], row["section_key"], norm)
            if dedupe_key in unique:
                dropped["duplicate"] += 1
                continue
            unique[dedupe_key] = row
    candidates = sorted(
        unique.values(),
        key=lambda row: (
            row["source_path"],
            row["section_key"],
            int(row["chunk_ordinal"]),
            row["path"],
            _sort_line_range(row["line_range"]),
        ),
    )
    for index, row in enumerate(candidates, start=1):
        row["chunk_id"] = f"chunk-{index:06d}"
        row["score"] = _keyword_score(row["content"])
        row["guardrail_preserved"] = _preserve_guardrail(row["content"])
    return candidates, dropped


def _select_reduced_chunks(
    candidates: List[Dict[str, Any]],
    *,
    max_total_chars: int,
    max_count: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    ordered = sorted(
        candidates,
        key=lambda row: (
            0 if bool(row["guardrail_preserved"]) else 1,
            -int(row["score"]),
            row["source_path"],
            row["section_key"],
            int(row["chunk_ordinal"]),
        ),
    )
    selected: List[Dict[str, Any]] = []
    dropped = {"cap_limit": 0}
    total_chars = 0

    for row in ordered:
        keep_reason = "guardrail_preserve" if row["guardrail_preserved"] else "score_selected"
        next_total = total_chars + int(row["char_count"])
        over_caps = len(selected) >= max_count or next_total > max_total_chars
        if over_caps and not row["guardrail_preserved"]:
            dropped["cap_limit"] += 1
            continue
        selected.append({**row, "keep_reason": keep_reason})
        total_chars = next_total
    selected_sorted = sorted(
        selected,
        key=lambda row: (
            0 if bool(row["guardrail_preserved"]) else 1,
            -int(row["score"]),
            row["source_path"],
            row["section_key"],
            int(row["chunk_ordinal"]),
        ),
    )
    return selected_sorted, dropped


def reduce_f0_input(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    phase = (input_payload.get("phases") or {}).get("D") or {}
    artifacts = phase.get("artifacts") if isinstance(phase, dict) else []
    candidates, dropped = _candidate_chunks(artifacts if isinstance(artifacts, list) else [], max_chunk_chars=F0_CAPS["max_chunk_chars"])
    selected, cap_dropped = _select_reduced_chunks(
        candidates,
        max_total_chars=F0_CAPS["max_total_chars"],
        max_count=F0_CAPS["max_chunks"],
    )
    batches = _batched(selected, target_chars=F0_CAPS["batch_target_chars"], prefix="F0_BATCH")
    return {
        "schema_version": "F0_INPUT_REDUCTION_V1",
        "step_id": "F0",
        "caps": dict(F0_CAPS),
        "source_artifact_count": len(artifacts) if isinstance(artifacts, list) else 0,
        "candidate_chunk_count": len(candidates),
        "selected_chunk_count": len(selected),
        "total_selected_chars": sum(int(row["char_count"]) for row in selected),
        "dropped_counts": {
            "empty": int(dropped["empty"]),
            "duplicate": int(dropped["duplicate"]),
            "cap_limit": int(cap_dropped["cap_limit"]),
        },
        "selected_chunks": selected,
        "batches": batches,
    }


def _make_l0_unit(
    *,
    family: str,
    source_artifact: str,
    source_path: str,
    path: str,
    line_range: List[int],
    content: str,
    unit_key: str,
) -> Dict[str, Any]:
    return {
        "family": family,
        "source_artifact": source_artifact,
        "source_path": source_path,
        "path": path,
        "line_range": _coerce_line_range(line_range),
        "section_key": unit_key,
        "content": _truncate_text(content, L0_CAPS["max_unit_chars"]),
        "char_count": min(len(content), L0_CAPS["max_unit_chars"] + len("\n...[TRUNCATED]...")),
    }


def _f1_units(prior_outputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = (((prior_outputs.get("F1") or {}).get("design_claims_classified") or {}).get("items") or [])
    units: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = _json_text(row)
        units.append(
            _make_l0_unit(
                family="F1",
                source_artifact="DESIGN_CLAIMS_CLASSIFIED.json",
                source_path=str(row.get("path") or "DESIGN_CLAIMS_CLASSIFIED.json"),
                path=str(row.get("path") or "DESIGN_CLAIMS_CLASSIFIED.json"),
                line_range=_coerce_line_range(row.get("line_range")),
                content=text,
                unit_key=str(row.get("id") or "classified_claim"),
            )
        )
    return units


def _artifact_units(artifacts: Iterable[Dict[str, Any]], *, family: str) -> List[Dict[str, Any]]:
    units: List[Dict[str, Any]] = []
    for artifact in artifacts:
        kind = str(artifact.get("kind") or "").strip().lower()
        if kind == "json":
            payload = artifact.get("payload")
            if isinstance(payload, dict) and isinstance(payload.get("items"), list):
                for index, item in enumerate(payload["items"]):
                    item_dict = item if isinstance(item, dict) else {"value": item}
                    units.append(
                        _make_l0_unit(
                            family=family,
                            source_artifact=artifact["artifact_name"],
                            source_path=artifact["source_path"],
                            path=str(item_dict.get("path") or artifact["source_path"]),
                            line_range=_coerce_line_range(item_dict.get("line_range")),
                            content=_json_text(item_dict),
                            unit_key=str(item_dict.get("id") or f"item_{index:04d}"),
                        )
                    )
                continue
        content = str(artifact.get("content") or _json_text(artifact.get("payload"))).strip()
        if content:
            units.append(
                _make_l0_unit(
                    family=family,
                    source_artifact=artifact["artifact_name"],
                    source_path=artifact["source_path"],
                    path=artifact["source_path"],
                    line_range=_line_range_from_text(content),
                    content=content,
                    unit_key=artifact["artifact_name"],
                )
            )
    return units


def _reduced_d_units(prior_outputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    reduction = prior_outputs.get("_f0_reduction")
    if not isinstance(reduction, dict):
        return []
    rows = reduction.get("selected_chunks")
    if not isinstance(rows, list):
        return []
    units: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        units.append(
            _make_l0_unit(
                family="D",
                source_artifact=str(row.get("source_artifact") or "D_REDUCED"),
                source_path=str(row.get("source_path") or ""),
                path=str(row.get("path") or row.get("source_path") or ""),
                line_range=_coerce_line_range(row.get("line_range")),
                content=str(row.get("content") or ""),
                unit_key=str(row.get("chunk_id") or row.get("section_key") or "d_chunk"),
            )
        )
    return units


def _dedupe_family_units(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    unique: Dict[Tuple[str, str, Tuple[int, int], str], Dict[str, Any]] = {}
    duplicates = 0
    for row in rows:
        content = str(row.get("content") or "").strip()
        if not content:
            continue
        key = (
            str(row.get("path") or ""),
            str(row.get("family") or ""),
            _sort_line_range(row.get("line_range")),
            _normalized_text(content),
        )
        if key in unique:
            duplicates += 1
            continue
        unique[key] = row
    deduped = sorted(
        unique.values(),
        key=lambda row: (
            row["family"],
            row["source_path"],
            _sort_line_range(row["line_range"]),
            row["section_key"],
        ),
    )
    for index, row in enumerate(deduped, start=1):
        row["chunk_id"] = f"unit-{index:06d}"
        row["score"] = _keyword_score(row["content"])
        row["guardrail_preserved"] = _preserve_guardrail(row["content"])
    return deduped, duplicates


def _select_family_units(rows: List[Dict[str, Any]], *, max_units: int, char_budget: int) -> Tuple[List[Dict[str, Any]], int]:
    ordered = sorted(
        rows,
        key=lambda row: (
            0 if bool(row["guardrail_preserved"]) else 1,
            -int(row["score"]),
            row["source_path"],
            _sort_line_range(row["line_range"]),
            row["section_key"],
        ),
    )
    selected: List[Dict[str, Any]] = []
    total_chars = 0
    dropped = 0
    for row in ordered:
        next_total = total_chars + int(row["char_count"])
        over_cap = len(selected) >= max_units or next_total > char_budget
        if over_cap and not row["guardrail_preserved"]:
            dropped += 1
            continue
        selected.append(
            {
                **row,
                "keep_reason": "guardrail_preserve" if row["guardrail_preserved"] else "family_budget_selected",
            }
        )
        total_chars = next_total
    return selected, dropped


def reduce_l0_input(input_payload: Dict[str, Any], prior_outputs: Dict[str, Any]) -> Dict[str, Any]:
    phases = input_payload.get("phases") or {}
    families: Dict[str, List[Dict[str, Any]]] = {
        "D": _reduced_d_units(prior_outputs),
        "F1": _f1_units(prior_outputs),
        "C": _artifact_units((((phases.get("C") or {}).get("artifacts")) or []), family="C"),
        "X": _artifact_units((((phases.get("X") or {}).get("artifacts")) or []), family="X"),
    }
    present = [family for family, rows in families.items() if rows]
    family_budget = max(10000, L0_CAPS["max_total_chars"] // max(1, len(present))) if present else L0_CAPS["max_total_chars"]

    selected_by_family: Dict[str, List[Dict[str, Any]]] = {}
    dropped_counts = {"duplicate": 0, "cap_limit": 0}
    batch_defs: List[Dict[str, Any]] = []
    for family in ("D", "F1", "C", "X"):
        deduped, duplicates = _dedupe_family_units(families[family])
        dropped_counts["duplicate"] += duplicates
        selected, dropped = _select_family_units(
            deduped,
            max_units=L0_CAPS["max_units_per_family"],
            char_budget=family_budget,
        )
        dropped_counts["cap_limit"] += dropped
        selected_by_family[family] = selected
        if selected:
            batch_defs.extend(
                _batched(selected, target_chars=L0_CAPS["batch_target_chars"], prefix=f"L0_BATCH_{family}")
            )

    all_selected = [row for family in ("D", "F1", "C", "X") for row in selected_by_family[family]]
    return {
        "schema_version": "L0_INPUT_REDUCTION_V1",
        "step_id": "L0",
        "caps": dict(L0_CAPS),
        "family_char_budget": family_budget,
        "selected_unit_count": len(all_selected),
        "total_selected_chars": sum(int(row["char_count"]) for row in all_selected),
        "dropped_counts": dict(dropped_counts),
        "selected_units": all_selected,
        "selected_by_family": selected_by_family,
        "batches": batch_defs,
    }


def merge_f0_batch_payloads(batch_payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    statuses: List[str] = []
    missing_evidence: List[str] = []
    for payload in batch_payloads:
        statuses.append(str(payload.get("status") or "UNKNOWN"))
        for row in (((payload.get("design_claims_raw") or {}).get("items")) or []):
            if isinstance(row, dict):
                items.append(dict(row))
        for row in payload.get("missing_evidence") or []:
            if isinstance(row, str) and row not in missing_evidence:
                missing_evidence.append(row)
    items_sorted = sorted(
        items,
        key=lambda row: (
            str(row.get("path") or ""),
            _sort_line_range(row.get("line_range")),
            str(row.get("claim_text") or ""),
            str(row.get("plane") or ""),
            str(row.get("source_artifact") or ""),
        ),
    )
    rewritten: List[Dict[str, Any]] = []
    for index, row in enumerate(items_sorted, start=1):
        rewritten.append({**row, "id": f"f0-{index:06d}"})
    status = "OK" if all(value == "OK" for value in statuses) else ("NEEDS_REVIEW" if "NEEDS_REVIEW" in statuses else "UNKNOWN")
    return {
        "status": status,
        "design_claims_raw": {
            "schema": "DESIGN_CLAIMS_RAW@v1",
            "items": rewritten,
        },
        "missing_evidence": missing_evidence,
    }


def merge_l0_batch_payloads(batch_payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    statuses: List[str] = []
    missing_evidence: List[str] = []
    unique: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
    for payload in batch_payloads:
        statuses.append(str(payload.get("status") or "UNKNOWN"))
        rows = (((payload.get("feature_candidates_raw") or {}).get("items")) or [])
        for row in rows:
            if not isinstance(row, dict):
                continue
            evidence = tuple(
                (
                    str(item.get("path") or ""),
                    tuple(_coerce_line_range(item.get("line_range"))),
                    str(item.get("excerpt") or ""),
                )
                for item in row.get("evidence") or []
                if isinstance(item, dict)
            )
            key = (
                str(row.get("title") or ""),
                str(row.get("trigger") or ""),
                str(row.get("outcome") or ""),
                str(row.get("domain") or ""),
                str(row.get("plane") or ""),
                str(row.get("evidence_class") or ""),
                str(row.get("temporal_status") or ""),
                str(row.get("path") or ""),
                tuple(_coerce_line_range(row.get("line_range"))),
                evidence,
            )
            if key not in unique:
                unique[key] = dict(row)
        for value in payload.get("missing_evidence") or []:
            if isinstance(value, str) and value not in missing_evidence:
                missing_evidence.append(value)
    rows_sorted = sorted(
        unique.values(),
        key=lambda row: (
            str(row.get("domain") or ""),
            str(row.get("plane") or ""),
            str(row.get("trigger") or ""),
            str(row.get("outcome") or ""),
            str(row.get("path") or ""),
            _sort_line_range(row.get("line_range")),
            str(row.get("title") or ""),
        ),
    )
    rewritten: List[Dict[str, Any]] = []
    for index, row in enumerate(rows_sorted, start=1):
        rewritten.append({**row, "id": f"l0-{index:06d}"})
    status = "OK" if all(value == "OK" for value in statuses) else ("NEEDS_REVIEW" if "NEEDS_REVIEW" in statuses else "UNKNOWN")
    return {
        "status": status,
        "feature_candidates_raw": {
            "schema": "FEATURE_CANDIDATES_RAW@v1",
            "items": rewritten,
        },
        "missing_evidence": missing_evidence,
    }
