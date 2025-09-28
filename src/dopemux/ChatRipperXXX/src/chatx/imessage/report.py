"""Missing attachment reporting for iCloud eviction scenarios."""

import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional


class MissingAttachmentItem(NamedTuple):
    """Individual missing attachment reference."""
    conv_guid: str
    msg_id: str
    filename: str
    transfer_name: Optional[str] = None
    attachment_rowid: int = 0


def check_attachment_file_exists(filename: str) -> bool:
    """Check if attachment file exists on disk.
    
    Args:
        filename: Attachment filename to check
        
    Returns:
        True if file exists, False otherwise
    """
    if not filename:
        return False
    
    # Common macOS attachment paths
    attachments_dir = Path.home() / "Library" / "Messages" / "Attachments"
    potential_paths = [
        attachments_dir / filename,
        attachments_dir / "Attachments" / filename,  # Nested structure
        Path(filename)  # Absolute path case
    ]
    
    for path in potential_paths:
        if path.exists():
            return True
    
    return False


def scan_for_missing_attachments(
    conn: sqlite3.Connection,
    contact: Optional[str] = None
) -> List[MissingAttachmentItem]:
    """Scan database for missing attachment files.
    
    Args:
        conn: SQLite database connection
        contact: Optional contact filter (if None, scans all)
        
    Returns:
        List of missing attachment references
    """
    # Query to get all attachments with message/conversation context
    query = """
    SELECT 
        c.guid as conv_guid,
        m.ROWID as msg_rowid,
        a.ROWID as att_rowid,
        a.filename,
        a.transfer_name,
        m.guid as msg_guid
    FROM attachment a
    JOIN message_attachment_join maj ON a.ROWID = maj.attachment_id
    JOIN message m ON maj.message_id = m.ROWID
    JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
    JOIN chat c ON cmj.chat_id = c.ROWID
    """
    
    params = []
    
    # Add contact filter if specified
    if contact:
        # Need to resolve contact to handle IDs first
        from chatx.imessage.extract import resolve_contact_handles
        handle_ids = resolve_contact_handles(conn, contact)
        
        if handle_ids:
            placeholders = ",".join("?" * len(handle_ids))
            query += f" WHERE (m.handle_id IN ({placeholders}) OR m.is_from_me = 1)"
            params.extend(handle_ids)
    
    query += " ORDER BY c.guid, m.ROWID"
    
    cursor = conn.execute(query, params)
    missing_items = []
    
    for row in cursor:
        conv_guid, msg_rowid, att_rowid, filename, transfer_name, msg_guid = row
        
        # Check if file exists on disk
        if not check_attachment_file_exists(filename):
            missing_items.append(MissingAttachmentItem(
                conv_guid=conv_guid,
                msg_id=f"msg_{msg_rowid}",
                filename=filename or transfer_name or f"attachment_{att_rowid}",
                transfer_name=transfer_name,
                attachment_rowid=att_rowid
            ))
    
    return missing_items


def generate_missing_attachments_report(
    conn: sqlite3.Connection,
    out_dir: Path,
    contact: Optional[str] = None
) -> Dict[str, int]:
    """Generate report of missing/evicted attachment files.
    
    Args:
        conn: SQLite database connection  
        out_dir: Output directory for report file
        contact: Optional contact filter for targeted reporting
        
    Returns:
        Dictionary with per-conversation missing counts
        
    Creates out_dir/missing_attachments.json with detailed report
    for operator remediation. Exit code remains 0 (non-fatal).
    """
    # Scan for missing attachments
    missing_items = scan_for_missing_attachments(conn, contact)
    
    # Group by conversation
    per_conversation = defaultdict(int)
    items_by_conv = defaultdict(list)
    
    for item in missing_items:
        per_conversation[item.conv_guid] += 1
        items_by_conv[item.conv_guid].append({
            "conv_guid": item.conv_guid,
            "msg_id": item.msg_id,
            "filename": item.filename
        })
    
    # Build report data matching schema
    report_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contact": contact,
        "items": [
            {
                "conv_guid": item.conv_guid,
                "msg_id": item.msg_id,
                "filename": item.filename
            }
            for item in missing_items
        ],
        "summary": {
            "total_missing": len(missing_items),
            "per_conversation": dict(per_conversation)
        },
        "remediation_guidance": {
            "manual_steps": [
                "Open Messages app on the device where attachments are stored",
                "Navigate to affected conversations (see summary above)",
                "Check if attachments show 'Download' buttons - tap to download",
                "For iCloud-optimized attachments, ensure device has sufficient storage",
                "Wait for downloads to complete, then re-run extraction",
                "Alternative: Use 'Export Chat' feature in Messages app to get attachments",
                "Consider disabling 'Optimize Mac Storage' in iCloud Photos settings"
            ]
        }
    }
    
    # Write report to file
    report_path = out_dir / "missing_attachments.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    return dict(per_conversation)


def validate_missing_attachments_report(report_path: Path) -> bool:
    """Validate missing attachments report against JSON schema.
    
    Args:
        report_path: Path to the report JSON file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        import jsonschema
        
        # Load schema
        schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / "missing_attachments_report.schema.json"
        
        if not schema_path.exists():
            # Schema not available, skip validation
            return True
        
        with open(schema_path) as f:
            schema = json.load(f)
        
        # Load report data
        with open(report_path) as f:
            report_data = json.load(f)
        
        # Validate
        jsonschema.validate(report_data, schema)
        return True
        
    except ImportError:
        # jsonschema not available, skip validation
        return True
    except (jsonschema.ValidationError, json.JSONDecodeError, OSError):
        return False
