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

# Add the backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models.research_task import ResearchType, ADHDConfiguration, ProjectContext
from services.orchestrator import ResearchTaskOrchestrator
from engines.search.search_orchestrator import SearchStrategy


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
                'context7_api_key': os.getenv('CONTEXT7_API_KEY'),
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
                        'topic': {'type': 'string', 'description': 'Research topic'},
                        'research_type': {
                            'type': 'string',
                            'enum': ['general', 'technical', 'academic'],
                            'default': 'general'
                        },
                        'max_time_minutes': {'type': 'number', 'default': 25}
                    },
                    'required': ['topic']
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
            # Step 1: Generate research plan
            logger.info(f"Generating research plan for task {task.id}")
            research_plan = await self.orchestrator.generate_research_plan(task.id)
            logger.info(f"Research plan generated with {len(research_plan)} questions")

            # Step 2: Execute each research step
            all_results = []
            for i in range(len(research_plan)):
                logger.info(f"Executing research step {i+1}/{len(research_plan)}")
                result = await self.orchestrator.execute_research_step(task.id, i)
                if result:
                    all_results.append({
                        'question': research_plan[i].question,
                        'answer': result.answer,
                        'confidence': result.confidence,
                        'sources': [s.url if hasattr(s, 'url') else str(s) for s in result.sources]
                    })

            # Step 3: Complete research
            logger.info(f"Completing research for task {task.id}")
            completed_task = await self.orchestrator.complete_research(task.id)

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

        # Execute search workflow
        try:
            results = await self._execute_full_research_workflow(task)

            # Limit results for quick search
            limited_results = results.get('results', [])[:max_results]

            return {
                'query': query,
                'task_id': str(task.id),
                'results': limited_results,
                'summary': results.get('summary', 'No summary available'),
                'status': 'completed' if not results.get('error') else 'failed'
            }
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Failed to execute research task: {str(e)}'}


    async def _deep_research(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep research on a topic"""
        topic = args['topic']
        research_type = args.get('research_type', 'general')
        max_time = args.get('max_time_minutes', 25)

        if not self.orchestrator:
            return {'error': 'Orchestrator not initialized'}

        try:
            # Map research type to backend ResearchType enum
            type_map = {
                'general': ResearchType.FEATURE_RESEARCH,
                'technical': ResearchType.TECHNOLOGY_EVALUATION,
                'academic': ResearchType.DOCUMENTATION_RESEARCH
            }

            # Create research task with correct API
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
        except Exception as e:
            logger.error(f"Error creating deep research task: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Failed to create research task: {str(e)}'}

        # Store active task
        self.active_tasks[str(task.id)] = task

        # Execute research workflow
        try:
            results = await self._execute_full_research_workflow(task)

            return {
                'topic': topic,
                'task_id': str(task.id),
                'research_type': research_type,
                'results': results.get('results', []),
                'summary': results.get('summary', ''),
                'key_findings': results.get('key_findings', []),
                'sources': results.get('sources', []),
                'total_questions': results.get('total_questions', 0),
                'confidence': results.get('confidence', 0.0),
                'status': 'completed' if not results.get('error') else 'failed'
            }
        except Exception as e:
            logger.error(f"Error executing deep research: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Failed to execute research task: {str(e)}'}


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