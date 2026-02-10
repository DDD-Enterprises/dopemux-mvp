import pytest
from datetime import datetime, timezone
from promotion.promotion import PromotionEngine, PromotedEntry

def test_promotion_extracts_provenance():
    """Verify that promote() extracts all 4 provenance fields from event envelope.
    
    Packet D §4.3: source_event_id, source_event_type, source_adapter, source_event_ts_utc
    must be propagated to PromotedEntry.
    """
    engine = PromotionEngine()
    
    # Event eligible for promotion (e.g., decision.logged)
    event = {
        "id": "evt-123",
        "type": "decision.logged",
        "source": "vscode",
        "ts": "2026-02-09T12:00:00Z",
        "data": {
            "decision_id": "dec-123",
            "title": "Use SQLite",
            "choice": "Approved",
            "rationale": "Local-first requirement",
            "context": ["local-first"],
            "alternatives": ["postgres"],
            "outcome": "approved"
        }
    }
    
    entry = engine.promote(event)
    
    assert entry is not None
    assert entry.source_event_id == "evt-123"
    assert entry.source_event_type == "decision.logged"
    assert entry.source_adapter == "vscode"
    assert entry.source_event_ts_utc == "2026-02-09T12:00:00Z"
    assert entry.promotion_rule == "decision.logged"

def test_promotion_rejects_missing_provenance():
    """Verify fail-closed behavior for missing provenance fields.
    
    Packet D §4.5: If any required provenance field is missing, promotion MUST fail.
    """
    engine = PromotionEngine()
    
    # Missing source
    event = {
        "id": "evt-123",
        "type": "decision.logged",
        # "source": "vscode",  <-- Missing
        "ts": "2026-02-09T12:00:00Z",
        "data": {"decision": "foo"}
    }
    
    with pytest.raises(ValueError, match="Promotion requires complete provenance"):
        engine.promote(event)

def test_promotion_rejects_sentinels():
    """Verify runtime ban on sentinel values.
    
    Packet D §7.8: Runtime promotions must not use 'unknown' or 'pre_migration'.
    """
    engine = PromotionEngine()
    
    # Sentinel source
    event = {
        "id": "evt-123",
        "type": "decision.logged",
        "source": "unknown",  # <-- Sentinel
        "ts": "2026-02-09T12:00:00Z",
        "data": {"decision": "foo"}
    }
    
    with pytest.raises(ValueError, match="sentinel values not allowed"):
        engine.promote(event)
