-- Top components by incoming evidence links
SELECT c.component_id, c.name, ed.evidence_incoming
FROM evidence_density_by_component ed
JOIN components c ON c.component_id = ed.component_id
ORDER BY ed.evidence_incoming DESC
LIMIT 50;

