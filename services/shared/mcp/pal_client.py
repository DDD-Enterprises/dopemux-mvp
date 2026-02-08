"""PAL MCP Client for multi-model reasoning and code generation."""

import logging

import asyncio
from typing import Dict, Any, Optional, List
import httpx
import json


logger = logging.getLogger(__name__)

class PALClient:
    """Client for PAL MCP multi-model reasoning tools."""

    def __init__(self, base_url: str, config: Any):
        self.base_url = base_url.rstrip('/')
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.api_key}" if hasattr(config, 'api_key') else ""
            },
            timeout=60.0
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    async def chat(self, prompt: str, model: str = "gpt-5-codex", temperature: float = 0.1,
                   max_tokens: int = 1000, continuation_id: Optional[str] = None) -> str:
        """Use PAL MCP chat tool for general conversation and code generation."""

        payload = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if continuation_id:
            payload["continuation_id"] = continuation_id

        try:
            response = await self._client.post(
                "/chat",
                json=payload,
                timeout=120.0  # Longer timeout for code generation
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "No response generated")

        except httpx.HTTPStatusError as e:
            raise Exception(f"PAL MCP chat failed with status {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"PAL MCP chat call error: {str(e)}")

            logger.error(f"Error: {e}")
    async def thinkdeep(self, step: str, step_number: int, total_steps: int,
                       next_step_required: bool, findings: str, model: str = "gpt-5") -> Dict[str, Any]:
        """Use PAL MCP thinkdeep for multi-step investigation."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "model": model
        }

        try:
            response = await self._client.post("/thinkdeep", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"PAL MCP thinkdeep call error: {str(e)}")

            logger.error(f"Error: {e}")
    async def planner(self, step: str, step_number: int, total_steps: int,
                     next_step_required: bool, model: str = "gpt-5") -> Dict[str, Any]:
        """Use PAL MCP planner for interactive planning."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "model": model
        }

        try:
            response = await self._client.post("/planner", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"PAL MCP planner call error: {str(e)}")

            logger.error(f"Error: {e}")
    async def consensus(self, step: str, step_number: int, total_steps: int,
                       next_step_required: bool, findings: str, models: List[Dict]) -> Dict[str, Any]:
        """Use PAL MCP consensus for multi-model decision making."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "models": models
        }

        try:
            response = await self._client.post("/consensus", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"PAL MCP consensus call error: {str(e)}")

            logger.error(f"Error: {e}")
    async def debug(self, step: str, step_number: int, total_steps: int,
                   next_step_required: bool, findings: str, model: str = "gemini-2.5-pro") -> Dict[str, Any]:
        """Use PAL MCP debug for systematic debugging."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "model": model
        }

        try:
            response = await self._client.post("/debug", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"PAL MCP debug call error: {str(e)}")

            logger.error(f"Error: {e}")
    async def codereview(self, step: str, step_number: int, total_steps: int,
                        next_step_required: bool, findings: str, model: str = "gpt-5-codex") -> Dict[str, Any]:
        """Use PAL MCP codereview for comprehensive code analysis."""
        payload = {
            "step": step,
            "step_number": step_number,
            "total_steps": total_steps,
            "next_step_required": next_step_required,
            "findings": findings,
            "model": model
        }

        try:
            response = await self._client.post("/codereview", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"PAL MCP codereview call error: {str(e)}")
