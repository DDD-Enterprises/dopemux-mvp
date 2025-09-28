#!/usr/bin/env python3
"""
Architecture & Design Orchestrator
Specialized system for handling architecture, design patterns, user stories, and high-level decisions
across the Context7-first multi-agent platform.

This orchestrator coordinates between agents to handle:
- Architectural decision records (ADRs)
- Design pattern recommendations  
- User story analysis and breakdown
- Cross-system design consistency
- Technical debt identification
- Migration planning
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ArchitecturalConcern(Enum):
    SYSTEM_DESIGN = "system_design"
    DATA_ARCHITECTURE = "data_architecture" 
    API_DESIGN = "api_design"
    SECURITY_ARCHITECTURE = "security_architecture"
    SCALABILITY = "scalability"
    PERFORMANCE = "performance"
    INTEGRATION_PATTERNS = "integration_patterns"
    DEPLOYMENT_ARCHITECTURE = "deployment_architecture"

class DesignComplexity(Enum):
    SIMPLE = "simple"           # Single agent can handle
    MODERATE = "moderate"       # 2-3 agents coordination
    COMPLEX = "complex"         # Multi-agent orchestration
    ENTERPRISE = "enterprise"   # Full platform coordination

@dataclass
class ArchitecturalDecision:
    id: str
    title: str
    concern: ArchitecturalConcern
    complexity: DesignComplexity
    description: str
    context: str
    options_considered: List[Dict[str, Any]]
    decision: str
    rationale: str
    consequences: List[str]
    agents_consulted: List[str]
    context7_patterns_referenced: List[str]
    status: str  # "proposed", "accepted", "rejected", "superseded"
    timestamp: datetime
    related_decisions: List[str] = None

@dataclass
class UserStory:
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    business_value: str
    complexity_estimate: DesignComplexity
    architectural_impact: List[ArchitecturalConcern]
    required_agents: List[str]
    context7_research_needed: List[str]
    technical_considerations: List[str]
    dependencies: List[str] = None
    status: str = "backlog"

class ArchitectureOrchestrator:
    def __init__(self, agent_registry: Dict[str, Any]):
        self.agent_registry = agent_registry
        self.decisions: Dict[str, ArchitecturalDecision] = {}
        self.user_stories: Dict[str, UserStory] = {}
        self.design_patterns_cache: Dict[str, Any] = {}
        
    async def analyze_architectural_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze incoming request to determine architectural approach needed"""
        
        # Determine if this is architecture, design, or story related
        request_type = self.classify_request(request)
        complexity = self.assess_complexity(request)
        
        if request_type == "architecture":
            return await self.handle_architectural_decision(request, complexity)
        elif request_type == "design": 
            return await self.handle_design_pattern_request(request, complexity)
        elif request_type == "user_story":
            return await self.handle_user_story(request, complexity)
        elif request_type == "system_analysis":
            return await self.handle_system_analysis(request, complexity)
        else:
            return await self.handle_general_design_consultation(request, complexity)
    
    def classify_request(self, request: Dict[str, Any]) -> str:
        """Classify the type of architectural request"""
        
        content = str(request).lower()
        
        # Architecture keywords
        arch_keywords = [
            "architecture", "architectural", "system design", "adr",
            "technical decision", "design decision", "migration",
            "scalability", "integration pattern"
        ]
        
        # Design pattern keywords
        design_keywords = [
            "design pattern", "pattern", "implementation approach",
            "code structure", "class design", "module design"
        ]
        
        # User story keywords  
        story_keywords = [
            "user story", "feature", "requirement", "acceptance criteria",
            "business value", "epic", "backlog"
        ]
        
        # System analysis keywords
        analysis_keywords = [
            "analyze system", "understand codebase", "review architecture",
            "assess current design", "technical debt", "refactoring"
        ]
        
        if any(keyword in content for keyword in arch_keywords):
            return "architecture"
        elif any(keyword in content for keyword in design_keywords):
            return "design"
        elif any(keyword in content for keyword in story_keywords):
            return "user_story"
        elif any(keyword in content for keyword in analysis_keywords):
            return "system_analysis"
        else:
            return "general"
    
    def assess_complexity(self, request: Dict[str, Any]) -> DesignComplexity:
        """Assess the complexity of the architectural request"""
        
        content = str(request).lower()
        
        # Enterprise-level indicators
        enterprise_indicators = [
            "microservices", "distributed system", "multi-tenant",
            "enterprise integration", "compliance", "governance",
            "cross-system", "platform-wide"
        ]
        
        # Complex indicators
        complex_indicators = [
            "multiple services", "integration", "migration",
            "performance critical", "security sensitive",
            "data consistency", "event sourcing"
        ]
        
        # Moderate indicators
        moderate_indicators = [
            "api design", "database design", "component design",
            "pattern selection", "refactoring"
        ]
        
        if any(indicator in content for indicator in enterprise_indicators):
            return DesignComplexity.ENTERPRISE
        elif any(indicator in content for indicator in complex_indicators):
            return DesignComplexity.COMPLEX
        elif any(indicator in content for indicator in moderate_indicators):
            return DesignComplexity.MODERATE
        else:
            return DesignComplexity.SIMPLE
    
    async def handle_architectural_decision(self, request: Dict[str, Any], 
                                          complexity: DesignComplexity) -> Dict[str, Any]:
        """Handle architectural decision making process"""
        
        logger.info(f"Processing architectural decision with complexity: {complexity.value}")
        
        # Step 1: Context7 research for architectural patterns
        context7_research = await self.research_architectural_patterns(request)
        
        # Step 2: Assemble appropriate agent team based on complexity
        agent_team = self.assemble_architecture_team(complexity, request)
        
        # Step 3: Coordinate multi-agent architectural analysis
        analysis_results = await self.coordinate_architectural_analysis(
            request, agent_team, context7_research
        )
        
        # Step 4: Create ADR (Architectural Decision Record)
        adr = await self.create_architectural_decision_record(
            request, analysis_results, context7_research
        )
        
        # Step 5: Store in ConPort for persistence
        await self.store_in_conport(adr, "architectural_decision")
        
        return {
            "type": "architectural_decision",
            "complexity": complexity.value,
            "adr_id": adr.id,
            "decision": adr.decision,
            "rationale": adr.rationale,
            "agents_involved": agent_team,
            "context7_patterns": adr.context7_patterns_referenced,
            "implementation_guidance": analysis_results.get("implementation_guidance", []),
            "next_steps": analysis_results.get("next_steps", [])
        }
    
    async def research_architectural_patterns(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Use Context7 to research relevant architectural patterns and best practices"""
        
        # Extract architectural concerns from request
        concerns = self.extract_architectural_concerns(request)
        
        context7_queries = []
        for concern in concerns:
            # Query Context7 for each architectural concern
            query = {
                "agent": "context7_agent",
                "operation": "search_architectural_patterns",
                "parameters": {
                    "concern": concern.value,
                    "query": f"architectural patterns for {concern.value}",
                    "focus": "design patterns, best practices, implementation examples"
                }
            }
            context7_queries.append(query)
        
        # Execute Context7 queries in parallel
        context7_results = await asyncio.gather(*[
            self.execute_agent_query(query) for query in context7_queries
        ])
        
        # Compile research results
        research = {
            "patterns_found": [],
            "best_practices": [],
            "implementation_examples": [],
            "anti_patterns": [],
            "considerations": []
        }
        
        for result in context7_results:
            if result.get("success"):
                research["patterns_found"].extend(result.get("patterns", []))
                research["best_practices"].extend(result.get("practices", []))
                research["implementation_examples"].extend(result.get("examples", []))
        
        logger.info(f"Context7 research completed: {len(research['patterns_found'])} patterns found")
        return research
    
    def extract_architectural_concerns(self, request: Dict[str, Any]) -> List[ArchitecturalConcern]:
        """Extract architectural concerns from the request"""
        
        content = str(request).lower()
        concerns = []
        
        concern_keywords = {
            ArchitecturalConcern.SYSTEM_DESIGN: ["system", "architecture", "overall design"],
            ArchitecturalConcern.DATA_ARCHITECTURE: ["database", "data", "storage", "persistence"],
            ArchitecturalConcern.API_DESIGN: ["api", "endpoint", "interface", "rest", "graphql"],
            ArchitecturalConcern.SECURITY_ARCHITECTURE: ["security", "authentication", "authorization"],
            ArchitecturalConcern.SCALABILITY: ["scalability", "scale", "performance", "load"],
            ArchitecturalConcern.INTEGRATION_PATTERNS: ["integration", "microservices", "communication"],
            ArchitecturalConcern.DEPLOYMENT_ARCHITECTURE: ["deployment", "infrastructure", "devops"]
        }
        
        for concern, keywords in concern_keywords.items():
            if any(keyword in content for keyword in keywords):
                concerns.append(concern)
        
        # Default to system design if no specific concerns identified
        if not concerns:
            concerns.append(ArchitecturalConcern.SYSTEM_DESIGN)
        
        return concerns
    
    def assemble_architecture_team(self, complexity: DesignComplexity, 
                                 request: Dict[str, Any]) -> List[str]:
        """Assemble appropriate agent team based on complexity and request type"""
        
        base_team = ["context7_agent"]  # Always include Context7 for authoritative patterns
        
        if complexity == DesignComplexity.SIMPLE:
            # Single specialized agent + Context7
            team = base_team + ["serena_agent"]  # For implementation insights
            
        elif complexity == DesignComplexity.MODERATE:
            # Small coordinated team
            team = base_team + ["serena_agent", "zen_reviewer", "conport_agent"]
            
        elif complexity == DesignComplexity.COMPLEX:
            # Multi-agent coordination
            team = base_team + [
                "serena_agent",        # Implementation analysis
                "zen_reviewer",        # Design review and validation  
                "taskmaster_agent",    # Task breakdown for implementation
                "conport_agent",       # Decision tracking
                "sequential_thinking_agent"  # Complex reasoning
            ]
            
        elif complexity == DesignComplexity.ENTERPRISE:
            # Full platform coordination
            team = base_team + [
                "serena_agent", "zen_reviewer", "taskmaster_agent", 
                "conport_agent", "sequential_thinking_agent",
                "exa_agent",           # Additional research
                "testing_agent",       # Testing strategy
                "openmemory_agent"     # Cross-project patterns
            ]
        
        logger.info(f"Assembled {len(team)} agents for {complexity.value} architectural task")
        return team
    
    async def coordinate_architectural_analysis(self, request: Dict[str, Any], 
                                              agent_team: List[str],
                                              context7_research: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multi-agent analysis of architectural decision"""
        
        # Phase 1: Parallel analysis by specialized agents
        analysis_tasks = []
        
        for agent in agent_team:
            if agent == "context7_agent":
                continue  # Already completed research phase
            
            task = {
                "agent": agent,
                "operation": self.get_agent_analysis_operation(agent),
                "parameters": {
                    "request": request,
                    "context7_research": context7_research,
                    "focus": self.get_agent_focus_area(agent)
                }
            }
            analysis_tasks.append(task)
        
        # Execute parallel analysis
        analysis_results = await asyncio.gather(*[
            self.execute_agent_query(task) for task in analysis_tasks
        ])
        
        # Phase 2: Synthesis and coordination
        synthesis_task = {
            "agent": "sequential_thinking_agent",
            "operation": "synthesize_architectural_analysis", 
            "parameters": {
                "request": request,
                "context7_research": context7_research,
                "agent_analyses": analysis_results,
                "synthesis_focus": "architectural decision synthesis"
            }
        }
        
        synthesis_result = await self.execute_agent_query(synthesis_task)
        
        # Compile comprehensive analysis
        comprehensive_analysis = {
            "individual_analyses": {
                agent_team[i]: result for i, result in enumerate(analysis_results)
            },
            "synthesis": synthesis_result,
            "implementation_guidance": synthesis_result.get("implementation_steps", []),
            "next_steps": synthesis_result.get("recommended_next_steps", []),
            "risks_identified": synthesis_result.get("risks", []),
            "alternatives_considered": synthesis_result.get("alternatives", [])
        }
        
        logger.info("Multi-agent architectural analysis completed")
        return comprehensive_analysis
    
    def get_agent_analysis_operation(self, agent: str) -> str:
        """Get the appropriate analysis operation for each agent type"""
        
        operations = {
            "serena_agent": "analyze_implementation_feasibility",
            "zen_reviewer": "review_architectural_quality",
            "taskmaster_agent": "break_down_architectural_tasks",
            "testing_agent": "analyze_testing_implications",
            "sequential_thinking_agent": "deep_architectural_reasoning",
            "exa_agent": "research_industry_patterns",
            "conport_agent": "track_decision_impact",
            "openmemory_agent": "reference_similar_decisions"
        }
        
        return operations.get(agent, "general_analysis")
    
    def get_agent_focus_area(self, agent: str) -> str:
        """Get the focus area for each agent in architectural analysis"""
        
        focus_areas = {
            "serena_agent": "implementation complexity, code structure, technical feasibility",
            "zen_reviewer": "design quality, maintainability, code review implications",
            "taskmaster_agent": "task breakdown, implementation timeline, resource requirements",
            "testing_agent": "testing strategy, quality assurance, validation approach",
            "sequential_thinking_agent": "deep reasoning, complex trade-offs, long-term implications",
            "exa_agent": "industry best practices, external research, competitive analysis",
            "conport_agent": "decision tracking, historical context, impact assessment",
            "openmemory_agent": "cross-project patterns, reusable approaches, lessons learned"
        }
        
        return focus_areas.get(agent, "general architectural considerations")
    
    async def execute_agent_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query against specific agent (placeholder for MCP integration)"""
        
        # This would integrate with your MCP infrastructure
        # For now, simulate agent responses based on their specialization
        
        agent = query["agent"]
        operation = query["operation"]
        
        logger.info(f"Executing {operation} on {agent}")
        
        # Simulate agent-specific responses
        if agent == "serena_agent":
            return {
                "success": True,
                "analysis": "Implementation analysis complete",
                "complexity_assessment": "moderate",
                "technical_considerations": ["Code structure implications", "Refactoring requirements"],
                "implementation_steps": ["Phase 1: Core structure", "Phase 2: Integration"]
            }
        elif agent == "zen_reviewer":
            return {
                "success": True,
                "quality_assessment": "high",
                "maintainability_score": 85,
                "design_patterns_recommended": ["Strategy", "Observer"],
                "potential_issues": ["Coupling concerns", "Testing complexity"]
            }
        # ... other agent simulations
        
        return {"success": True, "message": f"Analysis completed by {agent}"}
    
    async def create_architectural_decision_record(self, request: Dict[str, Any],
                                                 analysis: Dict[str, Any],
                                                 context7_research: Dict[str, Any]) -> ArchitecturalDecision:
        """Create comprehensive ADR from analysis results"""
        
        adr_id = f"ADR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Extract decision components from analysis
        synthesis = analysis.get("synthesis", {})
        
        adr = ArchitecturalDecision(
            id=adr_id,
            title=request.get("title", "Architectural Decision"),
            concern=self.extract_primary_concern(request),
            complexity=self.assess_complexity(request),
            description=request.get("description", ""),
            context=synthesis.get("context", ""),
            options_considered=synthesis.get("alternatives", []),
            decision=synthesis.get("recommended_decision", ""),
            rationale=synthesis.get("rationale", ""),
            consequences=synthesis.get("consequences", []),
            agents_consulted=list(analysis.get("individual_analyses", {}).keys()),
            context7_patterns_referenced=context7_research.get("patterns_found", []),
            status="proposed",
            timestamp=datetime.now()
        )
        
        self.decisions[adr_id] = adr
        logger.info(f"Created ADR {adr_id}: {adr.title}")
        
        return adr
    
    def extract_primary_concern(self, request: Dict[str, Any]) -> ArchitecturalConcern:
        """Extract the primary architectural concern from request"""
        concerns = self.extract_architectural_concerns(request)
        return concerns[0] if concerns else ArchitecturalConcern.SYSTEM_DESIGN
    
    async def store_in_conport(self, adr: ArchitecturalDecision, type_name: str):
        """Store ADR in ConPort for persistent project memory"""
        
        conport_entry = {
            "agent": "conport_agent",
            "operation": "log_decision",
            "parameters": {
                "summary": f"{adr.title} (ADR-{adr.id})",
                "rationale": adr.rationale,
                "implementation_details": f"Decision: {adr.decision}. Consequences: {', '.join(adr.consequences)}",
                "tags": [adr.concern.value, adr.complexity.value, "adr", "architecture"]
            }
        }
        
        await self.execute_agent_query(conport_entry)
        logger.info(f"Stored ADR {adr.id} in ConPort")
    
    async def handle_user_story(self, request: Dict[str, Any], 
                              complexity: DesignComplexity) -> Dict[str, Any]:
        """Handle user story analysis and architectural impact assessment"""
        
        logger.info(f"Processing user story with complexity: {complexity.value}")
        
        # Analyze architectural impact of the user story
        architectural_impact = await self.assess_story_architectural_impact(request)
        
        # Create user story with technical considerations
        story = await self.create_technical_user_story(request, complexity, architectural_impact)
        
        # Store in ConPort
        await self.store_user_story_in_conport(story)
        
        return {
            "type": "user_story",
            "story_id": story.id,
            "complexity": complexity.value,
            "architectural_impact": [concern.value for concern in story.architectural_impact],
            "required_agents": story.required_agents,
            "context7_research": story.context7_research_needed,
            "technical_breakdown": story.technical_considerations,
            "implementation_approach": architectural_impact.get("implementation_approach", "")
        }
    
    async def assess_story_architectural_impact(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the architectural impact of a user story"""
        
        # Use Context7 to research relevant patterns for the story
        story_research = await self.research_story_patterns(request)
        
        # Analyze with architectural lens
        impact_analysis = {
            "affected_systems": [],
            "new_components_needed": [],
            "integration_requirements": [],
            "data_implications": [],
            "security_considerations": [],
            "performance_implications": [],
            "implementation_approach": ""
        }
        
        # This would involve more sophisticated analysis in practice
        content = str(request).lower()
        
        if "user" in content or "authentication" in content:
            impact_analysis["affected_systems"].append("Authentication System")
            impact_analysis["security_considerations"].append("User credential handling")
        
        if "api" in content or "endpoint" in content:
            impact_analysis["affected_systems"].append("API Layer")
            impact_analysis["integration_requirements"].append("REST API design")
        
        if "data" in content or "database" in content:
            impact_analysis["data_implications"].append("Database schema changes")
        
        return impact_analysis
    
    async def research_story_patterns(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Research implementation patterns for user story using Context7"""
        
        context7_query = {
            "agent": "context7_agent",
            "operation": "research_implementation_patterns",
            "parameters": {
                "story_description": request.get("description", ""),
                "focus": "implementation patterns, code examples, best practices"
            }
        }
        
        return await self.execute_agent_query(context7_query)
    
    async def create_technical_user_story(self, request: Dict[str, Any], 
                                        complexity: DesignComplexity,
                                        architectural_impact: Dict[str, Any]) -> UserStory:
        """Create user story with technical and architectural considerations"""
        
        story_id = f"US-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Determine required agents based on complexity and impact
        required_agents = self.determine_story_agents(complexity, architectural_impact)
        
        # Determine Context7 research needs
        context7_research = self.determine_context7_research_needs(architectural_impact)
        
        story = UserStory(
            id=story_id,
            title=request.get("title", "User Story"),
            description=request.get("description", ""),
            acceptance_criteria=request.get("acceptance_criteria", []),
            business_value=request.get("business_value", ""),
            complexity_estimate=complexity,
            architectural_impact=self.map_impact_to_concerns(architectural_impact),
            required_agents=required_agents,
            context7_research_needed=context7_research,
            technical_considerations=self.extract_technical_considerations(architectural_impact)
        )
        
        self.user_stories[story_id] = story
        logger.info(f"Created user story {story_id}: {story.title}")
        
        return story
    
    def determine_story_agents(self, complexity: DesignComplexity, 
                             impact: Dict[str, Any]) -> List[str]:
        """Determine which agents are needed for user story implementation"""
        
        agents = ["context7_agent"]  # Always need Context7 for patterns
        
        # Always need implementation agent
        agents.append("serena_agent")
        
        # Add based on impact
        if impact.get("integration_requirements"):
            agents.append("exa_agent")  # For integration research
        
        if impact.get("security_considerations"):
            agents.append("zen_reviewer")  # For security review
        
        if complexity in [DesignComplexity.COMPLEX, DesignComplexity.ENTERPRISE]:
            agents.extend(["taskmaster_agent", "conport_agent"])
        
        return list(set(agents))  # Remove duplicates
    
    def determine_context7_research_needs(self, impact: Dict[str, Any]) -> List[str]:
        """Determine what Context7 research is needed for the story"""
        
        research_needs = []
        
        if impact.get("integration_requirements"):
            research_needs.append("Integration patterns and best practices")
        
        if impact.get("security_considerations"):
            research_needs.append("Security implementation patterns")
        
        if impact.get("data_implications"):
            research_needs.append("Data access patterns and ORM usage")
        
        if impact.get("performance_implications"):
            research_needs.append("Performance optimization patterns")
        
        return research_needs
    
    def map_impact_to_concerns(self, impact: Dict[str, Any]) -> List[ArchitecturalConcern]:
        """Map architectural impact to architectural concerns"""
        
        concerns = []
        
        if impact.get("integration_requirements"):
            concerns.append(ArchitecturalConcern.INTEGRATION_PATTERNS)
        
        if impact.get("security_considerations"):
            concerns.append(ArchitecturalConcern.SECURITY_ARCHITECTURE)
        
        if impact.get("data_implications"):
            concerns.append(ArchitecturalConcern.DATA_ARCHITECTURE)
        
        if impact.get("performance_implications"):
            concerns.append(ArchitecturalConcern.PERFORMANCE)
        
        # Default to system design if no specific concerns
        if not concerns:
            concerns.append(ArchitecturalConcern.SYSTEM_DESIGN)
        
        return concerns
    
    def extract_technical_considerations(self, impact: Dict[str, Any]) -> List[str]:
        """Extract technical considerations from architectural impact"""
        
        considerations = []
        
        for key, value in impact.items():
            if value and isinstance(value, list):
                considerations.extend([f"{key}: {item}" for item in value])
            elif value and isinstance(value, str):
                considerations.append(f"{key}: {value}")
        
        return considerations
    
    async def store_user_story_in_conport(self, story: UserStory):
        """Store user story in ConPort for tracking"""
        
        conport_entry = {
            "agent": "conport_agent", 
            "operation": "log_progress",
            "parameters": {
                "description": f"User Story: {story.title}",
                "status": story.status,
                "context": f"Complexity: {story.complexity_estimate.value}, Agents: {', '.join(story.required_agents)}"
            }
        }
        
        await self.execute_agent_query(conport_entry)
        logger.info(f"Stored user story {story.id} in ConPort")

# Integration with main platform
async def handle_architecture_request(request: Dict[str, Any], 
                                    agent_registry: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for architecture, design, and story requests"""
    
    orchestrator = ArchitectureOrchestrator(agent_registry)
    return await orchestrator.analyze_architectural_request(request)

if __name__ == "__main__":
    # Test the orchestrator
    test_request = {
        "type": "architectural_decision",
        "title": "API Authentication Strategy",
        "description": "Decide on authentication approach for REST API",
        "context": "Building user authentication system for web application"
    }
    
    agent_registry = {
        "context7_agent": {"status": "active"},
        "serena_agent": {"status": "active"},
        "zen_reviewer": {"status": "active"}
    }
    
    result = asyncio.run(handle_architecture_request(test_request, agent_registry))
    print(json.dumps(result, indent=2, default=str))