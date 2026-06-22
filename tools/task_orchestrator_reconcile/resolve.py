from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import ACTIVE_DOPEMUX_DB_SLUG


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def insert_database_decisions(
    conn: sqlite3.Connection,
    *,
    import_run_id: str,
    archive_sha256: str,
) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT source_db_slug, source_database_path, source_schema_hash,
               source_mtime_utc, adjudication_class, canonical_treatment
        FROM source_databases
        ORDER BY source_db_slug
        """
    ).fetchall()
    created_at = utc_now()
    for row in rows:
        decision = (
            "promote_to_current"
            if row["source_db_slug"] == ACTIVE_DOPEMUX_DB_SLUG
            else "provenance_only"
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO reconciliation_decisions (
                source_db_slug, source_database_path, source_schema_hash,
                source_table, source_row_id, source_mtime_utc, import_run_id,
                archive_sha256, decision_type, decision, reason, evidence_ref,
                created_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_db_slug"],
                row["source_database_path"],
                row["source_schema_hash"],
                "DATABASE_INDEX.csv",
                row["source_db_slug"],
                row["source_mtime_utc"],
                import_run_id,
                archive_sha256,
                "database_adjudication",
                decision,
                row["canonical_treatment"],
                row["adjudication_class"],
                created_at,
            ),
        )
    return dict(
        Counter(
            row["decision"]
            for row in conn.execute(
                "SELECT decision FROM reconciliation_decisions "
                "WHERE decision_type = 'database_adjudication'"
            )
        )
    )


def materialize_current_work_items(conn: sqlite3.Connection) -> int:
    decision_id = conn.execute(
        """
        SELECT id FROM reconciliation_decisions
        WHERE source_db_slug = ? AND decision_type = 'database_adjudication'
        """,
        (ACTIVE_DOPEMUX_DB_SLUG,),
    ).fetchone()
    if decision_id is None:
        raise ValueError("active dopemux database decision is missing")

    conn.execute("DELETE FROM canonical_current_work_items")
    active_rows = conn.execute(
        """
        SELECT *
        FROM source_work_items
        WHERE source_db_slug = ?
        ORDER BY title, source_row_id
        """,
        (ACTIVE_DOPEMUX_DB_SLUG,),
    ).fetchall()
    for row in active_rows:
        conn.execute(
            """
            INSERT INTO canonical_current_work_items (
                source_db_slug, source_database_path, source_schema_hash,
                source_table, source_row_id, source_mtime_utc, import_run_id,
                archive_sha256, canonical_identity, role, status_label, priority,
                tags, title, summary, decision_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_db_slug"],
                row["source_database_path"],
                row["source_schema_hash"],
                row["source_table"],
                row["source_row_id"],
                row["source_mtime_utc"],
                row["import_run_id"],
                row["archive_sha256"],
                f"{row['source_db_slug']}:{row['source_row_id']}",
                row["role"],
                row["status_label"],
                row["priority"],
                row["tags"],
                row["title"],
                row["summary"],
                decision_id["id"],
            ),
        )
    return len(active_rows)


def duplicate_title_report(conn: sqlite3.Connection) -> dict[str, Any]:
    duplicates = []
    title_rows = conn.execute(
        """
        SELECT title, COUNT(DISTINCT source_db_slug) AS db_count, COUNT(*) AS row_count
        FROM source_work_items
        GROUP BY title
        HAVING db_count > 1
        ORDER BY db_count DESC, title
        """
    ).fetchall()
    for row in title_rows:
        entries = conn.execute(
            """
            SELECT source_db_slug, source_row_id, role, status_label
            FROM source_work_items
            WHERE title = ?
            ORDER BY source_db_slug, source_row_id
            """,
            (row["title"],),
        ).fetchall()
        duplicates.append(
            {
                "title": row["title"],
                "database_count": row["db_count"],
                "row_count": row["row_count"],
                "entries": [dict(entry) for entry in entries],
                "decision": "conflict_not_identity",
            }
        )
    return {"duplicate_title_conflicts": duplicates, "total": len(duplicates)}


def coldstart_report(conn: sqlite3.Connection, repo_root: Path) -> dict[str, Any]:
    active_rows = conn.execute(
        """
        SELECT source_row_id, role, status_label, title, summary, tags
        FROM source_work_items
        WHERE source_db_slug = ? AND (title LIKE '%COLDSTART%' OR tags LIKE '%coldstart%')
        ORDER BY title
        """,
        (ACTIVE_DOPEMUX_DB_SLUG,),
    ).fetchall()
    completed = {
        "TP-DMX-COLDSTART-L0-DEP-AUDIT-100": "#886",
        "TP-DMX-COLDSTART-SALVAGE-COLDSTART-LIB-101": "#887",
        "TP-DMX-COLDSTART-ORCH-HTTP-CUTOVER-109": "#888",
    }
    high_risk = {"107", "108", "113", "118"}
    items = []
    for row in active_rows:
        title = row["title"]
        proof_dir = repo_root / "proof" / title
        proof_json = proof_dir / "PROOF.json"
        if title in completed:
            classification = "repo_pr_proof_observed"
            decision = "accepted_do_not_rerun"
            evidence = {
                "pr": completed[title],
                "proof_json": str(proof_json) if proof_json.exists() else None,
                "proof_exists": proof_json.exists(),
            }
        elif title == "DMX-COLDSTART task-packet series":
            classification = "active_root_in_progress"
            decision = "remain_active_in_progress"
            evidence = {"role": row["role"], "status_label": row["status_label"]}
        elif title.endswith("-102"):
            classification = "explicit_blocked"
            decision = "keep_blocked_until_repo_packet_allowlist_exists"
            evidence = {"role": row["role"], "status_label": row["status_label"]}
        elif title.startswith("OP-DMX-COLDSTART"):
            classification = "operator_gate"
            decision = "operator_only_do_not_automate"
            evidence = {"role": row["role"]}
        else:
            packet_number = title.rsplit("-", 1)[-1]
            classification = "queue_only"
            decision = "do_not_infer_readiness_from_to_role"
            if packet_number in high_risk:
                classification = "queue_only_supervisor_required"
            evidence = {"role": row["role"]}
        items.append(
            {
                "source_row_id": row["source_row_id"],
                "title": title,
                "role": row["role"],
                "status_label": row["status_label"],
                "classification": classification,
                "decision": decision,
                "evidence": evidence,
            }
        )
    counts = Counter(item["classification"] for item in items)
    return {
        "active_db_slug": ACTIVE_DOPEMUX_DB_SLUG,
        "items": items,
        "classification_counts": dict(sorted(counts.items())),
        "root_decision": "remain_active_in_progress",
    }


def build_resolve_report(conn: sqlite3.Connection, repo_root: Path) -> dict[str, Any]:
    database_decisions = dict(
        Counter(
            row["decision"]
            for row in conn.execute(
                "SELECT decision FROM reconciliation_decisions "
                "WHERE decision_type = 'database_adjudication'"
            )
        )
    )
    current_count = conn.execute(
        "SELECT COUNT(*) AS count FROM canonical_current_work_items"
    ).fetchone()["count"]
    class_counts = dict(
        Counter(
            row["adjudication_class"]
            for row in conn.execute("SELECT adjudication_class FROM source_databases")
        )
    )
    return {
        "active_db_slug": ACTIVE_DOPEMUX_DB_SLUG,
        "database_decisions": database_decisions,
        "source_database_classes": dict(sorted(class_counts.items())),
        "canonical_current_work_items": current_count,
        "duplicate_titles": duplicate_title_report(conn),
        "coldstart": coldstart_report(conn, repo_root),
    }
