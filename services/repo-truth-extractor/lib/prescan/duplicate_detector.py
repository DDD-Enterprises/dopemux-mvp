import hashlib
import logging
import re
from pathlib import PurePosixPath
from .models import FileEntry, PrescanConfig

logger = logging.getLogger(__name__)

_VERSION_PATTERNS = [
    (re.compile(r"^(.+?)[-_]v(\d+)(\.|$)"), "v-suffix"),
    (re.compile(r"^(.+?)[-_](\d+)(\.|$)"), "num-suffix"),
    (
        re.compile(r"^(.+?)[-_](old|new|bak|backup|orig|copy)(\.|$)", re.I),
        "name-suffix",
    ),
    (re.compile(r"^(.+?)\.(v\d+)$"), "dotversion"),
]

class DuplicateDetector:
    def __init__(self, config: PrescanConfig):
        self.config = config

    def detect(self, entries: list[FileEntry]) -> dict:
        """Run all duplicate detection and return summary dictionaries."""
        self.detect_duplicates(entries)
        self.detect_version_chains(entries)
        
        groups = {}
        chains = {}
        for e in entries:
            if e.duplicate_group_id:
                groups.setdefault(e.duplicate_group_id, []).append(e.rel_path)
            if e.version_chain_id:
                chains.setdefault(e.version_chain_id, []).append({
                    "path": e.rel_path,
                    "ordinal": e.version_ordinal,
                    "is_latest": e.is_latest_version
                })
        return {"groups": groups, "chains": chains}

    def detect_duplicates(self, entries: list[FileEntry]) -> int:
        """
        Group included files by SHA256 hash.
        Marks duplicate_group_id/is_duplicate/canonical_duplicate in-place.
        Returns number of duplicate groups found.
        """
        hash_groups: dict[str, list[FileEntry]] = {}
        for e in entries:
            if e.include and e.content_hash and not e.is_ghost:
                hash_groups.setdefault(e.content_hash, []).append(e)

        groups_found = 0
        for h, group in hash_groups.items():
            if len(group) < 2:
                continue
            groups_found += 1
            group_id = h[:8]
            canonical = min(group, key=lambda x: len(x.rel_path))
            for e in group:
                e.duplicate_group_id = group_id
                if e is canonical:
                    e.is_duplicate = False
                else:
                    e.is_duplicate = True
                    e.canonical_duplicate = canonical.rel_path

        return groups_found

    def detect_version_chains(self, entries: list[FileEntry]) -> int:
        """
        Detect version chains from filename patterns (-v2, -2, -old, etc.).
        Assigns version_chain_id/version_ordinal/is_latest_version in-place.
        Returns number of chains found.
        """
        by_dir: dict[str, list[FileEntry]] = {}
        for e in entries:
            if not e.include and not e.is_ghost:
                continue
            d = str(PurePosixPath(e.rel_path).parent)
            by_dir.setdefault(d, []).append(e)

        chain_map: dict[str, list[FileEntry]] = {}
        for dir_path, dir_entries in by_dir.items():
            for e in dir_entries:
                fname = PurePosixPath(e.rel_path).stem
                ext = e.extension
                for pattern, _ in _VERSION_PATTERNS:
                    m = pattern.match(fname)
                    if m:
                        base = m.group(1)
                        chain_key = f"{dir_path}::{base}{ext}"
                        chain_map.setdefault(chain_key, []).append(e)
                        break

        chains_found = 0
        for chain_key, chain_entries in chain_map.items():
            if len(chain_entries) < 2:
                continue
            chains_found += 1
            chain_id = hashlib.sha256(chain_key.encode()).hexdigest()[:8]

            def _version_key(e: FileEntry) -> int:
                m = re.search(r"(\d+)$", PurePosixPath(e.rel_path).stem)
                return int(m.group(1)) if m else 0

            sorted_chain = sorted(chain_entries, key=_version_key)
            last_idx = len(sorted_chain) - 1
            for ordinal, e in enumerate(sorted_chain):
                e.version_chain_id = chain_id
                e.version_ordinal = ordinal
                e.is_latest_version = ordinal == last_idx

        return chains_found
