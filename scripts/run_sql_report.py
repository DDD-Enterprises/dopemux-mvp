#!/usr/bin/env python3
import argparse
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run a canned SQL report and output TSV")
    parser.add_argument("db", help="Path to SQLite DB (registries.db)")
    parser.add_argument("sql", help="Path to SQL file")
    parser.add_argument("--out", required=True, help="Output TSV path")
    args = parser.parse_args()

    db_path = Path(args.db)
    sql_path = Path(args.sql)
    out_path = Path(args.out)

    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")
    if not sql_path.exists():
        raise SystemExit(f"SQL file not found: {sql_path}")

    sql = sql_path.read_text(encoding="utf-8")
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    rows = cur.execute(sql).fetchall()
    headers = [d[0] for d in cur.description] if cur.description else []
    conn.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        if headers:
            f.write("\t".join(headers) + "\n")
        for r in rows:
            f.write("\t".join(str(v) if v is not None else "" for v in r) + "\n")

    print(f"✅ Wrote report: {out_path}")


if __name__ == "__main__":
    main()

