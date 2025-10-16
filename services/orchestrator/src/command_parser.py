"""
Command Parser - Step 2 of Phase 1
Parse user input into actionable commands with intent classification

Complexity: 0.45 (Medium)
Effort: 5 focus blocks (125 minutes)
"""

from typing import Optional, Literal
from dataclasses import dataclass
from enum import Enum
import re


class CommandMode(Enum):
    """Workflow modes for AI orchestration."""

    RESEARCH = "research"
    PLAN = "plan"
    IMPLEMENT = "implement"
    DEBUG = "debug"
    REVIEW = "review"
    CHAT = "chat"  # Default conversational mode


class TargetAgent(Enum):
    """Available AI agents."""

    CLAUDE = "claude"
    GEMINI = "gemini"
    GROK = "grok"
    ALL = "all"  # Parallel execution
    AUTO = "auto"  # Automatic selection


@dataclass
class ParsedCommand:
    """
    Structured representation of parsed user command.

    Attributes:
        raw_input: Original user input
        command_type: Slash command or natural language
        mode: Current workflow mode
        target_agent: Which AI instance(s) to use
        message: The actual content/question
        parameters: Additional command parameters
        complexity_score: Estimated task complexity (0.0-1.0)
    """

    raw_input: str
    command_type: Literal["slash", "natural"]
    mode: CommandMode
    target_agent: TargetAgent
    message: str
    parameters: dict[str, str]
    complexity_score: float


class CommandParser:
    """
    Parse user input into structured commands for AI routing.

    Supports:
    - Slash commands: /mode research, /agent gemini, /consensus
    - Natural language: "Research OAuth2 best practices"
    - Intent classification for automatic routing
    """

    # Slash command patterns
    SLASH_COMMANDS = {
        "/mode": r"^/mode\s+(research|plan|implement|debug|review)(?:\s+(.*))?$",
        "/agent": r"^/agent\s+(claude|gemini|grok|all)(?:\s+(.*))?$",
        "/consensus": r"^/consensus(?:\s+(.+))?$",
        "/parallel": r"^/parallel(?:\s+(.+))?$",
        "/pause": r"^/pause$",
        "/resume": r"^/resume$",
        "/context": r"^/context\s+(save|load|summary)$",
        "/memory": r"^/memory\s+(.+)$",
        "/break": r"^/break(?:\s+(\d+))?$",  # Optional duration
        "/focus": r"^/focus$",
        "/energy": r"^/energy(?:\s+(low|medium|high))?$",
        "/suggest": r"^/suggest$",
        "/status": r"^/status$",
        "/health": r"^/health$",
        "/help": r"^/help$",
    }

    # Intent classification keywords
    INTENT_PATTERNS = {
        CommandMode.REVIEW: {
            # REVIEW first - more specific than IMPLEMENT
            "keywords": ["review", "check", "validate", "audit", "assess", "quality", "security"],
            "indicators": ["is this good", "any issues", "code review", "for security", "for quality"],
        },
        CommandMode.DEBUG: {
            # DEBUG second - also specific
            "keywords": ["debug", "fix", "error", "bug", "not working", "failing", "broken"],
            "indicators": ["why is", "error:", "failed"],
        },
        CommandMode.RESEARCH: {
            "keywords": ["research", "find out", "investigate", "analyze", "explore", "search"],
            "indicators": ["what", "how does", "why", "tell me about"],
        },
        CommandMode.PLAN: {
            "keywords": ["design", "plan", "architect", "structure", "organize"],
            "indicators": ["how should", "what's the best way", "strategy for"],
        },
        CommandMode.IMPLEMENT: {
            # IMPLEMENT last - most generic
            "keywords": ["write", "code", "implement", "create", "build", "add", "generate"],
            "indicators": ["make", "create function", "add feature"],
        },
    }

    def __init__(self, default_mode: CommandMode = CommandMode.CHAT):
        """
        Initialize command parser.

        Args:
            default_mode: Default mode if no explicit command
        """
        self.current_mode = default_mode
        self.current_agent = TargetAgent.AUTO

    def parse(self, user_input: str) -> ParsedCommand:
        """
        Parse user input into structured command.

        Args:
            user_input: Raw user input string

        Returns:
            ParsedCommand with routing information

        Examples:
            >>> parser.parse("/mode research")
            ParsedCommand(mode=RESEARCH, ...)

            >>> parser.parse("/agent gemini what is OAuth2?")
            ParsedCommand(target_agent=GEMINI, message="what is OAuth2?")

            >>> parser.parse("Implement JWT token generation")
            ParsedCommand(mode=IMPLEMENT, message="...", complexity=0.7)
        """
        user_input = user_input.strip()

        # Try slash command first
        slash_result = self._parse_slash_command(user_input)
        if slash_result:
            return slash_result

        # Fall back to natural language
        return self._parse_natural_language(user_input)

    def _parse_slash_command(self, input_str: str) -> Optional[ParsedCommand]:
        """Parse slash commands like /mode, /agent, etc."""

        # Check each slash command pattern
        for cmd, pattern in self.SLASH_COMMANDS.items():
            match = re.match(pattern, input_str, re.IGNORECASE)
            if match:
                return self._handle_slash_command(cmd, match)

        return None

    def _handle_slash_command(self, command: str, match: re.Match) -> ParsedCommand:
        """Handle specific slash command matches."""

        groups = match.groups()

        if command == "/mode":
            new_mode = CommandMode(groups[0])
            self.current_mode = new_mode
            message = groups[1] if len(groups) > 1 and groups[1] else f"Mode changed to {new_mode.value}"

            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=new_mode,
                target_agent=self.current_agent,
                message=message,
                parameters={"mode_changed": new_mode.value},
                complexity_score=0.1,  # Meta command, low complexity
            )

        elif command == "/agent":
            target = TargetAgent(groups[0])
            self.current_agent = target
            message = groups[1] if len(groups) > 1 and groups[1] else f"Agent set to {target.value}"

            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=self.current_mode,
                target_agent=target,
                message=message,
                parameters={"agent_changed": target.value},
                complexity_score=self._assess_complexity(message) if groups[1] else 0.1,
            )

        elif command == "/consensus":
            message = groups[0] if groups[0] else "No question provided"

            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=CommandMode.REVIEW,  # Consensus is a review operation
                target_agent=TargetAgent.ALL,  # Requires multiple models
                message=message,
                parameters={"consensus_request": True},
                complexity_score=0.7,  # Consensus is moderately complex
            )

        elif command == "/parallel":
            message = groups[0] if groups[0] else "No task provided"

            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=self.current_mode,
                target_agent=TargetAgent.ALL,
                message=message,
                parameters={"parallel_execution": True},
                complexity_score=self._assess_complexity(message),
            )

        elif command in ["/pause", "/resume"]:
            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=self.current_mode,
                target_agent=TargetAgent.ALL,
                message=command[1:],  # Remove slash
                parameters={"control_command": command[1:]},
                complexity_score=0.1,
            )

        elif command == "/context":
            action = groups[0]  # save|load|summary

            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=self.current_mode,
                target_agent=TargetAgent.AUTO,
                message=f"Context {action}",
                parameters={"context_action": action},
                complexity_score=0.2,
            )

        elif command == "/memory":
            query = groups[0]

            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=CommandMode.RESEARCH,  # Memory query is research
                target_agent=TargetAgent.AUTO,
                message=query,
                parameters={"memory_query": query},
                complexity_score=0.3,
            )

        elif command == "/break":
            duration = int(groups[0]) if groups[0] else 5  # Default 5 minutes

            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=self.current_mode,
                target_agent=TargetAgent.AUTO,
                message=f"Starting {duration} minute break",
                parameters={"break_duration": duration},
                complexity_score=0.1,
            )

        elif command in ["/focus", "/suggest", "/status", "/health", "/help"]:
            cmd_name = command[1:]  # Remove slash

            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=self.current_mode,
                target_agent=TargetAgent.AUTO,
                message=cmd_name,
                parameters={"meta_command": cmd_name},
                complexity_score=0.1,
            )

        elif command == "/energy":
            new_energy = groups[0] if groups[0] else None

            return ParsedCommand(
                raw_input=match.string,
                command_type="slash",
                mode=self.current_mode,
                target_agent=TargetAgent.AUTO,
                message=f"Energy: {new_energy}" if new_energy else "Check energy",
                parameters={"energy_level": new_energy} if new_energy else {},
                complexity_score=0.1,
            )

        # Default for unknown slash commands
        return ParsedCommand(
            raw_input=match.string,
            command_type="slash",
            mode=self.current_mode,
            target_agent=self.current_agent,
            message=f"Unknown command: {command}",
            parameters={"error": "unknown_command"},
            complexity_score=0.0,
        )

    def _parse_natural_language(self, input_str: str) -> ParsedCommand:
        """Parse natural language input and classify intent."""

        # Classify intent
        detected_mode = self._classify_intent(input_str)

        # Assess complexity
        complexity = self._assess_complexity(input_str)

        # Select agent based on mode and complexity
        agent = self._select_agent(detected_mode, complexity)

        return ParsedCommand(
            raw_input=input_str,
            command_type="natural",
            mode=detected_mode,
            target_agent=agent,
            message=input_str,
            parameters={},
            complexity_score=complexity,
        )

    def _classify_intent(self, text: str) -> CommandMode:
        """
        Classify user intent from natural language.

        Uses keyword matching and pattern detection.
        Falls back to current mode if unclear.
        """
        text_lower = text.lower()

        # Score each mode
        scores = {mode: 0.0 for mode in CommandMode}

        for mode, patterns in self.INTENT_PATTERNS.items():
            # Check keywords
            for keyword in patterns["keywords"]:
                if keyword in text_lower:
                    scores[mode] += 1.0

            # Check indicators (question patterns, etc.)
            for indicator in patterns["indicators"]:
                if indicator in text_lower:
                    scores[mode] += 0.5

        # Find highest scoring mode
        if max(scores.values()) > 0:
            detected = max(scores, key=scores.get)
            return detected

        # Fall back to current mode
        return self.current_mode

    def _assess_complexity(self, text: str) -> float:
        """
        Assess task complexity from text description.

        Returns:
            Complexity score 0.0-1.0
            - 0.0-0.3: Low (quick tasks)
            - 0.3-0.6: Medium (standard tasks)
            - 0.6-1.0: High (complex tasks)
        """
        score = 0.3  # Default to medium-low

        text_lower = text.lower()

        # Scope indicators
        scope_keywords = {
            "file": 0.1,
            "function": 0.1,
            "module": 0.2,
            "system": 0.3,
            "entire": 0.4,
            "all": 0.3,
            "complete": 0.3,
            "full": 0.2,
        }

        for keyword, weight in scope_keywords.items():
            if keyword in text_lower:
                score = max(score, weight)

        # Action complexity
        complex_actions = ["refactor", "redesign", "migrate", "optimize", "debug"]
        for action in complex_actions:
            if action in text_lower:
                score += 0.2

        # Multi-file indicators
        if any(word in text_lower for word in ["multiple", "several", "across"]):
            score += 0.2

        # Integration/coordination indicators
        if any(word in text_lower for word in ["integrate", "coordinate", "connect"]):
            score += 0.15

        # Cap at 1.0
        return min(1.0, score)

    def _select_agent(self, mode: CommandMode, complexity: float) -> TargetAgent:
        """
        Select appropriate AI agent based on mode and complexity.

        Agent selection strategy:
        - RESEARCH → Gemini (1M context, analysis strength)
        - PLAN → Claude (architectural thinking)
        - IMPLEMENT → Grok (code specialist, FREE!)
        - DEBUG → Gemini (analytical strength)
        - REVIEW → ALL (multi-model consensus)
        - High complexity (>0.7) → Consider parallel

        Returns:
            Recommended TargetAgent
        """
        # If user set explicit agent, use that
        if self.current_agent != TargetAgent.AUTO:
            return self.current_agent

        # Mode-based selection (validated by research + Zen analysis)
        mode_to_agent = {
            CommandMode.RESEARCH: TargetAgent.GEMINI,  # 1M context, analysis strength
            CommandMode.PLAN: TargetAgent.CLAUDE,  # Architectural thinking
            CommandMode.IMPLEMENT: TargetAgent.GROK,  # Code specialist, FREE!
            CommandMode.DEBUG: TargetAgent.GEMINI,  # Analytical strength
            CommandMode.REVIEW: TargetAgent.ALL,  # Multi-model consensus
            CommandMode.CHAT: TargetAgent.CLAUDE,  # Default conversational
        }

        selected = mode_to_agent[mode]  # Use [] not .get() to catch bugs

        # High complexity override - suggest parallel
        if complexity >= 0.7 and selected != TargetAgent.ALL:
            # Complex tasks benefit from multi-model approach
            selected = TargetAgent.ALL

        return selected


class IntentClassifier:
    """
    Advanced intent classification using pattern matching.

    Future enhancement: Could use ML-based classification if rule-based
    accuracy falls below 85% target.
    """

    def classify(self, text: str) -> tuple[CommandMode, float]:
        """
        Classify intent with confidence score.

        Args:
            text: User input text

        Returns:
            Tuple of (CommandMode, confidence_score)
        """
        # For now, delegate to CommandParser's classifier
        # This class exists as extension point for ML-based classification
        parser = CommandParser()
        mode = parser._classify_intent(text)

        # Calculate confidence based on keyword strength
        confidence = self._calculate_confidence(text, mode)

        return mode, confidence

    def _calculate_confidence(self, text: str, mode: CommandMode) -> float:
        """Calculate confidence in classification."""
        # Simple confidence: 0.8 if strong keywords, 0.5 if weak
        text_lower = text.lower()

        if mode == CommandMode.CHAT:
            return 0.5  # Ambiguous

        patterns = CommandParser.INTENT_PATTERNS.get(mode, {})
        keyword_matches = sum(1 for kw in patterns.get("keywords", []) if kw in text_lower)

        if keyword_matches >= 2:
            return 0.9  # High confidence
        elif keyword_matches == 1:
            return 0.7  # Medium confidence
        else:
            return 0.5  # Low confidence (fallback)


if __name__ == "__main__":
    """Test command parser."""

    parser = CommandParser()

    # Test cases
    test_inputs = [
        "/mode research",
        "/agent gemini analyze the authentication flow",
        "/consensus should we use JWT or sessions?",
        "Research OAuth2 PKCE flow best practices",
        "Design authentication system architecture",
        "Implement JWT token generation",
        "Debug why authentication fails",
        "Review code for security issues",
        "/break 10",
        "/context save",
    ]

    print("Testing Command Parser:")
    print("=" * 60)

    for inp in test_inputs:
        result = parser.parse(inp)
        print(f"\nInput: {inp}")
        print(f"  Type: {result.command_type}")
        print(f"  Mode: {result.mode.value}")
        print(f"  Agent: {result.target_agent.value}")
        print(f"  Message: {result.message}")
        print(f"  Complexity: {result.complexity_score:.2f}")
        if result.parameters:
            print(f"  Params: {result.parameters}")
