"""Safety classification for macOS system-data findings."""

from __future__ import annotations

from pathlib import Path


def classify_path(path: Path) -> tuple[str, str, str, str, tuple[str, ...]]:
    text = str(path)
    lower = text.lower()
    if text.startswith(("/System/", "/private/var/db/", "/Library/Apple/", "/usr/")):
        return ("blocked", "blocked", "blocked", "Protected system path; Dopemux reports it and keeps its hands off.", ())
    if "Library/Messages/Attachments" in text:
        return (
            "review_first",
            "quarantine_or_explicit_delete",
            "review_attachments",
            "Messages attachments can be user-important media; broad deletion is blocked.",
            ("Messages",),
        )
    if "com.apple.MobileSMS/Data/tmp" in text:
        return (
            "safe_clear",
            "delete",
            "clear_safe_path",
            "Messages tmp is temporary bloat and safe to clear when Messages is closed.",
            ("Messages",),
        )
    if "Library/Messages/Caches/Previews" in text:
        return (
            "safe_clear",
            "delete",
            "clear_safe_path",
            "Messages previews are rebuildable cache data.",
            ("Messages",),
        )
    if "Library/Caches/CloudKit" in text:
        return (
            "rebuildable_cache",
            "delete",
            "clear_safe_path",
            "CloudKit cache is rebuildable; the next sync may do some work.",
            (),
        )
    if "com.docker.docker" in text or ".docker" in lower:
        return (
            "tool_mediated",
            "tool",
            "docker_prune",
            "Docker storage should be handled through Docker first, not raw VM surgery.",
            ("Docker",),
        )
    if "Library/Caches/Homebrew" in text:
        return (
            "tool_mediated",
            "tool",
            "homebrew_cleanup",
            "Homebrew cache cleanup should use brew cleanup so receipts stay sane.",
            (),
        )
    if "Library/Developer/Xcode/DerivedData" in text:
        return (
            "safe_clear",
            "delete",
            "clear_safe_path",
            "Xcode DerivedData is rebuildable build/index output.",
            ("Xcode",),
        )
    if "Library/Developer/Xcode/Archives" in text:
        return (
            "review_first",
            "quarantine_or_explicit_delete",
            "review_archives",
            "Xcode archives may be release evidence; review before deleting.",
            ("Xcode",),
        )
    if "MobileSync/Backup" in text:
        return (
            "review_first",
            "quarantine_or_explicit_delete",
            "review_ios_backups",
            "iOS device backups may be the only backup someone has; review first.",
            (),
        )
    if "CoreSimulator/Profiles/Runtimes" in text:
        return (
            "review_first",
            "quarantine_or_explicit_delete",
            "review_simulator_runtimes",
            "Simulator runtimes are large but reinstall cost and project needs vary.",
            ("Simulator", "Xcode"),
        )
    if "Library/Developer/CoreSimulator" in text:
        return (
            "tool_mediated",
            "tool",
            "simctl_delete_unavailable",
            "Simulator cleanup should use simctl for unavailable devices.",
            ("Simulator", "Xcode"),
        )
    if any(token in lower for token in ("/.npm", "/library/caches/yarn", "/library/caches/pip", "/.cargo", "/.gradle", "/.m2")):
        return (
            "safe_clear",
            "delete",
            "clear_safe_path",
            "Developer package cache is rebuildable; first rebuild may fetch again.",
            (),
        )
    if text.endswith("/Downloads") or "/Downloads/" in text:
        return (
            "review_first",
            "quarantine_or_explicit_delete",
            "review_downloads",
            "Downloads is a junk drawer, but still a user-owned junk drawer.",
            (),
        )
    if "Library/Caches" in text:
        return (
            "rebuildable_cache",
            "delete",
            "clear_safe_path",
            "User cache data is rebuildable; targeted cleanup beats panic sweeping.",
            (),
        )
    return (
        "unknown",
        "advise",
        "advise_only",
        "No explicit safety policy matched this path.",
        (),
    )
