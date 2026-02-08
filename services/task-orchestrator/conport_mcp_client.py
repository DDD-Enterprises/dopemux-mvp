"""
ConPort MCP Client Wrapper - Components 4 & 5

Provides async wrapper around ConPort MCP tools for Task-Orchestrator integration.
Handles all ConPort MCP calls with proper error handling and logging.

Component 4: Write operations (log_progress, update_progress, link_items, etc.)
Component 5: Read operations (get_decisions, get_patterns, semantic_search, etc.)

Created: 2025-10-19 (Component 4 - Write operations)
Enhanced: 2025-10-20 (Component 5 - Cross-plane query operations)
"""

import logging
from typing import Any, Dict, List, Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dopemux.mcp.parallel_executor import MCPParallelExecutor
from dopemux.file_ops.batch_handler import BatchFileOps

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

    def _resolve_semantic_search_tool(self) -> Any:
        """
        Resolve semantic-search MCP tool with compatibility fallback.

        Preferred:
        - mcp__conport__semantic_search
        Legacy fallback:
        - mcp__conport__semantic_search_conport
        """
        preferred = getattr(self.mcp_tools, "mcp__conport__semantic_search", None)
        if callable(preferred):
            return preferred, "mcp__conport__semantic_search"

        legacy = getattr(self.mcp_tools, "mcp__conport__semantic_search_conport", None)
        if callable(legacy):
            return legacy, "mcp__conport__semantic_search_conport"

        raise AttributeError(
            "No ConPort semantic-search MCP tool found "
            "(expected mcp__conport__semantic_search or mcp__conport__semantic_search_conport)"
        )

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

    # ========================================================================
    # Component 5: Cross-Plane Query Methods
    # ========================================================================

    async def get_decisions(
        self,
        workspace_id: str,
        limit: Optional[int] = None,
        tags_filter_include_any: Optional[List[str]] = None,
        tags_filter_include_all: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get decisions from ConPort.

        Args:
            workspace_id: Absolute path to workspace
            limit: Optional limit on number of decisions
            tags_filter_include_any: Filter decisions that include ANY of these tags
            tags_filter_include_all: Filter decisions that include ALL of these tags

        Returns:
            Dict with {"result": [decisions]}

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {"workspace_id": workspace_id}

            if limit:
                params["limit"] = limit

            if tags_filter_include_any:
                params["tags_filter_include_any"] = tags_filter_include_any

            if tags_filter_include_all:
                params["tags_filter_include_all"] = tags_filter_include_all

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__get_decisions(**params)

            logger.debug(f"ConPort get_decisions: {len(result.get('result', []))} decisions")
            return result

        except Exception as e:
            logger.error(f"ConPort get_decisions failed: {e}")
            raise

    async def get_system_patterns(
        self,
        workspace_id: str,
        limit: Optional[int] = None,
        tags_filter_include_any: Optional[List[str]] = None,
        tags_filter_include_all: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get system patterns from ConPort.

        Args:
            workspace_id: Absolute path to workspace
            limit: Optional limit on number of patterns
            tags_filter_include_any: Filter patterns that include ANY of these tags
            tags_filter_include_all: Filter patterns that include ALL of these tags

        Returns:
            Dict with patterns data

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {"workspace_id": workspace_id}

            if limit:
                params["limit"] = limit

            if tags_filter_include_any:
                params["tags_filter_include_any"] = tags_filter_include_any

            if tags_filter_include_all:
                params["tags_filter_include_all"] = tags_filter_include_all

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__get_system_patterns(**params)

            logger.debug(f"ConPort get_system_patterns: Retrieved patterns")
            return result

        except Exception as e:
            logger.error(f"ConPort get_system_patterns failed: {e}")
            raise

    async def get_linked_items(
        self,
        workspace_id: str,
        item_type: str,
        item_id: str,
        relationship_type_filter: Optional[str] = None,
        linked_item_type_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get items linked to a specific ConPort item.

        Args:
            workspace_id: Absolute path to workspace
            item_type: Type of item (decision, progress_entry, system_pattern)
            item_id: ID of item
            relationship_type_filter: Optional filter by relationship type
            linked_item_type_filter: Optional filter by linked item type
            limit: Optional limit on results

        Returns:
            Dict with linked items

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "item_type": item_type,
                "item_id": item_id
            }

            if relationship_type_filter:
                params["relationship_type_filter"] = relationship_type_filter

            if linked_item_type_filter:
                params["linked_item_type_filter"] = linked_item_type_filter

            if limit:
                params["limit"] = limit

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__get_linked_items(**params)

            logger.debug(f"ConPort get_linked_items: {item_type}/{item_id}")
            return result

        except Exception as e:
            logger.error(f"ConPort get_linked_items failed: {e}")
            raise

    async def semantic_search(
        self,
        workspace_id: str,
        query_text: str,
        top_k: int = 5,
        filter_item_types: Optional[List[str]] = None,
        filter_tags_include_any: Optional[List[str]] = None,
        filter_tags_include_all: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Semantic search across ConPort items.

        Args:
            workspace_id: Absolute path to workspace
            query_text: Natural language query
            top_k: Number of results (default 5, max 25)
            filter_item_types: Optional filter by item types
            filter_tags_include_any: Optional filter by tags (any)
            filter_tags_include_all: Optional filter by tags (all)

        Returns:
            Dict with search results

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "query_text": query_text,
                "top_k": str(min(top_k, 25))  # Enforce max 25 as string for MCP validation
            }

            if filter_item_types:
                params["filter_item_types"] = filter_item_types

            if filter_tags_include_any:
                params["filter_tags_include_any"] = filter_tags_include_any

            if filter_tags_include_all:
                params["filter_tags_include_all"] = filter_tags_include_all

            tool, tool_name = self._resolve_semantic_search_tool()
            result = await tool(**params)

            if isinstance(result, dict):
                result.setdefault("_tool_used", tool_name)
                result_count = len(result.get("results", []))
            else:
                result_count = 0
            logger.debug(
                "ConPort semantic_search via %s: '%s' -> %s results",
                tool_name,
                query_text,
                result_count,
            )
            return result

        except Exception as e:
            logger.error(f"ConPort semantic_search failed: {e}")
            raise

    async def semantic_search_conport(
        self,
        workspace_id: str,
        query_text: str,
        top_k: int = 5,
        filter_item_types: Optional[List[str]] = None,
        filter_tags_include_any: Optional[List[str]] = None,
        filter_tags_include_all: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Backward-compatible alias for semantic_search().

        Keep until all downstream callers migrate off the legacy method name.
        """
        return await self.semantic_search(
            workspace_id=workspace_id,
            query_text=query_text,
            top_k=top_k,
            filter_item_types=filter_item_types,
            filter_tags_include_any=filter_tags_include_any,
            filter_tags_include_all=filter_tags_include_all,
        )

    async def get_active_context(
        self,
        workspace_id: str
    ) -> Dict[str, Any]:
        """
        Get current active context from ConPort.

        Returns current session state including ADHD metrics (energy, attention).

        Args:
            workspace_id: Absolute path to workspace

        Returns:
            Dict with active context data

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {"workspace_id": workspace_id}

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__get_active_context(**params)

            logger.debug(f"ConPort get_active_context: Retrieved current state")
            return result

        except Exception as e:
            logger.error(f"ConPort get_active_context failed: {e}")
            raise

    async def search_decisions_fts(
        self,
        workspace_id: str,
        query_term: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Full-text search across decisions.

        Args:
            workspace_id: Absolute path to workspace
            query_term: Search term
            limit: Number of results (default 10)

        Returns:
            Dict with matching decisions

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "query_term": query_term,
                "limit": limit
            }

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__search_decisions_fts(**params)

            logger.debug(f"ConPort search_decisions_fts: '{query_term}' -> {len(result.get('results', []))} results")
            return result

        except Exception as e:
            logger.error(f"ConPort search_decisions_fts failed: {e}")
            raise

    async def get_custom_data(
        self,
        workspace_id: str,
        category: Optional[str] = None,
        key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get custom data from ConPort.

        Args:
            workspace_id: Absolute path to workspace
            category: Optional category filter
            key: Optional key filter (requires category)

        Returns:
            Dict with custom data entries

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {"workspace_id": workspace_id}

            if category:
                params["category"] = category

            if key:
                params["key"] = key

            # Call ConPort MCP tool
            result = await self.mcp_tools.mcp__conport__get_custom_data(**params)

            logger.debug(f"ConPort get_custom_data: category={category}, key={key}")
            return result

        except Exception as e:
            logger.error(f"ConPort get_custom_data failed: {e}")
            raise

    async def log_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: str,
        value: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Persist custom data to ConPort.

        Args:
            workspace_id: Absolute path to workspace
            category: Custom data category
            key: Key within category
            value: JSON payload to store

        Returns:
            Dict with persistence result payload

        Raises:
            Exception: If MCP call fails
        """
        try:
            params = {
                "workspace_id": workspace_id,
                "category": category,
                "key": key,
                "value": value,
            }
            result = await self.mcp_tools.mcp__conport__log_custom_data(**params)
            logger.debug("ConPort log_custom_data: category=%s key=%s", category, key)
            return result
        except Exception as e:
            logger.error(f"ConPort log_custom_data failed: {e}")
            raise

    async def upsert_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: str,
        value: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Upsert custom data entry in ConPort.

        ConPort custom-data writes are key-addressed; writes to the same
        category/key pair replace prior value.
        """
        return await self.log_custom_data(
            workspace_id=workspace_id,
            category=category,
            key=key,
            value=value,
        )

    # ===== PARALLEL OPERATIONS =====

    def __init_parallel_components(self):
        """Initialize parallel operation components."""
        if not hasattr(self, '_parallel_executor'):
            self._parallel_executor = MCPParallelExecutor(max_concurrent=5)
        if not hasattr(self, '_batch_file_ops'):
            self._batch_file_ops = BatchFileOps(max_concurrent=10)

    async def batch_log_progress(
        self,
        workspace_id: str,
        progress_entries: List[Dict[str, Any]],
        return_exceptions: bool = True
    ) -> List[Any]:
        """
        Log multiple progress entries in parallel.

        Args:
            workspace_id: Workspace identifier
            progress_entries: List of progress entry dicts (each with status, description, etc.)
            return_exceptions: If True, exceptions are returned instead of raised

        Returns:
            List of results, one per progress entry

        Example:
            entries = [
                {"status": "DONE", "description": "Task 1 complete"},
                {"status": "IN_PROGRESS", "description": "Task 2 in progress"}
            ]
            results = await client.batch_log_progress(workspace_id, entries)
        """
        self.__init_parallel_components()

        # Add workspace_id to each entry
        call_specs = []
        for entry in progress_entries:
            entry_with_workspace = {**entry, "workspace_id": workspace_id}
            call_specs.append({
                "method": "log_progress",
                "kwargs": entry_with_workspace
            })

        logger.info(f"Batch logging {len(progress_entries)} progress entries in parallel")
        return await self._parallel_executor.execute_batch(self, call_specs, return_exceptions)

    async def batch_update_progress(
        self,
        workspace_id: str,
        progress_updates: List[Dict[str, Any]],
        return_exceptions: bool = True
    ) -> List[Any]:
        """
        Update multiple progress entries in parallel.

        Args:
            workspace_id: Workspace identifier
            progress_updates: List of update dicts (each must include progress_id)
            return_exceptions: If True, exceptions are returned instead of raised

        Returns:
            List of results, one per update

        Example:
            updates = [
                {"progress_id": 123, "status": "DONE"},
                {"progress_id": 124, "description": "Updated task"}
            ]
            results = await client.batch_update_progress(workspace_id, updates)
        """
        self.__init_parallel_components()

        # Add workspace_id to each update
        call_specs = []
        for update in progress_updates:
            update_with_workspace = {**update, "workspace_id": workspace_id}
            call_specs.append({
                "method": "update_progress",
                "kwargs": update_with_workspace
            })

        logger.info(f"Batch updating {len(progress_updates)} progress entries in parallel")
        return await self._parallel_executor.execute_batch(self, call_specs, return_exceptions)

    async def batch_log_decisions(
        self,
        workspace_id: str,
        decisions: List[Dict[str, Any]],
        return_exceptions: bool = True
    ) -> List[Any]:
        """
        Log multiple decisions in parallel.

        Args:
            workspace_id: Workspace identifier
            decisions: List of decision dicts (each with summary, rationale, etc.)
            return_exceptions: If True, exceptions are returned instead of raised

        Returns:
            List of results, one per decision
        """
        self.__init_parallel_components()

        call_specs = []
        for decision in decisions:
            decision_with_workspace = {**decision, "workspace_id": workspace_id}
            call_specs.append({
                "method": "log_decision",
                "kwargs": decision_with_workspace
            })

        logger.info(f"Batch logging {len(decisions)} decisions in parallel")
        return await self._parallel_executor.execute_batch(self, call_specs, return_exceptions)

    async def parallel_semantic_search(
        self,
        workspace_id: str,
        queries: List[str],
        return_exceptions: bool = True
    ) -> List[Any]:
        """
        Perform multiple semantic searches in parallel.

        Args:
            workspace_id: Workspace identifier
            queries: List of search query strings
            return_exceptions: If True, exceptions are returned instead of raised

        Returns:
            List of search results, one per query
        """
        self.__init_parallel_components()

        call_specs = []
        for query in queries:
            call_specs.append({
                "method": "semantic_search",
                "kwargs": {
                    "workspace_id": workspace_id,
                    "query_text": query
                }
            })

        logger.info(f"Parallel semantic search for {len(queries)} queries")
        return await self._parallel_executor.execute_batch(self, call_specs, return_exceptions)

    # ===== BATCH FILE OPERATIONS =====

    async def batch_read_configs(
        self,
        config_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Read multiple configuration files in parallel and merge them.

        Args:
            config_paths: List of configuration file paths

        Returns:
            Merged configuration dictionary

        Example:
            configs = await client.batch_read_configs(['app.json', 'user.json'])
        """
        self.__init_parallel_components()

        logger.info(f"Batch reading {len(config_paths)} config files")
        return await self._batch_file_ops.read_config_batch(config_paths)

    async def batch_backup_files(
        self,
        file_paths: List[str],
        backup_suffix: str = '.backup'
    ) -> Dict[str, Any]:
        """
        Create backup copies of multiple files in parallel.

        Args:
            file_paths: Files to backup
            backup_suffix: Suffix for backup files

        Returns:
            Dict of backup results
        """
        self.__init_parallel_components()

        logger.info(f"Batch backing up {len(file_paths)} files")
        return await self._batch_file_ops.backup_files(file_paths, backup_suffix)
