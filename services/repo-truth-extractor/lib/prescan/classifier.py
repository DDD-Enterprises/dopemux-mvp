import logging
from pathlib import PurePosixPath
from .models import FileEntry, PrescanConfig

logger = logging.getLogger(__name__)

AUTHORITY_CLASSES = (
    "canonical",
    "historical",
    "operational",
    "audit",
    "template",
    "generated",
    "noise",
    "ghost",
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

class Classifier:
    def __init__(self, config: PrescanConfig):
        self.config = config

    def classify_file(self, entry: FileEntry) -> str:
        """Classify a file into an authority class. First match wins."""
        p = PurePosixPath(entry.rel_path)
        parts_lower = [part.lower() for part in p.parts]
        name = p.name
        name_lower = name.lower()
        ext = entry.extension

        # If already excluded, classify as noise
        if not entry.include:
            return "noise"

        # ── noise ──
        if ext in BINARY_EXTENSIONS:
            return "noise"

        # ── generated ──
        if "runs" in parts_lower and any(
            x in ("extraction", "repo-truth-extractor") for x in parts_lower
        ):
            return "generated"
        if name_lower.startswith("latest_run_id"):
            return "generated"
        if "doctor" in parts_lower and ext == ".json":
            return "generated"
        if parts_lower[0] == "out" if parts_lower else False:
            return "generated"

        # ── template ──
        if "templates" in parts_lower:
            return "template"
        if ".claude" in parts_lower and "prompts" in parts_lower:
            return "template"
        if ".claude" in parts_lower and "modules" in parts_lower:
            return "template"
        if "upgrades" in parts_lower and "promptgen" in parts_lower:
            return "template"
        if "promptsets" in parts_lower:
            return "template"

        # ── historical ──
        if "archive" in parts_lower:
            return "historical"
        if "deprecated" in " ".join(parts_lower):
            return "historical"
        if "system_archive" in parts_lower:
            return "historical"
        if "completed-projects" in parts_lower:
            return "historical"
        if "implementation-history" in parts_lower:
            return "historical"
        if "old" in parts_lower and "sessions" in parts_lower:
            return "historical"

        # ── audit ──
        if parts_lower and parts_lower[0] == "reports":
            return "audit"
        if parts_lower and parts_lower[0] == "proof":
            return "audit"
        if "audit" in name_lower:
            return "audit"
        if "_audit_" in name_lower:
            return "audit"

        # ── operational ──
        if any(x in ("92-runbooks", "runbooks") for x in parts_lower):
            return "operational"
        if any(x in ("02-how-to", "01-tutorials") for x in parts_lower):
            return "operational"
        if name in ("INSTALL.md", "QUICK_START.md", "SETUP.md"):
            return "operational"
        if name == "README.md":
            return "operational"
        if "deploy" in parts_lower:
            return "operational"

        # ── canonical ──
        if "planes" in parts_lower:
            return "canonical"
        if any(x in ("03-reference", "04-explanation") for x in parts_lower):
            return "canonical"
        if any(x in ("90-adr", "91-rfc") for x in parts_lower):
            return "canonical"
        if name == "CLAUDE.md":
            return "canonical"
        if name in (
            "model_map_v2_tp008.yaml",
            "pyproject.toml",
            "compose.yml",
            "dopemux.toml",
            "litellm.config",
            "Makefile",
        ):
            return "canonical"

        # ── Fallbacks by directory ──
        if parts_lower and parts_lower[0] == "docs":
            return "canonical"
        if parts_lower and parts_lower[0] == ".claude":
            return "canonical"
        if parts_lower and parts_lower[0] == "upgrades":
            return "canonical"
        if parts_lower and parts_lower[0] == "scripts" and ext == ".md":
            return "operational"
        if parts_lower and parts_lower[0] == "scripts":
            return "operational"
        if len(p.parts) == 1 and ext in (".yaml", ".yml", ".toml"):
            return "canonical"

        # ── default ──
        return "generated"

    def classify_all(self, entries: list[FileEntry]) -> None:
        """Classify all entries in-place."""
        for entry in entries:
            entry.authority_class = self.classify_file(entry)

    def classify(self, entries: list[FileEntry]) -> list[FileEntry]:
        """Compatibility wrapper for engine callers expecting a return value."""
        self.classify_all(entries)
        return entries


FileClassifier = Classifier
