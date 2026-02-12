"""
CLI interface for Copilot Transcript Ingester.

Usage:
    python -m copilot_transcript_ingester ingest --session-id <UUID> [--since <ISO_TIMESTAMP>]
    python -m copilot_transcript_ingester stats --session-id <UUID>
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from .parser import JSONLParser
from .ingester import ChronicleIngester
from .mapper import EventTypeMapper


def get_session_dir(session_id: str) -> Path:
    """Get session directory from session ID."""
    copilot_dir = Path.home() / ".copilot" / "session-state" / session_id
    if not copilot_dir.exists():
        raise FileNotFoundError(f"Session directory not found: {copilot_dir}")
    return copilot_dir


def find_chronicle_db() -> Path:
    """Find Chronicle SQLite database."""
    # Search in working-memory-assistant/chronicle/
    possible_paths = [
        Path.home() / "code" / "dopemux-mvp" / "services" / "working-memory-assistant" / "chronicle" / "chronicle.db",
        Path.cwd() / "chronicle.db",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Chronicle database not found. "
        "Searched: services/working-memory-assistant/chronicle/chronicle.db"
    )


def cmd_ingest(args):
    """Ingest Copilot transcript into Chronicle."""
    try:
        # Locate session directory
        session_dir = get_session_dir(args.session_id)
        events_file = session_dir / "events.jsonl"

        if not events_file.exists():
            print(f"Error: events.jsonl not found in {session_dir}")
            return 1

        # Find Chronicle database
        db_path = find_chronicle_db()
        print(f"Using database: {db_path}")

        # Initialize ingester
        workspace_id = args.workspace_id or str(Path.home() / "code" / "dopemux-mvp")
        instance_id = args.instance_id or "copilot-cli-macos"

        ingester = ChronicleIngester(str(db_path), workspace_id, instance_id)
        ingester.connect()

        # Parse and ingest events
        print(f"Ingesting events from: {events_file}")
        parser = JSONLParser(str(events_file))

        # Get session metadata
        metadata = parser.get_session_metadata()
        print(f"Session metadata: {json.dumps(metadata, indent=2)}")

        # Parse events with optional since filter
        since = None
        if args.since:
            since = datetime.fromisoformat(args.since.rstrip("Z"))

        events = list(parser.parse_events(since=since))
        print(f"Parsed {len(events)} events")

        # Ingest events
        inserted = ingester.ingest_events(events, args.session_id)
        print(f"✅ Ingested {inserted}/{len(events)} events into Chronicle")

        # Print stats
        stats = ingester.get_ingestion_stats(args.session_id)
        print(f"\nEvent type distribution:")
        for event_type, count in stats["event_counts"].items():
            print(f"  {event_type}: {count}")

        ingester.disconnect()
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_stats(args):
    """Show ingestion statistics for a session."""
    try:
        db_path = find_chronicle_db()

        workspace_id = args.workspace_id or str(Path.home() / "code" / "dopemux-mvp")
        instance_id = args.instance_id or "copilot-cli-macos"

        ingester = ChronicleIngester(str(db_path), workspace_id, instance_id)
        ingester.connect()

        stats = ingester.get_ingestion_stats(args.session_id)
        print(json.dumps(stats, indent=2))

        ingester.disconnect()
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list_sessions(args):
    """List available Copilot CLI sessions."""
    try:
        session_dir = Path.home() / ".copilot" / "session-state"
        if not session_dir.exists():
            print(f"No Copilot session directory found at {session_dir}")
            return 1

        sessions = sorted([d.name for d in session_dir.iterdir() if d.is_dir()])
        print(f"Found {len(sessions)} sessions:\n")

        for session_id in sessions:
            session_path = session_dir / session_id
            events_file = session_path / "events.jsonl"

            if events_file.exists():
                parser = JSONLParser(str(events_file))
                count = parser.count_events()
                metadata = parser.get_session_metadata()
                start_time = metadata.get("start_timestamp", "unknown") if metadata else "unknown"
                print(f"  {session_id}")
                print(f"    Events: {count}")
                print(f"    Started: {start_time}\n")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest Copilot CLI transcripts into Dope-Memory Chronicle"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Ingest command
    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest Copilot session transcript"
    )
    ingest_parser.add_argument(
        "--session-id", required=True, help="Copilot session UUID"
    )
    ingest_parser.add_argument(
        "--workspace-id",
        default=None,
        help="Workspace ID (default: ~/code/dopemux-mvp)",
    )
    ingest_parser.add_argument(
        "--instance-id",
        default=None,
        help="Instance ID (default: copilot-cli-macos)",
    )
    ingest_parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Only ingest events after this ISO timestamp",
    )
    ingest_parser.set_defaults(func=cmd_ingest)

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show ingestion statistics")
    stats_parser.add_argument(
        "--session-id", required=True, help="Copilot session UUID"
    )
    stats_parser.add_argument(
        "--workspace-id",
        default=None,
        help="Workspace ID (default: ~/code/dopemux-mvp)",
    )
    stats_parser.add_argument(
        "--instance-id",
        default=None,
        help="Instance ID (default: copilot-cli-macos)",
    )
    stats_parser.set_defaults(func=cmd_stats)

    # List sessions command
    list_parser = subparsers.add_parser("list", help="List available sessions")
    list_parser.set_defaults(func=cmd_list_sessions)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
