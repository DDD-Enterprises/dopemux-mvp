"""Instagram official data ZIP extractor.

Reads ZIP entries streaming without extracting and normalizes messages to
CanonicalMessage records. Protects against Zip Slip/path traversal by validating
member paths before reading.
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence, Set

from chatx.schemas.message import Attachment, CanonicalMessage, Reaction, SourceRef


def _is_safe_member(name: str) -> bool:
    """Return True if the ZIP member path is safe (no abs/traversal)."""
    # Disallow absolute paths and any parent directory reference
    if name.startswith("/") or name.startswith("\\"):
        return False
    parts = Path(name).parts
    return all(p not in ("..", "") for p in parts)


def _iter_thread_json_entries(zf: zipfile.ZipFile) -> Iterator[tuple[str, zipfile.ZipInfo]]:
    """Yield (thread_dir, ZipInfo) for message_*.json entries under messages/inbox."""
    for info in zf.infolist():
        name = info.filename
        if not _is_safe_member(name):
            raise ValueError(f"Unsafe ZIP entry detected: {name}")
        # We only care about messages/inbox/<thread>/message_*.json
        p = Path(name)
        if len(p.parts) >= 4 and p.parts[0] == "messages" and p.parts[1] == "inbox":
            thread = p.parts[2]
            if p.name.lower().startswith("message_") and p.suffix.lower() == ".json":
                yield thread, info


def _participants_from_data(data: dict) -> List[str]:
    parts = data.get("participants") or []
    names: List[str] = []
    for p in parts:
        name = p.get("name") if isinstance(p, dict) else None
        if isinstance(name, str):
            names.append(name)
    return names


def _parse_message_items(
    thread: str,
    data: dict,
    *,
    authors_only: Optional[Set[str]] = None,
    me_username_cf: Optional[str] = None,
) -> Iterator[CanonicalMessage]:
    messages = data.get("messages") or []
    # Derive the source path hint if present (Instagram often stores 'thread_path')
    thread_path = data.get("thread_path") or f"messages/inbox/{thread}"

    # Build messages
    for idx, item in enumerate(messages):
        sender = item.get("sender_name") or "Unknown"
        ts_ms = item.get("timestamp_ms") or 0
        # Convert ms to UTC datetime
        ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
        text = item.get("content")

        # Attachments (reference only)
        attachments: List[Attachment] = []
        # Photos
        for photo in item.get("photos", []) or []:
            uri = photo.get("uri") or ""
            if isinstance(uri, str) and uri:
                attachments.append(Attachment(type="image", filename=uri, abs_path=None, mime_type=None, uti=None, transfer_name=None))
        # Videos
        for video in item.get("videos", []) or []:
            uri = video.get("uri") or ""
            if isinstance(uri, str) and uri:
                attachments.append(Attachment(type="video", filename=uri, abs_path=None, mime_type=None, uti=None, transfer_name=None))
        # Audio files
        for aud in item.get("audio_files", []) or []:
            uri = aud.get("uri") or ""
            if isinstance(uri, str) and uri:
                attachments.append(Attachment(type="audio", filename=uri, abs_path=None, mime_type=None, uti=None, transfer_name=None))

        # Reactions (fold into message)
        reactions: List[Reaction] = []
        for r in item.get("reactions", []) or []:
            actor = r.get("actor") or "Unknown"
            kind = r.get("reaction") or "like"
            r_ts = r.get("timestamp_ms") or ts_ms
            reactions.append(Reaction(kind=str(kind), **{"from": actor}, ts=datetime.fromtimestamp(r_ts / 1000.0, tz=timezone.utc)))

        # Apply author-only filter if provided
        if authors_only is not None and sender.casefold() not in authors_only:
            continue

        # Build deterministic msg_id (no stable id in export); combine ts and idx
        msg_id = f"ig:{thread}:{ts_ms}:{idx}"

        msg = CanonicalMessage(
            msg_id=msg_id,
            conv_id=thread,
            platform="instagram",
            timestamp=ts,
            sender=sender,
            sender_id=sender,  # Will be pseudonymized in PR-13
            is_me=(sender.casefold() == me_username_cf) if me_username_cf else False,
            text=text,
            reply_to_msg_id=None,
            reactions=reactions,
            attachments=attachments,
            source_ref=SourceRef(guid=None, path=thread_path),
            source_meta={"raw_keys": list(item.keys())},
        )
        # Add pseudonymous sender token into source_meta (keep sender_id for now)
        try:
            from chatx.identity.normalize import load_local_salt, pseudonymize
            salt, _ = load_local_salt()
            msg.source_meta["sender_pid"] = pseudonymize(sender, salt)
        except Exception:
            pass
        yield msg


def extract_messages_from_zip(
    zip_path: Path,
    *,
    include_threads_with: Optional[Sequence[str]] = None,
    authors_only: Optional[Sequence[str]] = None,
    me_username: Optional[str] = None,
) -> List[CanonicalMessage]:
    """Extract and normalize Instagram messages from the official data ZIP.

    Returns a merged, chronologically sorted list of CanonicalMessage.
    """
    results: List[CanonicalMessage] = []
    # Normalize filters (case-insensitive)
    thread_participant_filter: Optional[Set[str]] = None
    if include_threads_with:
        thread_participant_filter = {u.casefold() for u in include_threads_with}
    author_filter: Optional[Set[str]] = None
    if authors_only:
        author_filter = {u.casefold() for u in authors_only}
    me_username_cf: Optional[str] = me_username.casefold() if isinstance(me_username, str) else None
    with zipfile.ZipFile(zip_path, "r") as zf:
        entries = list(_iter_thread_json_entries(zf))
        # Sort by thread then by message file name natural ordering
        entries.sort(key=lambda t: (t[0], t[1].filename))
        for thread, info in entries:
            with zf.open(info, "r") as f:
                # Read JSON safely
                data = json.load(io.TextIOWrapper(f, encoding="utf-8"))
                # Thread-level participant filter
                if thread_participant_filter is not None:
                    participants = _participants_from_data(data)
                    participants_cf = {p.casefold() for p in participants}
                    if participants_cf.isdisjoint(thread_participant_filter):
                        continue
                for msg in _parse_message_items(
                    thread,
                    data,
                    authors_only=author_filter,
                    me_username_cf=me_username_cf,
                ):
                    results.append(msg)

    # Global chronological order
    results.sort(key=lambda m: m.timestamp)
    return results
