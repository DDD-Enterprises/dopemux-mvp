from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any


def create_instagram_zip_fixture(tmp_dir: Path) -> Path:
    """Create a synthetic Instagram export ZIP matching expected messages."""
    zip_path = tmp_dir / "instagram_fixture.zip"
    thread = "mythread_xx"

    part1 = {
        "participants": [{"name": "Me"}, {"name": "Friend"}],
        "messages": [
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
        "title": thread,
        "thread_path": f"messages/inbox/{thread}",
        "thread_type": "Regular",
        "is_still_participant": True,
    }

    part2 = {
        "participants": [{"name": "Me"}, {"name": "Friend"}],
        "messages": [
            {
                "sender_name": "Friend",
                "timestamp_ms": 1_700_000_200_000,
                "content": "Photo",
                "photos": [
                    {"uri": f"messages/inbox/{thread}/photos/001.jpg"}
                ],
            }
        ],
        "title": thread,
        "thread_path": f"messages/inbox/{thread}",
        "thread_type": "Regular",
        "is_still_participant": True,
    }

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"messages/inbox/{thread}/message_1.json", json.dumps(part1))
        zf.writestr(f"messages/inbox/{thread}/message_2.json", json.dumps(part2))

    return zip_path


def get_expected_instagram_messages() -> list[dict[str, Any]]:
    """Return expected canonical messages for the synthetic Instagram ZIP."""
    return [
        {
            "msg_id": "ig:mythread_xx:1700000000000:0",
            "conv_id": "mythread_xx",
            "platform": "instagram",
            "timestamp": "2023-11-14T22:13:20+00:00",
            "sender": "Friend",
            "sender_id": "Friend",
            "is_me": False,
            "text": "Hi",
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        {
            "msg_id": "ig:mythread_xx:1700000100000:1",
            "conv_id": "mythread_xx",
            "platform": "instagram",
            "timestamp": "2023-11-14T22:15:00+00:00",
            "sender": "Me",
            "sender_id": "Me",
            "is_me": True,
            "text": "Hello",
            "reply_to_msg_id": None,
            "reactions": [
                {"from": "Friend", "kind": "❤️", "ts": "2023-11-14T22:15:00.100000Z"}
            ],
            "attachments": [],
        },
        {
            "msg_id": "ig:mythread_xx:1700000200000:0",
            "conv_id": "mythread_xx",
            "platform": "instagram",
            "timestamp": "2023-11-14T22:16:40+00:00",
            "sender": "Friend",
            "sender_id": "Friend",
            "is_me": False,
            "text": "Photo",
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [
                {
                    "type": "image",
                    "filename": "messages/inbox/mythread_xx/photos/001.jpg",
                    "abs_path": None,
                    "mime_type": None,
                    "uti": None,
                    "transfer_name": None,
                }
            ],
        },
    ]

