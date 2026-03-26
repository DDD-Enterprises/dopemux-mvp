"""Normalized PM-plane chronicle read/write contracts."""

import logging
from typing import Any, Dict, List, Optional
from dopemux.pm.chronicle_models import (
    PMChronicleReadResult,
    PMChronicleProvenance,
    PMChronicleSupportingSource,
    PMChronicleWriteReceipt,
)
from dopemux.pm.adapters.dope_memory import DopeMemoryAdapter
import httpx

logger = logging.getLogger(__name__)

# Single instance of the adapter to use
_adapter = DopeMemoryAdapter()

async def pm_get_work_chronicle(
    *,
    workspace_id: str,
    canonical_id: Optional[str] = None,
    linked_ids: Optional[Dict[str, str]] = None,
    session_id: Optional[str] = None,
    category: Optional[str] = None,
    entry_type: Optional[str] = None,
    tags_any: Optional[List[str]] = None,
    time_range: str = "week",
    top_k: int = 3,
    next_token: Optional[str] = None,
) -> PMChronicleReadResult:
    """Read normalized PM-plane chronicle from dope-memory authority.
    
    Returns fail-closed empty result if backend is down.
    """
    try:
        raw_result = await _adapter.search_chronicle(
            workspace_id=workspace_id,
            session_id=session_id,
            category=category,
            entry_type=entry_type,
            tags_any=tags_any,
            time_range=time_range,
            top_k=top_k,
            cursor=next_token,
        )
    except httpx.HTTPError:
        logger.warning("dope-memory backend unavailable. Returning fail-closed empty result.")
        raw_result = {"items": [], "more_count": 0, "next_token": None}
    except Exception as e:
        logger.error(f"Unexpected error calling dope-memory: {e}")
        raw_result = {"items": [], "more_count": 0, "next_token": None}

    items = raw_result.get("items", [])
    entry_ids = [str(item.get("id")) for item in items if "id" in item]

    provenance = PMChronicleProvenance(
        source="dope-memory",
        query_mode="work_chronicle",
        workspace_id=workspace_id,
        time_range=time_range,
    )

    supporting_source = PMChronicleSupportingSource(
        kind="canonical",
        backend="dope-memory",
        entry_ids=entry_ids,
    )

    return PMChronicleReadResult(
        canonical_backend="dope-memory",
        canonical_id=canonical_id,
        linked_ids=linked_ids or {},
        provenance=provenance,
        supporting_sources=[supporting_source],
        items=items,
        more_count=raw_result.get("more_count", 0),
        next_token=raw_result.get("next_token"),
    )


async def pm_append_work_chronicle(
    *,
    workspace_id: str,
    canonical_id: str,
    linked_ids: Dict[str, str],
    entry_type: str,
    summary: str,
    details: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    actor: Optional[str] = None,
    source_system: str = "pm-plane",
    idempotency_key: str,
    category: str = "work_chronicle",
) -> PMChronicleWriteReceipt:
    """Append a normalized PM-plane chronicle entry to dope-memory authority.
    
    Includes canonical_id and linked_ids in the metadata/details payload.
    """
    # Merge PM linkage into details or links
    augmented_details = details.copy() if details else {}
    augmented_details.update({
        "canonical_id": canonical_id,
        "actor": actor,
        "source_system": source_system,
    })

    # Put linked_ids into links
    links = linked_ids.copy()
    if canonical_id:
        links["pm_canonical"] = canonical_id

    try:
        result = await _adapter.append_chronicle(
            workspace_id=workspace_id,
            entry_type=entry_type,
            summary=summary,
            category=category,
            details=augmented_details,
            tags=tags,
            links=links,
            idempotency_key=idempotency_key,
        )
        
        success = result.get("success", False) or "entry_id" in result
        entry_id = result.get("entry_id", "unknown")

        return PMChronicleWriteReceipt(
            canonical_backend="dope-memory",
            canonical_id=canonical_id,
            entry_id=entry_id,
            linked_ids=linked_ids,
            success=success,
            error=result.get("error"),
        )
    except httpx.HTTPError as e:
        logger.warning(f"dope-memory backend unavailable during append: {e}")
        return PMChronicleWriteReceipt(
            canonical_backend="dope-memory",
            canonical_id=canonical_id,
            entry_id="unknown",
            linked_ids=linked_ids,
            success=False,
            error="Backend unavailable",
        )
    except Exception as e:
        logger.error(f"Unexpected error calling dope-memory append: {e}")
        return PMChronicleWriteReceipt(
            canonical_backend="dope-memory",
            canonical_id=canonical_id,
            entry_id="unknown",
            linked_ids=linked_ids,
            success=False,
            error=str(e),
        )


async def pm_correct_work_chronicle(
    *,
    workspace_id: str,
    canonical_id: str,
    chronicle_entry_id: str,
    correction_reason: str,
    corrected_summary: Optional[str] = None,
    corrected_details: Optional[Dict[str, Any]] = None,
    actor: Optional[str] = None,
    source_system: str = "pm-plane",
    idempotency_key: str,
) -> PMChronicleWriteReceipt:
    """Correct/supersede a normalized PM-plane chronicle entry in dope-memory authority.
    
    Uses memory_correct (correction_type="summary") if available, otherwise appends.
    """
    correction_type = "summary" if corrected_summary else "retraction"
    
    try:
        result = await _adapter.correct_chronicle(
            workspace_id=workspace_id,
            entry_id=chronicle_entry_id,
            correction_type=correction_type,
            corrected_summary=corrected_summary or correction_reason,
            corrected_tags=None,
            idempotency_key=idempotency_key,
        )

        success = result.get("success", False)
        entry_id = result.get("entry_id", "unknown")

        return PMChronicleWriteReceipt(
            canonical_backend="dope-memory",
            canonical_id=canonical_id,
            entry_id=entry_id,
            linked_ids={},
            success=success,
            error=result.get("error"),
        )
    except httpx.HTTPStatusError as e:
        # If the endpoint doesn't exist or returns 404, we fall back to append.
        if e.response.status_code == 404:
            logger.info("memory_correct endpoint returned 404, falling back to append-only correction.")
            # Fall back to append
            return await pm_append_work_chronicle(
                workspace_id=workspace_id,
                canonical_id=canonical_id,
                linked_ids={},
                entry_type="correction",
                summary=f"Correction for {chronicle_entry_id}: {corrected_summary or correction_reason}",
                details={"superseded_entry_id": chronicle_entry_id, "reason": correction_reason},
                actor=actor,
                source_system=source_system,
                idempotency_key=idempotency_key,
            )
        else:
            logger.warning(f"dope-memory backend HTTP error during correct: {e}")
            return PMChronicleWriteReceipt(
                canonical_backend="dope-memory",
                canonical_id=canonical_id,
                entry_id="unknown",
                linked_ids={},
                success=False,
                error="Backend unavailable",
            )
    except httpx.HTTPError as e:
        logger.warning(f"dope-memory backend unavailable during correct: {e}")
        return PMChronicleWriteReceipt(
            canonical_backend="dope-memory",
            canonical_id=canonical_id,
            entry_id="unknown",
            linked_ids={},
            success=False,
            error="Backend unavailable",
        )
    except Exception as e:
        logger.error(f"Unexpected error calling dope-memory correct: {e}")
        return PMChronicleWriteReceipt(
            canonical_backend="dope-memory",
            canonical_id=canonical_id,
            entry_id="unknown",
            linked_ids={},
            success=False,
            error=str(e),
        )
