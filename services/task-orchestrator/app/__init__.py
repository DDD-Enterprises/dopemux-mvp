"""Task-orchestrator application package.

This file intentionally marks `app/` as a regular package so imports like
`app.models.workflow` resolve deterministically to this service's modules
during mixed-repo test runs.
"""

