"""
Query Classification Engine - Layer 1 of Multi-Layer Architecture

Intelligent classification system that analyzes incoming research queries and determines:
- Research type and scope
- Required search engines and tools
- Appropriate output formats
- ADHD-specific optimizations needed

This enables adaptive research workflows optimized for different use cases and user needs.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from models.research_task import ResearchType, ADHDConfiguration

class QueryIntent(str, Enum):
    """Primary intent behind the research query"""
    FEATURE_PLANNING = "feature_planning"
    BUG_INVESTIGATION = "bug_investigation"
    TECHNOLOGY_EVALUATION = "technology_evaluation"
    ARCHITECTURE_DESIGN = "architecture_design"
    DOCUMENTATION_RESEARCH = "documentation_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    SECURITY_ASSESSMENT = "security_assessment"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    INTEGRATION_PLANNING = "integration_planning"
    EXPLORATORY_RESEARCH = "exploratory_research"

class ResearchScope(str, Enum):
    """Depth and breadth of research required"""
    QUICK_OVERVIEW = "quick_overview"        # 5-10 minutes, 2-3 sources
    STANDARD_RESEARCH = "standard_research"  # 15-25 minutes, 5-8 sources
    DEEP_DIVE = "deep_dive"                 # 30-45 minutes, 10+ sources
    COMPREHENSIVE = "comprehensive"          # 45+ minutes, 15+ sources

class OutputFormat(str, Enum):
    """Preferred output format for results"""
    PRD = "prd"                    # Product Requirements Document
    ADR = "adr"                    # Architectural Decision Record
    RCA = "rca"                    # Root Cause Analysis
    TECHNICAL_GUIDE = "technical_guide"  # Implementation guide
    COMPARISON_MATRIX = "comparison_matrix"  # Feature/tool comparison
    SECURITY_REPORT = "security_report"  # Security assessment
    JSON_STRUCTURED = "json_structured"  # Structured data
    NARRATIVE_REPORT = "narrative_report"  # Traditional research report

class SearchEngineStrategy(str, Enum):
    """Search engine selection strategy"""
    DOCUMENTATION_FIRST = "documentation_first"  # Context7 → Exa → Tavily
    RECENT_DEVELOPMENTS = "recent_developments"   # Tavily → Perplexity → Exa
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"   # Exa → Context7 → Tavily
    BALANCED_APPROACH = "balanced_approach"       # All engines simultaneously

@dataclass
class ClassificationResult:
    """Result of query classification analysis"""
    # Core classification
    intent: QueryIntent
    research_type: ResearchType
    scope: ResearchScope

    # Strategy selection
    search_strategy: SearchEngineStrategy
    output_format: OutputFormat

    # Tool orchestration
    required_tools: List[str]
    optional_tools: List[str]

    # ADHD optimizations
    adhd_config: ADHDConfiguration
    estimated_duration_minutes: int
    complexity_score: float  # 0.0-1.0

    # Reasoning
    confidence: float  # 0.0-1.0
    reasoning: str
    keywords_detected: List[str]

class QueryClassificationEngine:
    """
    Intelligent query classification for adaptive research workflows

    Analyzes natural language queries to determine optimal research strategy,
    tool selection, and ADHD accommodations.
    """

    def __init__(self):
        """Initialize classification engine with pattern libraries"""
        self._load_classification_patterns()
        self._load_complexity_indicators()
        self._load_adhd_optimization_rules()

    async def classify_query(self,
                           query: str,
                           user_context: Optional[Dict] = None,
                           project_context: Optional[Dict] = None) -> ClassificationResult:
        """
        Classify a research query and determine optimal strategy

        Args:
            query: Natural language research query
            user_context: User preferences and history
            project_context: Project-specific context

        Returns:
            Complete classification with recommendations
        """
        # Step 1: Extract keywords and patterns
        keywords = self._extract_keywords(query)
        patterns = self._detect_patterns(query)

        # Step 2: Determine primary intent
        intent = self._classify_intent(query, keywords, patterns)

        # Step 3: Map to research type
        research_type = self._map_to_research_type(intent, patterns)

        # Step 4: Assess scope and complexity
        scope, complexity = self._assess_scope_and_complexity(query, keywords, user_context)

        # Step 5: Select search strategy
        search_strategy = self._select_search_strategy(intent, scope, patterns)

        # Step 6: Determine output format
        output_format = self._determine_output_format(intent, research_type, user_context)

        # Step 7: Plan tool orchestration
        required_tools, optional_tools = self._plan_tool_orchestration(
            intent, scope, search_strategy, patterns
        )

        # Step 8: Configure ADHD optimizations
        adhd_config = self._configure_adhd_optimizations(
            scope, complexity, user_context
        )

        # Step 9: Calculate estimates
        duration = self._estimate_duration(scope, complexity, len(required_tools))

        # Step 10: Generate reasoning
        confidence, reasoning = self._generate_reasoning(
            query, intent, scope, complexity, keywords
        )

        return ClassificationResult(
            intent=intent,
            research_type=research_type,
            scope=scope,
            search_strategy=search_strategy,
            output_format=output_format,
            required_tools=required_tools,
            optional_tools=optional_tools,
            adhd_config=adhd_config,
            estimated_duration_minutes=duration,
            complexity_score=complexity,
            confidence=confidence,
            reasoning=reasoning,
            keywords_detected=keywords
        )

    def _load_classification_patterns(self):
        """Load pattern libraries for intent classification"""
        self.intent_patterns = {
            QueryIntent.FEATURE_PLANNING: [
                r"\b(feature|functionality|capability|requirement)\b",
                r"\b(implement|build|create|develop|add)\b",
                r"\b(user story|epic|requirement|spec)\b",
                r"\b(how to build|how to implement|how to create)\b"
            ],
            QueryIntent.BUG_INVESTIGATION: [
                r"\b(bug|error|issue|problem|failure)\b",
                r"\b(debug|troubleshoot|investigate|diagnose)\b",
                r"\b(not working|failing|broken|crash)\b",
                r"\b(why is|what's wrong|root cause)\b"
            ],
            QueryIntent.TECHNOLOGY_EVALUATION: [
                r"\b(compare|vs|versus|alternative|option)\b",
                r"\b(choose|select|pick|decide|evaluate)\b",
                r"\b(best|better|pros and cons|advantages)\b",
                r"\b(technology|tool|framework|library|platform)\b"
            ],
            QueryIntent.ARCHITECTURE_DESIGN: [
                r"\b(architecture|design|pattern|structure)\b",
                r"\b(system|infrastructure|deployment|scaling)\b",
                r"\b(microservices|monolith|distributed|cloud)\b",
                r"\b(design decision|architectural|system design)\b"
            ],
            QueryIntent.DOCUMENTATION_RESEARCH: [
                r"\b(documentation|docs|guide|tutorial|manual)\b",
                r"\b(how to use|getting started|setup|install)\b",
                r"\b(API reference|configuration|examples)\b",
                r"\b(learn|understand|explain|overview)\b"
            ],
            QueryIntent.SECURITY_ASSESSMENT: [
                r"\b(security|vulnerability|attack|threat)\b",
                r"\b(audit|assessment|penetration|secure)\b",
                r"\b(encryption|authentication|authorization)\b",
                r"\b(OWASP|CVE|security best practices)\b"
            ]
        }

        self.scope_indicators = {
            ResearchScope.QUICK_OVERVIEW: [
                r"\b(quick|brief|summary|overview|simple)\b",
                r"\b(just|only|basic|simple|fast)\b"
            ],
            ResearchScope.DEEP_DIVE: [
                r"\b(comprehensive|detailed|thorough|in-depth)\b",
                r"\b(complete|full|extensive|deep)\b"
            ],
            ResearchScope.COMPREHENSIVE: [
                r"\b(everything|all|complete analysis|full research)\b",
                r"\b(exhaustive|comprehensive study|detailed analysis)\b"
            ]
        }

    def _load_complexity_indicators(self):
        """Load indicators for complexity assessment"""
        self.complexity_indicators = {
            'high': [
                r"\b(enterprise|large-scale|production|mission-critical)\b",
                r"\b(complex|complicated|sophisticated|advanced)\b",
                r"\b(integration|microservices|distributed|cloud-native)\b",
                r"\b(multiple|several|various|many)\b"
            ],
            'medium': [
                r"\b(application|system|service|platform)\b",
                r"\b(moderate|standard|typical|normal)\b",
                r"\b(some|few|couple|pair)\b"
            ],
            'low': [
                r"\b(simple|basic|straightforward|easy)\b",
                r"\b(small|single|one|individual)\b",
                r"\b(minimal|light|quick|fast)\b"
            ]
        }

    def _load_adhd_optimization_rules(self):
        """Load ADHD-specific optimization rules"""
        self.adhd_rules = {
            'high_complexity': {
                'max_concurrent_sources': 3,
                'break_duration_minutes': 10,
                'progressive_disclosure': True,
                'gentle_notifications': True
            },
            'medium_complexity': {
                'max_concurrent_sources': 5,
                'break_duration_minutes': 5,
                'progressive_disclosure': True,
                'gentle_notifications': True
            },
            'low_complexity': {
                'max_concurrent_sources': 7,
                'break_duration_minutes': 5,
                'progressive_disclosure': False,
                'gentle_notifications': False
            }
        }

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Simple keyword extraction - in production, use NLP libraries
        words = re.findall(r'\b\w+\b', query.lower())

        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'cannot', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}

        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        # Return top 10 most relevant keywords
        return keywords[:10]

    def _detect_patterns(self, query: str) -> Dict[str, List[str]]:
        """Detect classification patterns in query"""
        detected = {}

        for intent, patterns in self.intent_patterns.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    matches.append(pattern)
            if matches:
                detected[intent.value] = matches

        return detected

    def _classify_intent(self, query: str, keywords: List[str], patterns: Dict) -> QueryIntent:
        """Determine primary intent of the query"""
        intent_scores = {}

        # Score based on pattern matches
        for intent_str, matches in patterns.items():
            intent_scores[intent_str] = len(matches)

        # Add keyword-based scoring
        intent_keywords = {
            'feature_planning': ['feature', 'implement', 'build', 'create', 'requirement'],
            'bug_investigation': ['bug', 'error', 'issue', 'problem', 'debug'],
            'technology_evaluation': ['compare', 'vs', 'choose', 'best', 'alternative'],
            'architecture_design': ['architecture', 'design', 'system', 'pattern'],
            'documentation_research': ['documentation', 'docs', 'guide', 'tutorial', 'how'],
            'security_assessment': ['security', 'vulnerability', 'secure', 'audit']
        }

        for intent_str, intent_words in intent_keywords.items():
            keyword_score = sum(1 for word in keywords if word in intent_words)
            intent_scores[intent_str] = intent_scores.get(intent_str, 0) + keyword_score

        # Return highest scoring intent or default
        if intent_scores:
            top_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            return QueryIntent(top_intent)

        return QueryIntent.EXPLORATORY_RESEARCH

    def _map_to_research_type(self, intent: QueryIntent, patterns: Dict) -> ResearchType:
        """Map query intent to research type"""
        mapping = {
            QueryIntent.FEATURE_PLANNING: ResearchType.FEATURE_RESEARCH,
            QueryIntent.BUG_INVESTIGATION: ResearchType.BUG_INVESTIGATION,
            QueryIntent.TECHNOLOGY_EVALUATION: ResearchType.TECHNOLOGY_EVALUATION,
            QueryIntent.ARCHITECTURE_DESIGN: ResearchType.SYSTEM_ARCHITECTURE,
            QueryIntent.DOCUMENTATION_RESEARCH: ResearchType.DOCUMENTATION_RESEARCH,
            QueryIntent.COMPETITIVE_ANALYSIS: ResearchType.COMPETITIVE_ANALYSIS,
            QueryIntent.SECURITY_ASSESSMENT: ResearchType.TECHNOLOGY_EVALUATION,
            QueryIntent.PERFORMANCE_OPTIMIZATION: ResearchType.SYSTEM_ARCHITECTURE,
            QueryIntent.INTEGRATION_PLANNING: ResearchType.SYSTEM_ARCHITECTURE,
            QueryIntent.EXPLORATORY_RESEARCH: ResearchType.DOCUMENTATION_RESEARCH
        }

        return mapping.get(intent, ResearchType.FEATURE_RESEARCH)

    def _assess_scope_and_complexity(self, query: str, keywords: List[str], user_context: Optional[Dict]) -> Tuple[ResearchScope, float]:
        """Assess research scope and complexity"""
        # Assess scope based on indicators
        scope_scores = {}
        for scope, indicators in self.scope_indicators.items():
            score = sum(1 for pattern in indicators if re.search(pattern, query, re.IGNORECASE))
            if score > 0:
                scope_scores[scope] = score

        # Default scope determination
        if not scope_scores:
            if len(keywords) <= 3:
                scope = ResearchScope.QUICK_OVERVIEW
            elif len(keywords) <= 7:
                scope = ResearchScope.STANDARD_RESEARCH
            else:
                scope = ResearchScope.DEEP_DIVE
        else:
            scope = max(scope_scores.items(), key=lambda x: x[1])[0]

        # Assess complexity
        complexity_score = 0.5  # Default medium complexity

        for level, indicators in self.complexity_indicators.items():
            for pattern in indicators:
                if re.search(pattern, query, re.IGNORECASE):
                    if level == 'high':
                        complexity_score += 0.2
                    elif level == 'low':
                        complexity_score -= 0.2

        # Clamp to valid range
        complexity_score = max(0.1, min(1.0, complexity_score))

        return scope, complexity_score

    def _select_search_strategy(self, intent: QueryIntent, scope: ResearchScope, patterns: Dict) -> SearchEngineStrategy:
        """Select optimal search engine strategy"""
        # Strategy based on intent
        intent_strategies = {
            QueryIntent.DOCUMENTATION_RESEARCH: SearchEngineStrategy.DOCUMENTATION_FIRST,
            QueryIntent.TECHNOLOGY_EVALUATION: SearchEngineStrategy.RECENT_DEVELOPMENTS,
            QueryIntent.BUG_INVESTIGATION: SearchEngineStrategy.TECHNICAL_DEEP_DIVE,
            QueryIntent.ARCHITECTURE_DESIGN: SearchEngineStrategy.TECHNICAL_DEEP_DIVE,
            QueryIntent.SECURITY_ASSESSMENT: SearchEngineStrategy.RECENT_DEVELOPMENTS
        }

        # Adjust based on scope
        strategy = intent_strategies.get(intent, SearchEngineStrategy.BALANCED_APPROACH)

        if scope in [ResearchScope.COMPREHENSIVE, ResearchScope.DEEP_DIVE]:
            strategy = SearchEngineStrategy.BALANCED_APPROACH

        return strategy

    def _determine_output_format(self, intent: QueryIntent, research_type: ResearchType, user_context: Optional[Dict]) -> OutputFormat:
        """Determine optimal output format"""
        format_mapping = {
            QueryIntent.FEATURE_PLANNING: OutputFormat.PRD,
            QueryIntent.BUG_INVESTIGATION: OutputFormat.RCA,
            QueryIntent.TECHNOLOGY_EVALUATION: OutputFormat.COMPARISON_MATRIX,
            QueryIntent.ARCHITECTURE_DESIGN: OutputFormat.ADR,
            QueryIntent.DOCUMENTATION_RESEARCH: OutputFormat.TECHNICAL_GUIDE,
            QueryIntent.SECURITY_ASSESSMENT: OutputFormat.SECURITY_REPORT
        }

        return format_mapping.get(intent, OutputFormat.NARRATIVE_REPORT)

    def _plan_tool_orchestration(self, intent: QueryIntent, scope: ResearchScope, strategy: SearchEngineStrategy, patterns: Dict) -> Tuple[List[str], List[str]]:
        """Plan which tools to use for research"""
        required_tools = ["context7"]  # Always start with documentation
        optional_tools = []

        # Add search engines based on strategy
        if strategy == SearchEngineStrategy.DOCUMENTATION_FIRST:
            required_tools.extend(["context7", "exa"])
            optional_tools.extend(["tavily", "perplexity"])
        elif strategy == SearchEngineStrategy.RECENT_DEVELOPMENTS:
            required_tools.extend(["tavily", "perplexity"])
            optional_tools.extend(["exa", "context7"])
        elif strategy == SearchEngineStrategy.TECHNICAL_DEEP_DIVE:
            required_tools.extend(["exa", "context7"])
            optional_tools.extend(["tavily"])
        else:  # BALANCED_APPROACH
            required_tools.extend(["context7", "exa", "tavily"])
            optional_tools.extend(["perplexity"])

        # Add analysis tools based on intent
        if intent in [QueryIntent.TECHNOLOGY_EVALUATION, QueryIntent.ARCHITECTURE_DESIGN]:
            optional_tools.append("zen-consensus")

        if scope in [ResearchScope.DEEP_DIVE, ResearchScope.COMPREHENSIVE]:
            optional_tools.append("mas-sequential-thinking")

        return required_tools, optional_tools

    def _configure_adhd_optimizations(self, scope: ResearchScope, complexity: float, user_context: Optional[Dict]) -> ADHDConfiguration:
        """Configure ADHD-specific optimizations"""
        # Determine complexity category
        if complexity >= 0.7:
            category = 'high_complexity'
        elif complexity >= 0.4:
            category = 'medium_complexity'
        else:
            category = 'low_complexity'

        rules = self.adhd_rules[category]

        # Adjust work duration based on scope
        work_duration = {
            ResearchScope.QUICK_OVERVIEW: 15,
            ResearchScope.STANDARD_RESEARCH: 25,
            ResearchScope.DEEP_DIVE: 35,
            ResearchScope.COMPREHENSIVE: 45
        }.get(scope, 25)

        return ADHDConfiguration(
            pomodoro_enabled=True,
            work_duration_minutes=work_duration,
            break_duration_minutes=rules['break_duration_minutes'],
            max_concurrent_sources=rules['max_concurrent_sources'],
            progressive_disclosure=rules['progressive_disclosure'],
            auto_save_interval_seconds=30,
            gentle_notifications=rules['gentle_notifications'],
            visual_progress_enabled=True
        )

    def _estimate_duration(self, scope: ResearchScope, complexity: float, tool_count: int) -> int:
        """Estimate research duration in minutes"""
        base_duration = {
            ResearchScope.QUICK_OVERVIEW: 8,
            ResearchScope.STANDARD_RESEARCH: 20,
            ResearchScope.DEEP_DIVE: 35,
            ResearchScope.COMPREHENSIVE: 50
        }.get(scope, 20)

        # Adjust for complexity
        duration = base_duration * (0.7 + 0.6 * complexity)

        # Adjust for tool count
        duration += (tool_count - 2) * 3

        return int(duration)

    def _generate_reasoning(self, query: str, intent: QueryIntent, scope: ResearchScope, complexity: float, keywords: List[str]) -> Tuple[float, str]:
        """Generate reasoning for classification decisions"""
        confidence = 0.8  # Base confidence

        reasoning_parts = [
            f"Query classified as {intent.value.replace('_', ' ')} based on detected patterns.",
            f"Research scope: {scope.value.replace('_', ' ')} (complexity: {complexity:.1f}).",
            f"Key terms: {', '.join(keywords[:5])}."
        ]

        # Adjust confidence based on keyword clarity
        if len(keywords) >= 5:
            confidence += 0.1
        if complexity > 0.8 or complexity < 0.3:
            confidence += 0.05

        reasoning = " ".join(reasoning_parts)

        return min(0.95, confidence), reasoning