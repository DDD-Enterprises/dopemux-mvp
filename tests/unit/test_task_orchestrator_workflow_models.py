from pathlib import Path
import sys

import pytest
from pydantic import ValidationError


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

# Prevent cross-test module collisions from other services that also expose
# a top-level `app.py` module on sys.path.
for module_name in list(sys.modules):
    if module_name == "app" or module_name.startswith("app."):
        sys.modules.pop(module_name, None)

from app.models.workflow import (  # noqa: E402
    CreateEpicRequest,
    CreateIdeaRequest,
    UpdateEpicRequest,
    UpdateIdeaRequest,
    WorkflowEpic,
    WorkflowIdea,
)


def test_workflow_idea_accepts_valid_payload():
    idea = WorkflowIdea(
        id="idea_123",
        title="Reduce context switching",
        description="Need smoother flow handoff",
        source="brainstorm",
        creator="hue",
        tags=["ux", "workflow", "ux"],
    )

    assert idea.id == "idea_123"
    assert idea.status == "new"
    assert idea.tags == ["ux", "workflow"]


def test_workflow_idea_rejects_invalid_id_prefix():
    with pytest.raises(ValidationError):
        WorkflowIdea(
            id="bad_123",
            title="x",
            description="y",
            source="other",
            creator="z",
        )


def test_workflow_epic_validates_priority_and_source_link():
    epic = WorkflowEpic(
        id="epic_123",
        title="Workflow hardening",
        description="Harden stage flow",
        business_value="Reduces friction",
        created_from_idea_id="idea_999",
        priority="high",
    )

    assert epic.priority == "high"
    assert epic.created_from_idea_id == "idea_999"


def test_update_requests_require_at_least_one_mutation_field():
    with pytest.raises(ValidationError):
        UpdateIdeaRequest()

    with pytest.raises(ValidationError):
        UpdateEpicRequest()


def test_create_requests_normalize_tags_and_criteria():
    idea = CreateIdeaRequest(
        title="  Idea  ",
        description="  Description  ",
        tags=[" one ", "one", "two", ""],
    )
    epic = CreateEpicRequest(
        title="Epic",
        description="Desc",
        business_value="Value",
        acceptance_criteria=["a", "  ", "b"],
        tags=["x", "x", "y"],
    )

    assert idea.tags == ["one", "two"]
    assert epic.acceptance_criteria == ["a", "b"]
    assert epic.tags == ["x", "y"]
