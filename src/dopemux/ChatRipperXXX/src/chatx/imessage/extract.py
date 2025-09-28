"""Core iMessage extraction logic - row to Message mapping."""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from chatx.schemas.message import CanonicalMessage


# Apple Core Data reference date: 2001-01-01 00:00:00 UTC
APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


def extract_messages(
    db_path: Path,
    contact: str,
    *,
    include_attachments: bool = False,
    copy_binaries: bool = False,
    thumbnails: bool = False,
    transcribe_audio: str = "off",
    out_dir: Path,
    backup_dir: Optional[Path] = None,
) -> Iterator[CanonicalMessage]:
    """Extract iMessage conversations for a contact.
    
    Args:
        db_path: Path to chat.db file
        contact: Phone number, email, or contact identifier
        include_attachments: Whether to include attachment metadata
        copy_binaries: Whether to copy attachment files to out_dir
        transcribe_audio: Transcription mode ('local' or 'off')
        out_dir: Output directory for files and reports
        
    Yields:
        CanonicalMessage objects with full fidelity (replies, reactions, attachments)
    """
    from chatx.imessage.db import copy_db_for_readonly, open_ro
    from chatx.schemas.message import SourceRef
    
    # Safe DB copy and read-only access
    with copy_db_for_readonly(db_path) as temp_db:
        conn = open_ro(temp_db)
        
        try:
            # Resolve contact to handle IDs  
            handle_ids = resolve_contact_handles(conn, contact)
            if not handle_ids:
                return  # No messages found for contact
            
            # Get conversation GUIDs for this contact
            conv_guids = get_conversation_guids(conn, handle_ids)
            
            # Extract messages for each conversation
            for conv_guid in conv_guids:
                yield from extract_messages_for_conversation(
                    conn,
                    conv_guid,
                    str(db_path),
                    include_attachments,
                    copy_binaries,
                    thumbnails,
                    transcribe_audio,
                    out_dir,
                    backup_dir,
                )
                
        finally:
            conn.close()


def extract_messages_for_conversation(
    conn: sqlite3.Connection,
    conv_guid: str,
    original_db_path: str,
    include_attachments: bool,
    copy_binaries: bool,
    thumbnails: bool,
    transcribe_audio: str,
    out_dir: Path,
    backup_dir: Optional[Path] = None,
) -> Iterator[CanonicalMessage]:
    """Extract messages for a specific conversation."""
    from chatx.schemas.message import SourceRef
    
    # SQL to get all messages with handle info and reaction/reply metadata
    query = """
    SELECT 
        m.ROWID,
        m.guid,
        m.text,
        m.attributedBody,
        m.is_from_me,
        m.service,
        m.date,
        m.handle_id,
        h.id as handle_address,
        c.guid as chat_guid,
        m.associated_message_guid,
        m.associated_message_type
    FROM message m
    JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
    JOIN chat c ON cmj.chat_id = c.ROWID
    LEFT JOIN handle h ON m.handle_id = h.ROWID
    WHERE c.guid = ?
    ORDER BY m.date ASC
    """
    
    cursor = conn.execute(query, (conv_guid,))
    
    # Collect all message data first for two-pass processing
    all_rows = cursor.fetchall()
    
    # First pass: build lookup tables and separate regular messages from reactions
    messages_by_guid = {}  # guid -> CanonicalMessage
    messages_by_rowid = {}  # rowid -> CanonicalMessage  
    reactions_data = []    # List of reaction data to process
    regular_messages = []  # List of regular messages to yield
    
    for row in all_rows:
        (
            msg_rowid, guid, text, attributed_body, is_from_me, service, date,
            handle_id, handle_address, chat_guid, associated_message_guid, associated_message_type
        ) = row
        
        from chatx.imessage.reactions import is_reaction, is_reply, get_reaction_type

        # Skip reactions in first pass - we'll fold them into parent messages
        if is_reaction(associated_message_type or 0):
            reaction_type = get_reaction_type(associated_message_type)

            # For custom emoji reactions, use the text field as the reaction content
            if reaction_type == "custom" and text:
                reaction_display = text  # The actual emoji
            else:
                reaction_display = reaction_type  # Traditional tapback name

            reactions_data.append({
                'rowid': msg_rowid,
                'guid': guid,
                'is_from_me': is_from_me,
                'handle_address': handle_address,
                'handle_id': handle_id,
                'target_guid': associated_message_guid,
                'reaction_type': reaction_display,
                'timestamp': date
            })
            continue
        
        # Determine sender information
        if is_from_me:
            sender = "Me"
            sender_id = "me"
        else:
            sender = handle_address or f"Unknown_{handle_id}"
            sender_id = handle_address or f"unknown_{handle_id}"
        
        # Handle text content (normalize attributed body if present and no plain text)
        message_text = text
        raw_attr_b64: str | None = None
        if attributed_body and not text:
            try:
                from chatx.imessage.body_normalize import normalize_attributed_body
                normalized = normalize_attributed_body(attributed_body)
                if normalized:
                    message_text = normalized
                import base64
                raw_attr_b64 = base64.b64encode(attributed_body).decode("ascii")
            except Exception:
                # Keep placeholder on failure
                message_text = message_text or "[ATTRIBUTED_BODY_CONTENT]"
        
        # Determine reply threading (will be resolved after all messages collected)
        reply_to_guid = None
        if is_reply(associated_message_type or 0, bool(associated_message_guid)):
            reply_to_guid = associated_message_guid

        # Convert Apple timestamp to ISO-8601 UTC and parse to datetime
        from chatx.imessage.time import to_iso_utc
        ts_iso = to_iso_utc(date) or datetime.now(timezone.utc).isoformat()
        # Create message with reactions/replies support
        message = CanonicalMessage(
            msg_id=f"msg_{msg_rowid}",
            conv_id=chat_guid or f"conv_{conv_guid}",
            platform="imessage",
            timestamp=datetime.fromisoformat(ts_iso.replace('Z', '+00:00')),
            sender=sender,
            sender_id=sender_id,
            is_me=bool(is_from_me),
            text=message_text,
            reply_to_msg_id=None,  # Will be set in third pass
            reactions=[],  # Will be populated in second pass
            attachments=[],  # Will be populated after message creation
            source_ref=SourceRef(
                guid=guid or f"msg_{msg_rowid}",
                path=original_db_path
            ),
            source_meta={
                "rowid": msg_rowid,
                "service": service,
                "date_raw": date,
                "has_attributed_body": bool(attributed_body)
            }
        )
        # Preserve raw attributedBody for provenance
        if raw_attr_b64:
            message.source_meta.setdefault("raw", {})
            message.source_meta["raw"]["attributed_body"] = raw_attr_b64

        # Add pseudonymous sender token (does not change sender_id to keep compatibility)
        try:
            from chatx.identity.normalize import load_local_salt, pseudonymize
            salt, _ = load_local_salt()
            message.source_meta["sender_pid"] = pseudonymize(sender_id or sender, salt)
        except Exception:
            # Non-fatal if identity module not available
            pass
        
        # Store in lookup tables
        if guid:
            messages_by_guid[guid] = message
        messages_by_rowid[msg_rowid] = message
        regular_messages.append((message, reply_to_guid))  # Store with reply info
    
    # Second pass: fold reactions into parent messages
    for reaction_data in reactions_data:
        target_guid = reaction_data['target_guid']
        if target_guid and target_guid in messages_by_guid:
            target_message = messages_by_guid[target_guid]
            
            # Create reaction object
            from chatx.schemas.message import Reaction
            from_name = reaction_data['handle_address'] or f"unknown_{reaction_data['handle_id']}" if not reaction_data['is_from_me'] else "me"
            ts_val = (
                datetime.fromisoformat((to_iso_utc(reaction_data['timestamp']) or datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
                if reaction_data['timestamp'] else datetime.now(timezone.utc)
            )
            # De-duplicate: skip if an identical reaction already exists
            dup = any(
                (r.kind == reaction_data['reaction_type'] and r.from_ == from_name and int(r.ts.timestamp()) == int(ts_val.timestamp()))
                for r in target_message.reactions
            )
            if dup:
                continue
            reaction = Reaction(
                kind=reaction_data['reaction_type'],
                **{"from": from_name},
                ts=ts_val,
            )
            
            # Add to target message reactions list
            target_message.reactions.append(reaction)
    
    # Third pass: resolve reply threading
    for message, reply_to_guid in regular_messages:
        if reply_to_guid and reply_to_guid in messages_by_guid:
            target_message = messages_by_guid[reply_to_guid]
            message.reply_to_msg_id = target_message.msg_id
    
    # Fourth pass: extract and attach attachment metadata
    if include_attachments:
        from chatx.imessage.attachments import (
            extract_attachment_metadata,
            copy_attachment_files,
            generate_thumbnail_files,
        )
        from chatx.imessage.transcribe import (
            is_audio_attachment,
            transcribe_local,
            check_attachment_file_exists,
        )
        
        attachments_with_transcripts = 0
        failed_transcriptions = 0
        dedupe_map: Dict[str, str] = {}

        for message, _ in regular_messages:
            # Extract attachment metadata
            attachments = extract_attachment_metadata(conn, message.source_meta["rowid"]) 
            
            # Copy binary files if requested
            if copy_binaries and attachments:
                attachments, dedupe_map = copy_attachment_files(
                    attachments, out_dir, dedupe_map=dedupe_map
                )
                # Emit attachment hashes into source_meta for observability/dedupe
                infos = []
                for att in attachments:
                    if att.abs_path:
                        file_hash = att.source_meta.get("hash", {}).get("sha256")
                        if file_hash:
                            infos.append(
                                {
                                    "filename": att.filename,
                                    "hash": file_hash,
                                    "path": att.abs_path,
                                }
                            )
                if infos:
                    message.source_meta.setdefault("attachments_info", infos)
            
            # Process audio transcription if enabled
            if transcribe_audio != "off" and attachments:
                for attachment in attachments:
                    # Check if this attachment is audio
                    if is_audio_attachment(
                        attachment.mime_type, 
                        attachment.uti, 
                        attachment.filename
                    ):
                        # Determine path for transcription
                        audio_path: Optional[Path] = None
                        if copy_binaries and attachment.abs_path:
                            audio_path = Path(attachment.abs_path)
                        else:
                            # Try to find file in default Messages attachments location
                            attachments_dir = Path.home() / "Library" / "Messages" / "Attachments"
                            if check_attachment_file_exists(attachment.filename):
                                audio_path = attachments_dir / attachment.filename
                            # If in backup mode, resolve via Manifest.db (hashed fileID path)
                            elif backup_dir is not None and attachment.filename:
                                try:
                                    from chatx.imessage.attachments import _relative_sms_attachments_path
                                    from chatx.imessage.backup import resolve_backup_file
                                    rel = _relative_sms_attachments_path(attachment.filename)
                                    if rel:
                                        audio_path = resolve_backup_file(Path(backup_dir), "HomeDomain", rel)
                                except Exception:
                                    audio_path = None

                        # Attempt transcription if file exists
                        if audio_path and audio_path.exists():
                            engine = "whisper" if transcribe_audio == "local" else "mock"
                            transcript_result = transcribe_local(audio_path, engine=engine)
                            
                            if transcript_result:
                                # Store transcript in message source_meta for provenance
                                if "transcripts" not in message.source_meta:
                                    message.source_meta["transcripts"] = []
                                
                                message.source_meta["transcripts"].append({
                                    "filename": attachment.filename,
                                    "transcript": transcript_result["transcript"],
                                    "engine": transcript_result["engine"],
                                    "confidence": transcript_result["confidence"]
                                })
                                
                                attachments_with_transcripts += 1
                            else:
                                failed_transcriptions += 1
            
            # Add attachments to message
            message.attachments = attachments
            # Generate thumbnails on demand
            if thumbnails and attachments:
                try:
                    from chatx.imessage.attachments import generate_thumbnail_files
                    thumb_map = generate_thumbnail_files(attachments, out_dir, backup_dir)
                    # Record a representative thumbnail path for observability
                    if thumb_map:
                        first_path = next(iter(thumb_map.values()))
                        message.source_meta.setdefault("image", {})["thumb_path"] = first_path
                except Exception:
                    pass
    
    # Yield all regular messages (now with reactions, replies, and attachments resolved)
    for message, _ in regular_messages:
        yield message


def get_conversation_guids(conn: sqlite3.Connection, handle_ids: List[int]) -> List[str]:
    """Get conversation GUIDs that involve the specified handles."""
    if not handle_ids:
        return []
    
    # Build query for conversations involving any of these handles
    placeholders = ",".join("?" * len(handle_ids))
    query = f"""
    SELECT DISTINCT c.guid
    FROM chat c
    JOIN chat_message_join cmj ON c.ROWID = cmj.chat_id  
    JOIN message m ON cmj.message_id = m.ROWID
    WHERE m.handle_id IN ({placeholders})
       OR m.is_from_me = 1  -- Include our own messages in these chats
    """
    
    cursor = conn.execute(query, handle_ids)
    return [row[0] for row in cursor if row[0]]


# Legacy kept for backward import stability in tests if any; use time.to_iso_utc instead.
def apple_timestamp_to_iso(apple_timestamp: int) -> str:  # pragma: no cover
    from chatx.imessage.time import to_iso_utc
    iso = to_iso_utc(apple_timestamp)
    if iso:
        return iso
    # Fallback: treat as nanoseconds relative to epoch for legacy tests
    try:
        seconds = apple_timestamp / 1_000_000_000
        dt = APPLE_EPOCH + timedelta(seconds=seconds)
        return dt.isoformat().replace('+00:00', 'Z')
    except Exception:
        return APPLE_EPOCH.isoformat().replace('+00:00', 'Z')


def resolve_contact_handles(conn: sqlite3.Connection, contact: str) -> List[int]:
    """Resolve contact identifier to all associated handle ROWIDs.
    
    Args:
        conn: SQLite database connection
        contact: Phone number, email, or name to resolve
        
    Returns:
        List of handle ROWIDs associated with the contact
    """
    handle_rowids = []
    
    # Direct exact match first
    cursor = conn.execute("SELECT ROWID FROM handle WHERE id = ?", (contact,))
    exact_match = cursor.fetchone()
    if exact_match:
        handle_rowids.append(exact_match[0])
    
    # Phone number variations (basic normalization)
    if contact.startswith('+') or contact.replace('-', '').replace('(', '').replace(')', '').replace(' ', '').isdigit():
        # Try different phone number formats
        normalized = ''.join(c for c in contact if c.isdigit())
        variations = [
            contact,
            f"+1{normalized}" if len(normalized) == 10 else contact,
            f"+{normalized}",
            normalized,
            f"({normalized[:3]}) {normalized[3:6]}-{normalized[6:]}" if len(normalized) == 10 else contact
        ]
        
        for variation in variations:
            cursor = conn.execute("SELECT ROWID FROM handle WHERE id = ?", (variation,))
            result = cursor.fetchone()
            if result and result[0] not in handle_rowids:
                handle_rowids.append(result[0])
    
    # Partial matching for emails and names (case insensitive)
    cursor = conn.execute(
        "SELECT ROWID FROM handle WHERE LOWER(id) LIKE LOWER(?)",
        (f"%{contact}%",)
    )
    for row in cursor:
        if row[0] not in handle_rowids:
            handle_rowids.append(row[0])
    
    return handle_rowids
