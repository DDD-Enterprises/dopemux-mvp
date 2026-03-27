"""PAL MCP Client for multi-model reasoning and code generation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx


logger = logging.getLogger(__name__)


class PALClient:
    """Client for PAL MCP multi-model reasoning tools."""

    def __init__(self, base_url: str, config: Any):
        auth_header = ""
        if hasattr(config, "api_key") and getattr(config, "api_key"):
            auth_header = f"Bearer {config.api_key}"
        self.base_url = base_url.rstrip("/")
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_header,
            },
            timeout=60.0,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    async def _post_json(
        self, path: str, payload: Dict[str, Any], *, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        try:
            response = await self._client.post(
                path,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPStatusError as exc:
            raise Exception(
                f"PAL MCP {path} failed with status {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except Exception as exc:
            raise Exception(f"PAL MCP {path} call error: {exc}") from exc
        if not isinstance(result, dict):
            raise Exception(
                f"PAL MCP {path} returned non-object JSON: {type(result).__name__}"
            )
        return result

    async def chat(
        self,
        prompt: str,
        model: str = "gpt-5-codex",
        temperature: float = 0.1,
        max_tokens: int = 1000,
        continuation_id: Optional[str] = None,
    ) -> str:
        """Use PAL MCP chat tool for general conversation and code generation."""
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if continuation_id:
            payload["continuation_id"] = continuation_id
        try:
            result = await self._post_json("/chat", payload, timeout=120.0)
            return str(result.get("response", "No response generated"))
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    async def apilookup(self, prompt: str) -> Dict[str, Any]:
        """Use PAL MCP apilookup to gather current API assumptions."""
        try:
            return await self._post_json("/apilookup", {"prompt": prompt}, timeout=120.0)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    async def challenge(self, prompt: str) -> Dict[str, Any]:
        """Use PAL MCP challenge to critically reassess a statement or evidence set."""
        try:
            return await self._post_json("/challenge", {"prompt": prompt}, timeout=60.0)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    async def thinkdeep(
        self,
        step: str,
        step_number: int,
        total_steps: int,
        next_step_required: bool,
        findings: str,
        model: str = "gpt-5",
    ) -> Dict[str, Any]:
        """Use PAL MCP thinkdeep for multi-step investigation."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "model": model,
        }
        try:
            return await self._post_json("/thinkdeep", payload)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    async def planner(
        self,
        step: str,
        step_number: int,
        total_steps: int,
        next_step_required: bool,
        model: str = "gpt-5",
    ) -> Dict[str, Any]:
        """Use PAL MCP planner for interactive planning."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "model": model,
        }
        try:
            return await self._post_json("/planner", payload)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    async def consensus(
        self,
        step: str,
        step_number: int,
        total_steps: int,
        next_step_required: bool,
        findings: str,
        models: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Use PAL MCP consensus for multi-model decision making."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "models": models,
        }
        try:
            return await self._post_json("/consensus", payload, timeout=120.0)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    async def debug(
        self,
        step: str,
        step_number: int,
        total_steps: int,
        next_step_required: bool,
        findings: str,
        model: str = "gemini-2.5-pro",
    ) -> Dict[str, Any]:
        """Use PAL MCP debug for systematic debugging."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "model": model,
        }
        try:
            return await self._post_json("/debug", payload)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    async def codereview(
        self,
        step: str,
        step_number: int,
        total_steps: int,
        next_step_required: bool,
        findings: str,
        model: str = "gpt-5-codex",
    ) -> Dict[str, Any]:
        """Use PAL MCP codereview for comprehensive code analysis."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "model": model,
        }
        try:
            return await self._post_json("/codereview", payload)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
