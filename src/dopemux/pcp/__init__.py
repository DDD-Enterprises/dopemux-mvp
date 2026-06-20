"""
dopemux.pcp — Project Control Plane evidence export package.

Provides a read-only runtime exporter that inspects an arbitrary Git repository
and emits a JSON evidence object validating against
schemas/project_control_plane/project_evidence_export.schema.json.

No writes, no network calls, no mutations to the target repository.
"""
