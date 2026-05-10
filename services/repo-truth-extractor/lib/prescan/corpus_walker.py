import fnmatch
import hashlib
import logging
from pathlib import Path, PurePosixPath
from .models import (
    DEFAULT_SECRET_BEARING_ALLOWLIST_BASENAMES,
    DEFAULT_SECRET_BEARING_EXCLUDE_GLOBS,
    FileEntry,
    PrescanConfig,
)

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = frozenset(
    {
        ".md", ".mdx", ".txt", ".yaml", ".yml", ".toml", ".json", ".py", ".sh",
        ".cfg", ".ini", ".rst", ".csv", ".env", ".html", ".css", ".js", ".ts",
        ".tsx", ".jsx",
    }
)

BINARY_EXTENSIONS = frozenset(
    {
        ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe", ".png", ".jpg", ".jpeg",
        ".gif", ".svg", ".ico", ".bmp", ".webp", ".woff", ".woff2", ".ttf",
        ".eot", ".otf", ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
        ".rar", ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv", ".sqlite",
        ".db", ".sqlite3", ".pickle", ".pkl", ".npy", ".npz", ".wasm", ".o",
        ".a", ".lib",
    }
)

HARDCODED_EXCLUDE_DIRS = frozenset(
    {
        "node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build",
        ".mypy_cache", ".pytest_cache", ".ruff_cache", "htmlcov", ".tox",
        ".eggs", ".egg-info", ".DS_Store", ".codex", ".conport",
        ".dopemux", ".dopetask",
    }
)

SECRET_BEARING_ALLOWLIST_BASENAMES = frozenset(
    DEFAULT_SECRET_BEARING_ALLOWLIST_BASENAMES
)
SECRET_BEARING_EXCLUDE_GLOB_SET = frozenset(DEFAULT_SECRET_BEARING_EXCLUDE_GLOBS)

class CorpusWalker:
    def __init__(self, config: PrescanConfig):
        self.config = config

    def walk(self) -> list[FileEntry]:
        """Walk repo and build list of FileEntry objects."""
        entries: list[FileEntry] = []
        repo_root = self.config.repo_root

        for path in sorted(repo_root.rglob("*")):
            if not path.is_file():
                continue

            rel_path = self._relative_posix_path(path, repo_root)
            template_allowlisted = path.name in SECRET_BEARING_ALLOWLIST_BASENAMES

            # Skip excluded directories
            if self._is_excluded_dir(path, repo_root):
                continue

            non_secret_excludes, secret_excludes = self._partition_exclude_globs(
                self._effective_exclude_globs()
            )
            # Path-level excludes (generated trees, caches, operator-local dirs) are
            # always honored — the secret-template allowlist only overrides
            # secret-bearing patterns, not unrelated directory excludes.
            if self._matches_any_glob(rel_path, non_secret_excludes):
                continue
            if not template_allowlisted and self._matches_any_glob(
                rel_path, secret_excludes
            ):
                continue

            ext = path.suffix.lower()
            size = path.stat().st_size

            entry = FileEntry(
                rel_path=rel_path,
                size_bytes=size,
                extension=ext,
            )

            # Exclusion checks (in priority order)
            if ext in BINARY_EXTENSIONS:
                entry.include = False
                entry.exclude_reason = f"binary_extension:{ext}"
            elif size > self._effective_max_file_size(ext):
                entry.include = False
                entry.exclude_reason = f"size_exceeds_max:{size}>{self.config.max_file_size}"
            elif ext == ".json" and size > self.config.large_json_threshold:
                entry.include = False
                entry.exclude_reason = (
                    f"large_json_blob:{size}>{self.config.large_json_threshold}"
                )
            elif (
                ext not in TEXT_EXTENSIONS
                and ext != ""
                and not template_allowlisted
            ):
                # Unknown extension — exclude unless it's small and looks textual
                entry.include = False
                entry.exclude_reason = f"unknown_extension:{ext}"

            # Compute hash for included files
            if entry.include:
                try:
                    entry.content_hash = self._sha256_file(path)
                except (OSError, PermissionError) as e:
                    entry.include = False
                    entry.exclude_reason = f"read_error:{e}"

            # Set directory class (top-level directory for grouping)
            parts = PurePosixPath(rel_path).parts
            entry.directory_class = parts[0] if len(parts) > 1 else "root"

            entries.append(entry)

        return entries

    def _relative_posix_path(self, path: Path, repo_root: Path) -> str:
        rel = path.relative_to(repo_root)
        return PurePosixPath(*rel.parts).as_posix()

    def _is_excluded_dir(self, path: Path, repo_root: Path) -> bool:
        """Check if any path component is a hardcoded exclude."""
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            return False
        for part in PurePosixPath(*rel.parts).parts:
            if part in HARDCODED_EXCLUDE_DIRS:
                return True
            if part.endswith(".egg-info"):
                return True
        return False

    def _matches_any_glob(self, rel_path_str: str, globs: list[str]) -> bool:
        """Check if relative path matches any glob pattern."""
        rel_path = PurePosixPath(rel_path_str.replace("\\", "/")).as_posix()
        for pattern in globs:
            normalized_pattern = PurePosixPath(pattern.replace("\\", "/")).as_posix()
            if fnmatch.fnmatchcase(rel_path, normalized_pattern):
                return True
            if fnmatch.fnmatchcase(rel_path + "/", normalized_pattern):
                return True
        return False

    def _partition_exclude_globs(
        self, globs: list[str]
    ) -> tuple[list[str], list[str]]:
        """Split exclude globs into (non_secret, secret) groups."""
        non_secret: list[str] = []
        secret: list[str] = []
        for pattern in globs:
            if pattern in SECRET_BEARING_EXCLUDE_GLOB_SET:
                secret.append(pattern)
            else:
                non_secret.append(pattern)
        return non_secret, secret

    def _effective_exclude_globs(self) -> list[str]:
        """Return exclude globs adjusted for deep mode.

        In deep mode, patterns that match ``deep_include_globs`` are removed
        so that archive directories are included in the corpus.
        """
        if not self.config.deep_mode:
            return self.config.exclude_globs

        deep_set = set(self.config.deep_include_globs)
        return [g for g in self.config.exclude_globs if g not in deep_set]

    def _effective_max_file_size(self, ext: str) -> int:
        """Return max file size, raised for .md in deep mode."""
        if self.config.deep_mode and ext == ".md":
            return max(self.config.max_file_size, 200 * 1024)
        return self.config.max_file_size

    def _sha256_file(self, path: Path) -> str:
        """Compute SHA256 hash of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
