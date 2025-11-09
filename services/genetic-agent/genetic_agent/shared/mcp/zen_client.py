"""Zen MCP client for advanced reasoning and analysis."""

from typing import Dict, Any, List, Optional
from .base_client import MCPClient


class ZenClient(MCPClient):
    """Client for Zen multi-model reasoning and analysis."""

    async def health_check(self) -> bool:
        """Check Zen service health."""
        try:
            async with self.session.get(f"{self.base_url}/version") as response:
                return response.status == 200
        except Exception:
            return False

    async def thinkdeep(self, step: str, step_number: int, total_steps: int,
                       next_step_required: bool, findings: str,
                       model: str = "gemini-2.5-pro") -> Dict[str, Any]:
        """Perform multi-step investigation and reasoning."""
        data = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "model": model
        }
        return await self._make_request("thinkdeep", data)

    async def planner(self, step: str, step_number: int, total_steps: int,
                     next_step_required: bool, model: str = "gemini-2.5-pro") -> Dict[str, Any]:
        """Interactive planning with revision support."""
        data = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "model": model
        }
        return await self._make_request("planner", data)

    async def consensus(self, step: str, step_number: int, total_steps: int,
                       next_step_required: bool, findings: str,
                       models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Multi-model decision making."""
        data = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "models": models
        }
        return await self._make_request("consensus", data)

    async def debug(self, step: str, step_number: int, total_steps: int,
                   next_step_required: bool, hypothesis: str, findings: str) -> Dict[str, Any]:
        """Systematic debugging with root cause analysis."""
        data = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "hypothesis": hypothesis,
            "findings": findings
        }
        return await self._make_request("debug", data)

    async def codereview(self, step: str, step_number: int, total_steps: int,
                        next_step_required: bool, findings: str,
                        relevant_files: List[str], model: str = "gemini-2.5-pro") -> Dict[str, Any]:
        """Comprehensive code review with expert validation."""
        data = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "relevant_files": relevant_files,
            "model": model
        }
        return await self._make_request("codereview", data)

    async def precommit(self, step: str, step_number: int, total_steps: int,
                       next_step_required: bool, findings: str,
                       path: str, model: str = "gemini-2.5-pro") -> Dict[str, Any]:
        """Pre-commit validation and analysis."""
        data = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "path": path,
            "model": model
        }
        return await self._make_request("precommit", data)