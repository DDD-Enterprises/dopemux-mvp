from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Sequence

from .models import Claim, Conflict, utf8_key


def classify_conflicts(claims: Sequence[Claim]) -> tuple[Conflict, ...]:
    """Return stable, visible disagreements without selecting a winner."""

    grouped: dict[tuple[str, str, str], list[Claim]] = defaultdict(list)
    for claim in claims:
        grouped[(claim.project_id, claim.lane_id, claim.field)].append(claim)

    conflicts: list[Conflict] = []
    for (project_id, lane_id, field), group in sorted(
        grouped.items(), key=lambda item: tuple(utf8_key(part) for part in item[0])
    ):
        values = tuple(sorted({claim.value for claim in group}, key=utf8_key))
        if len(values) < 2:
            continue
        sources = tuple(
            sorted(
                {claim.source for claim in group},
                key=lambda item: tuple(
                    utf8_key(part)
                    for part in (
                        item.locator,
                        item.sha256,
                        item.observed_head,
                        item.fetched_at,
                    )
                ),
            )
        )
        identity = json.dumps(
            [project_id, lane_id, field, values],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        conflicts.append(
            Conflict(
                conflict_id=f"conflict:{hashlib.sha256(identity).hexdigest()}",
                project_id=project_id,
                lane_id=lane_id,
                field=field,
                values=values,
                sources=sources,
                materiality=(
                    "BLOCKING"
                    if any(claim.materiality == "BLOCKING" for claim in group)
                    else "NON_BLOCKING"
                ),
                status="OPEN",
                resolution_authority="SOURCE_REPOSITORY",
            )
        )
    return tuple(conflicts)
