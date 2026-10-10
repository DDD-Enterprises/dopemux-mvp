# MCP Integration Patterns
**Model Context Protocol Implementation Guide for Dopemux**

## Executive Summary

This guide establishes implementation patterns for Dopemux's 12+ MCP (Model Context Protocol) servers, providing intelligent tool routing, fallback strategies, and optimization patterns. Based on research synthesis from research/findings/local-servers-config-gen.md and research/findings/local-servers-examples.md, these patterns ensure robust, efficient, and coordinated multi-tool operations achieving sub-100ms latencies and 99.5% uptime targets.

**Core Philosophy**: Context7-first development with intelligent delegation and graceful degradation.

---

## MCP Server Architecture

### Primary Server Stack

#### **Tier 1: Essential Servers (Always Available)**
```yaml
essential_servers:
  context7:
    priority: 1
    purpose: "Primary documentation source - CRITICAL for all code work"
    fallback: "exa web search"
    uptime_requirement: 99.9%

  zen:
    priority: 2
    purpose: "Multi-model AI orchestration and complex reasoning"
    fallback: "sequential-thinking"
    uptime_requirement: 99.5%

  serena:
    priority: 3
    purpose: "Semantic code operations and project memory"
    fallback: "native file operations"
    uptime_requirement: 99.0%
```

#### **Tier 2: Specialized Servers (Domain-Specific)**
```yaml
specialized_servers:
  sequential-thinking:
    purpose: "Complex reasoning and hypothesis testing"
    triggers: ["debug", "architectural_analysis", "multi_step_reasoning"]
    fallback: "zen chat with structured prompts"

  task-master-ai:
    purpose: "Task management and PRD processing"
    triggers: ["prd_parsing", "task_breakdown", "project_management"]
    fallback: "manual task management with TodoWrite"

  magic:
    purpose: "UI component generation from 21st.dev patterns"
    triggers: ["ui_component", "design_system", "frontend_generation"]
    fallback: "manual component development with context7 patterns"

  playwright:
    purpose: "Browser automation and E2E testing"
    triggers: ["e2e_testing", "visual_validation", "accessibility_testing"]
    fallback: "manual testing with documentation"
```

#### **Tier 3: Support Servers (Enhancement)**
```yaml
support_servers:
  morphllm-fast-apply:
    purpose: "Pattern-based bulk code transformations"
    triggers: ["bulk_edits", "style_enforcement", "pattern_application"]
    fallback: "individual file edits with MultiEdit"

  claude-context:
    purpose: "Semantic code search across repositories"
    triggers: ["codebase_search", "pattern_discovery", "dependency_analysis"]
    fallback: "grep and glob operations"

  conport:
    purpose: "Project memory and decision tracking"
    triggers: ["decision_logging", "progress_tracking", "knowledge_management"]
    fallback: "manual documentation"

  exa:
    purpose: "Web research and current information"
    triggers: ["web_research", "community_solutions", "current_trends"]
    fallback: "websearch tool"
```

---

## Integration Patterns

### 1. Context7-First Development Pattern

**Mandatory Sequence**: ALWAYS check Context7 before any code-related work.

```python
class Context7FirstPattern:
    async def implement_feature(self, feature_request: str, context: dict) -> dict:
        """Mandatory Context7-first implementation pattern"""

        # STEP 1: ALWAYS check Context7 first (NON-NEGOTIABLE)
        try:
            docs = await self.context7.get_documentation(feature_request)
            api_patterns = await self.context7.get_api_reference(feature_request)
            best_practices = await self.context7.get_implementation_guides(feature_request)

            if not docs and not api_patterns:
                # Only fall back to Exa if Context7 has NO information
                docs = await self.exa.search_documentation(feature_request)

        except Exception as e:
            # If Context7 is down, this is a critical failure
            return await self.handle_context7_failure(feature_request, e)

        # STEP 2: Validate documentation availability
        if not docs:
            raise DocumentationRequiredError(
                f"Cannot implement {feature_request} without documentation. "
                f"Context7 returned no patterns, Exa fallback failed."
            )

        # STEP 3: Route to implementation tools based on documentation
        implementation_plan = await self.plan_with_documentation(docs, context)

        # STEP 4: Execute with documentation context
        result = await self.execute_with_patterns(implementation_plan, docs)

        # STEP 5: Validate against documentation patterns
        validation = await self.validate_against_patterns(result, docs)

        return {
            'implementation': result,
            'documentation_source': docs.source,
            'patterns_used': docs.patterns,
            'validation_score': validation.score,
            'compliance': validation.compliance
        }

    async def handle_context7_failure(self, request: str, error: Exception) -> dict:
        """Critical failure handling when Context7 is unavailable"""

        # Log critical failure
        await self.log_critical_failure('context7', error)

        # Attempt emergency fallback
        emergency_docs = await self.exa.emergency_documentation_search(request)

        if not emergency_docs:
            return {
                'status': 'failed',
                'reason': 'no_documentation_available',
                'message': 'Cannot proceed with implementation without documentation',
                'suggested_action': 'Wait for Context7 recovery or find manual documentation'
            }

        # Proceed with degraded capability
        return await self.implement_with_degraded_docs(request, emergency_docs)
```

### 2. Multi-Server Coordination Pattern

**Intelligent Server Selection**: Route tasks to optimal servers based on complexity and requirements.

```python
class MCPCoordinationEngine:
    def __init__(self):
        self.server_capabilities = {
            'zen': ['reasoning', 'analysis', 'orchestration', 'consensus'],
            'sequential-thinking': ['debugging', 'hypothesis_testing', 'complex_analysis'],
            'serena': ['symbol_operations', 'refactoring', 'memory_management'],
            'magic': ['ui_components', 'design_systems', 'frontend'],
            'playwright': ['testing', 'automation', 'validation'],
            'task-master-ai': ['project_management', 'task_breakdown', 'prd_processing']
        }

    async def route_task(self, task: dict, context: dict) -> dict:
        """Intelligent task routing based on requirements and server capabilities"""

        # Analyze task requirements
        requirements = await self.analyze_task_requirements(task)

        # Select optimal servers
        primary_server = await self.select_primary_server(requirements)
        support_servers = await self.select_support_servers(requirements)

        # Coordinate execution
        if requirements.complexity == 'high':
            return await self.orchestrated_execution(task, primary_server, support_servers)
        else:
            return await self.direct_execution(task, primary_server)

    async def orchestrated_execution(self, task: dict, primary: str, support: List[str]) -> dict:
        """Multi-server coordination for complex tasks"""

        # Phase 1: Documentation and Planning (Context7 + Zen)
        docs = await self.context7.get_documentation(task['requirements'])
        plan = await self.zen.create_implementation_plan(task, docs)

        # Phase 2: Specialized Analysis
        analysis = {}
        if 'sequential-thinking' in support:
            analysis['reasoning'] = await self.sequential_thinking.analyze(task, plan)
        if 'serena' in support:
            analysis['code_structure'] = await self.serena.analyze_project_structure()
        if 'task-master-ai' in support:
            analysis['task_breakdown'] = await self.task_master_ai.break_down_tasks(plan)

        # Phase 3: Implementation with Primary Server
        implementation = await getattr(self, primary).implement(task, plan, analysis)

        # Phase 4: Validation and Testing
        if 'playwright' in support:
            validation = await self.playwright.validate_implementation(implementation)
        else:
            validation = await self.native_validation(implementation)

        return {
            'task': task,
            'plan': plan,
            'analysis': analysis,
            'implementation': implementation,
            'validation': validation,
            'servers_used': [primary] + support
        }
```

### 3. Graceful Degradation Pattern

**Fallback Strategies**: Maintain functionality when servers are unavailable.

```python
class FallbackStrategy:
    def __init__(self):
        self.fallback_chains = {
            'context7': ['exa', 'websearch', 'manual_documentation'],
            'zen': ['sequential-thinking', 'native_reasoning'],
            'serena': ['claude-context', 'native_search', 'manual_navigation'],
            'magic': ['context7_patterns', 'manual_component_development'],
            'playwright': ['manual_testing', 'unit_tests'],
            'sequential-thinking': ['zen_structured_prompts', 'native_analysis']
        }

    async def execute_with_fallback(self, server: str, operation: str, params: dict) -> dict:
        """Execute operation with automatic fallback handling"""

        try:
            # Attempt primary server
            result = await self.call_server(server, operation, params)
            return {
                'result': result,
                'server_used': server,
                'fallback_level': 0
            }

        except ServerUnavailableError:
            # Try fallback chain
            fallback_chain = self.fallback_chains.get(server, [])

            for i, fallback_server in enumerate(fallback_chain):
                try:
                    result = await self.call_fallback_server(fallback_server, operation, params)
                    return {
                        'result': result,
                        'server_used': fallback_server,
                        'fallback_level': i + 1,
                        'original_server': server
                    }
                except Exception as e:
                    await self.log_fallback_failure(fallback_server, e)
                    continue

            # All fallbacks failed
            raise AllServersUnavailableError(f"Primary ({server}) and all fallbacks failed")

    async def call_fallback_server(self, server: str, operation: str, params: dict) -> dict:
        """Call fallback server with adapted parameters"""

        if server == 'exa' and operation == 'get_documentation':
            # Adapt Context7 documentation request to Exa search
            return await self.exa.search_documentation(params['query'])

        elif server == 'websearch' and operation == 'get_documentation':
            # Final fallback to basic web search
            return await self.websearch.search(f"{params['query']} documentation")

        elif server == 'manual_testing' and operation == 'validate_ui':
            # Fallback to manual testing instructions
            return {
                'status': 'manual_testing_required',
                'instructions': await self.generate_manual_test_instructions(params),
                'checklist': await self.generate_test_checklist(params)
            }

        # Generic fallback handling
        return await getattr(self, server).execute(operation, params)
```

### 4. Performance Optimization Pattern

**Parallel Execution**: Optimize performance through intelligent batching and concurrency.

```python
class PerformanceOptimizer:
    async def parallel_server_execution(self, tasks: List[dict]) -> List[dict]:
        """Execute independent tasks in parallel across servers"""

        # Group tasks by server compatibility
        task_groups = await self.group_tasks_by_server(tasks)

        # Execute groups in parallel
        results = await asyncio.gather(*[
            self.execute_task_group(server, group)
            for server, group in task_groups.items()
        ])

        return self.merge_results(results)

    async def optimize_server_calls(self, operations: List[dict]) -> dict:
        """Batch and optimize server calls for efficiency"""

        # Batch similar operations
        batched_ops = await self.batch_similar_operations(operations)

        # Identify parallel execution opportunities
        parallel_groups = await self.identify_parallel_groups(batched_ops)

        # Execute with optimal concurrency
        results = {}
        for group in parallel_groups:
            if group['parallelizable']:
                group_results = await asyncio.gather(*[
                    self.execute_operation(op) for op in group['operations']
                ])
            else:
                group_results = []
                for op in group['operations']:
                    result = await self.execute_operation(op)
                    group_results.append(result)

            results.update({op['id']: result for op, result in zip(group['operations'], group_results)})

        return results

    async def cache_server_responses(self, server: str, operation: str, params: dict) -> dict:
        """Implement intelligent caching for server responses"""

        cache_key = self.generate_cache_key(server, operation, params)

        # Check cache first
        cached_result = await self.get_from_cache(cache_key)
        if cached_result and not self.is_cache_stale(cached_result):
            return {
                'result': cached_result['data'],
                'cache_hit': True,
                'server_used': f"{server}_cached"
            }

        # Execute and cache result
        result = await self.call_server(server, operation, params)
        await self.store_in_cache(cache_key, result, ttl=self.get_cache_ttl(server, operation))

        return {
            'result': result,
            'cache_hit': False,
            'server_used': server
        }
```

---

## Server-Specific Implementation Patterns

### Context7 Integration Pattern

```python
class Context7Integration:
    async def get_framework_documentation(self, framework: str, version: str = None) -> dict:
        """Get official framework documentation with version specificity"""

        library_id = await self.resolve_library_id(framework)

        if version:
            library_id = f"{library_id}/{version}"

        docs = await self.context7.get_library_docs(
            context7CompatibleLibraryID=library_id,
            tokens=5000,  # Standard documentation token limit
            topic=None    # Get general documentation
        )

        return {
            'framework': framework,
            'version': version or 'latest',
            'documentation': docs,
            'api_patterns': await self.extract_api_patterns(docs),
            'best_practices': await self.extract_best_practices(docs),
            'examples': await self.extract_code_examples(docs)
        }

    async def validate_implementation_against_docs(self, code: str, docs: dict) -> dict:
        """Validate code implementation against official documentation patterns"""

        patterns = docs.get('api_patterns', [])
        best_practices = docs.get('best_practices', [])

        validation_results = {
            'pattern_compliance': [],
            'best_practice_adherence': [],
            'security_compliance': [],
            'performance_compliance': []
        }

        for pattern in patterns:
            compliance = await self.check_pattern_compliance(code, pattern)
            validation_results['pattern_compliance'].append(compliance)

        for practice in best_practices:
            adherence = await self.check_best_practice(code, practice)
            validation_results['best_practice_adherence'].append(adherence)

        return validation_results
```

### Zen Orchestration Pattern

```python
class ZenOrchestration:
    async def coordinate_complex_task(self, task: dict, context: dict) -> dict:
        """Use Zen for multi-model analysis and decision making"""

        # Step 1: Get multiple AI perspectives
        consensus_result = await self.zen.consensus(
            step=task['description'],
            models=[
                {'model': 'o3', 'stance': 'for'},
                {'model': 'gemini-2.5-pro', 'stance': 'against'},
                {'model': 'claude-opus-4.1', 'stance': 'neutral'}
            ],
            relevant_files=context.get('files', []),
            continuation_id=context.get('session_id')
        )

        # Step 2: Deep analysis if needed
        if task['complexity'] == 'high':
            analysis = await self.zen.thinkdeep(
                step=f"Analyze implementation approach for {task['description']}",
                findings=consensus_result['findings'],
                model='o3',  # Use strongest reasoning model
                use_websearch=True
            )

        # Step 3: Create implementation plan
        plan = await self.zen.planner(
            step=f"Create detailed implementation plan for {task['description']}",
            model='claude-opus-4.1',  # Use best planning model
            use_assistant_model=True
        )

        return {
            'consensus': consensus_result,
            'analysis': analysis if task['complexity'] == 'high' else None,
            'implementation_plan': plan,
            'recommended_approach': await self.extract_recommendation(consensus_result, analysis, plan)
        }
```

### Serena Memory Pattern

```python
class SerenaMemoryIntegration:
    async def activate_project_with_memory(self, project_path: str) -> dict:
        """Activate project and load persistent memory"""

        # Activate project
        activation = await self.serena.activate_project(project_path)

        # Load existing memories
        memories = await self.serena.list_memories()

        # Read relevant project context
        project_context = {}
        for memory in memories:
            if 'project_' in memory or 'architecture_' in memory:
                content = await self.serena.read_memory(memory)
                project_context[memory] = content

        return {
            'activation_status': activation,
            'memories_loaded': len(memories),
            'project_context': project_context,
            'session_restored': True
        }

    async def save_session_state(self, context: dict) -> dict:
        """Save current session state to Serena memory"""

        # Save current task context
        await self.serena.write_memory(
            'current_session',
            f"Session state: {context['current_task']}\n"
            f"Progress: {context['progress']}\n"
            f"Next steps: {context['next_steps']}"
        )

        # Save architectural decisions
        if context.get('decisions'):
            await self.serena.write_memory(
                'architectural_decisions',
                json.dumps(context['decisions'], indent=2)
            )

        # Save code patterns discovered
        if context.get('patterns'):
            await self.serena.write_memory(
                'code_patterns',
                json.dumps(context['patterns'], indent=2)
            )

        return {'session_saved': True, 'memories_updated': 3}
```

---

## Error Handling and Monitoring

### Server Health Monitoring

```python
class MCPHealthMonitor:
    async def monitor_server_health(self) -> dict:
        """Continuous health monitoring for all MCP servers"""

        health_status = {}

        for server in self.all_servers:
            try:
                # Ping server with lightweight operation
                start_time = time.time()
                response = await getattr(self, server).health_check()
                latency = time.time() - start_time

                health_status[server] = {
                    'status': 'healthy',
                    'latency': latency,
                    'last_check': datetime.utcnow(),
                    'uptime': response.get('uptime', 'unknown')
                }

            except Exception as e:
                health_status[server] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.utcnow(),
                    'fallback_available': len(self.fallback_chains.get(server, [])) > 0
                }

        # Update uptime metrics
        await self.update_uptime_metrics(health_status)

        return health_status

    async def handle_server_failure(self, server: str, error: Exception) -> dict:
        """Handle server failure with appropriate fallback"""

        # Log failure
        await self.log_server_failure(server, error)

        # Notify monitoring system
        await self.send_alert(f"MCP Server {server} failed: {error}")

        # Activate fallback
        fallback_server = self.get_primary_fallback(server)

        if fallback_server:
            await self.activate_fallback(server, fallback_server)
            return {
                'fallback_activated': True,
                'fallback_server': fallback_server,
                'estimated_recovery': 'immediate'
            }
        else:
            return {
                'fallback_activated': False,
                'manual_intervention_required': True,
                'impact': await self.assess_failure_impact(server)
            }
```

This integration pattern ensures robust, efficient, and coordinated operation of Dopemux's MCP server ecosystem while maintaining the critical Context7-first development approach and providing graceful degradation when servers are unavailable.
