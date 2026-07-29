#!/usr/bin/env python3
"""Validation gates for the TP-DMX-FDOS-004 ChatGPT Project 40-source package.

Runs: source count, filename, source identity (bytes match EXECUTION_BASE_SHA),
hash, duplicate-content, JSON, YAML, open-PR conservation, and secret-scan
gates. Writes PACKAGE_VALIDATION.json with a PASS/FAIL result per gate and
exits non-zero if any gate fails.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SECRET_PATTERNS = [
    ("openai_style_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("private_key_pem", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("bearer_header_with_value", re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9\-_.]{20,}")),
]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--execution-base-sha", required=True)
    ap.add_argument("--package-dir", required=True)
    ap.add_argument("--open-pr-dir", required=True)
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    package_dir = Path(args.package_dir).resolve()
    upload_dir = package_dir / "UPLOAD_FILES"
    open_pr_dir = Path(args.open_pr_dir).resolve()

    gates = {}

    files = sorted(p for p in upload_dir.iterdir() if p.is_file())
    gates["source_count"] = {"pass": len(files) == 40, "detail": f"{len(files)} files"}

    names = [p.name for p in files]
    expected_slots = {f"{i:02d}" for i in range(1, 41)}
    got_slots = {n.split("_", 1)[0] for n in names}
    hidden = [n for n in names if n.startswith(".")]
    gates["filename"] = {
        "pass": len(set(names)) == len(names) and got_slots == expected_slots and not hidden,
        "detail": {"unique": len(set(names)) == len(names), "slots": sorted(got_slots), "hidden": hidden},
    }

    manifest = json.loads((upload_dir / "39_PROJECT_SOURCE_MANIFEST.json").read_text())

    # Manifest-to-disk coverage: every on-disk file must have exactly one
    # manifest entry naming it, and vice versa. Without this, a manifest entry
    # silently missing (or a bundle_filename typo) lets a corrupted/renamed
    # disk file pass every other gate uninspected.
    disk_names = {p.name for p in files}
    manifest_names = {entry["bundle_filename"] for entry in manifest["files"]}
    gates["manifest_disk_coverage"] = {
        "pass": disk_names == manifest_names,
        "detail": {
            "on_disk_only": sorted(disk_names - manifest_names),
            "manifest_only": sorted(manifest_names - disk_names),
        },
    }

    identity_failures = []
    hash_failures = []
    for entry in manifest["files"]:
        # Hash-check every entry that declares a sha256, not only
        # artifact_type=="copied_source" -- generated slots (38, 40) also
        # carry a real sha256 and must not be exempt from corruption checks.
        # Slot 39 (the manifest itself) is the sole legitimate null-sha256
        # entry (see build_chatgpt_project_sources.py's self-hash note).
        if entry.get("sha256"):
            path = upload_dir / entry["bundle_filename"]
            actual = path.read_bytes()
            if hashlib.sha256(actual).hexdigest() != entry["sha256"]:
                hash_failures.append(entry["bundle_filename"])

        if not entry.get("artifact_type") == "copied_source":
            continue
        path = upload_dir / entry["bundle_filename"]
        expected = subprocess.run(
            ["git", "show", f"{args.execution_base_sha}:{entry['source_path']}"],
            cwd=repo_root, capture_output=True, check=True,
        ).stdout
        actual = path.read_bytes()
        if expected != actual:
            identity_failures.append(entry["bundle_filename"])
        blob_sha = subprocess.run(
            ["git", "rev-parse", f"{args.execution_base_sha}:{entry['source_path']}"],
            cwd=repo_root, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if blob_sha != entry["source_blob_sha"]:
            identity_failures.append(f"{entry['bundle_filename']} (blob sha mismatch)")

    gates["source_identity"] = {"pass": not identity_failures, "detail": identity_failures}
    gates["hash"] = {"pass": not hash_failures, "detail": hash_failures}

    by_hash = {}
    for entry in manifest["files"]:
        if entry.get("sha256"):
            by_hash.setdefault(entry["sha256"], []).append(entry["bundle_filename"])
    dupes = {h: v for h, v in by_hash.items() if len(v) > 1}
    gates["duplicate_content"] = {"pass": not dupes, "detail": dupes}

    json_failures = []
    for p in files:
        if p.suffix == ".json":
            try:
                json.loads(p.read_text())
            except Exception as e:
                json_failures.append(f"{p.name}: {e}")
    gates["json"] = {"pass": not json_failures, "detail": json_failures}

    yaml_failures = []
    for p in files:
        if p.suffix in (".yaml", ".yml"):
            if yaml is None:
                yaml_failures.append(f"{p.name}: PyYAML not available -- NOT_AVAILABLE")
                continue
            try:
                yaml.safe_load(p.read_text())
            except Exception as e:
                yaml_failures.append(f"{p.name}: {e}")
    gates["yaml"] = {"pass": not yaml_failures, "detail": yaml_failures}

    initial = json.loads((open_pr_dir / "OPEN_PRS_INITIAL.json").read_text())
    ledger_text = (upload_dir / "40_OPEN_PR_IMPACT_LEDGER.md").read_text()
    ledger_pr_numbers = set(int(n) for n in re.findall(r"### PR #(\d+)", ledger_text))
    initial_numbers = set(pr["number"] for pr in initial)
    gates["open_pr_conservation"] = {
        "pass": ledger_pr_numbers == initial_numbers,
        "detail": {
            "initial_count": len(initial_numbers),
            "ledger_count": len(ledger_pr_numbers),
            "missing_from_ledger": sorted(initial_numbers - ledger_pr_numbers),
            "extra_in_ledger": sorted(ledger_pr_numbers - initial_numbers),
        },
    }

    secret_hits = []
    for p in files:
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for name, pattern in SECRET_PATTERNS:
            for m in pattern.finditer(text):
                secret_hits.append({"file": p.name, "pattern": name, "match_prefix": m.group(0)[:12]})
    gates["secret_scan"] = {"pass": not secret_hits, "detail": secret_hits}

    all_pass = all(g["pass"] for g in gates.values())
    result = {
        "package_disposition_input": manifest["package_disposition"],
        "all_gates_pass": all_pass,
        "gates": gates,
    }
    (package_dir / "PACKAGE_VALIDATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
