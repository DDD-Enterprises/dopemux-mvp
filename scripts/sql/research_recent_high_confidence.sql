-- Recent high-confidence research items (<= 90 days, confidence >= 0.8)
SELECT research_id, title, research_type, recency_days, source_quality, confidence
FROM research_recent_high_confidence
LIMIT 100;

