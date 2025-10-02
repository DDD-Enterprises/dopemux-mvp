-- Components with missing security metadata
SELECT component_id, name, subsystem_id, security_notes, threat_model_refs
FROM components
WHERE (security_notes IS NULL OR security_notes = '')
   OR (threat_model_refs IS NULL OR threat_model_refs = '')
ORDER BY subsystem_id, name;

