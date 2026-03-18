import datetime as dt
import logging
import subprocess
from pathlib import Path, PurePosixPath
from .models import FileEntry, PrescanConfig

logger = logging.getLogger(__name__)

_COMMIT_SEP = "!!!COMMIT!!!"

class GitEnricher:
    def __init__(self, config: PrescanConfig):
        self.config = config

    def enrich(self, entries: list[FileEntry]) -> None:
        """Enrich FileEntry list with git metadata. Modifies entries in-place."""
        repo_root = self.config.repo_root
        per_file = self._parse_git_log_for_files(repo_root)
        renames = self._parse_renames(repo_root)
        today = dt.date.today()

        for entry in entries:
            if entry.is_ghost:
                continue
            commits = per_file.get(entry.rel_path, [])
            if not commits:
                entry.lifecycle_stage = "unknown"
                continue

            entry.last_commit_sha = commits[0][0]
            entry.last_author = commits[0][1]
            entry.last_commit_date = commits[0][2]
            entry.first_commit_date = commits[-1][2]
            entry.commit_count = len(commits)
            entry.contributor_count = len({c[1] for c in commits})

            try:
                last_d = dt.date.fromisoformat(entry.last_commit_date)
                entry.days_since_modified = (today - last_d).days
            except (ValueError, TypeError):
                pass

            if entry.first_commit_date and entry.days_since_modified is not None:
                try:
                    first_d = dt.date.fromisoformat(entry.first_commit_date)
                    age_days = max((today - first_d).days, 1)
                    entry.churn_score = round(entry.commit_count / (age_days / 30), 3)
                except (ValueError, TypeError):
                    pass

            dsm = entry.days_since_modified
            if dsm is not None:
                if dsm < 30:
                    entry.lifecycle_stage = "fresh"
                elif dsm < 90:
                    entry.lifecycle_stage = "active"
                elif dsm < 365:
                    entry.lifecycle_stage = "stale"
                else:
                    entry.lifecycle_stage = "frozen"

            prev = renames.get(entry.rel_path, [])
            if prev:
                entry.was_renamed = True
                entry.previous_paths = prev[:5]

    def recover_ghost_files(
        self,
        existing_paths: set[str],
        max_ghosts: int = 50,
    ) -> list[FileEntry]:
        """
        Recover recently-deleted doc files from git history.
        Returns synthetic ghost FileEntry list (authority_class='ghost').
        """
        repo_root = self.config.repo_root
        _GHOST_SEP = "!!!DEL!!!"
        ghost_exts = {".md", ".yaml", ".yml", ".toml", ".py", ".rst", ".txt"}
        ghost_exclude = {
            "node_modules", ".venv", "venv", "__pycache__", ".git", "htmlcov",
            "extraction", "runs", "tmp", "dist", "build",
        }

        try:
            raw = subprocess.check_output(
                [
                    "git", "log", "--diff-filter=D", "--name-only",
                    f"--format={_GHOST_SEP}%H|%ad", "--date=short",
                ],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                timeout=60,
            ).decode(errors="replace")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return []

        ghosts: list[FileEntry] = []
        seen_paths: set[str] = set()
        current_meta: tuple[str, str] = ("", "")

        for line in raw.splitlines():
            if line.startswith(_GHOST_SEP):
                parts = line[len(_GHOST_SEP) :].split("|", 1)
                sha = parts[0] if parts else ""
                date = parts[1].strip() if len(parts) > 1 else ""
                current_meta = (sha, date)
            elif line.strip() and current_meta[0]:
                fp = line.strip()
                ext = Path(fp).suffix.lower()
                if ext not in ghost_exts:
                    continue
                if fp in existing_paths or fp in seen_paths:
                    continue
                parts_fp = PurePosixPath(fp).parts
                if any(p in ghost_exclude for p in parts_fp):
                    continue
                seen_paths.add(fp)
                ghost = FileEntry(
                    rel_path=fp,
                    size_bytes=0,
                    extension=ext,
                    authority_class="ghost",
                    include=True,
                    directory_class=parts_fp[0] if len(parts_fp) > 1 else "root",
                    is_ghost=True,
                    deleted_at_sha=current_meta[0],
                    deleted_date=current_meta[1],
                    recovery_source="git_history",
                )
                ghosts.append(ghost)
                if len(ghosts) >= max_ghosts:
                    break

        return ghosts

    def _parse_git_log_for_files(self, repo_root: Path) -> dict[str, list[tuple[str, str, str]]]:
        """Single git log call -> {rel_path: [(sha, author, date), ...]} newest-first."""
        try:
            raw = subprocess.check_output(
                [
                    "git", "log", f"--format={_COMMIT_SEP}%H|%an|%ad",
                    "--date=short", "--name-only", "--diff-filter=AMRC",
                ],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                timeout=120,
            ).decode(errors="replace")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return {}

        per_file: dict[str, list[tuple[str, str, str]]] = {}
        current: tuple[str, str, str] | None = None

        for line in raw.splitlines():
            if line.startswith(_COMMIT_SEP):
                header = line[len(_COMMIT_SEP) :]
                parts = header.split("|", 2)
                sha = parts[0] if parts else ""
                author = parts[1] if len(parts) > 1 else ""
                date = parts[2].strip() if len(parts) > 2 else ""
                current = (sha, author, date)
            elif line.strip() and current:
                per_file.setdefault(line.strip(), []).append(current)

        return per_file

    def _parse_renames(self, repo_root: Path) -> dict[str, list[str]]:
        """Returns {new_path: [old_path1, ...]} from git rename history."""
        try:
            raw = subprocess.check_output(
                ["git", "log", "--diff-filter=R", "--name-status", "--format="],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                timeout=60,
            ).decode(errors="replace")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return {}

        renames: dict[str, list[str]] = {}
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("R"):
                parts = line.split("\t")
                if len(parts) == 3:
                    old_path, new_path = parts[1], parts[2]
                    renames.setdefault(new_path, []).append(old_path)
        return renames
