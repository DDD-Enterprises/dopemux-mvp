from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ArchiveResolution:
    archive_path: str | None  # None when not expected
    archive_present: bool
    archive_expected: bool  # = len(supporting_artifacts) > 0
    note: str


class DopetaskArchiveResolver:
    """Resolves whether an archive is expected and present for a bundle."""

    def resolve(
        self, bundle_path: Path, supporting_artifacts: list[str]
    ) -> ArchiveResolution:
        archive_expected = len(supporting_artifacts) > 0
        candidate = bundle_path.parent.parent / f"{bundle_path.parent.name}.zip"

        if not archive_expected:
            return ArchiveResolution(
                archive_path=None,
                archive_present=False,
                archive_expected=False,
                note="No supporting artifacts; archive not expected.",
            )

        # Only a regular file counts as an archive. A directory (or any other
        # non-file entry) that merely carries the expected .zip name must not
        # produce a false archive-present proof. Contents are never opened.
        archive_present = candidate.is_file()
        note = (
            f"Archive found: {candidate}"
            if archive_present
            else f"Archive not found: {candidate}"
        )
        return ArchiveResolution(
            archive_path=str(candidate),
            archive_present=archive_present,
            archive_expected=True,
            note=note,
        )
