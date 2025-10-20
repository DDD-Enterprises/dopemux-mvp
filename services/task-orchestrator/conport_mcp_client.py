"""
ConPort MCP Client Wrapper - Component 4

Provides async wrapper around ConPort MCP tools for Task-Orchestrator integration.
Handles all ConPort MCP calls with proper error handling and logging.

Created: 2025-10-19 (Component 4)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConPortMCPClient:
    """
    Async wrapper for ConPort MCP tools.

    Provides convenient methods for ConPort operations used by Task-Orchestrator.
    All methods are async and include error handling.

    Usage:
        client = ConPortMCPClient(mcp_tools)
        result = await client.log_progress(workspace_id, status, description, tags)
    """

    def __init__(self, mcp_tools: Any):
        """
        Initialize ConPort MCP client.

        Args:
            mcp_tools: MCP tools object with ConPort tool methods
        """
        self.mcp_tools = mcp_tools

    async def log_progress(
        self,
        workspace_id: str,
        status: str,
        description: str,
        tags: Optional[List[str]] = None,
        linked_item_type: Optional[str] = None,
        linked_item_id: Optional[str] = None,
        link_relationship_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log progress entry to ConPort.

        Args:
            workspace_id: Absolute path to workspace
            status: TODO, IN_PROGRESS, DONE, BLOCKED
            description: Task description
            tags: Optional list of tags
            linked_item_type: Optional type of linked item
            linked_item_id: Optional ID of linked item
            link_relationship_type: Optional relationship type

        Returns:
            Dict with {"id": int, ...} on success

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "status": status,
                "description": description
            }

            if tags:
                params["tags"] = tags

            if linked_item_type and linked_item_id:
                params["linked_item_type"] = linked_item_type
                params["linked_item_id"] = linked_item_id

            if link_relationship_type:
                params["link_relationship_type"] = link_relationship_type

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__log_progress(**params)

            logger.debug(f"ConPort log_progress: {result}")
            return result

        except Exception as e:
            logger.error(f"ConPort log_progress failed: {e}")
            raise

    async def update_progress(
        self,
        workspace_id: str,
        progress_id: int,
        status: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update existing progress entry in ConPort.

        Args:
            workspace_id: Absolute path to workspace
            progress_id: ConPort progress entry ID
            status: Optional new status
            description: Optional new description

        Returns:
            Dict with update result

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "progress_id": str(progress_id)  # ConPort expects string ID
            }

            if status:
                params["status"] = status

            if description:
                params["description"] = description

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__update_progress(**params)

            logger.debug(f"ConPort update_progress: {result}")
            return result

        except Exception as e:
            logger.error(f"ConPort update_progress failed: {e}")
            raise

    async def get_progress(
        self,
        workspace_id: str,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
        parent_id_filter: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get progress entries from ConPort.

        Args:
            workspace_id: Absolute path to workspace
            status_filter: Optional status filter (TODO, IN_PROGRESS, etc.)
            limit: Optional limit on number of entries
            parent_id_filter: Optional parent task ID filter

        Returns:
            Dict with {"result": [progress_entries]}

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {"workspace_id": workspace_id}

            if status_filter:
                params["status_filter"] = status_filter

            if limit:
                params["limit"] = limit

            if parent_id_filter:
                params["parent_id_filter"] = str(parent_id_filter)

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__get_progress(**params)

            logger.debug(f"ConPort get_progress: {len(result.get('result', []))} entries")
            return result

        except Exception as e:
            logger.error(f"ConPort get_progress failed: {e}")
            raise

    async def link_conport_items(
        self,
        workspace_id: str,
        source_item_type: str,
        source_item_id: str,
        target_item_type: str,
        target_item_id: str,
        relationship_type: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create relationship link between ConPort items.

        Args:
            workspace_id: Absolute path to workspace
            source_item_type: Type of source item (progress_entry, decision, etc.)
            source_item_id: ID of source item
            target_item_type: Type of target item
            target_item_id: ID of target item
            relationship_type: Type of relationship (depends_on, extends, etc.)
            description: Optional description of relationship

        Returns:
            Dict with link result

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "source_item_type": source_item_type,
                "source_item_id": source_item_id,
                "target_item_type": target_item_type,
                "target_item_id": target_item_id,
                "relationship_type": relationship_type
            }

            if description:
                params["description"] = description

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__link_conport_items(**params)

            logger.debug(f"ConPort link_items: {source_item_id} -> {target_item_id}")
            return result

        except Exception as e:
            logger.error(f"ConPort link_items failed: {e}")
            raise

    async def update_active_context(
        self,
        workspace_id: str,
        patch_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update ConPort active context.

        Args:
            workspace_id: Absolute path to workspace
            patch_content: Dict of changes to apply

        Returns:
            Dict with update result

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "patch_content": patch_content
            }

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__update_active_context(**params)

            logger.debug(f"ConPort update_active_context: {list(patch_content.keys())}")
            return result

        except Exception as e:
            logger.error(f"ConPort update_active_context failed: {e}")
            raise

    async def log_decision(
        self,
        workspace_id: str,
        summary: str,
        rationale: Optional[str] = None,
        implementation_details: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Log decision to ConPort.

        Args:
            workspace_id: Absolute path to workspace
            summary: Decision summary
            rationale: Optional decision rationale
            implementation_details: Optional implementation details
            tags: Optional list of tags

        Returns:
            Dict with {"id": int, ...} on success

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "summary": summary
            }

            if rationale:
                params["rationale"] = rationale

            if implementation_details:
                params["implementation_details"] = implementation_details

            if tags:
                params["tags"] = tags

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__log_decision(**params)

            logger.debug(f"ConPort log_decision: {summary}")
            return result

        except Exception as e:
            logger.error(f"ConPort log_decision failed: {e}")
            raise
