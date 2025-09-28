"""iMessage extractor for macOS/iOS chat.db SQLite databases."""

import plistlib
import shutil
import sqlite3
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from chatx.extractors.base import BaseExtractor, ExtractionError
from chatx.schemas.message import Attachment, CanonicalMessage, Reaction, SourceRef
from chatx.utils.logging import get_logger

logger = get_logger(__name__)

# Apple epoch starts at 2001-01-01T00:00:00Z
APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=UTC)

# Reaction type mappings
REACTION_TYPES = {
    2000: "love",
    2001: "like",
    2002: "dislike",
    2003: "laugh",
    2004: "emphasize",
    2005: "question",
}


class IMessageExtractor(BaseExtractor):
    """Extract messages from iMessage chat.db SQLite database.
    
    Implements the iMessage specification with support for:
    - Message extraction with proper Apple epoch conversion
    - Reaction folding into target messages
    - Reply chain resolution
    - Attachment metadata extraction
    - Lossless source_meta preservation
    """

    @property
    def platform(self) -> str:
        return "imessage"

    def validate_source(self) -> bool:
        """Validate that source is an iMessage database."""
        if not self.source_path.suffix == '.db':
            return False

        try:
            with sqlite3.connect(self.source_path) as conn:
                cursor = conn.cursor()
                # Check for required iMessage tables
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name IN ('message', 'chat', 'handle')
                    """
                )
                tables = {row[0] for row in cursor.fetchall()}
                return {'message', 'chat', 'handle'}.issubset(tables)
        except Exception as e:
            logger.warning(f"Failed to validate iMessage database: {e}")
            return False
    
    def _decode_attributed_body(self, attributed_body: bytes | memoryview | None) -> str | None:
        """Best‑effort decode of attributedBody to extract plain text.

        Tries plist parsing (binary or XML) first, then falls back to a UTF‑8
        heuristic. If no meaningful text is found, returns a placeholder to
        indicate attributed content is present.
        """
        if not attributed_body:
            return None

        try:
            if isinstance(attributed_body, memoryview):
                attributed_body = attributed_body.tobytes()

            # Attempt plist parsing (handles both binary and XML)

            try:
                data = plistlib.loads(attributed_body)
                text_candidate = self._extract_text_from_nested(data)
                if text_candidate:
                    return text_candidate
            except Exception as e:
                logger.debug(f"attributedBody plist parse failed: {e}")

            # Heuristic UTF‑8 scan as fallback
            decoded = attributed_body.decode("utf-8", errors="ignore")
            cleaned = ' '.join(''.join(
                ch if ch.isprintable() else ' ' for ch in decoded
            ).split())
            if cleaned and not cleaned.lower().startswith("bplist"):
                return cleaned
        except Exception as e:
            logger.warning(f"Failed to decode attributedBody: {e}")
            return "[ATTRIBUTED_BODY_CONTENT]"

        return "[ATTRIBUTED_BODY_CONTENT]"
    
    def _decode_message_summary_info(self, conn: sqlite3.Connection, msg_rowid: int) -> str | None:
        """Best‑effort decode of iOS 16+ message_summary_info (edited messages)."""
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content FROM message_summary_info WHERE message_rowid = ?",
                (msg_rowid,)
            )
            row = cursor.fetchone()
            if not row or not row[0]:
                return None

            blob = row[0]
            if isinstance(blob, memoryview):
                blob = blob.tobytes()

            if isinstance(blob, (bytes, bytearray)):
                try:
                    data = plistlib.loads(bytes(blob))
                    text_candidate = self._extract_text_from_nested(data)
                    if text_candidate:
                        return text_candidate
                except Exception as e:
                    logger.debug(f"message_summary_info plist parse failed: {e}")

                # Fallback: UTF‑8 heuristic
                try:
                    decoded = bytes(blob).decode("utf-8", errors="ignore")
                    cleaned = ' '.join(decoded.split())
                    if cleaned and not cleaned.lower().startswith("bplist"):
                        return cleaned
                except Exception:
                    pass
                return "[EDITED_MESSAGE_CONTENT]"

        except Exception as e:
            logger.warning(f"Failed to decode message_summary_info: {e}")
            return None
    
    def _extract_message_text(
        self, conn: sqlite3.Connection, msg_data: dict[str, Any]
    ) -> str | None:
        """Extract message text using modern format-aware approach.

        Handles the evolution of iMessage text storage:
        1. Legacy: Plain text in 'text' column (including None and empty strings)
        2. macOS Ventura+: Encoded in 'attributedBody' column
        3. iOS 16+: Edited messages in 'message_summary_info' table

        Args:
            conn: SQLite connection
            msg_data: Raw message row data

        Returns:
            Extracted message text or None
        """
        msg_rowid = msg_data.get('msg_rowid')
        logger.debug(f"Extracting text for message {msg_rowid}")
        
        # 1. Check legacy text column first (including None and empty strings)
        body = cast(str | None, msg_data.get("body"))
        logger.debug(f"Message {msg_rowid}: body = {body!r} (type: {type(body)})")
        if body is not None:  # Explicitly check for None to allow empty strings
            return body
            
        # 2. Try attributedBody for macOS Ventura+ messages
        body_rich = msg_data.get('body_rich')
        logger.debug(f"Message {msg_rowid}: body_rich = {body_rich!r}")
        if body_rich:
            decoded_text = self._decode_attributed_body(body_rich)
            logger.debug(f"Message {msg_rowid}: decoded_attributed_body = {decoded_text!r}")
            if decoded_text:
                return decoded_text
                
        # 3. Try message_summary_info for iOS 16+ edited messages
        if msg_rowid:
            summary_text = self._decode_message_summary_info(conn, msg_rowid)
            logger.debug(f"Message {msg_rowid}: decoded_summary_info = {summary_text!r}")
            if summary_text:
                return summary_text
                
        # 4. Return None if no text found in any format
        logger.debug(f"Message {msg_rowid}: returning None")
        return None

    def _convert_apple_timestamp(self, ts: float | None) -> datetime | None:
        """Convert Apple timestamp to UTC datetime using shared helper."""
        from chatx.imessage.time import to_iso_utc
        iso = to_iso_utc(ts)
        if not iso:
            return None
        # Normalize 'Z' to +00:00 for parsing
        return datetime.fromisoformat(iso.replace('Z', '+00:00'))

    def _extract_text_from_nested(self, obj: Any) -> str | None:
        """Search nested structures for plausible text and return the longest string.

        Traverses dicts/lists and prefers common text keys when available.
        """
        best: str | None = None

        def consider(s: str | None) -> None:
            nonlocal best
            if not s:
                return
            s_trim = ' '.join(s.split())
            if not s_trim:
                return
            if best is None or len(s_trim) > len(best):
                best = s_trim

        try:
            if isinstance(obj, str):
                consider(obj)
            elif isinstance(obj, dict):
                # Check likely keys first
                for k in ("string", "text", "body", "summary", "NS.string"):
                    v = obj.get(k)
                    if isinstance(v, str):
                        consider(v)
                for v in obj.values():
                    res = self._extract_text_from_nested(v)
                    if isinstance(res, str):
                        consider(res)
            elif isinstance(obj, list | tuple | set):
                for v in obj:
                    res = self._extract_text_from_nested(v)
                    if isinstance(res, str):
                        consider(res)
        except Exception:
            pass

        return best
    
    def _copy_database(self) -> Path:
        """Copy database to temporary location to avoid file locks.
        
        Returns:
            Path to temporary database copy
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="chatx_imessage_"))
        temp_db = temp_dir / "chat.db"

        # Copy main database
        shutil.copy2(self.source_path, temp_db)

        # Copy WAL file if present
        wal_path = self.source_path.with_suffix('.db-wal')
        if wal_path.exists():
            temp_wal = temp_db.with_suffix('.db-wal')
            shutil.copy2(wal_path, temp_wal)

        # Copy SHM file if present
        shm_path = self.source_path.with_suffix('.db-shm')
        if shm_path.exists():
            temp_shm = temp_db.with_suffix('.db-shm')
            shutil.copy2(shm_path, temp_shm)

        return temp_db

    def _fetch_raw_messages(self, conn: sqlite3.Connection) -> list[dict[str, Any]]:
        """Fetch all messages with joins to related tables.
        
        Args:
            conn: SQLite connection
            
        Returns:
            List of raw message dictionaries
        """
        cursor = conn.cursor()

        # Determine if the message table includes the Ventura `attributedBody` column
        cursor.execute("PRAGMA table_info(message)")
        msg_columns = {row[1] for row in cursor.fetchall()}
        body_rich_select = (
            "m.attributedBody as body_rich,"
            if "attributedBody" in msg_columns
            else "NULL as body_rich,"
        )

        def col(name: str, alias: str) -> str:
            return f"m.{name} as {alias}" if name in msg_columns else f"NULL as {alias}"

        order_column = "m.date" if "date" in msg_columns else "m.ROWID"

        handle_join = (
            "LEFT JOIN handle h ON h.ROWID = m.handle_id"
            if "handle_id" in msg_columns
            else ""
        )
        handle_resolved_select = (
            "h.id as handle_id_resolved"
            if "handle_id" in msg_columns
            else "NULL as handle_id_resolved"
        )

        query = f"""
        SELECT
          m.ROWID as msg_rowid,
          m.guid as msg_guid,
          m.text as body,
          {body_rich_select}
          {col('is_from_me', 'is_me')},
          {col('handle_id', 'handle_id')},
          {col('service', 'service')},
          {col('date', 'date_raw')},
          {col('associated_message_guid', 'assoc_guid')},
          {col('associated_message_type', 'assoc_type')},
          {col('cache_has_attachments', 'has_attachments')},
          {col('balloon_bundle_id', 'balloon_bundle_id')},
          c.guid as chat_guid,
          {handle_resolved_select}
        FROM message m
        LEFT JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
        LEFT JOIN chat c ON c.ROWID = cmj.chat_id
        {handle_join}
        ORDER BY {order_column} ASC
        """

        cursor.execute(query)

        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]

    def _fetch_attachments(self, conn: sqlite3.Connection, msg_rowid: int) -> list[Attachment]:
        """Fetch attachments for a specific message.
        
        Args:
            conn: SQLite connection
            msg_rowid: Message ROWID
            
        Returns:
            List of Attachment objects
        """
        query = """
        SELECT
          a.filename,
          a.uti,
          a.mime_type,
          a.transfer_name,
          a.total_bytes,
          a.created_date,
          a.start_date,
          a.user_info
        FROM message_attachment_join maj
        JOIN attachment a ON maj.attachment_id = a.ROWID
        WHERE maj.message_id = ?
        """

        cursor = conn.cursor()
        try:
            cursor.execute(query, (msg_rowid,))
        except sqlite3.OperationalError:
            # Attachment tables not present in minimal databases
            return []

        attachments = []
        for row in cursor.fetchall():
            (
                filename,
                uti,
                mime_type,
                transfer_name,
                total_bytes,
                created_date,
                start_date,
                user_info,
            ) = row

            # Determine attachment type from UTI or filename
            att_type = "unknown"
            if uti:
                uti_lower = uti.lower()
                if ("image" in uti_lower or "jpeg" in uti_lower or "png" in uti_lower or
                    "gif" in uti_lower or "tiff" in uti_lower or "heic" in uti_lower):
                    att_type = "image"
                elif ("video" in uti_lower or "movie" in uti_lower or "mpeg" in uti_lower or
                      "mp4" in uti_lower or "quicktime" in uti_lower):
                    att_type = "video"
                elif "audio" in uti_lower or "mp3" in uti_lower or "wav" in uti_lower:
                    att_type = "audio"
                else:
                    att_type = "file"
            elif filename and '.' in filename:
                ext = filename.split('.')[-1].lower()
                if ext in {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'heic'}:
                    att_type = "image"
                elif ext in {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'm4v'}:
                    att_type = "video"
                elif ext in {'mp3', 'wav', 'aac', 'm4a', 'flac', 'ogg'}:
                    att_type = "audio"
                else:
                    att_type = "file"

            attachment = Attachment(
                type=att_type,  # type: ignore
                filename=filename or transfer_name or "unknown",
                mime_type=mime_type,
                uti=uti,
                transfer_name=transfer_name,
            )
            attachments.append(attachment)

        return attachments

    def _group_reactions(
        self, raw_messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[str, list[Reaction]]]:
        """Group reactions by target message and filter out reaction rows.
        
        Args:
            raw_messages: List of raw message dictionaries
            
        Returns:
            Tuple of (non-reaction messages, reactions grouped by target guid)
        """
        reactions_by_target: dict[str, list[Reaction]] = {}
        non_reaction_messages = []

        for msg in raw_messages:
            assoc_type = msg.get('assoc_type')
            assoc_guid = msg.get('assoc_guid')

            # Check if this is a reaction (tapback)
            if assoc_type in REACTION_TYPES and assoc_guid:
                # This is a reaction - fold it into target message
                reaction_kind = REACTION_TYPES[assoc_type]

                # Determine sender
                if msg['is_me']:
                    sender = "Me"
                else:
                    sender = msg.get('handle_id_resolved', 'Unknown')

                # Convert timestamp
                timestamp = self._convert_apple_timestamp(msg['date_raw'])
                if timestamp is None:
                    timestamp = datetime.now(UTC)

                reaction = Reaction(
                    from_=sender,  # type: ignore
                    kind=reaction_kind,
                    ts=timestamp
                )

                if assoc_guid not in reactions_by_target:
                    reactions_by_target[assoc_guid] = []
                reactions_by_target[assoc_guid].append(reaction)

                self.report.reactions_folded += 1

            else:
                # Regular message
                non_reaction_messages.append(msg)

        return non_reaction_messages, reactions_by_target

    def _build_guid_to_rowid_map(self, messages: list[dict[str, Any]]) -> dict[str, str]:
        """Build mapping from message GUID to ROWID for reply resolution.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary mapping GUID to string ROWID
        """
        return {msg['msg_guid']: str(msg['msg_rowid']) for msg in messages if msg.get('msg_guid')}

    def extract_messages(self) -> Iterator[CanonicalMessage]:
        """Extract messages from iMessage database."""
        if not self.validate_source():
            raise ExtractionError(f"Invalid iMessage database: {self.source_path}")

        # Copy database to temporary location
        temp_db = self._copy_database()

        try:
            with sqlite3.connect(temp_db) as conn:
                # Fetch all raw messages
                raw_messages = self._fetch_raw_messages(conn)
                logger.info(f"Found {len(raw_messages)} raw messages")

                # Group reactions and filter out reaction messages
                messages, reactions_by_target = self._group_reactions(raw_messages)
                logger.info(f"Grouped {self.report.reactions_folded} reactions")

                # Build GUID to ROWID mapping for reply resolution
                guid_to_rowid = self._build_guid_to_rowid_map(messages)

                # Process each message
                for msg in messages:
                    try:
                        # Convert timestamp
                        timestamp = self._convert_apple_timestamp(msg['date_raw'])
                        if timestamp is None:
                            timestamp = datetime.now(UTC)

                        # Determine sender
                        if msg['is_me']:
                            sender = "Me"
                            sender_id = "me"
                        else:
                            handle = msg.get('handle_id_resolved') or 'Unknown'
                            sender = handle
                            sender_id = handle.lower() if handle else "unknown"

                        # Handle replies
                        reply_to_msg_id = None
                        assoc_guid = msg.get('assoc_guid')
                        assoc_type = msg.get('assoc_type')

                        if assoc_guid and assoc_type not in REACTION_TYPES:
                            # This might be a reply
                            if assoc_guid in guid_to_rowid:
                                reply_to_msg_id = guid_to_rowid[assoc_guid]
                            else:
                                # Unresolved reply - track in source_meta
                                self.report.unresolved_replies += 1

                        # Get reactions for this message
                        msg_reactions = reactions_by_target.get(msg['msg_guid'], [])

                        # Fetch attachments
                        attachments = self._fetch_attachments(conn, msg['msg_rowid'])

                        # Build source_meta with all original fields
                        source_meta = {
                            'msg_rowid': msg['msg_rowid'],
                            'service': msg.get('service'),
                            'assoc_guid': msg.get('assoc_guid'),
                            'assoc_type': msg.get('assoc_type'),
                            'has_attachments': msg.get('has_attachments'),
                            'balloon_bundle_id': msg.get('balloon_bundle_id'),
                            'body_rich': msg.get('body_rich'),
                        }

                        # Remove None values
                        source_meta = {k: v for k, v in source_meta.items() if v is not None}

                        # Extract text using format-aware approach
                        message_text = self._extract_message_text(conn, msg)

                        # Create canonical message
                        canonical_msg = CanonicalMessage(
                            msg_id=str(msg['msg_rowid']),
                            conv_id=msg.get('chat_guid', 'unknown'),
                            platform="imessage",
                            timestamp=timestamp,
                            sender=sender,
                            sender_id=sender_id,
                            is_me=bool(msg['is_me']),
                            text=message_text,
                            reply_to_msg_id=reply_to_msg_id,
                            reactions=msg_reactions,
                            attachments=attachments,
                            source_ref=SourceRef(
                                guid=msg.get('chat_guid'),
                                path=str(self.source_path)
                            ),
                            source_meta=source_meta
                        )

                        yield canonical_msg

                    except Exception as e:
                        error_msg = (
                            f"Failed to process message {msg.get('msg_rowid', 'unknown')}: {e}"
                        )
                        logger.error(error_msg)
                        self.report.errors.append(error_msg)
                        continue

        finally:
            # Clean up temporary database
            try:
                shutil.rmtree(temp_db.parent)
            except Exception as e:
                logger.warning(f"Failed to clean up temp database: {e}")
