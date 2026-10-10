#!/usr/bin/env python3
"""Move docs into the in-repo archive (git mv) and record them in a JSONL manifest.

Nothing is ever deleted. Exit codes: 0 success, 1 refusal, 2 usage error.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence


class Refusal(Exception):
    pass


def git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    if done.returncode != 0:
        raise Refusal(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def tracked_files(root: Path) -> List[str]:
    return [p for p in git(root, "ls-files", "-z").split("\0") if p]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_under(path: str, base: str) -> bool:
    return path == base or path.startswith(base + "/")


def rel_posix(root: Path, raw: str) -> str:
    resolved = (root / raw).resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        raise Refusal(f"path outside repo: {raw}")


def make_row(wave: str, reason: str, disposition: str, **fields: str) -> Dict[str, str]:
    return {
        "original_path": fields["original_path"],
        "archive_path": fields["archive_path"],
        "sha256": fields["sha256"],
        "source_commit": fields["source_commit"],
        "wave": wave,
        "reason": reason,
        "disposition_candidate": disposition,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def plan_moves(root: Path, args: argparse.Namespace, archive: str) -> List[List[str]]:
    tracked = tracked_files(root)
    pairs: List[List[str]] = []
    for raw in args.paths:
        rel = rel_posix(root, raw)
        if is_under(rel, archive) or is_under(archive, rel):
            raise Refusal(f"input is (or contains) the archive root: {raw}")
        files = [t for t in tracked if is_under(t, rel)]
        if not files:
            raise Refusal(f"not git-tracked: {raw}")
        pairs += [[f, f"{archive}/{args.wave}/{f}"] for f in files]
    for _, dest in pairs:
        if not is_under(rel_posix(root, dest), archive):
            raise Refusal(f"destination outside archive root: {dest}")
        if (root / dest).exists():
            raise Refusal(f"destination exists: {dest}")
    return pairs


def seed_rows(root: Path, args: argparse.Namespace, archive: str, manifest: str):
    done = set()
    if (root / manifest).exists():
        for line in (root / manifest).read_text().splitlines():
            done.add(json.loads(line)["archive_path"])
    files = sorted(f for f in tracked_files(root) if is_under(f, archive))
    files = [f for f in files if f != manifest]
    digests = {f: sha256_of(root / f) for f in files}
    first: Dict[str, str] = {}
    commit = git(root, "rev-parse", "HEAD").strip()
    rows = []
    for f in files:
        dup_of = first.setdefault(digests[f], f)
        if f in done:
            continue
        reason, disp = args.reason, args.disposition
        if dup_of != f:
            reason, disp = f"exact-duplicate-of:{dup_of}", "delete-later"
        rows.append(
            make_row(
                args.wave,
                reason,
                disp,
                original_path=f,
                archive_path=f,
                sha256=digests[f],
                source_commit=commit,
            )
        )
    return [], rows


def move_rows(root: Path, args: argparse.Namespace, archive: str, manifest: str):
    pairs = plan_moves(root, args, archive)
    commit = git(root, "rev-parse", "HEAD").strip()
    rows = [
        make_row(
            args.wave,
            args.reason,
            args.disposition,
            original_path=src,
            archive_path=dst,
            sha256=sha256_of(root / src),
            source_commit=commit,
        )
        for src, dst in pairs
    ]
    return pairs, rows


def run(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve()
    archive = rel_posix(root, args.archive_root)
    manifest = rel_posix(root, args.manifest)
    build = seed_rows if args.seed else move_rows
    pairs, rows = build(root, args, archive, manifest)
    for src, dst in pairs:
        print(f"{'WOULD MOVE' if args.dry_run else 'MOVE'} {src} -> {dst}")
    if args.dry_run:
        for row in rows:
            print("ROW " + json.dumps(row))
    else:
        for src, dst in pairs:
            (root / dst).parent.mkdir(parents=True, exist_ok=True)
            git(root, "mv", src, dst)
        if rows:
            (root / manifest).parent.mkdir(parents=True, exist_ok=True)
            with (root / manifest).open("a") as fh:
                fh.writelines(json.dumps(r) + "\n" for r in rows)
    print(f"moved={len(pairs)} recorded={len(rows)}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--wave", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument(
        "--disposition",
        default="keep",
        choices=["keep", "delete-later", "export-later"],
    )
    p.add_argument("--manifest", default="docs/archive/MANIFEST.jsonl")
    p.add_argument("--archive-root", default="docs/archive")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--seed", action="store_true")
    p.add_argument("paths", nargs="*")
    args = p.parse_args(argv)
    if args.seed == bool(args.paths):
        p.error("give paths to move, or --seed without paths")
    try:
        return run(args)
    except Refusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
