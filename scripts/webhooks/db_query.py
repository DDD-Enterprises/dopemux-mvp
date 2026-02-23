#!/usr/bin/env python3
import sqlite3
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[2]
    db_path = root / ".dopemux" / "webhook_receiver" / "webhook_receiver.db"

    if not db_path.exists():
        print(f"Error: DB not found at {db_path}", file=sys.stderr)
        print("Start the webhook receiver and send a test payload first.", file=sys.stderr)
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT count(*) as total FROM webhook_events")
        total_webhooks = cursor.fetchone()['total']

        cursor.execute("SELECT count(*) as total FROM run_events")
        total_runs = cursor.fetchone()['total']

        print(f"--- Webhook DB Stats ---")
        print(f"Total Webhook Events: {total_webhooks}")
        print(f"Total Run Events:     {total_runs}")
        print(f"------------------------")

        cursor.execute("""
            SELECT event_id, event_type, provider, dedupe_key, created_at
            FROM run_events
            ORDER BY created_at DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            print("\nLast 5 Run Events:")
            for row in rows:
                d = dict(row)
                print(f" [{d['created_at']}] {d['provider']} | type={d['event_type']} | id={d['event_id']} | dedupe={str(d['dedupe_key'])[:8]}...")
        else:
            print("\nNo run events found yet.")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
