from __future__ import annotations

from dataclasses import dataclass, field

CANONICAL_BODY_FIELDS = frozenset(
    {"status", "summary", "acceptance_checks", "validation", "artifacts", "manifest"}
)

_FIELD_DEFAULTS: dict[str, object] = {
    "status": "UNKNOWN",
    "acceptance_checks": [],
    "validation": {"outcome": "UNKNOWN", "gates": []},
}


@dataclass
class CompatibilityResult:
    is_canonical: bool
    missing_canonical: list[str]
    normalized: dict
    warnings: list[str] = field(default_factory=list)


class DopetaskCompatibilityMode:
    """Detects canonical vs legacy bundles and normalizes missing fields."""

    def check(self, bundle: dict) -> CompatibilityResult:
        has_id = bool(bundle.get("id") or bundle.get("tp_id") or bundle.get("pr_id"))
        body = bundle.get("body", bundle)  # support flat or nested
        missing_body = sorted(CANONICAL_BODY_FIELDS - set(body.keys()))

        is_canonical = has_id and len(missing_body) == 0
        if is_canonical:
            return CompatibilityResult(
                is_canonical=True,
                missing_canonical=[],
                normalized=bundle,
                warnings=[],
            )

        normalized, warnings = self._normalize(bundle, missing_body)
        return CompatibilityResult(
            is_canonical=False,
            missing_canonical=missing_body,
            normalized=normalized,
            warnings=warnings,
        )

    def _normalize(self, bundle: dict, missing: list[str]) -> tuple[dict, list[str]]:
        normalized = dict(bundle)
        warnings: list[str] = []

        for field_name in missing:
            if field_name in _FIELD_DEFAULTS:
                normalized.setdefault(field_name, _FIELD_DEFAULTS[field_name])
                warnings.append(
                    f"Legacy manifest: missing field '{field_name}' defaulted to "
                    f"{_FIELD_DEFAULTS[field_name]!r}."
                )
            elif field_name == "summary":
                summary = normalized.get("next_tactic", "")
                normalized["summary"] = summary
                warnings.append(
                    f"Legacy manifest: 'summary' synthesized from 'next_tactic': {summary!r}."
                )
            elif field_name == "manifest":
                generator = normalized.get("generator", "legacy_manifest")
                normalized["manifest"] = {
                    "generator": generator,
                    "version": "legacy",
                }
                warnings.append(
                    f"Legacy manifest: 'manifest' block synthesized from generator={generator!r}."
                )
            else:
                warnings.append(
                    f"Legacy manifest: missing field '{field_name}' has no default; left absent."
                )

        if missing:
            warnings.insert(
                0,
                f"Compatibility mode activated: missing canonical fields: "
                f"{', '.join(missing)}.",
            )

        return normalized, warnings
