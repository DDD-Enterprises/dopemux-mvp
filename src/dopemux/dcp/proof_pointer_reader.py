"""Local DCP proof pointer reader."""

from __future__ import annotations

from pathlib import Path

from dopemux.dcp.proof_family import ArtifactInspection, classify_artifact


def read_proof_pointer(
    artifact_path: str | Path,
    *,
    expected_head_sha: str | None = None,
) -> ArtifactInspection:
    """Read and classify a local DCP proof pointer artifact."""

    return classify_artifact(artifact_path, expected_head_sha=expected_head_sha)
