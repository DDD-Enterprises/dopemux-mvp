#!/usr/bin/env python3
"""
DopeClaude: SuperClaude Enhanced with Dopemux Intelligence

This bridge system preserves SuperClaude's elegant command structure while
transparently adding Dopemux's advanced MCP orchestration, ADHD optimizations,
and intelligence amplification.

Architecture:
- Intercepts SuperClaude /sc: commands
- Routes through MetaMCP for intelligent tool selection
- Applies ADHD accommodations and session management
- Preserves SuperClaude's workflow patterns with enhanced capabilities
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dopemux.mcp.broker import MetaMCPBroker, BrokerConfig, ToolCallRequest
from dopemux.mcp.roles import RoleManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DopeCaudeSession:
    """Enhanced session with ADHD accommodations and SuperClaude workflow continuity"""
    session_id: str
    current_role: str = "developer"
    current_persona: Optional[str] = None

    # ADHD session management
    start_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    focus_duration: int = 1500  # 25 minutes
    break_count: int = 0

    # Workflow context preservation
    workflow_chain: List[Dict[str, Any]] = field(default_factory=list)
    active_context: Dict[str, Any] = field(default_factory=dict)
    preserved_state: Dict[str, Any] = field(default_factory=dict)

    # Progress tracking
    tasks_completed: List[str] = field(default_factory=list)
    current_chunk: Optional[str] = None
    progress_markers: List[str] = field(default_factory=list)

    # SuperClaude workflow preservation
    command_history: List[str] = field(default_factory=list)
    context_injections: List[str] = field(default_factory=list)

    @property
    def session_duration(self) -> int:
        """Current session duration in seconds"""
        return int(time.time() - self.start_time)

    @property
    def time_until_break(self) -> int:
        """Time until break suggestion in seconds"""
        return max(0, self.focus_duration - self.session_duration)

    @property
    def should_suggest_break(self) -> bool:
        """Whether to suggest a break based on ADHD accommodations"""
        return self.session_duration >= self.focus_duration

    @property
    def focus_remaining_display(self) -> str:
        """Human-readable focus time remaining"""
        remaining = self.time_until_break
        return f"{remaining // 60}:{remaining % 60:02d}"


class DopeCladueBridge:
    """
    DopeClaude Bridge: SuperClaude + Dopemux Intelligence

    Core Features:
    - Transparent command interception and enhancement
    - MetaMCP intelligent tool routing
    - ADHD-optimized session management
    - Cross-session context preservation
    - Progressive disclosure and cognitive load management
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "integration/superclaude/dopeclaude-config.yaml"
        self.sessions: Dict[str, DopeCaudeSession] = {}
        self.current_session_id = "dopeclaude-main"

        # Core systems
        self.broker: Optional[MetaMCPBroker] = None
        self.config = {}

        # Command mappings
        self.superclaude_commands = {
            # Analysis commands
            "analyze", "review", "audit", "critique",
            # Implementation commands
            "implement", "build", "code", "refactor",
            # Design commands
            "design", "plan", "workflow", "brainstorm",
            # Research commands
            "research", "document", "explore",
            # Operations commands
            "deploy", "test", "monitor", "optimize",
            # Debugging commands
            "debug", "troubleshoot", "diagnose"
        }

        self.cognitive_personas = {
            "architect", "frontend", "backend", "security",
            "analyzer", "qa", "performance", "refactorer", "mentor"
        }

    async def initialize(self) -> bool:
        """Initialize DopeClaude bridge with all subsystems"""
        try:
            logger.info("🚀 Initializing DopeClaude Bridge...")

            # Load configuration
            await self._load_configuration()

            # Initialize MetaMCP broker
            await self._initialize_metamcp()

            # Create default session
            await self._create_session(self.current_session_id)

            logger.info("✅ DopeClaude Bridge initialization complete")
            return True

        except Exception as e:
            logger.error(f"❌ DopeClaude initialization failed: {e}")
            return False

    async def _load_configuration(self):
        """Load DopeClaude configuration with intelligent defaults"""
        config_file = Path(self.config_path)

        # Default configuration
        default_config = {
            "dopeclaude": {
                "mode": "enhanced",  # standard|enhanced|dopemux-full

                # SuperClaude preservation
                "superclaude": {
                    "commands_enabled": True,
                    "personas_enabled": True,
                    "context_injection": True,
                    "workflow_chaining": True
                },

                # Dopemux enhancements
                "dopemux": {
                    "metamcp_orchestration": True,
                    "adhd_optimizations": True,
                    "memory_persistence": True,
                    "multi_model_consensus": True,
                    "progressive_disclosure": True
                },

                # ADHD accommodations
                "adhd": {
                    "session_length": 1500,  # 25 minutes
                    "break_reminders": True,
                    "gentle_guidance": True,
                    "progress_tracking": True,
                    "context_preservation": True,
                    "cognitive_load_management": True
                },

                # Persona-to-role mappings
                "persona_mappings": {
                    "architect": {"role": "architect", "tools": ["zen", "sequential-thinking", "context7"]},
                    "frontend": {"role": "developer", "tools": ["serena", "morphllm-fast-apply", "claude-context"]},
                    "backend": {"role": "developer", "tools": ["serena", "claude-context", "zen"]},
                    "security": {"role": "reviewer", "tools": ["zen", "sequential-thinking", "context7"]},
                    "analyzer": {"role": "researcher", "tools": ["exa", "claude-context", "sequential-thinking"]},
                    "qa": {"role": "reviewer", "tools": ["claude-context", "zen", "sequential-thinking"]},
                    "performance": {"role": "developer", "tools": ["morphllm-fast-apply", "zen", "claude-context"]},
                    "refactorer": {"role": "developer", "tools": ["morphllm-fast-apply", "serena", "claude-context"]},
                    "mentor": {"role": "planner", "tools": ["task-master-ai", "zen", "sequential-thinking"]}
                },

                # Command-to-capability mappings
                "command_mappings": {
                    "analyze": {"role": "researcher", "tools": ["zen", "claude-context"], "consensus": True},
                    "implement": {"role": "developer", "tools": ["serena", "morphllm-fast-apply"], "chunking": True},
                    "design": {"role": "architect", "tools": ["zen", "sequential-thinking"], "consensus": True},
                    "research": {"role": "researcher", "tools": ["exa", "context7", "sequential-thinking"], "depth": "deep"},
                    "review": {"role": "reviewer", "tools": ["claude-context", "zen"], "consensus": True},
                    "optimize": {"role": "developer", "tools": ["morphllm-fast-apply", "zen"], "performance": True},
                    "troubleshoot": {"role": "debugger", "tools": ["zen", "sequential-thinking", "claude-context"], "systematic": True},
                    "plan": {"role": "planner", "tools": ["task-master-ai", "zen"], "chunking": True},
                    "brainstorm": {"role": "architect", "tools": ["zen", "sequential-thinking"], "creative": True},
                    "refactor": {"role": "developer", "tools": ["morphllm-fast-apply", "claude-context"], "safety": True}
                }
            }
        }

        if config_file.exists():
            with open(config_file) as f:
                user_config = yaml.safe_load(f)
                # Deep merge user config with defaults
                self.config = self._deep_merge(default_config, user_config)
        else:
            self.config = default_config

        logger.info(f"📋 Configuration loaded: {self.config['dopeclaude']['mode']} mode")

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge configuration dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    async def _initialize_metamcp(self):
        """Initialize MetaMCP broker for intelligent tool orchestration"""
        config = BrokerConfig(
            name="dopeclaude-metamcp-bridge",
            version="1.0.0",
            broker_config_path="config/mcp/broker.yaml",
            policy_config_path="config/mcp/policy.yaml",
            role_based_mounting=True,
            budget_aware_hooks=True,
            adhd_optimizations=True,
            letta_integration=True
        )

        self.broker = MetaMCPBroker(config)
        await self.broker.start()
        logger.info("🔗 MetaMCP broker initialized")

    async def _create_session(self, session_id: str, role: str = "developer") -> DopeCaudeSession:
        """Create new DopeClaude session with ADHD accommodations"""
        session = DopeCaudeSession(
            session_id=session_id,
            current_role=role,
            focus_duration=self.config["dopeclaude"]["adhd"]["session_length"]
        )

        self.sessions[session_id] = session

        # Initialize role in MetaMCP
        await self.broker.switch_role(session_id, role)

        logger.info(f"🎯 Session created: {session_id} (role: {role})")
        return session

    def parse_command(self, input_text: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Parse SuperClaude and DopeClaude commands

        Supported formats:
        - /sc:analyze "microservices" --focus security --persona architect
        - /dx:focus --duration 25min
        - @agent-architect "design auth system"
        - /sc:implement "user auth" --chunk --safe-mode
        """
        input_text = input_text.strip()

        # SuperClaude commands (/sc:)
        if input_text.startswith("/sc:"):
            pattern = r"/sc:(\w+)(?:\s+[\"']([^\"']*)[\"'])?(?:\s+(.+))?"
            match = re.match(pattern, input_text)
            if match:
                command = match.group(1)
                argument = match.group(2) or ""
                flags_str = match.group(3) or ""
                flags = self._parse_flags(flags_str)
                return "superclaude", command, {"argument": argument, **flags}

        # DopeClaude commands (/dx:)
        elif input_text.startswith("/dx:"):
            pattern = r"/dx:(\w+)(?:\s+[\"']([^\"']*)[\"'])?(?:\s+(.+))?"
            match = re.match(pattern, input_text)
            if match:
                command = match.group(1)
                argument = match.group(2) or ""
                flags_str = match.group(3) or ""
                flags = self._parse_flags(flags_str)
                return "dopeclaude", command, {"argument": argument, **flags}

        # Agent invocations (@agent-)
        elif input_text.startswith("@agent-"):
            pattern = r"@agent-(\w+)(?:\s+[\"']([^\"']*)[\"'])?"
            match = re.match(pattern, input_text)
            if match:
                persona = match.group(1)
                argument = match.group(2) or ""
                return "persona", persona, {"argument": argument}

        return "unknown", "", {}

    def _parse_flags(self, flags_str: str) -> Dict[str, Any]:
        """Parse command flags like --flag value --boolean-flag"""
        flags = {}
        if not flags_str:
            return flags

        # Parse --flag value and --flag patterns
        flag_patterns = re.findall(r'--(\w+)(?:\s+([^\s--]+))?', flags_str)
        for flag, value in flag_patterns:
            if value:
                # Type conversion
                if value.lower() in ['true', 'false']:
                    flags[flag] = value.lower() == 'true'
                elif value.isdigit():
                    flags[flag] = int(value)
                elif value.endswith('min'):
                    flags[flag] = int(value[:-3]) * 60  # Convert minutes to seconds
                else:
                    flags[flag] = value
            else:
                flags[flag] = True

        return flags

    async def process_command(self, input_text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process command with enhanced SuperClaude + Dopemux capabilities"""
        session_id = session_id or self.current_session_id
        session = self.sessions.get(session_id)

        if not session:
            session = await self._create_session(session_id)

        # Update activity tracking
        session.last_activity = time.time()
        session.command_history.append(input_text)

        # Parse command
        command_type, command, params = self.parse_command(input_text)

        try:
            if command_type == "superclaude":
                return await self._process_superclaude_command(command, params, session)
            elif command_type == "dopeclaude":
                return await self._process_dopeclaude_command(command, params, session)
            elif command_type == "persona":
                return await self._process_persona_activation(command, params, session)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command format: {input_text}",
                    "suggestion": "Use /sc:command, /dx:command, or @agent-persona format",
                    "examples": [
                        "/sc:analyze 'code quality' --focus security",
                        "/dx:focus --duration 25min",
                        "@agent-architect 'design microservices'"
                    ]
                }

        except Exception as e:
            logger.error(f"❌ Command processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_info": self._get_session_info(session),
                "suggestion": "Check server health or try a simpler command"
            }

    async def _process_superclaude_command(self, command: str, params: Dict[str, Any], session: DopeCaudeSession) -> Dict[str, Any]:
        """Process SuperClaude command with Dopemux intelligence enhancement"""

        # Validate SuperClaude command
        if command not in self.superclaude_commands:
            return {
                "success": False,
                "error": f"Unknown SuperClaude command: {command}",
                "available_commands": list(self.superclaude_commands),
                "suggestion": f"Did you mean one of: {', '.join(sorted(self.superclaude_commands))}"
            }

        # Get command configuration
        command_config = self.config["dopeclaude"]["command_mappings"].get(command, {})
        suggested_role = command_config.get("role", session.current_role)
        suggested_tools = command_config.get("tools", [])

        # Handle persona override
        if "persona" in params:
            persona = params["persona"]
            if persona in self.cognitive_personas:
                persona_config = self.config["dopeclaude"]["persona_mappings"].get(persona, {})
                suggested_role = persona_config.get("role", suggested_role)
                suggested_tools = persona_config.get("tools", suggested_tools)
                session.current_persona = persona

        # Auto role switching for optimal tool access
        if suggested_role != session.current_role:
            role_result = await self._switch_role(suggested_role, session)
            if not role_result["success"]:
                logger.warning(f"⚠️ Role switch failed, continuing with {session.current_role}")

        # Create enhanced execution context
        enhanced_context = await self._create_enhanced_context(command, params, session, command_config)

        # Execute enhanced SuperClaude command
        return await self._execute_enhanced_command(command, params, session, enhanced_context)

    async def _create_enhanced_context(self, command: str, params: Dict[str, Any], session: DopeCaudeSession, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced execution context with ADHD accommodations"""
        return {
            "command": command,
            "session_info": self._get_session_info(session),
            "adhd_accommodations": {
                "progressive_disclosure": self.config["dopeclaude"]["adhd"]["progressive_disclosure"],
                "gentle_guidance": self.config["dopeclaude"]["adhd"]["gentle_guidance"],
                "chunking_enabled": config.get("chunking", False),
                "break_suggestion": session.should_suggest_break
            },
            "dopemux_enhancements": {
                "multi_model_consensus": config.get("consensus", False),
                "systematic_approach": config.get("systematic", False),
                "performance_optimized": config.get("performance", False),
                "safety_checks": config.get("safety", False)
            },
            "workflow_context": {
                "previous_commands": session.command_history[-3:],  # Last 3 commands
                "active_context": session.active_context,
                "current_chunk": session.current_chunk
            }
        }

    async def _execute_enhanced_command(self, command: str, params: Dict[str, Any], session: DopeCaudeSession, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SuperClaude command with full Dopemux enhancement"""

        argument = params.get("argument", "")

        # Route to specific enhanced implementations
        if command == "analyze":
            return await self._enhanced_analyze(argument, params, session, context)
        elif command == "implement":
            return await self._enhanced_implement(argument, params, session, context)
        elif command == "design":
            return await self._enhanced_design(argument, params, session, context)
        elif command == "research":
            return await self._enhanced_research(argument, params, session, context)
        elif command == "review":
            return await self._enhanced_review(argument, params, session, context)
        elif command == "optimize":
            return await self._enhanced_optimize(argument, params, session, context)
        elif command == "troubleshoot":
            return await self._enhanced_troubleshoot(argument, params, session, context)
        elif command == "plan":
            return await self._enhanced_plan(argument, params, session, context)
        else:
            # Generic enhanced processing for other commands
            return await self._generic_enhanced_command(command, argument, params, session, context)

    async def _switch_role(self, new_role: str, session: DopeCaudeSession) -> Dict[str, Any]:
        """Switch session role with MetaMCP integration"""
        try:
            old_role = session.current_role
            result = await self.broker.switch_role(session.session_id, new_role)

            if result.get("success"):
                session.current_role = new_role

                return {
                    "success": True,
                    "old_role": old_role,
                    "new_role": new_role,
                    "mounted_tools": result.get("mounted_tools", []),
                    "message": f"🔄 **Role Switch**: {old_role} → {new_role}\n\nMounted tools: {', '.join(result.get('mounted_tools', []))}"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown role switch error")
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_session_info(self, session: DopeCaudeSession) -> Dict[str, Any]:
        """Get comprehensive session information"""
        return {
            "session_id": session.session_id,
            "current_role": session.current_role,
            "current_persona": session.current_persona,
            "duration_minutes": round(session.session_duration / 60, 1),
            "focus_remaining": session.focus_remaining_display,
            "should_suggest_break": session.should_suggest_break,
            "break_count": session.break_count,
            "tasks_completed": len(session.tasks_completed),
            "current_chunk": session.current_chunk,
            "workflow_depth": len(session.workflow_chain),
            "commands_executed": len(session.command_history)
        }

    # Enhanced command implementations will be added in the next file
    # to keep this file manageable

    async def _enhanced_analyze(self, argument: str, params: Dict[str, Any], session: DopeCaudeSession, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced analysis with multi-model consensus and ADHD accommodations"""

        focus_area = params.get("focus", "general")

        # Create analysis request with enhancements
        if context["dopemux_enhancements"]["multi_model_consensus"]:
            # Use Zen for multi-model consensus
            tool_request = ToolCallRequest(
                session_id=session.session_id,
                tool_name="zen",
                method="consensus",
                args={
                    "query": f"Analyze {argument}",
                    "focus_area": focus_area,
                    "models": ["claude", "gpt4", "gemini"],
                    "consensus_threshold": 0.8
                },
                role=session.current_role
            )
        else:
            # Use claude-context for focused analysis
            tool_request = ToolCallRequest(
                session_id=session.session_id,
                tool_name="claude-context",
                method="analyze",
                args={
                    "query": argument,
                    "focus_area": focus_area
                },
                role=session.current_role
            )

        response = await self.broker.call_tool(tool_request)

        if response.success:
            # Format with ADHD accommodations
            result_text = f"🔍 **Analysis Complete: {argument}**\n\n"

            if context["adhd_accommodations"]["progressive_disclosure"]:
                result_text += "**Key Insights** (expand for details):\n"
                result_text += "• " + str(response.result)[:200] + "...\n\n"
                result_text += "*Use /dx:expand for full details*\n\n"
            else:
                result_text += str(response.result) + "\n\n"

            # Add gentle break suggestion
            if context["adhd_accommodations"]["break_suggestion"]:
                result_text += "🌿 *Gentle reminder: You've been focusing well! Consider a 5-minute break after reviewing this analysis.*\n"

            # Track progress
            session.tasks_completed.append(f"Analysis: {argument}")
            session.workflow_chain.append({
                "command": "analyze",
                "argument": argument,
                "timestamp": time.time(),
                "result_summary": str(response.result)[:100]
            })

            return {
                "success": True,
                "command": "analyze",
                "result": result_text,
                "session_info": self._get_session_info(session),
                "next_suggestions": ["refine", "implement", "research further"]
            }
        else:
            return {
                "success": False,
                "error": f"Analysis failed: {response.error}",
                "suggestion": "Try switching to researcher role or breaking down into smaller analysis chunks"
            }

async def main():
    """Test DopeClaude bridge functionality"""
    bridge = DopeCladueBridge()

    if await bridge.initialize():
        print("🎉 DopeClaude Bridge initialized successfully!")

        # Test various command formats
        test_commands = [
            "/sc:analyze 'authentication system' --focus security --persona architect",
            "/dx:focus --duration 25min",
            "@agent-security 'review login flow'",
            "/sc:implement 'user registration' --chunk --safe-mode",
            "/dx:status --session"
        ]

        for cmd in test_commands:
            print(f"\n🧪 Testing: {cmd}")
            result = await bridge.process_command(cmd)
            print(f"✅ Success: {result.get('success', False)}")
            if result.get('result'):
                print(f"📝 Result: {result['result'][:150]}...")
    else:
        print("❌ Failed to initialize DopeClaude bridge")

if __name__ == "__main__":
    asyncio.run(main())