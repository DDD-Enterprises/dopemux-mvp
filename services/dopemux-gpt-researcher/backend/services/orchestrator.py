"""
Research Task Orchestrator - ADHD-optimized wrapper for GPT Researcher

This module implements the proxy pattern that transforms the monolithic GPT Researcher
into a transparent, interruptible, ADHD-friendly research system.

Key features:
- Decouples Planner from Executor for step-by-step transparency
- Enables pause/resume with full context preservation
- Provides real-time progress updates via WebSocket
- Integrates with ConPort for persistent memory
- Implements Pomodoro timing for ADHD focus management
"""

import asyncio
import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from models.research_task import (
    ADHDConfiguration,
    ProjectContext,
    ResearchQuestion,
    ResearchResult,
    ResearchTask,
    ResearchType,
    TaskStatus
)
from engines.query_classifier import (
    QueryClassificationEngine,
    QueryIntent,
    ResearchScope,
    OutputFormat,
    SearchEngineStrategy
)
from engines.search.search_orchestrator import SearchOrchestrator, SearchStrategy
from engines.search.exa_adapter import ExaSearchAdapter
from engines.search.tavily_adapter import TavilySearchAdapter
from engines.search.perplexity_adapter import PerplexitySearchAdapter
from engines.search.context7_adapter import Context7SearchAdapter

# Discrete integrations for ADHD-friendly research enhancement
try:
    from ..adapters.context7_helper import discrete_enhance_research, analyze_for_documentation_hints
except ImportError:
    # Ultra-discrete fallback
    async def discrete_enhance_research(query, results): return results
    async def analyze_for_documentation_hints(query): return []

# Note: In production, these would import from the actual gpt-researcher
# For now, we'll create interface stubs that match the expected API
try:
    from gpt_researcher import GPTResearcher
    from gpt_researcher.planner import ResearchPlanner
    from gpt_researcher.agent import ResearchAgent
except ImportError:
    # Fallback stubs for development
    class GPTResearcher:
        async def conduct_research(self): pass
    class ResearchPlanner:
        async def plan(self): pass
    class ResearchAgent:
        async def research(self): pass


logger = logging.getLogger(__name__)


class ResearchTaskOrchestrator:
    """
    Orchestrates enhanced research with ADHD optimizations

    This class wraps the original GPT Researcher functionality and adds:
    - Transparent planning phase with user review
    - Step-by-step execution with progress visibility
    - Pause/resume capability for context switching
    - Automatic state persistence
    - Pomodoro timing integration
    """

    def __init__(self,
                 conport_adapter=None,
                 websocket_streamer=None,
                 project_context: Optional[ProjectContext] = None,
                 search_api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize the orchestrator with dependencies

        Args:
            conport_adapter: Adapter for ConPort integration
            websocket_streamer: WebSocket handler for progress updates
            project_context: Project-specific context
            search_api_keys: Dictionary of API keys for search engines
        """
        self.conport = conport_adapter
        self.websocket = websocket_streamer
        self.project_context = project_context

        # Original GPT Researcher components
        self.gpt_researcher = GPTResearcher()
        self.planner = ResearchPlanner()
        self.agent = ResearchAgent()

        # Enhanced engines (Layer 1 Multi-Tool Orchestration)
        self.query_classifier = QueryClassificationEngine()

        # Initialize Search Orchestrator with all engines
        self.search_orchestrator = self._initialize_search_orchestrator(search_api_keys or {})

        # State management
        self.active_tasks: Dict[UUID, ResearchTask] = {}
        self.auto_save_tasks = {}  # Track auto-save coroutines

    def _initialize_search_orchestrator(self, api_keys: Dict[str, str]) -> SearchOrchestrator:
        """
        Initialize SearchOrchestrator with all available search engines

        Args:
            api_keys: Dictionary of API keys for different search engines

        Returns:
            Configured SearchOrchestrator instance
        """
        engines = {}

        # Initialize each search engine adapter if API key is available
        if api_keys.get('exa_api_key'):
            try:
                engines['exa'] = ExaSearchAdapter(api_keys['exa_api_key'])
                logger.info("Initialized Exa search adapter")
            except Exception as e:
                logger.warning(f"Failed to initialize Exa adapter: {e}")

        if api_keys.get('tavily_api_key'):
            try:
                engines['tavily'] = TavilySearchAdapter(api_keys['tavily_api_key'])
                logger.info("Initialized Tavily search adapter")
            except Exception as e:
                logger.warning(f"Failed to initialize Tavily adapter: {e}")

        if api_keys.get('perplexity_api_key'):
            try:
                engines['perplexity'] = PerplexitySearchAdapter(api_keys['perplexity_api_key'])
                logger.info("Initialized Perplexity search adapter")
            except Exception as e:
                logger.warning(f"Failed to initialize Perplexity adapter: {e}")

        # Context7 doesn't require API key, uses MCP integration
        try:
            engines['context7'] = Context7SearchAdapter()
            logger.info("Initialized Context7 search adapter")
        except Exception as e:
            logger.warning(f"Failed to initialize Context7 adapter: {e}")

        if not engines:
            logger.warning("No search engines available, creating minimal orchestrator")
            # Create a mock engine for development
            from engines.search.base_adapter import BaseSearchAdapter, SearchMetadata
            class MockAdapter(BaseSearchAdapter):
                def __init__(self):
                    super().__init__("mock_key")
                    self.engine_name = "mock"
                async def search(self, query, **kwargs):
                    return [], SearchMetadata(
                        engine_name="mock",
                        query_time_ms=0,
                        total_results=0,
                        results_returned=0
                    )
            engines['mock'] = MockAdapter()

        # Initialize orchestrator with ADHD optimizations enabled
        orchestrator = SearchOrchestrator(
            engines=engines,
            strategy=SearchStrategy.COMPREHENSIVE,
            adhd_mode=True,
            enable_parallel=True,
            deduplicate_results=True
        )

        logger.info(f"SearchOrchestrator initialized with {len(engines)} engines: {list(engines.keys())}")
        return orchestrator

    async def create_research_task(self,
                                   user_id: str,
                                   prompt: str,
                                   research_type: Optional[ResearchType] = None,
                                   adhd_config: Optional[ADHDConfiguration] = None,
                                   user_context: Optional[Dict] = None) -> ResearchTask:
        """
        Create a new research task with intelligent classification and ADHD optimizations

        Args:
            user_id: User identifier
            prompt: Research query
            research_type: Type of research (auto-detected if not specified)
            adhd_config: ADHD-specific configuration (auto-optimized if not specified)
            user_context: User preferences and history

        Returns:
            Initialized ResearchTask with intelligent configuration
        """
        # Step 1: Classify the query for intelligent configuration
        classification = await self.query_classifier.classify_query(
            query=prompt,
            user_context=user_context,
            project_context=self.project_context.model_dump() if self.project_context else None
        )

        logger.info(f"Query classified: {classification.intent.value} (confidence: {classification.confidence:.2f})")

        # Step 2: Use classification results or provided overrides
        final_research_type = research_type or classification.research_type
        final_adhd_config = adhd_config or classification.adhd_config

        # Step 3: Create task with enhanced configuration
        task = ResearchTask(
            user_id=user_id,
            initial_prompt=prompt,
            research_type=final_research_type,
            adhd_config=final_adhd_config,
            project_context=self.project_context
        )

        # Step 4: Store classification metadata for orchestration
        task.metadata = {
            'classification': asdict(classification),
            'estimated_duration_minutes': classification.estimated_duration_minutes,
            'search_strategy': classification.search_strategy.value,
            'output_format': classification.output_format.value,
            'required_tools': classification.required_tools,
            'optional_tools': classification.optional_tools
        }

        self.active_tasks[task.id] = task

        # Step 5: Discrete ConPort integration (ADHD memory support)
        if self.conport:
            try:
                # Discretely log research task initiation
                await self.conport.save_task_state(task)
            except Exception:
                pass  # Fail silently - research continues

        # Step 6: Discrete Context7 documentation hints (ADHD cognitive support)
        try:
            doc_hints = await analyze_for_documentation_hints(prompt)
            if doc_hints:
                # Discretely enhance task metadata with documentation context
                task.metadata['documentation_hints'] = [
                    {'library': h.library, 'topic': h.topic, 'confidence': h.confidence}
                    for h in doc_hints[:2]  # Limit to prevent overwhelm
                ]
        except Exception:
            pass  # Ultra-discrete - any failure is invisible

        # Step 7: Emit classification results via WebSocket
        if self.websocket:
            await self.websocket.emit_progress(task.id, {
                "phase": "task_created",
                "classification": {
                    "intent": classification.intent.value,
                    "scope": classification.scope.value,
                    "complexity": classification.complexity_score,
                    "estimated_duration": classification.estimated_duration_minutes,
                    "confidence": classification.confidence,
                    "reasoning": classification.reasoning
                },
                "adhd_optimizations": {
                    "work_duration": final_adhd_config.work_duration_minutes,
                    "max_sources": final_adhd_config.max_concurrent_sources,
                    "progressive_disclosure": final_adhd_config.progressive_disclosure
                }
            })

        # Step 6: Start auto-save for this task
        if self.conport:
            self.auto_save_tasks[task.id] = asyncio.create_task(
                self._auto_save_loop(task)
            )

        logger.info(f"Created research task {task.id} for user {user_id} ({classification.intent.value}, {classification.scope.value})")
        return task

    async def generate_research_plan(self, task_id: UUID) -> List[ResearchQuestion]:
        """
        Generate research plan using original Planner

        This is Phase 1 of the ADHD workflow - transparent planning
        """
        task = self._get_task(task_id)
        task.transition_to(TaskStatus.PLANNING)

        try:
            # Use original planner with enhanced prompt
            enhanced_prompt = await self._enhance_prompt(task)

            # This would call the actual GPT Researcher planner
            # plan_result = await self.planner.plan(enhanced_prompt)

            # For now, create a mock plan structure
            plan_result = await self._mock_planning(enhanced_prompt, task.research_type)

            # Convert to our ResearchQuestion format
            questions = []
            for i, question_text in enumerate(plan_result.get('questions', [])):
                question = ResearchQuestion(
                    question=question_text,
                    priority=i + 1,
                    estimated_duration_minutes=plan_result.get('estimated_minutes', 5)
                )
                questions.append(question)

            task.research_plan = questions
            task.enhanced_prompt = enhanced_prompt

            # Emit progress update
            if self.websocket:
                await self.websocket.emit_progress(task_id, {
                    "phase": "planning_complete",
                    "plan": [q.model_dump() for q in questions],
                    "total_questions": len(questions),
                    "estimated_duration": sum(q.estimated_duration_minutes for q in questions)
                })

            logger.info(f"Generated plan with {len(questions)} questions for task {task_id}")
            return questions

        except Exception as e:
            logger.error(f"Planning failed for task {task_id}: {e}")
            task.transition_to(TaskStatus.FAILED)
            raise

    async def execute_research_step(self, task_id: UUID, question_index: int) -> ResearchResult:
        """
        Execute a single research question

        This enables step-by-step transparency and pause points
        """
        task = self._get_task(task_id)

        if question_index >= len(task.research_plan):
            raise ValueError(f"Question index {question_index} out of range")

        question = task.research_plan[question_index]
        task.current_question_index = question_index

        # Check for pause request
        if task.status == TaskStatus.PAUSED:
            logger.info(f"Task {task_id} is paused, creating checkpoint")
            task.create_checkpoint({"paused_at_question": question_index})
            return None

        task.transition_to(TaskStatus.EXECUTING)
        question.status = TaskStatus.EXECUTING

        try:
            start_time = time.time()

            # Emit progress update
            if self.websocket:
                await self.websocket.emit_progress(task_id, {
                    "phase": "executing_question",
                    "question_index": question_index,
                    "question": question.question,
                    "progress": task.calculate_progress()
                })

            # Execute research using SearchOrchestrator
            result_data = await self._execute_search_research(question, task)

            processing_time = time.time() - start_time

            # Create result object
            result = ResearchResult(
                question_id=question.id,
                answer=result_data.get('answer', ''),
                sources=result_data.get('sources', [])[:task.adhd_config.max_concurrent_sources],
                confidence=result_data.get('confidence', 0.8),
                search_engines_used=result_data.get('engines', ['mock']),
                processing_time_seconds=processing_time
            )

            # Update task state
            task.results[question.id] = result
            question.status = TaskStatus.COMPLETED
            question.sources_found = len(result.sources)
            question.confidence_score = result.confidence

            # Update overall task stats
            task.total_processing_time += processing_time
            task.sources_discovered += len(result.sources)

            # Emit completion update
            if self.websocket:
                await self.websocket.emit_progress(task_id, {
                    "phase": "question_complete",
                    "question_index": question_index,
                    "result": result.model_dump(),
                    "progress": task.calculate_progress()
                })

            logger.info(f"Completed question {question_index} for task {task_id}")
            return result

        except Exception as e:
            logger.error(f"Execution failed for question {question_index} in task {task_id}: {e}")
            question.status = TaskStatus.FAILED
            task.transition_to(TaskStatus.FAILED)
            raise

    async def pause_task(self, task_id: UUID, reason: str = "User requested") -> bool:
        """
        Pause a research task with state preservation

        Essential for ADHD context switching
        """
        task = self._get_task(task_id)

        if task.status != TaskStatus.EXECUTING:
            logger.warning(f"Cannot pause task {task_id} in status {task.status}")
            return False

        task.transition_to(TaskStatus.PAUSED)

        # Create checkpoint
        snapshot = task.create_checkpoint({
            "pause_reason": reason,
            "pause_timestamp": datetime.now().isoformat(),
            "current_progress": task.calculate_progress()
        })

        # Save to ConPort if available
        if self.conport:
            await self.conport.save_task_snapshot(task, snapshot)

        # Emit pause notification
        if self.websocket:
            await self.websocket.emit_progress(task_id, {
                "phase": "paused",
                "reason": reason,
                "snapshot_id": snapshot.id,
                "recovery_instructions": snapshot.recovery_instructions
            })

        logger.info(f"Paused task {task_id}: {reason}")
        return True

    async def resume_task(self, task_id: UUID) -> bool:
        """
        Resume a paused research task

        Restores full context for seamless continuation
        """
        task = self._get_task(task_id)

        if task.status != TaskStatus.PAUSED:
            logger.warning(f"Cannot resume task {task_id} in status {task.status}")
            return False

        # Get latest snapshot
        snapshot = task.get_latest_snapshot()
        if snapshot:
            task.current_question_index = snapshot.current_question_index

        task.transition_to(TaskStatus.EXECUTING)

        # Emit resume notification
        if self.websocket:
            await self.websocket.emit_progress(task_id, {
                "phase": "resumed",
                "current_question": task.current_question_index,
                "progress": task.calculate_progress()
            })

        logger.info(f"Resumed task {task_id}")
        return True

    async def complete_research(self, task_id: UUID) -> ResearchTask:
        """
        Mark research as complete and finalize results
        """
        task = self._get_task(task_id)
        task.transition_to(TaskStatus.COMPLETED)

        # Calculate final statistics
        total_sources = sum(len(result.sources) for result in task.results.values())
        avg_confidence = (
            sum(result.confidence for result in task.results.values()) / len(task.results)
            if task.results else 0.0
        )

        task.sources_discovered = total_sources
        task.confidence_score = avg_confidence

        # Save final state to ConPort
        if self.conport:
            await self.conport.save_final_results(task)

        # Stop auto-save
        if task_id in self.auto_save_tasks:
            self.auto_save_tasks[task_id].cancel()
            del self.auto_save_tasks[task_id]

        # Emit completion
        if self.websocket:
            await self.websocket.emit_progress(task_id, {
                "phase": "completed",
                "final_stats": {
                    "total_questions": len(task.research_plan),
                    "total_sources": total_sources,
                    "avg_confidence": avg_confidence,
                    "total_time_minutes": task.total_processing_time / 60
                }
            })

        logger.info(f"Completed research task {task_id}")
        return task

    # Private helper methods

    def _get_task(self, task_id: UUID) -> ResearchTask:
        """Get task by ID with error checking"""
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not found")
        return self.active_tasks[task_id]

    async def get_task_status(self, task_id: UUID) -> Dict[str, Any]:
        """Get comprehensive task status for API responses"""
        try:
            # Handle both string and UUID inputs
            if isinstance(task_id, str):
                task_id = UUID(task_id)
            task = self._get_task(task_id)
            progress_info = task.calculate_progress()

            # Extract key findings from results
            key_findings = []
            results_list = []

            for result in task.results.values():
                # Add to results list
                results_list.append({
                    'question': next((q.question for q in task.research_plan if q.id == result.question_id), 'Unknown'),
                    'answer': result.answer,
                    'confidence': result.confidence,
                    'sources_count': len(result.sources),
                    'timestamp': result.timestamp.isoformat()
                })

                # Extract key findings (first sentence of each answer)
                if result.answer:
                    first_sentence = result.answer.split('.')[0] + '.'
                    if len(first_sentence) > 10:  # Avoid very short fragments
                        key_findings.append(first_sentence)

            # Generate summary
            if results_list:
                summary = f"Research on '{task.initial_prompt}' - {len(results_list)} questions completed"
                if progress_info['progress_percentage'] == 100:
                    summary += f" with {task.confidence_score:.1f} confidence score"
            else:
                summary = f"Research task in progress: {task.status.value}"

            return {
                'status': task.status.value,
                'progress': int(progress_info['progress_percentage']),
                'results': results_list,
                'summary': summary,
                'key_findings': key_findings[:5],  # Limit to top 5 findings
                'meta': {
                    'total_questions': progress_info['total_questions'],
                    'completed_questions': progress_info['completed_questions'],
                    'current_question': progress_info['current_question'],
                    'estimated_remaining_minutes': progress_info['estimated_remaining_minutes'],
                    'elapsed_time_minutes': progress_info['elapsed_time_minutes'],
                    'sources_discovered': task.sources_discovered,
                    'confidence_score': task.confidence_score,
                    'break_suggested': task.should_suggest_break()
                }
            }

        except ValueError as e:
            # Task not found
            return {
                'status': 'not_found',
                'progress': 0,
                'results': [],
                'summary': str(e),
                'key_findings': [],
                'meta': {}
            }

    async def _enhance_prompt(self, task: ResearchTask) -> str:
        """Enhance the original prompt with context"""
        enhanced = task.initial_prompt

        # Add project context if available
        if task.project_context:
            enhanced += f"\n\nProject Context:\n"
            enhanced += f"Tech Stack: {', '.join(task.project_context.tech_stack)}\n"
            enhanced += f"Architecture: {', '.join(task.project_context.architecture_patterns)}\n"

        # Add research type specific enhancements
        if task.research_type == ResearchType.FEATURE_RESEARCH:
            enhanced += "\n\nFocus on: User stories, technical requirements, implementation approach"
        elif task.research_type == ResearchType.BUG_INVESTIGATION:
            enhanced += "\n\nFocus on: Root cause analysis, similar issues, recommended fixes"

        return enhanced

    async def _mock_planning(self, prompt: str, research_type: ResearchType) -> Dict[str, Any]:
        """Mock planning logic for development"""
        # This would be replaced with actual GPT Researcher planning
        base_questions = {
            ResearchType.FEATURE_RESEARCH: [
                "What are the core requirements for this feature?",
                "What are the technical implementation options?",
                "What are the potential risks and challenges?",
                "What are the success metrics and testing approaches?"
            ],
            ResearchType.BUG_INVESTIGATION: [
                "What are the symptoms and error patterns?",
                "What are similar issues and their solutions?",
                "What are the most likely root causes?",
                "What are the recommended fixes and prevention strategies?"
            ]
        }

        questions = base_questions.get(research_type, [
            "What is the current state of this topic?",
            "What are the best practices and approaches?",
            "What are the latest developments?",
            "What are the implementation recommendations?"
        ])

        return {
            "questions": questions,
            "estimated_minutes": 5
        }

    async def _execute_search_research(self, question: ResearchQuestion, task: ResearchTask) -> Dict[str, Any]:
        """
        Execute research using SearchOrchestrator with intelligent strategy selection

        Args:
            question: Research question to investigate
            task: Current research task with metadata and configuration

        Returns:
            Dictionary with answer, sources, confidence, and engines used
        """
        try:
            # Get search strategy from task classification
            classification_strategy = task.metadata.get('search_strategy', 'balanced_approach')

            # Map QueryClassificationEngine strategy to SearchOrchestrator strategy
            strategy_mapping = {
                'documentation_first': SearchStrategy.DOCUMENTATION_FIRST,
                'recent_developments': SearchStrategy.RECENT_DEVELOPMENTS,
                'technical_deep_dive': SearchStrategy.TECHNICAL_DEEP_DIVE,
                'balanced_approach': SearchStrategy.COMPREHENSIVE
            }

            search_strategy = strategy_mapping.get(classification_strategy, SearchStrategy.COMPREHENSIVE)

            # Execute orchestrated search
            search_results, search_metadata = await self.search_orchestrator.search(
                query=question.question,
                strategy=search_strategy,
                max_results=task.adhd_config.max_concurrent_sources * 2,  # Get extra for filtering
                adhd_mode=True
            )

            # Convert SearchResults to format expected by ResearchResult
            sources = []
            for result in search_results[:task.adhd_config.max_concurrent_sources]:
                source = {
                    "title": result.title,
                    "url": result.url,
                    "relevance": result.relevance_score,
                    "summary": result.summary,
                    "content": result.content[:500] if result.content else "",  # Truncate for ADHD
                    "source_quality": result.source_quality.value if result.source_quality else "good",
                    "reading_time_minutes": result.reading_time_minutes,
                    "complexity_level": result.complexity_level,
                    "key_points": result.key_points[:3] if result.key_points else []  # Limit for ADHD
                }
                sources.append(source)

            # Generate comprehensive answer from search results
            answer = self._synthesize_answer_from_sources(question.question, search_results)

            # Calculate overall confidence based on search quality
            confidence = self._calculate_research_confidence(search_results, search_metadata)

            # Get list of engines that actually returned results
            engines_used = list(search_metadata.engine_metadata.keys()) if search_metadata.engine_metadata else ["search_orchestrator"]

            logger.info(f"Research executed for '{question.question}': {len(sources)} sources from {len(engines_used)} engines")

            # Step 7: Discrete Context7 documentation enhancement
            enhanced_sources = sources
            try:
                from ..adapters.context7_helper import discrete_enhance_research
                enhanced_sources = await discrete_enhance_research(question.question, sources)
                if enhanced_sources != sources:
                    logger.debug(f"Context7 discretely enhanced results for '{question.question}'")
            except Exception:
                pass  # Ultra-discrete - any failure is invisible

            return {
                "answer": answer,
                "sources": enhanced_sources,
                "confidence": confidence,
                "engines": engines_used,
                "search_metadata": {
                    "strategy_used": search_strategy.value,
                    "total_query_time_ms": search_metadata.query_time_ms,
                    "total_results_found": search_metadata.total_results,
                    "engines_used": engines_used
                }
            }

        except Exception as e:
            logger.error(f"Search research failed for question '{question.question}': {e}")

            # Fallback to minimal response
            return {
                "answer": f"Research temporarily unavailable for: {question.question}. Error: {str(e)}",
                "sources": [],
                "confidence": 0.1,
                "engines": ["error_fallback"],
                "search_metadata": {"error": str(e)}
            }

    def _synthesize_answer_from_sources(self, question: str, search_results: List) -> str:
        """
        Synthesize a comprehensive answer from search results

        Args:
            question: Original research question
            search_results: List of SearchResult objects

        Returns:
            Synthesized answer string
        """
        if not search_results:
            return f"No reliable sources found for: {question}"

        # For now, create a structured summary
        # In production, this would use LLM synthesis

        answer_parts = [f"Research findings for: {question}\n"]

        # Add key insights from top sources
        for i, result in enumerate(search_results[:3], 1):
            if result.summary:
                answer_parts.append(f"{i}. {result.summary}")
            elif result.content:
                # Extract first meaningful sentence
                first_sentence = result.content.split('.')[0][:200]
                answer_parts.append(f"{i}. {first_sentence}...")

        # Add source count and quality note
        answer_parts.append(f"\nBased on {len(search_results)} sources with average quality rating.")

        return "\n".join(answer_parts)

    def _calculate_research_confidence(self, search_results: List, search_metadata) -> float:
        """
        Calculate confidence score based on search quality

        Args:
            search_results: List of SearchResult objects
            search_metadata: SearchMetadata object

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not search_results:
            return 0.1

        # Base confidence from result count
        result_count_score = min(1.0, len(search_results) / 5.0)  # Full confidence at 5+ results

        # Average relevance score
        avg_relevance = sum(r.relevance_score for r in search_results) / len(search_results)

        # Source quality bonus
        quality_scores = {
            "excellent": 1.0,
            "good": 0.8,
            "moderate": 0.6,
            "questionable": 0.3
        }

        avg_quality = sum(
            quality_scores.get(getattr(r, 'source_quality', 'good'), 0.6)
            for r in search_results
        ) / len(search_results)

        # Engine diversity bonus (more engines = higher confidence)
        engine_count = len(search_metadata.engine_metadata) if search_metadata.engine_metadata else 1
        engine_bonus = min(0.2, engine_count * 0.05)

        # Combine factors
        confidence = (result_count_score * 0.3 + avg_relevance * 0.4 + avg_quality * 0.3) + engine_bonus

        return min(0.95, max(0.1, confidence))

    async def _auto_save_loop(self, task: ResearchTask):
        """Auto-save task state every configured interval"""
        while task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            try:
                await asyncio.sleep(task.adhd_config.auto_save_interval_seconds)

                if self.conport and task.id in self.active_tasks:
                    await self.conport.save_task_state(task)
                    logger.debug(f"Auto-saved task {task.id}")

            except asyncio.CancelledError:
                logger.info(f"Auto-save cancelled for task {task.id}")
                break
            except Exception as e:
                logger.error(f"Auto-save failed for task {task.id}: {e}")
                await asyncio.sleep(10)  # Retry after delay