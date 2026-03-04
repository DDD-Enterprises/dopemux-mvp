#!/usr/bin/env python3
"""Ensure docs markdown files have valid, consistent YAML frontmatter.

- Repairs malformed YAML frontmatter where possible
- Adds missing fields required by docs validation hooks
- Supports checking specific files (pre-commit) or all docs (manual runs)
"""

import argparse
import datetime
import io
import os
import re
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import yaml


TODAY = datetime.date.today()
DEFAULT_OWNER = "@hu3mann"
DEFAULT_AUTHOR = "@hu3mann"
VALID_DOC_TYPES = {
    "adr",
    "rfc",
    "caveat",
    "pattern",
    "runbook",
    "tutorial",
    "how-to",
    "reference",
    "explanation",
}


def parse_frontmatter(text: str) -> Tuple[Optional[Dict], str, bool]:
    """Parse frontmatter block and attempt small YAML repairs."""
    if not text.startswith("---\n"):
        return None, text, False

    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text, False

    fm = text[4:end]
    body = text[end + 5 :]

    try:
        data = yaml.safe_load(fm) or {}
        return data if isinstance(data, dict) else None, body, False
    except Exception:
        repaired_fm = re.sub(
            r"(^|\n)(\s*owner\s*:\s*)(@[^\n]+)",
            r'\1\2"\3"',
            fm,
        )
        try:
            data = yaml.safe_load(repaired_fm) or {}
            return data if isinstance(data, dict) else None, body, True
        except Exception:
            return None, body, False


def build_frontmatter(data: Dict) -> str:
    buf = io.StringIO()
    yaml.safe_dump(data, buf, sort_keys=False)
    return f"---\n{buf.getvalue()}---\n"


def default_title(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()


def default_prelude(path: Path, title: str) -> str:
    doc_type = guess_type(str(path))
    return f"{title} ({doc_type}) for dopemux documentation and developer workflows."


def guess_type(path: str) -> str:
    p = path.replace("\\", "/")
    if "/90-adr/" in p or "/adr/" in p:
        return "adr"
    if "/91-rfc/" in p or "/rfc/" in p:
        return "rfc"
    if "/92-runbooks/" in p or "/runbooks/" in p:
        return "runbook"
    if "/01-tutorials/" in p or "/tutorials/" in p:
        return "tutorial"
    if "/02-how-to/" in p or "/how-to/" in p or "/deployment/" in p:
        return "how-to"
    if "/03-reference/" in p or "/reference/" in p or "/05-audit-reports/" in p or "/06-research/" in p or "/systems/" in p:
        return "reference"
    return "explanation"


def normalize_type(path: Path, value: object) -> str:
    if isinstance(value, str) and value in VALID_DOC_TYPES:
        return value
    return guess_type(str(path))


def normalize_status(doc_type: str, status: object) -> Optional[str]:
    if not isinstance(status, str):
        return None

    normalized = status.strip().lower()
    if doc_type == "adr" and normalized == "approved":
        return "accepted"
    return normalized


def ensure_type_specific_fields(data: Dict, path: Path) -> bool:
    changed = False
    doc_type = data.get("type", "explanation")

    if doc_type == "adr":
        status = normalize_status("adr", data.get("status"))
        if status and status != data.get("status"):
            data["status"] = status
            changed = True
        if "status" not in data:
            data["status"] = "proposed"
            changed = True
        if "graph_metadata" not in data or not isinstance(data.get("graph_metadata"), dict):
            data["graph_metadata"] = {"node_type": "ADR", "impact": "medium", "relates_to": []}
            changed = True
        if not data.get("prelude"):
            data["prelude"] = default_prelude(path, data["title"])
            changed = True

    elif doc_type == "rfc":
        status = normalize_status("rfc", data.get("status"))
        if status and status != data.get("status"):
            data["status"] = status
            changed = True
        if "status" not in data:
            data["status"] = "draft"
            changed = True
        if "derived_from" not in data:
            data["derived_from"] = []
            changed = True
        if not data.get("prelude"):
            data["prelude"] = default_prelude(path, data["title"])
            changed = True

    elif doc_type == "caveat":
        if "severity" not in data:
            data["severity"] = "medium"
            changed = True
        if "impact" not in data:
            data["impact"] = "medium"
            changed = True
        if not data.get("prelude"):
            data["prelude"] = default_prelude(path, data["title"])
            changed = True

    elif doc_type == "pattern":
        if "usage_context" not in data:
            data["usage_context"] = "general"
            changed = True
        if not data.get("prelude"):
            data["prelude"] = default_prelude(path, data["title"])
            changed = True

    return changed


def ensure_frontmatter(path: Path, fix: bool = False) -> bool:
    # Skip quarantined files
    if "docs/04-explanation/history/sourceFiles/" in str(path).replace("\\", "/"):
        return False

    text = path.read_text(encoding="utf-8")
    data, body, repaired = parse_frontmatter(text)
    changed = bool(repaired)

    if data is None:
        data = {}
        changed = True

    if not isinstance(data, dict):
        data = {}
        changed = True

    if "id" not in data:
        data["id"] = path.stem
        changed = True

    if "title" not in data:
        data["title"] = default_title(path)
        changed = True

    normalized_type = normalize_type(path, data.get("type"))
    if data.get("type") != normalized_type:
        data["type"] = normalized_type
        changed = True

    if "owner" not in data:
        data["owner"] = DEFAULT_OWNER
        changed = True

    if "author" not in data:
        data["author"] = DEFAULT_AUTHOR
        changed = True

    if "date" not in data:
        data["date"] = str(TODAY)
        changed = True

    if "last_review" not in data:
        data["last_review"] = str(TODAY)
        changed = True

    if "next_review" not in data:
        data["next_review"] = str(TODAY + datetime.timedelta(days=90))
        changed = True

    if "prelude" not in data:
        data["prelude"] = default_prelude(path, data["title"])
        changed = True

    changed = ensure_type_specific_fields(data, path) or changed

    if changed and fix:
        fm = build_frontmatter(data)
        path.write_text(fm + body.lstrip(), encoding="utf-8")

    return changed


def iter_markdown_files(cli_files: Iterable[str]) -> Iterable[Path]:
    files = [Path(p) for p in cli_files if p.endswith(".md")]
    if files:
        for path in files:
            if path.exists() and path.is_file():
                yield path
        return

    docs_root = Path("docs")
    if not docs_root.exists():
        return

    for path in docs_root.rglob("*.md"):
        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate/fix docs frontmatter")
    parser.add_argument("--fix", action="store_true", help="Apply fixes in place")
    parser.add_argument("files", nargs="*", help="Specific markdown files to validate")
    args = parser.parse_args()

    changed_files = []
    for path in iter_markdown_files(args.files):
        if ensure_frontmatter(path, fix=args.fix):
            changed_files.append(str(path))

    if changed_files:
        action = "Updated" if args.fix else "Needs update"
        print(f"{action} {len(changed_files)} file(s):")
        for path in changed_files:
            print(f" - {path}")
        # Always return 1 if files were changed/need change, to signal pre-commit
        return 1

    print("All docs have valid frontmatter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
