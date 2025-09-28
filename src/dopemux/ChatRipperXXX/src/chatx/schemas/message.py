"""Pydantic schemas for canonical message format."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Reaction(BaseModel):
    """Message reaction model."""
    
    from_: str = Field(..., alias="from", description="User who added the reaction")
    kind: str = Field(..., description="Reaction type (love, like, dislike, laugh, etc.)")
    ts: datetime = Field(..., description="Reaction timestamp")

    model_config = {"populate_by_name": True}


class Attachment(BaseModel):
    """Message attachment model."""
    
    type: Literal["image", "video", "audio", "file", "unknown"] = Field(
        ..., description="Attachment type"
    )
    filename: str = Field(..., description="Attachment filename")
    abs_path: str | None = Field(None, description="Absolute path when available (local only)")
    mime_type: str | None = Field(None, description="MIME type")
    uti: str | None = Field(None, description="Apple UTI when available")
    transfer_name: str | None = Field(None, description="Transfer name")
    # Keep attachment-specific metadata internal; exclude from JSON to satisfy schema
    source_meta: dict[str, Any] = Field(
        default_factory=dict, description="Attachment-specific metadata", exclude=True
    )


class SourceRef(BaseModel):
    """Source reference for traceability."""
    
    guid: str | None = Field(None, description="Conversation GUID (iMessage) or equivalent")
    path: str = Field(..., description="Original source path (e.g., chat.db)")


class CanonicalMessage(BaseModel):
    """Canonical message format (pre-redaction) for all platforms.
    
    This model represents the unified message format that all platform
    extractors should produce. It maintains fidelity to the original
    data while providing a consistent interface.
    """
    
    msg_id: str = Field(..., description="Stable message identifier (platform rowid or GUID)")
    conv_id: str = Field(..., description="Conversation/thread identifier")
    platform: Literal["imessage", "instagram", "whatsapp", "txt"] = Field(
        ..., description="Origin platform"
    )
    timestamp: datetime = Field(..., description="Message timestamp (UTC)")
    sender: str = Field(..., description="Displayable sender name or address; 'Me' permitted")
    sender_id: str = Field(..., description="Stable sender id: 'me' or normalized handle")
    is_me: bool = Field(..., description="Whether this message was sent by the user")
    text: str | None = Field(None, description="Raw message body; may be empty or null")
    reply_to_msg_id: str | None = Field(
        None, description="Parent message ID if this is a reply"
    )
    reactions: list[Reaction] = Field(default_factory=list, description="Message reactions")
    attachments: list[Attachment] = Field(default_factory=list, description="Message attachments")
    source_ref: SourceRef = Field(..., description="Source reference for traceability")
    source_meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Platform-specific raw fields; NEVER sent to cloud"
    )

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }
