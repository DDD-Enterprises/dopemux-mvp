"""DopetaskBundleLoader — find, validate, and parse Dopetask proof bundles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dopetask_status_mapper import DopetaskProofRef


class BundleSchemaError(ValueError):
    """Raised when a bundle is missing required fields."""


class DopetaskBundleLoader:
    """Find, validate, and parse Dopetask flight-deck proof bundles.

    Bundles are JSON files emitted by ClosedLoopEngine, PatchEngine, or FusionEngine.
    This loader abstracts over naming conventions across lanes.
    """

    # Hard-required: at least one ID field and artifacts list.
    # Other fields (status, summary, etc.) are expected in full bundles but
    # handled with defaults when absent (e.g. lean manifests from engine lanes).
    REQUIRED_FIELDS: frozenset[str] = frozenset({"artifacts"})
    # Expected in full bundles; absence triggers DEGRADED (not ERROR)
    EXPECTED_FIELDS: frozenset[str] = frozenset(
        {
            "status",
            "summary",
            "acceptance_checks",
            "validation",
            "manifest",
        }
    )
    # Either tp_id or pr_id must be present — checked separately.
    ID_FIELDS = {"tp_id", "pr_id"}

    def __init__(self, bundle_root: Path) -> None:
        self.bundle_root = Path(bundle_root)

    def find_bundle(self, tp_id: str) -> Path | None:
        """Locate a bundle file for the given TP ID.

        Search order:
        1. TP-{tp_id}_PROOF_BUNDLE.json  (canonical)
        2. *MANIFEST.json                (closed_loop lane)
        3. *BUNDLE.json                  (generic fallback)

        Returns the first match, or None if nothing found.
        """
        # Canonical name
        canonical = self.bundle_root / f"TP-{tp_id}_PROOF_BUNDLE.json"
        if canonical.exists():
            return canonical

        # Manifest fallback
        manifests = sorted(self.bundle_root.glob("*MANIFEST.json"))
        if manifests:
            return manifests[0]

        # Generic bundle fallback
        bundles = sorted(self.bundle_root.glob("*BUNDLE.json"))
        if bundles:
            return bundles[0]

        return None

    def load(self, bundle_path: Path) -> dict:
        """Load and validate a bundle JSON file.

        Raises:
            FileNotFoundError: if bundle_path does not exist.
            json.JSONDecodeError: if the file is not valid JSON.
            BundleSchemaError: if the JSON is not an object, required fields are
                missing, ``artifacts`` is not a list of non-blank strings, or no
                valid packet identity is present (``tp_id``: non-blank string;
                ``pr_id``: non-blank string or integer PR number).
        """
        raw = Path(bundle_path).read_text(encoding="utf-8")
        bundle = json.loads(raw)

        # Shape guard: a bundle must be a JSON object, not a list/scalar/null.
        if not isinstance(bundle, dict):
            raise BundleSchemaError(
                f"Bundle must be a JSON object, got {type(bundle).__name__}"
            )

        # Packet identity: at least one of tp_id/pr_id must be valid. tp_id is a
        # non-blank string; pr_id is a non-blank string or an integer PR number
        # (DopetaskPacketLauncher copies context["pr_id"] in unconverted).
        # Present-but-null is tolerated for the *other* field; any other value
        # (blank string, bool, float, list, object) is rejected.
        id_values = {k: bundle[k] for k in self.ID_FIELDS if k in bundle}
        bad_ids = sorted(
            k
            for k, v in id_values.items()
            if v is not None and not self._is_valid_identity(k, v)
        )
        if bad_ids:
            raise BundleSchemaError(
                "Bundle identity fields must be non-blank strings "
                f"(pr_id may be an integer): {', '.join(bad_ids)}"
            )
        has_id = any(v is not None for v in id_values.values())

        # Check hard-required fields + at least one ID field
        missing_required = sorted(self.REQUIRED_FIELDS - set(bundle.keys()))
        if missing_required or not has_id:
            all_missing = list(missing_required)
            if not has_id:
                all_missing.append("tp_id|pr_id")
            raise BundleSchemaError(
                f"Bundle missing required fields: {', '.join(sorted(all_missing))}"
            )

        # Artifacts must be a list of strings (consumed as relative file names).
        artifacts = bundle["artifacts"]
        if not isinstance(artifacts, list):
            raise BundleSchemaError(
                f"Bundle field 'artifacts' must be a list, got {type(artifacts).__name__}"
            )
        bad_members = [
            i
            for i, name in enumerate(artifacts)
            if not isinstance(name, str) or not name.strip()
        ]
        if bad_members:
            raise BundleSchemaError(
                "Bundle field 'artifacts' must contain only non-blank strings; "
                f"invalid at indices: {', '.join(str(i) for i in bad_members)}"
            )

        return bundle

    @staticmethod
    def _is_valid_identity(field: str, value: object) -> bool:
        """True for a non-blank string, or an int (not bool) for ``pr_id``."""
        if isinstance(value, str):
            return bool(value.strip())
        return field == "pr_id" and isinstance(value, int) and not isinstance(value, bool)

    def load_canonical(self, bundle_path: Path) -> dict:
        """Load a bundle and raise BundleSchemaError if any EXPECTED_FIELDS are missing.

        Use this when strict canonical validation is required (no compatibility fallback).

        Raises:
            FileNotFoundError: if bundle_path does not exist.
            json.JSONDecodeError: if the file is not valid JSON.
            BundleSchemaError: if required fields OR expected canonical fields are missing.
        """
        bundle = self.load(bundle_path)

        missing_expected = sorted(self.EXPECTED_FIELDS - set(bundle.keys()))
        if missing_expected:
            raise BundleSchemaError(
                f"Bundle missing canonical fields: {', '.join(missing_expected)}"
            )

        return bundle

    def extract_proof_ref(self, bundle: dict, bundle_path: Path) -> "DopetaskProofRef":
        """Build a DopetaskProofRef from a loaded bundle and its path."""
        # Import here to avoid circular imports at module level
        from .dopetask_status_mapper import DopetaskProofRef

        bundle_path = Path(bundle_path)

        # Derive archive path: sibling of bundle_root parent with .zip extension
        # e.g. closed_loop/MANIFEST.json → closed_loop.zip (in parent dir)
        archive_path: str | None = None
        archive_present = False
        parent = bundle_path.parent
        zip_candidate = parent.parent / f"{parent.name}.zip"
        if zip_candidate.exists():
            archive_path = str(zip_candidate)
            archive_present = True
        else:
            # Store the candidate path even if absent
            archive_path = str(zip_candidate)

        # Supporting artifacts from bundle["artifacts"] list
        supporting: list[str] = []
        for name in bundle.get("artifacts", []):
            candidate = bundle_path.parent / name
            supporting.append(str(candidate))

        return DopetaskProofRef(
            bundle_path=str(bundle_path),
            bundle_present=bundle_path.exists(),
            archive_path=archive_path,
            archive_present=archive_present,
            supporting_artifacts=supporting,
        )
