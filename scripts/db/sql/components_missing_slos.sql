-- Components missing any SLO fields
SELECT component_id, name, subsystem_id, slo_availability, slo_latency
FROM components
WHERE (slo_availability IS NULL OR slo_availability = '')
   OR (slo_latency IS NULL OR slo_latency = '')
ORDER BY subsystem_id, name;

