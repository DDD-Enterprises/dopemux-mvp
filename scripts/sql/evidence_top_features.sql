-- Top features by incoming evidence links
SELECT f.feature_id, f.title, ed.evidence_incoming
FROM evidence_density_by_feature ed
JOIN features f ON f.feature_id = ed.feature_id
ORDER BY ed.evidence_incoming DESC
LIMIT 50;

