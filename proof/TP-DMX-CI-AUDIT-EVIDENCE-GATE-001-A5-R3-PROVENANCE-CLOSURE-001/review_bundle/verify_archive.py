"""Verify supplied supervisor archive without executing its contents."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile

import jsonschema

root = Path(sys.argv[1]).resolve()
repo = Path.cwd()
counts = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def child(directory, name):
    path = PurePosixPath(name)
    assert not path.is_absolute() and ".." not in path.parts, name
    target = directory / path
    assert target.resolve().is_relative_to(root), name
    return target


def checksums(directory, manifest):
    rows = []
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        target = child(directory, name.lstrip("*"))
        assert target.is_file(), name
        assert digest(target.read_bytes()) == expected, name
        rows.append(target.relative_to(root).as_posix())
    assert len(rows) == len(set(rows))
    return rows


def inventory(directory, manifest):
    data = json.loads(manifest.read_text())
    entries = data["files"] if isinstance(data, dict) else data
    assert len(entries) == len({e["path"] for e in entries})
    for entry in entries:
        data = child(directory, entry["path"]).read_bytes()
        assert len(data) == entry["bytes"], entry["path"]
        assert digest(data) == entry["sha256"], entry["path"]
    return len(entries)


assert not any(p.is_symlink() for p in root.rglob("*"))
listed = checksums(root, root / "06_MANIFEST/SHA256SUMS.txt")
counts["top_level_checksums"] = len(listed)
actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
unlisted = sorted(actual - set(listed))
assert set(unlisted) <= {".DS_Store", "06_MANIFEST/SHA256SUMS.txt"}, unlisted
counts["top_level_inventory"] = inventory(root, root / "06_MANIFEST/FILE_INVENTORY.json")
expanded = root / "03_WSAC_PROGRAM/expanded/DMX-WHOLE-SYSTEM-ARCH-CONVERGENCE-001"
counts["internal_checksums"] = len(checksums(expanded, expanded / "manifest/SHA256SUMS.txt"))
counts["internal_inventory"] = inventory(expanded, expanded / "manifest/FILE_INVENTORY.json")
original = root / "03_WSAC_PROGRAM/original"
archive_path = original / "DMX-WHOLE-SYSTEM-ARCH-CONVERGENCE-001-R2.zip"
checksums(original, original / (archive_path.name + ".sha256"))
archive_sha = digest(archive_path.read_bytes())
assert archive_sha == "7a6d8dff43f7e67312bcc13a107f68cfaa2c2b2c3eef364fdd3071cce5a21e97"
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    members = [m for m in archive.infolist() if not m.is_dir()]
    assert len(members) == len({m.filename for m in members})
    for member in members:
        assert not stat.S_ISLNK(member.external_attr >> 16), member.filename
        target = child(root / "03_WSAC_PROGRAM/expanded", member.filename)
        assert target.read_bytes() == archive.read(member), member.filename
    counts["zip_files"] = len(members)
    assert {m.filename for m in members} == {
        p.relative_to(root / "03_WSAC_PROGRAM/expanded").as_posix()
        for p in expanded.rglob("*") if p.is_file()
    }

json_files = list(root.rglob("*.json"))
for path in json_files:
    json.loads(path.read_text())
counts["json_files"] = len(json_files)
schema_path = repo / "docs/03-reference/spec/dopetask/dopetask-canonical-spec.json"
schema = json.loads(schema_path.read_text())
packets = list(expanded.glob("task-packets/*.json"))
packets += list(root.glob("04_CI_AUDIT_EVIDENCE_GATE/**/TP-*.json"))
for path in packets:
    jsonschema.validate(json.loads(path.read_text()), schema)
counts["packets_schema_validated"] = len(packets)

lineage_count = 0
for manifest in root.glob("04_CI_AUDIT_EVIDENCE_GATE/**/MANIFEST.json"):
    data = json.loads(manifest.read_text())
    entries = data.get("files")
    if isinstance(entries, dict):
        pairs = [(name, value["sha256"] if isinstance(value, dict) else value)
                 for name, value in entries.items()]
    elif isinstance(entries, list):
        pairs = [(entry["file"], entry["sha256"]) for entry in entries]
        for entry in entries:
            assert len(child(manifest.parent, entry["file"]).read_bytes()) == entry["bytes"]
    elif "packet_sha256" in data:
        pairs = [(data["packet"], data["packet_sha256"]), (data["launch"], data["launch_sha256"])]
    elif "json_sha256" in data:
        pairs = [(data["packet_id"] + ".json", data["json_sha256"]),
                 (data["packet_id"] + ".md", data["runbook_sha256"])]
    else:
        raise AssertionError("Unsupported lineage manifest: " + manifest.name)
    for name, expected in pairs:
        assert digest(child(manifest.parent, name).read_bytes()) == expected, name
        lineage_count += 1
counts["lineage_checksums"] = lineage_count
scan = subprocess.run(
    ["gitleaks", "dir", str(root), "--redact=100", "--no-banner", "--max-archive-depth", "4"],
    capture_output=True, text=True,
)
assert scan.returncode == 0, "Secret scan failed; raw output withheld"
print(json.dumps({
    "status": "PASS",
    "scope": "Archive integrity, inventories, nested ZIP, JSON syntax, packet schemas, secret scan; not runtime truth.",
    "counts": counts,
    "unmanifested": unlisted,
    "excluded_authority": [".DS_Store"],
    "manifest_self_hash": "SHA256SUMS cannot include its own digest; external authenticity is not proven.",
    "sha256sums_sha256": digest((root / "06_MANIFEST/SHA256SUMS.txt").read_bytes()),
    "wsac_zip_sha256": archive_sha,
    "task_packet_schema_sha256": digest(schema_path.read_bytes()),
    "secret_scan_exit_code": scan.returncode,
    "secret_scan_archive_depth": 4,
}, indent=2, sort_keys=True))
