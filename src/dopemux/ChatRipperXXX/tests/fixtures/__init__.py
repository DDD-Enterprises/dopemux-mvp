"""Test fixtures for ChatX extractors."""

import sqlite3
import tempfile
from pathlib import Path
from typing import Any


def create_imessage_test_db() -> Path:
    """Create a temporary iMessage test database with comprehensive test data.
    
    Returns:
        Path to the created temporary database file
    """
    # Create temporary database file
    temp_dir = Path(tempfile.mkdtemp(prefix="chatx_test_"))
    db_path = temp_dir / "test_chat.db"
    
    # Read SQL fixture file
    fixtures_dir = Path(__file__).parent
    sql_file = fixtures_dir / "imessage_test_data.sql"
    
    with open(sql_file) as f:
        sql_content = f.read()
    
    # Create and populate database
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql_content)
        conn.commit()
    
    return db_path


def get_expected_messages() -> list[dict[str, Any]]:
    """Get expected canonical messages for testing extraction results.
    
    Returns:
        List of expected message dictionaries matching the test data
    """
    return [
        {
            "msg_id": "1",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "+15551234567",
            "sender_id": "+15551234567",
            "is_me": False,
            "text": "Hello there!",
            "reply_to_msg_id": None,
            "reactions": [
                # msg-001 gets emphasize reaction from msg_id 10
                {"from": "Me", "kind": "emphasize"}
            ],
            "attachments": [],
        },
        {
            "msg_id": "2",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "Me",
            "sender_id": "me",
            "is_me": True,
            "text": "Hey! How are you?",
            "reply_to_msg_id": None,
            "reactions": [
                # msg-002 gets laugh reaction from msg_id 9
                {"from": "+15551234567", "kind": "laugh"}
            ],
            "attachments": [],
        },
        {
            "msg_id": "3",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "+15551234567",
            "sender_id": "+15551234567",
            "is_me": False,
            "text": "I'm doing well, thanks for asking",
            "reply_to_msg_id": None,
            "reactions": [
                # msg-003 gets love reaction from msg_id 8
                {"from": "Me", "kind": "love"}
            ],
            "attachments": [],
        },
        {
            "msg_id": "4",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "Me",
            "sender_id": "me",
            "is_me": True,
            "text": "Want to grab lunch sometime?",
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        {
            "msg_id": "5",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "+15551234567",
            "sender_id": "+15551234567",
            "is_me": False,
            "text": "Sure! How about tomorrow?",
            "reply_to_msg_id": "4",  # Reply to msg-004
            "reactions": [],
            "attachments": [],
        },
        {
            "msg_id": "6",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "Me",
            "sender_id": "me",
            "is_me": True,
            "text": "Perfect! Let's meet at noon.",
            "reply_to_msg_id": "5",  # Reply to msg-005
            "reactions": [
                # msg-006 gets like reaction from msg_id 7
                {"from": "+15551234567", "kind": "like"}
            ],
            "attachments": [],
        },
        # Messages with different timestamp formats
        {
            "msg_id": "11",
            "conv_id": "iMessage;-;friend@example.com",
            "platform": "imessage",
            "sender": "friend@example.com",
            "sender_id": "friend@example.com",
            "is_me": False,
            "text": "Testing nanosecond timestamps",
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        {
            "msg_id": "12",
            "conv_id": "iMessage;-;friend@example.com",
            "platform": "imessage",
            "sender": "Me",
            "sender_id": "me",
            "is_me": True,
            "text": "Testing microsecond timestamps",
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        # SMS message
        {
            "msg_id": "13",
            "conv_id": "iMessage;-;group123",  # Note: this might be wrong, need to check JOIN
            "platform": "imessage",
            "sender": "+15559876543",
            "sender_id": "+15559876543",
            "is_me": False,
            "text": "This is an SMS message",
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        # Message with attachment
        {
            "msg_id": "14",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "Me",
            "sender_id": "me",
            "is_me": True,
            "text": "Check out this photo!",
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [
                {
                    "type": "image",
                    "filename": "photo.jpg",
                    "mime_type": "image/jpeg",
                    "uti": "public.jpeg",
                    "transfer_name": "IMG_001.jpeg"
                }
            ],
        },
        # Edge cases
        {
            "msg_id": "16",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "Unknown",  # No handle_id
            "sender_id": "unknown",
            "is_me": False,
            "text": "Message with no handle",
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        {
            "msg_id": "17",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "Me",
            "sender_id": "me",
            "is_me": True,
            "text": None,  # Null text
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        {
            "msg_id": "18",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "+15551234567",
            "sender_id": "+15551234567",
            "is_me": False,
            "text": "",  # Empty text
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        # Modern format messages (macOS Ventura+ attributedBody)
        {
            "msg_id": "19",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "+15551234567",
            "sender_id": "+15551234567",
            "is_me": False,
            "text": "[ATTRIBUTED_BODY_CONTENT]",  # Decoded from attributedBody
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        {
            "msg_id": "20",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "Me",
            "sender_id": "me",
            "is_me": True,
            "text": "[ATTRIBUTED_BODY_CONTENT]",  # Decoded from attributedBody
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
        # iOS 16+ edited message (text from message_summary_info)
        {
            "msg_id": "21",
            "conv_id": "iMessage;-;+15551234567",
            "platform": "imessage",
            "sender": "Me",
            "sender_id": "me",
            "is_me": True,
            "text": "[EDITED_MESSAGE_CONTENT]",  # Decoded from message_summary_info
            "reply_to_msg_id": None,
            "reactions": [],
            "attachments": [],
        },
    ]
