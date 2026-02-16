import hashlib
import json
from typing import Any, Dict, List, Tuple


def build_file_manifest_hash(paths: List[str], inventory_by_path: Dict[str, Dict[str, Any]]) -> str:
    rows: List[Dict[str, Any]] = []
    for path in sorted(paths):
        info = inventory_by_path.get(path, {})
        rows.append(
            {
                "path": path,
                "sha256": str(info.get("sha256", "")),
                "size": int(info.get("size", 0) or 0),
                "mtime": float(info.get("mtime", 0.0) or 0.0),
            }
        )
    digest_source = json.dumps(rows, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(digest_source.encode("utf-8", errors="ignore")).hexdigest()


def plan_chunks_for_step(
    partitions: List[Dict[str, Any]],
    inventory_by_path: Dict[str, Dict[str, Any]],
    max_files: int,
    max_chars: int,
) -> List[Dict[str, Any]]:
    planned: List[Dict[str, Any]] = []
    soft_target = max(int(max_chars * 0.7), 2048)
    idx = 1

    def _sort_key(path: str) -> Tuple[str, float, int]:
        info = inventory_by_path.get(path, {})
        return (path, float(info.get("mtime", 0.0) or 0.0), int(info.get("size", 0) or 0))

    for partition in sorted(partitions, key=lambda item: str(item.get("id", ""))):
        base_id = str(partition.get("id", ""))
        paths = sorted((str(path) for path in partition.get("paths", [])), key=_sort_key)
        if not paths:
            chunk_id = f"{base_id}_C{idx:04d}"
            planned.append(
                {
                    "id": chunk_id,
                    "chunk_id": chunk_id,
                    "base_partition_id": base_id,
                    "paths": [],
                    "ordered_paths": [],
                    "file_count": 0,
                    "char_count_estimate": 0,
                    "file_manifest_hash": build_file_manifest_hash([], inventory_by_path),
                }
            )
            idx += 1
            continue

        current_paths: List[str] = []
        current_chars = 0

        def flush_current() -> None:
            nonlocal current_paths, current_chars, idx
            if not current_paths:
                return
            chunk_id_local = f"{base_id}_C{idx:04d}"
            planned.append(
                {
                    "id": chunk_id_local,
                    "chunk_id": chunk_id_local,
                    "base_partition_id": base_id,
                    "paths": list(current_paths),
                    "ordered_paths": list(current_paths),
                    "file_count": len(current_paths),
                    "char_count_estimate": current_chars,
                    "file_manifest_hash": build_file_manifest_hash(current_paths, inventory_by_path),
                }
            )
            idx += 1
            current_paths = []
            current_chars = 0

        for path in paths:
            item = inventory_by_path.get(path, {})
            est_chars = int(item.get("char_count_estimate", 0) or 0) + min(len(path) + 80, 2000)
            est_chars = max(est_chars, 1)
            too_many_files = len(current_paths) >= max_files
            too_many_chars = current_paths and (current_chars + est_chars > soft_target)
            if too_many_files or too_many_chars:
                flush_current()
            current_paths.append(path)
            current_chars += est_chars
        flush_current()

    planned.sort(key=lambda item: str(item.get("id", "")))
    return planned


def build_partition_context(
    partition_paths: List[str],
    read_text_fn: Any,
    file_truncate_chars: int,
    max_files: int,
    max_chars: int,
    tail_chars: int,
) -> Tuple[str, Dict[str, int], List[Dict[str, Any]]]:
    chunks: List[str] = []
    file_entries: List[Dict[str, Any]] = []
    skipped_files = 0
    context_bytes = 0
    truncated_files = 0
    tail_snippet_files = 0

    for path_str in partition_paths:
        if len(chunks) >= max_files:
            skipped_files += 1
            continue

        content = read_text_fn(path_str)
        original_chars = len(content)
        truncated = False
        used_tail = False

        if len(content) > file_truncate_chars:
            head_chars = max(file_truncate_chars - max(tail_chars, 0), 0)
            head_part = content[:head_chars]
            tail_part = content[-tail_chars:] if tail_chars > 0 else ""
            content = (
                f"{head_part}\n...[TRUNCATED_HEAD]...\n"
                + (f"\n...[TRUNCATED_TAIL]...\n{tail_part}" if tail_part else "")
            )
            truncated = True
            used_tail = bool(tail_part)

        chunk_text = f"--- FILE: {path_str} ---\n{content}\n"
        chunk_bytes = len(chunk_text.encode("utf-8"))

        if chunks and (context_bytes + chunk_bytes > max_chars):
            skipped_files += 1
            continue

        if not chunks and chunk_bytes > max_chars:
            encoded = chunk_text.encode("utf-8")
            head_len = max(max_chars - max(tail_chars, 0), 0)
            head = encoded[:head_len].decode("utf-8", errors="ignore")
            tail = encoded[-tail_chars:].decode("utf-8", errors="ignore") if tail_chars > 0 else ""
            chunk_text = (
                f"{head}\n...[CONTEXT_TRUNCATED_FOR_LIMIT]...\n"
                + (f"{tail}\n" if tail else "")
            )
            chunk_bytes = len(chunk_text.encode("utf-8"))
            truncated = True
            used_tail = bool(tail)

        chunks.append(chunk_text)
        context_bytes += chunk_bytes

        if truncated:
            truncated_files += 1
        if used_tail:
            tail_snippet_files += 1

        file_entries.append(
            {
                "path": path_str,
                "source_chars": original_chars,
                "injected_bytes": chunk_bytes,
                "truncated": truncated,
                "used_tail_snippet": used_tail,
            }
        )

    context = "\n".join(chunks)
    stats = {
        "files_total": len(partition_paths),
        "files_included": len(chunks),
        "files_skipped": skipped_files,
        "context_bytes": len(context.encode("utf-8")),
        "truncated_files": truncated_files,
        "tail_snippet_files": tail_snippet_files,
    }
    return context, stats, file_entries


def estimate_tokens_from_text(text: str) -> int:
    if not text:
        return 0
    return max(int(len(text) / 4), 1)
