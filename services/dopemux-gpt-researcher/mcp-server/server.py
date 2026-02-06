#!/usr/bin/env python3
"""
GPT-Researcher MCP Server
Provides research capabilities through MCP protocol for Dopemux integration
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Add the research_api directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'research_api'))

from models.research_task import ResearchType, ADHDConfiguration, ProjectContext
from services.orchestrator import ResearchTaskOrchestrator
from engines.search.search_orchestrator import SearchStrategy

# MCP Token Budget Constants
MCP_MAX_TOKENS = 10000
SAFE_TOKEN_BUDGET = 9000  # 10% headroom for safety

def estimate_tokens(text: str) -> int:
    """
    Conservative token estimation: 1 token ≈ 4 chars.
    Used to enforce MCP 10K token hard limit.
    """
    if text is None:
        return 0
    return len(str(text)) // 4

def enforce_token_budget(result: Dict[str, Any], tool_name: str, max_tokens: int = SAFE_TOKEN_BUDGET) -> Dict[str, Any]:
    """
    Enforce MCP token budget on research results.

    Truncates result fields to fit within 9K token budget (90% of 10K hard limit).
    Preserves most important information (task_id, status, summary) while
    truncating verbose fields (results, sources, key_findings).

    Args:
        result: Research tool result dictionary
        tool_name: Name of the tool that generated this result
        max_tokens: Maximum tokens allowed (default 9000)

    Returns:
        Truncated result dictionary with token budget metadata
    """
    try:
        # Clean result of None values that could cause JSON serialization issues
        def clean_for_json(obj):
            if obj is None:
                return "None"
            elif isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            else:
                return str(obj)

        # Clean the result
        clean_result = clean_for_json(result)

        # Estimate current token usage
        result_json = json.dumps(clean_result, indent=2)
        current_tokens = estimate_tokens(result_json)
    except Exception as e:
        logger.error(f"Error in token budget enforcement: {e}")
        # Return a safe minimal response
        return {
            'error': f'Token budget enforcement failed: {str(e)}',
            'tool_name': tool_name,
            '_token_budget_failed': True
        }

    # If under budget, return as-is
    if current_tokens <= max_tokens:
        logger.info(f"Tool {tool_name}: {current_tokens} tokens (under budget)")
        return result

    logger.warning(f"Tool {tool_name}: {current_tokens} tokens (over {max_tokens} budget) - truncating")

    # Create truncated copy
    truncated = result.copy()

    # Progressive truncation strategy for research results
    overhead_tokens = 500  # Reserve for structure
    available_tokens = max_tokens - overhead_tokens

    # Truncate verbose fields
    if 'results' in truncated and isinstance(truncated['results'], list):
        # Truncate individual result answers
        for r in truncated['results']:
            if 'answer' in r:
                r['answer'] = r['answer'][:1000] + "... [truncated]" if len(r['answer']) > 1000 else r['answer']

        # Limit number of results
        max_results = 5
        if len(truncated['results']) > max_results:
            truncated['results'] = truncated['results'][:max_results]
            truncated['results_truncated'] = True
            truncated['original_result_count'] = len(result.get('results', []))

    if 'sources' in truncated and isinstance(truncated['sources'], list):
        # Limit number of sources
        max_sources = 10
        if len(truncated['sources']) > max_sources:
            truncated['sources'] = truncated['sources'][:max_sources]
            truncated['sources_truncated'] = True

    if 'summary' in truncated and isinstance(truncated['summary'], str):
        # Truncate summary
        max_summary_chars = 2000
        if len(truncated['summary']) > max_summary_chars:
            truncated['summary'] = truncated['summary'][:max_summary_chars] + "\n\n... [truncated to fit MCP 10K token budget]"

    if 'key_findings' in truncated and isinstance(truncated['key_findings'], list):
        # Limit key findings
        max_findings = 5
        if len(truncated['key_findings']) > max_findings:
            truncated['key_findings'] = truncated['key_findings'][:max_findings]

    # Add metadata
    truncated['_token_budget_enforced'] = True
    truncated['_original_tokens'] = current_tokens
    truncated['_truncated_tokens'] = estimate_tokens(json.dumps(truncated))

    logger.info(f"Tool {tool_name}: Truncated from {current_tokens} to {truncated['_truncated_tokens']} tokens")

    return truncated


class MCPServer:
    """MCP Server implementation for GPT-Researcher"""

    def __init__(self):
        self.request_id_counter = 0
        self.orchestrator = None
        self.active_tasks = {}

    async def initialize(self):
        """Initialize the server and research orchestrator"""
        try:
            # Get API keys from environment
            api_keys = {
                'exa_api_key': os.getenv('EXA_API_KEY'),
                'tavily_api_key': os.getenv('TAVILY_API_KEY'),
                'perplexity_api_key': os.getenv('PERPLEXITY_API_KEY'),
            }

            # Initialize project context
            project_context = ProjectContext(
                workspace_path=os.getenv('WORKSPACE_PATH', '/Users/hue/code/dopemux-mvp'),
                tech_stack=['Python', 'TypeScript', 'React'],
                architecture_patterns=['MCP', 'microservices', 'event-driven']
            )

            # Initialize orchestrator
            self.orchestrator = ResearchTaskOrchestrator(
                project_context=project_context,
                search_api_keys=api_keys
            )

            logger.info("GPT-Researcher MCP Server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')

        try:
            if method == 'initialize':
                return await self._handle_initialize(request_id, params)
            elif method == 'tools/list':
                return await self._handle_list_tools(request_id)
            elif method == 'tools/call':
                return await self._handle_tool_call(request_id, params)
            elif method == 'resources/list':
                return await self._handle_list_resources(request_id)
            elif method == 'resources/read':
                return await self._handle_read_resource(request_id, params)
            else:
                return self._create_error_response(
                    request_id, -32601, f"Method not found: {method}"
                )
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._create_error_response(
                request_id, -32603, f"Internal error: {str(e)}"
            )

    async def _handle_initialize(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'protocolVersion': '0.1.0',
                'capabilities': {
                    'tools': {},
                    'resources': {
                        'subscribe': False,
                        'list': True,
                        'read': True
                    }
                },
                'serverInfo': {
                    'name': 'gpt-researcher-mcp',
                    'version': '0.1.0'
                }
            }
        }

    async def _handle_list_tools(self, request_id: Any) -> Dict[str, Any]:
        """List available research tools"""
        tools = [
            {
                'name': 'quick_search',
                'description': 'Quick search for immediate answers (ADHD-optimized)',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'query': {'type': 'string', 'description': 'Search query'},
                        'max_results': {'type': 'number', 'default': 5}
                    },
                    'required': ['query']
                }
            },
            {
                'name': 'deep_research',
                'description': 'Comprehensive research with multiple sources',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'query': {'type': 'string', 'description': 'Research query'},
                        'research_type': {
                            'type': 'string',
                            'enum': ['general', 'technical', 'academic'],
                            'default': 'general'
                        },
                        'max_time_minutes': {'type': 'number', 'default': 25}
                    },
                    'required': ['query']
                }
            },
            {
                'name': 'documentation_search',
                'description': 'Search technical documentation and APIs',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'technology': {'type': 'string', 'description': 'Technology/framework name'},
                        'query': {'type': 'string', 'description': 'Specific query'},
                        'version': {'type': 'string', 'description': 'Version (optional)'}
                    },
                    'required': ['technology', 'query']
                }
            },
            {
                'name': 'code_examples',
                'description': 'Find code examples and implementations',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'language': {'type': 'string', 'description': 'Programming language'},
                        'concept': {'type': 'string', 'description': 'Concept or pattern'},
                        'framework': {'type': 'string', 'description': 'Framework (optional)'}
                    },
                    'required': ['language', 'concept']
                }
            },
            {
                'name': 'trend_analysis',
                'description': 'Analyze trends and recent developments',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'domain': {'type': 'string', 'description': 'Domain/field'},
                        'timeframe': {
                            'type': 'string',
                            'enum': ['day', 'week', 'month', 'year'],
                            'default': 'month'
                        }
                    },
                    'required': ['domain']
                }
            },
            {
                'name': 'summarize_research',
                'description': 'Summarize previous research results (ADHD-friendly)',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'task_id': {'type': 'string', 'description': 'Research task ID'},
                        'format': {
                            'type': 'string',
                            'enum': ['brief', 'detailed', 'bullets'],
                            'default': 'brief'
                        }
                    },
                    'required': ['task_id']
                }
            }
        ]

        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'tools': tools
            }
        }

    async def _handle_tool_call(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a research tool"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        try:
            if tool_name == 'quick_search':
                result = await self._quick_search(arguments)
            elif tool_name == 'deep_research':
                result = await self._deep_research(arguments)
            elif tool_name == 'documentation_search':
                result = await self._documentation_search(arguments)
            elif tool_name == 'code_examples':
                result = await self._code_examples(arguments)
            elif tool_name == 'trend_analysis':
                result = await self._trend_analysis(arguments)
            elif tool_name == 'summarize_research':
                result = await self._summarize_research(arguments)
            else:
                return self._create_error_response(
                    request_id, -32602, f"Unknown tool: {tool_name}"
                )

            # Enforce MCP token budget before returning (10K hard limit)
            result = enforce_token_budget(result, tool_name, max_tokens=SAFE_TOKEN_BUDGET)

            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps(result, indent=2)
                        }
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return self._create_error_response(
                request_id, -32603, f"Tool execution error: {str(e)}"
            )

    async def _execute_full_research_workflow(self, task) -> Dict[str, Any]:
        """Execute the complete research workflow from plan to completion"""
        try:
            # Validate task object
            if task is None:
                return {
                    'results': [],
                    'summary': 'Research workflow failed: Task object is None',
                    'key_findings': [],
                    'sources': [],
                    'error': 'Task object is None'
                }

            task_id = getattr(task, 'id', None)
            if task_id is None:
                return {
                    'results': [],
                    'summary': 'Research workflow failed: Task has no ID',
                    'key_findings': [],
                    'sources': [],
                    'error': 'Task has no ID attribute'
                }

            # Step 1: Generate research plan
            logger.info(f"Generating research plan for task {task_id}")
            research_plan = await self.orchestrator.generate_research_plan(task_id)

            if research_plan is None:
                return {
                    'results': [],
                    'summary': 'Research workflow failed: Unable to generate research plan',
                    'key_findings': [],
                    'sources': [],
                    'error': 'Research plan generation failed'
                }

            logger.info(f"Research plan generated with {len(research_plan)} questions")

            # Step 2: Execute each research step
            all_results = []
            for i in range(len(research_plan)):
                logger.info(f"Executing research step {i+1}/{len(research_plan)}")
                result = await self.orchestrator.execute_research_step(task_id, i)
                if result:
                    all_results.append({
                        'question': research_plan[i].question,
                        'answer': getattr(result, 'answer', 'No answer available'),
                        'confidence': getattr(result, 'confidence', 0.0),
                        'sources': [getattr(s, 'url', str(s)) for s in getattr(result, 'sources', [])]
                    })

            # Step 3: Complete research
            logger.info(f"Completing research for task {task_id}")
            completed_task = await self.orchestrator.complete_research(task_id)

            # Step 4: Format results
            summary = "\n\n".join([
                f"**{r['question']}**\n{r['answer']}"
                for r in all_results
            ]) if all_results else "No results found"

            return {
                'results': all_results,
                'summary': summary,
                'key_findings': [r['answer'][:200] + "..." if len(r['answer']) > 200 else r['answer'] for r in all_results],
                'sources': [src for r in all_results for src in r['sources']],
                'total_questions': len(research_plan),
                'confidence': sum(r['confidence'] for r in all_results) / len(all_results) if all_results else 0.0
            }

        except Exception as e:
            logger.error(f"Error in research workflow: {e}")
            import traceback
            traceback.print_exc()
            return {
                'results': [],
                'summary': f'Research workflow failed: {str(e)}',
                'key_findings': [],
                'sources': [],
                'error': str(e)
            }

    async def _quick_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a quick search"""
        query = args['query']
        max_results = args.get('max_results', 5)

        if not self.orchestrator:
            return {'error': 'Orchestrator not initialized'}

        try:
            # Create a quick search task with correct API
            task = await self.orchestrator.create_research_task(
                user_id='mcp-user',
                prompt=query,
                research_type=ResearchType.DOCUMENTATION_RESEARCH,
                adhd_config=ADHDConfiguration(
                    pomodoro_enabled=True,
                    work_duration_minutes=10,
                    break_duration_minutes=5,
                    max_concurrent_sources=3
                ),
                user_context={'source': 'mcp', 'quick_search': True}
            )
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Failed to create research task: {str(e)}'}

        # Execute search workflow with auto-retry
        max_retries = 2  # Fewer retries for quick search
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Executing quick search (attempt {attempt + 1}/{max_retries})")
                results = await self._execute_full_research_workflow(task)

                # Limit results for quick search
                limited_results = results.get('results', [])[:max_results]

                return {
                    'query': query,
                    'task_id': str(task.id),
                    'results': limited_results,
                    'summary': results.get('summary', 'No summary available'),
                    'status': 'completed' if not results.get('error') else 'failed',
                    'attempts_used': attempt + 1
                }
            except Exception as e:
                logger.warning(f"Quick search attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    logger.info(f"Retrying quick search in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5  # Gentle backoff for quick searches
                else:
                    logger.error(f"All {max_retries} quick search attempts failed. Final error: {e}")
                    import traceback
                    traceback.print_exc()
                    return {
                        'error': f'Failed to execute quick search after {max_retries} attempts: {str(e)}',
                        'attempts_used': max_retries
                    }


    async def _deep_research(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep research on a topic"""
        query = args.get('query')
        if not query:
            return {'error': 'Query parameter is required for deep research'}

        topic = query  # Use query as topic for backward compatibility
        research_type = args.get('research_type', 'general')
        max_time = args.get('max_time_minutes', 25)

        try:
            # Validate orchestrator
            if not self.orchestrator:
                return {'error': 'Research orchestrator not initialized'}

            # Map research type to backend ResearchType enum
            type_map = {
                'general': ResearchType.FEATURE_RESEARCH,
                'technical': ResearchType.TECHNOLOGY_EVALUATION,
                'academic': ResearchType.DOCUMENTATION_RESEARCH
            }

            # Create research task with correct API
            logger.info(f"Creating deep research task for query: {query[:50]}...")
            task = await self.orchestrator.create_research_task(
                user_id='mcp-user',
                prompt=topic,
                research_type=type_map.get(research_type, ResearchType.FEATURE_RESEARCH),
                adhd_config=ADHDConfiguration(
                    pomodoro_enabled=True,
                    work_duration_minutes=max_time,
                    break_duration_minutes=5,
                    max_concurrent_sources=5
                ),
                user_context={'source': 'mcp', 'deep_research': True}
            )

            # Validate task creation
            if task is None:
                return {'error': 'Research task creation returned None'}

            logger.info(f"Successfully created research task: {getattr(task, 'id', 'no-id')}")

        except Exception as e:
            logger.error(f"Error creating deep research task: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Failed to create research task: {str(e)}'}

        # Store active task
        task_id_str = str(getattr(task, 'id', 'unknown'))
        self.active_tasks[task_id_str] = task

        # Execute research workflow with auto-retry
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Executing deep research (attempt {attempt + 1}/{max_retries})")
                results = await self._execute_full_research_workflow(task)

                return {
                    'query': query,
                    'task_id': str(task.id),
                    'research_type': research_type,
                    'results': results.get('results', []),
                    'summary': results.get('summary', ''),
                    'key_findings': results.get('key_findings', []),
                    'sources': results.get('sources', []),
                    'total_questions': results.get('total_questions', 0),
                    'confidence': results.get('confidence', 0.0),
                    'status': 'completed' if not results.get('error') else 'failed',
                    'attempts_used': attempt + 1
                }
            except Exception as e:
                logger.warning(f"Deep research attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All {max_retries} attempts failed. Final error: {e}")
                    import traceback
                    traceback.print_exc()
                    return {
                        'error': f'Failed to execute research task after {max_retries} attempts: {str(e)}',
                        'attempts_used': max_retries
                    }


    async def _documentation_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search technical documentation"""
        technology = args['technology']
        query = args['query']
        version = args.get('version', '')

        search_query = f"{technology} {query}"
        if version:
            search_query += f" version {version}"

        # Use documentation-focused search
        return await self._quick_search({
            'query': f"documentation {search_query}",
            'max_results': 10
        })

    async def _code_examples(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find code examples"""
        language = args['language']
        concept = args['concept']
        framework = args.get('framework', '')

        search_query = f"{language} {concept} code example"
        if framework:
            search_query += f" {framework}"

        # Search for code examples
        return await self._quick_search({
            'query': search_query,
            'max_results': 10
        })

    async def _trend_analysis(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends in a domain"""
        domain = args['domain']
        timeframe = args.get('timeframe', 'month')

        # Create trend analysis query
        timeframe_map = {
            'day': 'today',
            'week': 'this week',
            'month': 'this month',
            'year': 'this year'
        }

        search_query = f"{domain} trends {timeframe_map.get(timeframe, 'recent')}"

        return await self._quick_search({
            'query': search_query,
            'max_results': 15
        })

    async def _summarize_research(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize previous research"""
        task_id = args['task_id']
        format_type = args.get('format', 'brief')

        # Get task from active tasks
        task = self.active_tasks.get(task_id)
        if not task:
            return {'error': f'Task {task_id} not found'}

        # Get task results
        if not self.orchestrator:
            return {'error': 'Orchestrator not initialized'}

        status = await self.orchestrator.get_task_status(task_id)

        # Format based on type
        if format_type == 'bullets':
            summary = {
                'task_id': task_id,
                'status': status['status'],
                'key_points': status.get('key_findings', []),
                'sources': len(status.get('sources', [])),
                'completion': status.get('progress', 0)
            }
        elif format_type == 'detailed':
            summary = status
        else:  # brief
            summary = {
                'task_id': task_id,
                'status': status['status'],
                'summary': status.get('summary', 'No summary available'),
                'completion': status.get('progress', 0)
            }

        return summary

    async def _handle_list_resources(self, request_id: Any) -> Dict[str, Any]:
        """List available resources"""
        resources = [
            {
                'uri': 'research://active-tasks',
                'name': 'Active Research Tasks',
                'description': 'List of currently active research tasks',
                'mimeType': 'application/json'
            },
            {
                'uri': 'research://history',
                'name': 'Research History',
                'description': 'Previous research results and summaries',
                'mimeType': 'application/json'
            }
        ]

        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'resources': resources
            }
        }

    async def _handle_read_resource(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a specific resource"""
        uri = params.get('uri')

        if uri == 'research://active-tasks':
            content = {
                'tasks': list(self.active_tasks.keys()),
                'count': len(self.active_tasks)
            }
        elif uri == 'research://history':
            content = {
                'history': [],  # Would load from persistence
                'message': 'History persistence not yet implemented'
            }
        else:
            return self._create_error_response(
                request_id, -32602, f"Unknown resource: {uri}"
            )

        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'contents': [
                    {
                        'uri': uri,
                        'mimeType': 'application/json',
                        'text': json.dumps(content, indent=2)
                    }
                ]
            }
        }

    def _create_error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': code,
                'message': message
            }
        }

    async def run_stdio(self):
        """Run the server in stdio mode"""
        logger.info("Starting GPT-Researcher MCP Server in stdio mode")

        # Initialize the server
        await self.initialize()

        # Read from stdin and write to stdout
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                # Read line from stdin
                line = await reader.readline()
                if not line:
                    break

                # Parse JSON-RPC request
                try:
                    request = json.loads(line.decode())
                    logger.debug(f"Received request: {request}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue

                # Handle the request
                response = await self.handle_request(request)

                # Send response
                response_str = json.dumps(response) + '\n'
                sys.stdout.write(response_str)
                sys.stdout.flush()
                logger.debug(f"Sent response: {response}")

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                continue


async def main():
    """Main entry point"""
    server = MCPServer()
    await server.run_stdio()


if __name__ == '__main__':
    # Run the server
    asyncio.run(main())
