"""
Leantime JSON-RPC 2.0 Client for Dopemux

This module provides a JSON-RPC 2.0 client for communicating with Leantime's API.
Follows the official Leantime API specification for authentication and method calls.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

import aiohttp

from core.exceptions import DopemuxIntegrationError, AuthenticationError
from core.config import Config


logger = logging.getLogger(__name__)


@dataclass
class LeantimeResponse:
    """Structured response from Leantime JSON-RPC API."""
    success: bool
    data: Any
    error: Optional[str] = None
    method: Optional[str] = None
    request_id: Optional[Union[int, str]] = None


class LeantimeJSONRPCClient:
    """
    JSON-RPC 2.0 client for Leantime API integration.

    Implements the official Leantime API specification:
    - Single endpoint: /api/jsonrpc
    - Authentication: x-api-key header
    - JSON-RPC 2.0 protocol
    - Method format: leantime.rpc.Module.Service.Method
    """

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.get('leantime.api_url', 'http://localhost:8080')
        self.api_token = config.get('leantime.api_token')
        self.endpoint = f"{self.base_url}/api/jsonrpc"

        self.session: Optional[aiohttp.ClientSession] = None
        self._request_id = 0
        self._connected = False

        # Validate configuration
        if not self.api_token:
            raise DopemuxIntegrationError("Leantime API token is required")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> bool:
        """
        Establish connection to Leantime API.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Setup HTTP headers for Leantime API
            headers = {
                'x-api-key': self.api_token,  # Leantime uses x-api-key header
                'Content-Type': 'application/json',
                'User-Agent': 'Dopemux-Leantime-Bridge/2.0'
            }

            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers=headers
            )

            # Test connection with a simple API call
            test_response = await self.call_method("leantime.rpc.Users.getCurrentUser")

            if test_response.success or test_response.error != "Authentication failed":
                self._connected = True
                logger.info("Successfully connected to Leantime JSON-RPC API")
                return True
            else:
                logger.error(f"Failed to authenticate with Leantime: {test_response.error}")
                await self.disconnect()
                return False

        except Exception as e:
            logger.error(f"Failed to connect to Leantime: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False

    async def disconnect(self):
        """Gracefully disconnect from Leantime API."""
        if self.session:
            await self.session.close()
            self.session = None
            self._connected = False
            logger.info("Disconnected from Leantime JSON-RPC API")

    def _next_request_id(self) -> int:
        """Generate next request ID."""
        self._request_id += 1
        return self._request_id

    async def call_method(self, method: str, params: Optional[Dict[str, Any]] = None) -> LeantimeResponse:
        """
        Call a JSON-RPC method on Leantime API.

        Args:
            method: JSON-RPC method name (e.g., 'leantime.rpc.Projects.getAllProjects')
            params: Optional parameters for the method

        Returns:
            LeantimeResponse with structured result
        """
        if not self.session:
            raise DopemuxIntegrationError("Not connected to Leantime")

        request_id = self._next_request_id()
        request_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }

        try:
            logger.debug(f"Calling Leantime method: {method}")

            async with self.session.post(self.endpoint, json=request_data) as response:
                response_data = await response.json()

                # Check for JSON-RPC error
                if 'error' in response_data:
                    error_msg = response_data['error'].get('message', 'Unknown error')
                    logger.warning(f"Leantime API error for {method}: {error_msg}")

                    return LeantimeResponse(
                        success=False,
                        data=None,
                        error=error_msg,
                        method=method,
                        request_id=request_id
                    )

                # Success response
                result = response_data.get('result')
                logger.debug(f"Successful response from {method}")

                return LeantimeResponse(
                    success=True,
                    data=result,
                    method=method,
                    request_id=request_id
                )

        except aiohttp.ClientError as e:
            error_msg = f"HTTP error calling {method}: {e}"
            logger.error(error_msg)
            return LeantimeResponse(
                success=False,
                data=None,
                error=error_msg,
                method=method,
                request_id=request_id
            )

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response from {method}: {e}"
            logger.error(error_msg)
            return LeantimeResponse(
                success=False,
                data=None,
                error=error_msg,
                method=method,
                request_id=request_id
            )

        except Exception as e:
            error_msg = f"Unexpected error calling {method}: {e}"
            logger.error(error_msg)
            return LeantimeResponse(
                success=False,
                data=None,
                error=error_msg,
                method=method,
                request_id=request_id
            )

    # Project Management Methods

    async def get_projects(self, limit: int = 50) -> LeantimeResponse:
        """
        Retrieve all projects from Leantime.

        Args:
            limit: Maximum number of projects to return

        Returns:
            LeantimeResponse with projects data
        """
        params = {"limit": limit} if limit != 50 else {}
        return await self.call_method("leantime.rpc.Projects.getAllProjects", params)

    async def get_project(self, project_id: int) -> LeantimeResponse:
        """
        Get specific project details.

        Args:
            project_id: Leantime project ID

        Returns:
            LeantimeResponse with project details
        """
        return await self.call_method("leantime.rpc.Projects.getProject", {"projectId": project_id})

    async def create_project(self, name: str, description: str = "", **kwargs) -> LeantimeResponse:
        """
        Create new project in Leantime.

        Args:
            name: Project name
            description: Project description
            **kwargs: Additional project parameters

        Returns:
            LeantimeResponse with created project data
        """
        params = {
            "name": name,
            "details": description,
            **kwargs
        }
        return await self.call_method("leantime.rpc.Projects.addProject", params)

    # Task/Ticket Management Methods

    async def get_tickets(self, project_id: Optional[int] = None,
                         status: Optional[str] = None,
                         limit: int = 100) -> LeantimeResponse:
        """
        Retrieve tickets/tasks from Leantime.

        Args:
            project_id: Optional project filter
            status: Optional status filter
            limit: Maximum number of tickets

        Returns:
            LeantimeResponse with tickets data
        """
        params = {"limit": limit}

        if project_id:
            params["projectId"] = project_id
        if status:
            params["status"] = status

        return await self.call_method("leantime.rpc.Tickets.getAllTickets", params)

    async def get_ticket(self, ticket_id: int) -> LeantimeResponse:
        """
        Get specific ticket details.

        Args:
            ticket_id: Leantime ticket ID

        Returns:
            LeantimeResponse with ticket details
        """
        return await self.call_method("leantime.rpc.Tickets.getTicket", {"ticketId": ticket_id})

    async def create_ticket(self, headline: str, description: str = "",
                           project_id: int = 0, **kwargs) -> LeantimeResponse:
        """
        Create new ticket in Leantime.

        Args:
            headline: Ticket title
            description: Ticket description
            project_id: Project ID for the ticket
            **kwargs: Additional ticket parameters

        Returns:
            LeantimeResponse with created ticket data
        """
        params = {
            "headline": headline,
            "description": description,
            "projectId": project_id,
            **kwargs
        }
        return await self.call_method("leantime.rpc.Tickets.addTicket", params)

    async def update_ticket(self, ticket_id: int, **kwargs) -> LeantimeResponse:
        """
        Update existing ticket in Leantime.

        Args:
            ticket_id: Ticket ID to update
            **kwargs: Fields to update

        Returns:
            LeantimeResponse with update result
        """
        params = {"ticketId": ticket_id, **kwargs}
        return await self.call_method("leantime.rpc.Tickets.updateTicket", params)

    async def delete_ticket(self, ticket_id: int) -> LeantimeResponse:
        """
        Delete ticket from Leantime.

        Args:
            ticket_id: Ticket ID to delete

        Returns:
            LeantimeResponse with deletion result
        """
        return await self.call_method("leantime.rpc.Tickets.deleteTicket", {"ticketId": ticket_id})

    # User Management Methods

    async def get_current_user(self) -> LeantimeResponse:
        """
        Get current user information.

        Returns:
            LeantimeResponse with user data
        """
        return await self.call_method("leantime.rpc.Users.getCurrentUser")

    async def get_users(self) -> LeantimeResponse:
        """
        Get all users.

        Returns:
            LeantimeResponse with users data
        """
        return await self.call_method("leantime.rpc.Users.getAllUsers")

    # Health Check

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health status of Leantime connection.

        Returns:
            Health status information
        """
        try:
            if not self._connected:
                return {
                    "status": "disconnected",
                    "connected": False,
                    "error": "Not connected to Leantime"
                }

            # Try a simple API call
            response = await self.get_current_user()

            return {
                "status": "healthy" if response.success else "unhealthy",
                "connected": True,
                "api_responsive": response.success,
                "last_error": response.error if not response.success else None
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": self._connected,
                "error": str(e)
            }


# Factory function for easy instantiation
def create_leantime_client(config: Config) -> LeantimeJSONRPCClient:
    """
    Factory function to create Leantime JSON-RPC client.

    Args:
        config: Dopemux configuration

    Returns:
        Configured Leantime JSON-RPC client
    """
    return LeantimeJSONRPCClient(config)
