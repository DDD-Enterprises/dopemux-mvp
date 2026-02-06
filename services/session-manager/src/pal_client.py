"""
PAL MCP Client - Simplified Multi-Model Access
Replaces complex CLI spawning with simple MCP tool calls

This is BETTER than spawning separate CLIs because:
- No TTY issues
- No process management
- Conversation continuity built-in
- 27+ models available
- Proven reliability

Complexity: 0.35 (Low-Medium) - Much simpler than agent_spawner!
"""

import logging
from typing import Optional, Literal
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ZenModel(Enum):
    """Available models via PAL MCP."""

    # Top tier (Intelligence 16-18)
    GEMINI_PRO = "gemini"  # 1M context, intelligence 18
    GROK_CODE = "grok-code"  # 2M context, intelligence 18, FREE!
    GPT5_CODEX = "gpt5codex"  # 400K context, intelligence 17
    GPT5 = "gpt5"  # 400K context, intelligence 16
    GROK4_FAST = "grok4-fast"  # 2M context, intelligence 16, FREE!

    # Mid tier (Intelligence 12-15)
    CLAUDE_SONNET = "sonnet"  # 200K context, intelligence 12
    O3_MINI = "o3-mini"  # 200K context, intelligence 12
    O3 = "o3"  # 200K context, intelligence 14
    DEEPSEEK = "deepseek"  # 65K context, intelligence 15

    # Fast models
    GEMINI_FLASH = "flash"  # 1M context, fast
    GROK3_FAST = "grok3fast"  # 131K context, fast


@dataclass
class ZenResponse:
    """Structured response from PAL MCP."""

    model_used: str
    content: str
    confidence: float  # If available from tool
    thinking: Optional[str] = None  # Extended thinking if used
    metadata: Optional[dict] = None


class PALMCPClient:
    """
    Client for PAL MCP multi-model reasoning.

    Much simpler than spawning separate CLIs!
    All models accessible through unified interface.
    """

    def __init__(self):
        """Initialize Zen client."""
        # In real implementation, this would connect to PAL MCP server
        # For now, we'll use placeholder that shows the pattern
        self.available_models = [m.value for m in ZenModel]

    def thinkdeep(
        self,
        step: str,
        model: str = "gemini",
        step_number: int = 1,
        total_steps: int = 1,
        confidence: str = "medium",
    ) -> ZenResponse:
        """
        Multi-step investigation with Zen.

        Args:
            step: Investigation step content
            model: Which model to use (gemini, o3-mini, gpt-5)
            step_number: Current step
            total_steps: Estimated total steps
            confidence: Current confidence level

        Returns:
            ZenResponse with analysis

        Example:
            >>> response = zen.thinkdeep(
            ...     step="Analyze authentication flow for race conditions",
            ...     model="gemini",
            ...     step_number=1,
            ...     total_steps=3
            ... )
        """
        # Call actual PAL MCP tool via HTTP
        try:
            import httpx
            zen_endpoint = "http://localhost:8002/mcp/zen/thinkdeep"
            request_data = {
                "step": step,
                "step_number": step_number,
                "total_steps": total_steps,
                "next_step_required": True,
                "findings": {},  # Initial findings
                "confidence": confidence,
                "model": model
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(zen_endpoint, json=request_data)
                if response.status_code == 200:
                    zen_data = response.json()
                    return ZenResponse(
                        model_used=model,
                        content=zen_data.get("content", "Zen thinkdeep analysis"),
                        confidence=zen_data.get("confidence", 0.8),
                        thinking=zen_data.get("thinking", None)
                    )
                else:
                    raise ValueError(f"PAL MCP returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Zen thinkdeep call failed: {e}")
            # Fallback to mock
            return ZenResponse(
                model_used=model,
                content=f"[Zen thinkdeep fallback]\nStep {step_number}/{total_steps}: {step} (service unavailable)",
                confidence=0.5,
            )

    def planner(
        self,
        step: str,
        model: str = "sonnet",
        step_number: int = 1,
        total_steps: int = 1,
    ) -> ZenResponse:
        """
        Interactive planning with Zen.

        Args:
            step: Planning step content
            model: Which model (sonnet, gpt-5, gemini)
            step_number: Current planning step
            total_steps: Estimated steps

        Returns:
            ZenResponse with plan

        Example:
            >>> response = zen.planner(
            ...     step="Break down OAuth implementation into phases",
            ...     model="sonnet"
            ... )
        """
        # Call actual PAL MCP planner via HTTP
        try:
            import httpx
            zen_endpoint = "http://localhost:8002/mcp/zen/planner"
            request_data = {
                "step": step,
                "step_number": step_number,
                "total_steps": total_steps,
                "next_step_required": True,
                "model": model
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(zen_endpoint, json=request_data)
                if response.status_code == 200:
                    zen_data = response.json()
                    return ZenResponse(
                        model_used=model,
                        content=zen_data.get("content", "Zen planner output"),
                        confidence=zen_data.get("confidence", 0.85),
                        thinking=zen_data.get("thinking", None)
                    )
                else:
                    raise ValueError(f"PAL MCP returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Zen planner call failed: {e}")
            # Fallback to mock
            return ZenResponse(
                model_used=model,
                content=f"[Zen planner fallback]\nStep {step_number}: {step} (service unavailable)",
                confidence=0.6,
            )

    def consensus(
        self, step: str, models: Optional[list[dict]] = None
    ) -> ZenResponse:
        """
        Multi-model consensus decision.

        Args:
            step: Decision question
            models: List of {model, stance} configs

        Returns:
            ZenResponse with synthesis

        Example:
            >>> response = zen.consensus(
            ...     step="Should we use JWT or sessions?",
            ...     models=[
            ...         {"model": "sonnet", "stance": "for"},
            ...         {"model": "gemini", "stance": "against"}
            ...     ]
            ... )
        """
        if not models:
            # Default: 3-model consensus
            models = [
                {"model": "sonnet", "stance": "neutral"},
                {"model": "gemini", "stance": "for"},
                {"model": "grok4-fast", "stance": "against"},
            ]

        # Call actual PAL MCP consensus via HTTP
        try:
            import httpx
            zen_endpoint = "http://localhost:8002/mcp/zen/consensus"
            request_data = {
                "step": step,
                "step_number": 1,
                "total_steps": len(models) if models else 3,
                "next_step_required": False,
                "findings": {},
                "model": "auto",  # Let Zen decide based on models list
                "questions": [],  # Not used for consensus
                "multiSelect": False,  # Not used
                "models": models or []
            }

            with httpx.Client(timeout=45.0) as client:  # Longer timeout for consensus
                response = client.post(zen_endpoint, json=request_data)
                if response.status_code == 200:
                    zen_data = response.json()
                    models_used = ", ".join(m["model"] for m in models) if models else "auto-selected"
                    return ZenResponse(
                        model_used=models_used,
                        content=zen_data.get("content", "Multi-model consensus"),
                        confidence=zen_data.get("confidence", 0.87),
                        metadata={"models_consulted": models},
                        thinking=zen_data.get("thinking", None)
                    )
                else:
                    raise ValueError(f"PAL MCP returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Zen consensus call failed: {e}")
            # Fallback to mock
            models_used = ", ".join(m["model"] for m in models) if models else "fallback"
            return ZenResponse(
                model_used=models_used,
                content=f"[Zen consensus fallback]\nQuestion: {step}\nModels: {models_used} (service unavailable)",
                confidence=0.6,
                metadata={"models_consulted": models},
            )

    def chat(self, prompt: str, model: str = "grok-code") -> ZenResponse:
        """
        Simple chat with specified model.

        Args:
            prompt: Question or task
            model: Which model to use

        Returns:
            ZenResponse with answer

        Example:
            >>> response = zen.chat(
            ...     prompt="Implement JWT token generation",
            ...     model="grok-code"
            ... )
        """
        # Call actual PAL MCP chat via HTTP
        try:
            import httpx
            zen_endpoint = "http://localhost:8002/mcp/zen/chat"
            request_data = {
                "prompt": prompt,
                "working_directory": "/tmp",  # Temporary working directory
                "model": model,
                "temperature": 0.7,  # Creative for chat
                "thinking_mode": "medium",
                "continuation_id": ""  # New conversation
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(zen_endpoint, json=request_data)
                if response.status_code == 200:
                    zen_data = response.json()
                    return ZenResponse(
                        model_used=model,
                        content=zen_data.get("response", f"[{model} response]"),
                        confidence=0.8,
                        thinking=zen_data.get("thinking", None)
                    )
                else:
                    raise ValueError(f"PAL MCP returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Zen chat call failed: {e}")
            # Fallback to mock
            return ZenResponse(
                model_used=model,
                content=f"[{model} fallback response to: {prompt}] (service unavailable)",
                confidence=0.5
            )

    def debug(
        self,
        step: str,
        hypothesis: str,
        model: str = "gemini",
    ) -> ZenResponse:
        """
        Systematic debugging with Zen.

        Args:
            step: Current investigation step
            hypothesis: Theory about root cause
            model: Which model (gemini recommended for analysis)

        Returns:
            ZenResponse with debug analysis

        Example:
            >>> response = zen.debug(
            ...     step="Authentication fails intermittently",
            ...     hypothesis="Race condition in token generation",
            ...     model="gemini"
            ... )
        """
        # Call actual PAL MCP debug via HTTP
        try:
            import httpx
            zen_endpoint = "http://localhost:8002/mcp/zen/debug"
            request_data = {
                "step": step,
                "step_number": 1,
                "total_steps": 1,
                "next_step_required": False,
                "findings": {},
                "hypothesis": hypothesis,
                "model": model,
                "temperature": 0.2,  # Low temperature for debugging
                "thinking_mode": "high"
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(zen_endpoint, json=request_data)
                if response.status_code == 200:
                    zen_data = response.json()
                    return ZenResponse(
                        model_used=model,
                        content=zen_data.get("content", "Debug analysis"),
                        confidence=zen_data.get("confidence", 0.75),
                        thinking=zen_data.get("thinking", None)
                    )
                else:
                    raise ValueError(f"PAL MCP returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Zen debug call failed: {e}")
            # Fallback to mock
            return ZenResponse(
                model_used=model,
                content=f"[Zen debug fallback]\nHypothesis: {hypothesis}\n{step} (service unavailable)",
                confidence=0.5,
            )

    def codereview(
        self,
        files: list[str],
        review_type: Literal["full", "security", "performance", "quick"] = "full",
        model: str = "gemini",
    ) -> ZenResponse:
        """
        Multi-model code review.

        Args:
            files: Files to review
            review_type: Type of review
            model: Primary model

        Returns:
            ZenResponse with review findings

        Example:
            >>> response = zen.codereview(
            ...     files=["src/auth.py", "src/session.py"],
            ...     review_type="security",
            ...     model="gemini"
            ... )
        """
        # Call actual PAL MCP codereview via HTTP
        try:
            import httpx
            zen_endpoint = "http://localhost:8002/mcp/zen/codereview"
            request_data = {
                "step": f"Review {len(files)} files with {review_type} focus",
                "step_number": 1,
                "total_steps": 1,
                "next_step_required": False,
                "findings": {},
                "relevant_files": files,
                "review_type": review_type,
                "focus_on": review_type,
                "model": model,
                "review_validation_type": "external",
                "severity_filter": "all"
            }

            with httpx.Client(timeout=60.0) as client:  # Longer timeout for code review
                response = client.post(zen_endpoint, json=request_data)
                if response.status_code == 200:
                    zen_data = response.json()
                    return ZenResponse(
                        model_used=model,
                        content=zen_data.get("content", f"Code review of {len(files)} files"),
                        confidence=zen_data.get("confidence", 0.82),
                        metadata={"files_reviewed": files},
                        thinking=zen_data.get("thinking", None)
                    )
                else:
                    raise ValueError(f"PAL MCP returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Zen codereview call failed: {e}")
            # Fallback to mock
            return ZenResponse(
                model_used=model,
                content=f"[Zen codereview fallback]\nReview of {len(files)} files\nType: {review_type} (service unavailable)",
                confidence=0.5,
                metadata={"files_reviewed": files},
            )


if __name__ == "__main__":
    """Test Zen client wrapper."""

    logger.info("Testing PAL MCP Client:")
    logger.info("=" * 60)

    zen = PALMCPClient()

    # Test thinkdeep
    logger.info("\n1. Testing thinkdeep (research mode):")
    response = zen.thinkdeep(
        step="Research OAuth2 PKCE flow best practices", model="gemini"
    )
    logger.info(f"   Model: {response.model_used}")
    logger.info(f"   Confidence: {response.confidence}")
    logger.info(f"   Content: {response.content[:80]}...")

    # Test planner
    logger.info("\n2. Testing planner (planning mode):")
    response = zen.planner(step="Design authentication architecture", model="sonnet")
    logger.info(f"   Model: {response.model_used}")
    logger.info(f"   Content: {response.content[:80]}...")

    # Test consensus
    logger.info("\n3. Testing consensus (multi-model):")
    response = zen.consensus(step="Should we use JWT or sessions?")
    logger.info(f"   Models: {response.model_used}")
    logger.info(f"   Confidence: {response.confidence}")

    # Test chat
    logger.info("\n4. Testing chat (implementation mode):")
    response = zen.chat(prompt="Implement JWT token generation", model="grok-code")
    logger.info(f"   Model: {response.model_used}")
    logger.info(f"   Content: {response.content[:80]}...")

    logger.info("\n✅ Zen client test complete")
    logger.info(f"\nAvailable models: {len(zen.available_models)}")
