import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Add src and task-orchestrator paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.models.workflow import WorkflowEpic, WorkflowIdea

client = TestClient(app)

# Helper to mock workflow service
def override_workflow_service(mock_service):
    app.dependency_overrides = {}

    # We need to mock the Request state since we use getattr(request.app.state, "coordinator")
    # A cleaner way is to mock the internal function in the module
    pass

class TestProjectWorkflowAPI(unittest.IsolatedAsyncioTestCase):

    @patch("app.api.project_workflow._workflow_service")
    def test_get_project_workflow_queue_success(self, mock_get_service):
        mock_service = AsyncMock()
        mock_service.list_epics.return_value = []
        mock_get_service.return_value = mock_service

        response = client.get("/api/projects/proj_123/workflow/queue")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["project_id"], "proj_123")
        self.assertIn("queue_items", data)
        self.assertEqual(data["legality_result"], "allowed")

    def test_get_project_workflow_queue_fail_closed_missing_project(self):
        response = client.get("/api/projects/unknown/workflow/queue")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "project not found")

    def test_get_project_workflow_queue_fail_closed_no_state(self):
        response = client.get("/api/projects/no_state/workflow/queue")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "workflow state unavailable")

    @patch("app.api.project_workflow._workflow_service")
    def test_get_project_workflow_blockers_success(self, mock_get_service):
        mock_service = AsyncMock()
        mock_service.list_epics.return_value = []
        mock_get_service.return_value = mock_service

        response = client.get("/api/projects/proj_123/workflow/blockers")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["project_id"], "proj_123")
        self.assertIn("active_blockers", data)
        self.assertEqual(data["legality_result"], "allowed")

    def test_get_project_workflow_blockers_fail_closed_missing_project(self):
        response = client.get("/api/projects/unknown/workflow/blockers")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "project not found")

    @patch("app.api.project_workflow._workflow_service")
    def test_get_project_workflow_state_success(self, mock_get_service):
        mock_service = AsyncMock()
        mock_service.list_epics.return_value = []
        mock_get_service.return_value = mock_service

        response = client.get("/api/projects/proj_123/workflow/state")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["project_id"], "proj_123")
        self.assertIn("state", data)
        self.assertIn("allowed_transitions", data)
        self.assertEqual(data["legality_result"], "allowed")

    def test_get_project_workflow_state_fail_closed_missing_project(self):
        response = client.get("/api/projects/unknown/workflow/state")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "project not found")

    @patch("app.api.project_workflow._workflow_service")
    def test_post_project_workflow_transition_success(self, mock_get_service):
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        payload = {
            "workflow_id": "wf_456",
            "transition": "start_work",
            "actor": "user_1"
        }
        response = client.post("/api/projects/proj_123/workflow/transition", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["project_id"], "proj_123")
        self.assertEqual(data["workflow_id"], "wf_456")
        self.assertIn("transition_receipt", data)
        self.assertIn("resulting_state", data)
        self.assertEqual(data["legality_result"], "allowed")

    def test_post_project_workflow_transition_fail_closed_missing_linkage(self):
        payload = {
            "workflow_id": "missing_linkage",
            "transition": "start_work"
        }
        response = client.post("/api/projects/proj_123/workflow/transition", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "missing required workflow entity linkage")

    def test_post_project_workflow_transition_fail_closed_illegal_target(self):
        payload = {
            "workflow_id": "wf_456",
            "transition": "illegal_target"
        }
        response = client.post("/api/projects/proj_123/workflow/transition", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "transition request references illegal or unresolved target")

    @patch("app.api.project_workflow._workflow_service")
    def test_post_project_workflow_transition_fail_closed_epic_not_found(self, mock_get_service):
        from app.services.workflow_service import WorkflowNotFoundError
        mock_service = AsyncMock()
        mock_service.get_epic.side_effect = WorkflowNotFoundError("not found")
        mock_get_service.return_value = mock_service

        payload = {
            "workflow_id": "epic_456",
            "transition": "start_work"
        }
        response = client.post("/api/projects/proj_123/workflow/transition", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "workflow entity not found")

if __name__ == '__main__':
    unittest.main()
