"""iMessage attachment processing utilities."""

import shutil
import sqlite3
from pathlib import Path
from typing import Optional

from chatx.media.hash import sha256_stream
from chatx.schemas.message import Attachment
from chatx.media.thumbnail import generate_thumbnail

# UTI to attachment type mapping (Apple Uniform Type Identifiers)
UTI_TYPE_MAP: dict[str, str] = {
    # Images
    "public.jpeg": "image",
    "public.png": "image", 
    "public.tiff": "image",
    "public.gif": "image",
    "public.heic": "image",
    "public.heif": "image",
    "com.apple.private.live-photo": "image",
    
    # Videos
    "public.mpeg-4": "video",
    "public.quicktime-movie": "video",
    "public.avi": "video",
    "com.apple.m4v-video": "video",
    "public.3gpp": "video",
    
    # Audio
    "public.mp3": "audio",
    "public.mpeg-4-audio": "audio",
    "com.apple.m4a-audio": "audio",
    "public.aiff-audio": "audio",
    "public.wav": "audio",
    "com.apple.coreaudio-format": "audio",
    
    # Documents
    "com.adobe.pdf": "file",
    "com.microsoft.word.doc": "file",
    "org.openxmlformats.wordprocessingml.document": "file",
    "com.microsoft.excel.xls": "file",
    "com.microsoft.powerpoint.ppt": "file",
    "public.plain-text": "file",
    "public.rtf": "file",
    
    # Archives
    "public.zip-archive": "file",
    "public.tar-archive": "file",
    "com.apple.binhex-archive": "file",
}

# MIME type fallback mapping
MIME_TYPE_MAP: dict[str, str] = {
    # Images
    "image/jpeg": "image",
    "image/png": "image",
    "image/gif": "image",
    "image/tiff": "image",
    "image/heic": "image",
    "image/heif": "image",
    
    # Videos  
    "video/mp4": "video",
    "video/quicktime": "video",
    "video/avi": "video",
    "video/3gpp": "video",
    
    # Audio
    "audio/mpeg": "audio",
    "audio/mp3": "audio", 
    "audio/mp4": "audio",
    "audio/wav": "audio",
    "audio/aiff": "audio",
    
    # Documents
    "application/pdf": "file",
    "application/msword": "file",
    "application/vnd.ms-excel": "file",
    "application/vnd.ms-powerpoint": "file",
    "text/plain": "file",
    "application/rtf": "file",
    
    # Archives
    "application/zip": "file",
    "application/x-tar": "file",
}


def _find_attachment_source(
    attachment: Attachment, backup_dir: Optional[Path] = None
) -> Optional[Path]:
    """Locate the source file for an attachment if present."""
    attachments_dir = Path.home() / "Library" / "Messages" / "Attachments"

    source_path: Optional[Path] = None
    if attachment.abs_path:
        candidate = Path(attachment.abs_path)
        if candidate.exists():
            return candidate

    if attachment.filename:
        # Try backup resolution
        if backup_dir:
            try:
                rel = _relative_sms_attachments_path(attachment.filename)
                if rel:
                    from chatx.imessage.backup import resolve_backup_file

                    source_path = resolve_backup_file(backup_dir, "HomeDomain", rel)
            except Exception:
                source_path = None

        # Fallback to local paths
        if source_path is None:
            potential = [
                attachments_dir / attachment.filename,
                attachments_dir / "Attachments" / attachment.filename,
                Path(attachment.filename),
            ]
            for path in potential:
                if path.exists():
                    source_path = path
                    break

    return source_path


def determine_attachment_type(uti: Optional[str], mime_type: Optional[str], filename: Optional[str]) -> str:
    """Determine attachment type from UTI, MIME type, and filename.
    
    Args:
        uti: Apple UTI (Uniform Type Identifier)
        mime_type: MIME type
        filename: Original filename
        
    Returns:
        Attachment type: "image", "video", "audio", "file", or "unknown"
    """
    # Try UTI first (most reliable on macOS)
    if uti and uti in UTI_TYPE_MAP:
        return UTI_TYPE_MAP[uti]
    
    # Fallback to MIME type
    if mime_type and mime_type in MIME_TYPE_MAP:
        return MIME_TYPE_MAP[mime_type]
    
    # Last resort: filename extension
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.heic', '.heif'}:
            return "image"
        elif ext in {'.mp4', '.mov', '.avi', '.mkv', '.3gp'}:
            return "video"
        elif ext in {'.mp3', '.m4a', '.wav', '.aiff', '.flac'}:
            return "audio"
        elif ext in {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.zip', '.tar'}:
            return "file"
    
    return "unknown"


def extract_attachment_metadata(
    conn: sqlite3.Connection,
    message_rowid: int
) -> list[Attachment]:
    """Extract attachment metadata for a message.
    
    Args:
        conn: SQLite database connection
        message_rowid: Message ROWID to get attachments for
        
    Returns:
        List of attachment metadata objects
    """
    query = """
    SELECT 
        a.ROWID,
        a.filename,
        a.uti,
        a.mime_type,
        a.transfer_name,
        a.total_bytes,
        a.created_date,
        a.start_date
    FROM attachment a
    JOIN message_attachment_join maj ON a.ROWID = maj.attachment_id
    WHERE maj.message_id = ?
    """
    
    cursor = conn.execute(query, (message_rowid,))
    attachments = []
    
    for row in cursor:
        (rowid, filename, uti, mime_type, transfer_name, total_bytes, created_date, start_date) = row
        
        # Determine attachment type
        att_type = determine_attachment_type(uti, mime_type, filename or transfer_name)
        
        # Use transfer_name if filename is None
        display_filename = filename or transfer_name or f"attachment_{rowid}"
        
        attachment = Attachment(
            type=att_type,
            filename=display_filename,
            abs_path=None,  # Will be set during file copying if requested
            mime_type=mime_type,
            uti=uti,
            transfer_name=transfer_name
        )
        
        attachments.append(attachment)
    
    return attachments


def copy_attachment_files(
    attachments: list[Attachment],
    out_dir: Path,
    backup_dir: Optional[Path] = None,
    *,
    dedupe_map: Optional[dict[str, str]] = None,
) -> tuple[list[Attachment], dict[str, str]]:
    """Copy attachment files to output directory with content hashing.

    Args:
        attachments: List of attachment metadata
        out_dir: Base output directory
        backup_dir: Optional MobileSync backup directory
        dedupe_map: Optional existing hash -> path mapping for deduplication

    Returns:
        Tuple of (updated attachments list, dedupe map)

    Uses content hashing for deduplication and collision avoidance:
    out_dir/attachments/<sha256[:2]>/<sha256>/<original_basename>
    """
    updated_attachments = []
    dedupe: dict[str, str] = dedupe_map or {}

    for attachment in attachments:
        # Resolve source file location
        source_path = _find_attachment_source(attachment, backup_dir)

        # Copy file if found
        if source_path and source_path.exists():
            try:
                # Compute content hash
                file_hash = compute_file_hash(source_path)

                # Determine destination path based on dedupe map
                if file_hash in dedupe:
                    dest_path = Path(dedupe[file_hash])
                else:
                    dest_subdir = out_dir / "attachments" / file_hash[:2]
                    dest_subdir.mkdir(parents=True, exist_ok=True)
                    dest_filename = f"{file_hash}_{Path(attachment.filename).name}"
                    dest_path = dest_subdir / dest_filename
                    if not dest_path.exists():
                        shutil.copy2(source_path, dest_path)
                    dedupe[file_hash] = str(dest_path)

                # Update attachment with copied file path and hash metadata
                attachment.abs_path = str(dest_path)
                attachment.source_meta.setdefault("hash", {})["sha256"] = file_hash

            except (OSError, IOError, shutil.Error):
                # File copy failed, but continue with metadata
                pass
        
        updated_attachments.append(attachment)
    
    return updated_attachments, dedupe


def _relative_sms_attachments_path(filename: str) -> Optional[str]:
    """Extract relative 'Library/SMS/Attachments/..' path from any filename string.

    Accepts absolute paths and returns the subpath starting at 'Library/SMS/Attachments'.
    Returns None if the pattern is not present and the filename is not a relative SMS path.
    """
    try:
        if not filename:
            return None
        marker = "Library/SMS/Attachments"
        if marker in filename:
            idx = filename.index(marker)
            return filename[idx:]
        # If already looks relative to Library/SMS/Attachments, accept it
        if filename.startswith("Library/SMS/Attachments/"):
            return filename
    except Exception:
        return None
    return None


def generate_thumbnail_files(
    attachments: list[Attachment],
    out_dir: Path,
    backup_dir: Optional[Path] = None,
) -> dict[str, str]:
    """Generate thumbnails for image attachments.

    Returns mapping of attachment filenames to thumbnail paths."""

    thumb_paths: dict[str, str] = {}

    for attachment in attachments:
        if attachment.type != "image":
            continue

        source_path = _find_attachment_source(attachment, backup_dir)
        if not source_path or not source_path.exists():
            continue

        file_hash = compute_file_hash(source_path)
        thumb_dir = out_dir / "thumbnails" / file_hash[:2]
        thumb_path = thumb_dir / f"{file_hash}.jpg"

        if not thumb_path.exists():
            try:
                generate_thumbnail(source_path, thumb_path)
            except Exception:
                continue

        if attachment.filename is not None:
            thumb_paths[attachment.filename] = str(thumb_path)

    return thumb_paths


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    return sha256_stream(file_path)
