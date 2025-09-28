from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from chatx.instagram.extract import extract_messages_from_zip


def _write_json(zf: zipfile.ZipFile, name: str, obj: dict) -> None:
    buf = io.BytesIO(json.dumps(obj).encode("utf-8"))
    zi = zipfile.ZipInfo(filename=name)
    zf.writestr(zi, buf.getvalue())


def _make_thread_json(
    messages: list[dict],
    thread: str,
    participants: list[str] | None = None,
) -> dict:
    parts = participants or ["Me", "Friend"]
    return {
        "participants": [{"name": n} for n in parts],
        "messages": messages,
        "title": thread,
        "thread_path": f"messages/inbox/{thread}",
        "thread_type": "Regular",
        "is_still_participant": True,
    }


def test_instagram_zip_basic_merge_and_normalize(tmp_path: Path) -> None:
    zip_path = tmp_path / "ig.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Thread dir name
        thread = "mythread_xx"
        # Two parts message_1.json, message_2.json with ascending timestamps
        part1 = _make_thread_json(
            [
                {"sender_name": "Friend", "timestamp_ms": 1_700_000_000_000, "content": "Hi"},
                {
                    "sender_name": "Me",
                    "timestamp_ms": 1_700_000_100_000,
                    "content": "Hello",
                    "reactions": [
                        {
                            "actor": "Friend",
                            "reaction": "❤️",
                            "timestamp_ms": 1_700_000_100_100,
                        }
                    ],
                },
            ],
            thread,
        )
        part2 = _make_thread_json(
            [
                {
                    "sender_name": "Friend",
                    "timestamp_ms": 1_700_000_200_000,
                    "content": "Photo",
                    "photos": [
                        {"uri": f"messages/inbox/{thread}/photos/001.jpg"},
                    ],
                },
            ],
            thread,
        )

        _write_json(zf, f"messages/inbox/{thread}/message_1.json", part1)
        _write_json(zf, f"messages/inbox/{thread}/message_2.json", part2)

    messages = extract_messages_from_zip(zip_path)
    # Expect 3 messages in chronological order
    assert len(messages) == 3
    assert [m.text for m in messages] == ["Hi", "Hello", "Photo"]
    assert all(m.platform == "instagram" for m in messages)
    assert all(m.conv_id == "mythread_xx" for m in messages)

    # Reactions folded into second message
    assert len(messages[1].reactions) == 1
    r = messages[1].reactions[0]
    assert r.kind in ("❤️", "like")
    assert r.from_ == "Friend"
    # Attachments detected on third message
    assert len(messages[2].attachments) == 1
    assert messages[2].attachments[0].type == "image"
    assert messages[2].attachments[0].filename.endswith("/photos/001.jpg")

    # With me_username, mark authorship
    messages_me = extract_messages_from_zip(zip_path, me_username="Me")
    assert [m.is_me for m in messages_me] == [False, True, False]


def test_instagram_zip_path_traversal_detected(tmp_path: Path) -> None:
    zip_path = tmp_path / "ig_bad.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Legit entry
        _write_json(zf, "messages/inbox/thread/message_1.json", _make_thread_json([], "thread"))
        # Malicious traversal
        zi = zipfile.ZipInfo(filename="messages/inbox/thread/../../evil.txt")
        zf.writestr(zi, b"boom")

    with pytest.raises(ValueError):
        extract_messages_from_zip(zip_path)


def test_instagram_zip_filters_by_thread_participant_and_author(tmp_path: Path) -> None:
    zip_path = tmp_path / "ig_filters.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Thread A with FriendA
        tA = "thread_a"
        partA = _make_thread_json(
            [
                {"sender_name": "FriendA", "timestamp_ms": 1_700_000_000_000, "content": "a1"},
                {"sender_name": "Me", "timestamp_ms": 1_700_000_000_500, "content": "a2"},
            ],
            tA,
            participants=["Me", "FriendA"],
        )
        _write_json(zf, f"messages/inbox/{tA}/message_1.json", partA)

        # Thread B with FriendB
        tB = "thread_b"
        partB = _make_thread_json(
            [
                {"sender_name": "FriendB", "timestamp_ms": 1_700_000_100_000, "content": "b1"},
                {"sender_name": "Me", "timestamp_ms": 1_700_000_100_500, "content": "b2"},
            ],
            tB,
            participants=["Me", "FriendB"],
        )
        _write_json(zf, f"messages/inbox/{tB}/message_1.json", partB)

    # Filter by participant FriendA -> only thread_a messages
    msgs_thread = extract_messages_from_zip(zip_path, include_threads_with=["FriendA"])
    assert all(m.conv_id == "thread_a" for m in msgs_thread)
    assert [m.text for m in msgs_thread] == ["a1", "a2"]

    # Author-only FriendB -> only messages authored by FriendB across threads
    msgs_author = extract_messages_from_zip(zip_path, authors_only=["FriendB"])
    assert [m.text for m in msgs_author] == ["b1"]
