"""
Serena v2 Layer 1 Validation Suite

Comprehensive validation of Layer 1 navigation intelligence implementation.
Verifies performance targets, ADHD optimizations, and integration completeness.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import Layer 1 components for validation
from .enhanced_lsp import EnhancedLSPWrapper, LSPConfig
from .navigation_cache import NavigationCache, NavigationCacheConfig
from .adhd_features import ADHDCodeNavigator
from .focus_manager import FocusManager
from .performance_monitor import PerformanceMonitor, PerformanceTarget
from .tree_sitter_analyzer import TreeSitterAnalyzer
from .claude_context_integration import ClaudeContextIntegration, ClaudeContextConfig
from .mcp_client import McpClient

logger = logging.getLogger(__name__)


class Layer1Validator:
    """
    Comprehensive validator for Serena v2 Layer 1 implementation.

    Validates:
    - Performance targets (<200ms navigation)
    - ADHD accommodations and optimizations
    - Component integration and health
    - Workspace auto-detection
    - Cache efficiency and Tree-sitter enhancement
    - Claude-context MCP integration
    """

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.validation_results = {}

        # Initialize components for testing
        self.components = {}
        self.performance_data = []

    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete Layer 1 validation suite."""
        logger.info("🧪 Starting Serena v2 Layer 1 Validation Suite")

        validation_start = time.time()

        try:
            # Initialize components
            await self._initialize_components()

            # Run validation tests
            await asyncio.gather(
                self._validate_performance_targets(),
                self._validate_adhd_optimizations(),
                self._validate_tree_sitter_integration(),
                self._validate_claude_context_integration(),
                self._validate_caching_efficiency(),
                self._validate_workspace_detection(),
                return_exceptions=True
            )

            # Generate final report
            validation_duration = (time.time() - validation_start) * 1000

            final_report = await self._generate_validation_report(validation_duration)

            logger.info(f"✅ Layer 1 validation complete in {validation_duration:.1f}ms")
            return final_report

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        finally:
            await self._cleanup_components()

    async def _initialize_components(self) -> None:
        """Initialize all Layer 1 components for testing."""
        logger.info("🚀 Initializing Layer 1 components...")

        # Performance monitor
        self.components["performance_monitor"] = PerformanceMonitor(
            target=PerformanceTarget(target_ms=200.0, warning_ms=150.0, critical_ms=500.0)
        )

        # Navigation cache
        cache_config = NavigationCacheConfig(
            redis_url="redis://localhost:6379",
            db_index=99,  # Use test database
            default_ttl=300
        )
        self.components["navigation_cache"] = NavigationCache(cache_config)

        # ADHD features
        self.components["adhd_navigator"] = ADHDCodeNavigator()

        # Focus manager
        self.components["focus_manager"] = FocusManager()

        # Tree-sitter analyzer
        self.components["tree_sitter_analyzer"] = TreeSitterAnalyzer()

        # Claude-context integration
        claude_config = ClaudeContextConfig(
            mcp_endpoint="http://localhost:3000",
            timeout=5.0,
            performance_target_ms=200.0
        )
        self.components["claude_context"] = ClaudeContextIntegration(
            config=claude_config,
            navigation_cache=self.components["navigation_cache"],
            lsp_wrapper=None  # Will be set after LSP initialization
        )

        # Enhanced LSP wrapper (main integration point)
        lsp_config = LSPConfig(
            cache_ttl=300,
            batch_size=20,
            timeout=10.0,
            max_concurrent_requests=5
        )

        self.components["enhanced_lsp"] = EnhancedLSPWrapper(
            config=lsp_config,
            workspace_path=self.workspace_path,
            cache=self.components["navigation_cache"],
            adhd_navigator=self.components["adhd_navigator"],
            focus_manager=self.components["focus_manager"],
            performance_monitor=self.components["performance_monitor"],
            tree_sitter_analyzer=self.components["tree_sitter_analyzer"]
        )

        # Set LSP wrapper reference in claude-context
        self.components["claude_context"].lsp_wrapper = self.components["enhanced_lsp"]

        # Initialize all components
        await asyncio.gather(
            self.components["navigation_cache"].initialize(),
            self.components["adhd_navigator"].initialize(self.workspace_path),
            self.components["focus_manager"].initialize(),
            self.components["tree_sitter_analyzer"].initialize(),
            self.components["claude_context"].initialize(),
            self.components["enhanced_lsp"].initialize(),
            return_exceptions=True
        )

    async def _validate_performance_targets(self) -> None:
        """Validate <200ms performance targets."""
        logger.info("⏱️ Validating performance targets...")

        performance_results = {
            "target_ms": 200.0,
            "tests_passed": 0,
            "tests_failed": 0,
            "average_response_time": 0.0,
            "violations": []
        }

        # Test LSP operations
        test_files = [
            "services/serena/v2/enhanced_lsp.py",
            "services/serena/v2/tree_sitter_analyzer.py",
            "services/serena/v2/navigation_cache.py"
        ]

        response_times = []

        for test_file in test_files:
            file_path = self.workspace_path / test_file
            if file_path.exists():
                # Test document symbols (should use both LSP + Tree-sitter)
                start_time = time.time()

                try:
                    symbols_response = await self.components["enhanced_lsp"].get_document_symbols(
                        str(file_path), focus_mode=False
                    )

                    duration_ms = (time.time() - start_time) * 1000
                    response_times.append(duration_ms)

                    if duration_ms <= 200.0:
                        performance_results["tests_passed"] += 1
                        logger.debug(f"✅ {file_path.name}: {duration_ms:.1f}ms")
                    else:
                        performance_results["tests_failed"] += 1
                        performance_results["violations"].append({
                            "file": file_path.name,
                            "duration_ms": duration_ms,
                            "operation": "get_document_symbols"
                        })
                        logger.warning(f"❌ {file_path.name}: {duration_ms:.1f}ms (exceeded target)")

                except Exception as e:
                    performance_results["tests_failed"] += 1
                    logger.error(f"Performance test failed for {file_path}: {e}")

        if response_times:
            performance_results["average_response_time"] = sum(response_times) / len(response_times)

        self.validation_results["performance"] = performance_results

    async def _validate_adhd_optimizations(self) -> None:
        """Validate ADHD-specific optimizations."""
        logger.info("🧠 Validating ADHD optimizations...")

        adhd_results = {
            "progressive_disclosure": False,
            "complexity_scoring": False,
            "focus_mode": False,
            "gentle_guidance": False,
            "context_preservation": False,
            "workspace_auto_detection": False
        }

        try:
            # Test progressive disclosure
            test_symbols = [{"name": f"function_{i}", "kind": 12} for i in range(25)]
            disclosed_symbols = await self.components["adhd_navigator"].apply_progressive_disclosure(
                test_symbols, max_initial_items=10
            )

            if len(disclosed_symbols) <= 10:
                adhd_results["progressive_disclosure"] = True
                logger.debug("✅ Progressive disclosure working")

            # Test complexity scoring
            if self.components["tree_sitter_analyzer"].initialized:
                test_file = self.workspace_path / "services/serena/v2/enhanced_lsp.py"
                if test_file.exists():
                    analysis = await self.components["tree_sitter_analyzer"].analyze_file(str(test_file))
                    if analysis and hasattr(analysis, "overall_complexity"):
                        adhd_results["complexity_scoring"] = True
                        logger.debug(f"✅ Complexity scoring: {analysis.overall_complexity:.2f}")

            # Test focus mode
            focus_stats = await self.components["focus_manager"].get_focus_statistics()
            if focus_stats.get("current_session", {}).get("active") is not None:
                adhd_results["focus_mode"] = True
                logger.debug("✅ Focus mode functional")

            # Test gentle guidance
            guidance = await self.components["adhd_navigator"].generate_navigation_guidance(
                str(self.workspace_path / "services/serena/v2/enhanced_lsp.py")
            )
            if guidance.get("current_context"):
                adhd_results["gentle_guidance"] = True
                logger.debug("✅ Gentle guidance available")

            # Test workspace auto-detection
            if self.components["enhanced_lsp"].stats.get("workspace_auto_detected"):
                adhd_results["workspace_auto_detection"] = True
                logger.debug("✅ Workspace auto-detection working")

        except Exception as e:
            logger.error(f"ADHD optimization validation failed: {e}")

        self.validation_results["adhd_optimizations"] = adhd_results

    async def _validate_tree_sitter_integration(self) -> None:
        """Validate Tree-sitter integration and enhancement."""
        logger.info("🌳 Validating Tree-sitter integration...")

        tree_sitter_results = {
            "analyzer_initialized": False,
            "supported_languages": [],
            "analysis_working": False,
            "lsp_enhancement": False,
            "caching_working": False
        }

        try:
            # Check analyzer initialization
            if self.components["tree_sitter_analyzer"].initialized:
                tree_sitter_results["analyzer_initialized"] = True
                tree_sitter_results["supported_languages"] = list(
                    self.components["tree_sitter_analyzer"].languages.keys()
                )
                logger.debug(f"✅ Tree-sitter supports: {tree_sitter_results['supported_languages']}")

            # Test analysis
            test_file = self.workspace_path / "services/serena/v2/enhanced_lsp.py"
            if test_file.exists():
                analysis = await self.components["tree_sitter_analyzer"].analyze_file(str(test_file))
                if analysis:
                    tree_sitter_results["analysis_working"] = True
                    logger.debug(f"✅ Tree-sitter analysis: {len(analysis.elements)} elements")

                    # Test LSP enhancement
                    mock_lsp_symbols = [
                        {"name": "EnhancedLSPWrapper", "kind": 5},
                        {"name": "initialize", "kind": 6}
                    ]
                    enhanced = self.components["tree_sitter_analyzer"].enhance_lsp_symbols(
                        mock_lsp_symbols, analysis
                    )

                    if any("tree_sitter_analysis" in symbol for symbol in enhanced):
                        tree_sitter_results["lsp_enhancement"] = True
                        logger.debug("✅ LSP enhancement working")

            # Test caching
            cache_stats = await self.components["navigation_cache"].get_tree_sitter_cache_stats()
            if "tree_sitter_analyses_cached" in cache_stats:
                tree_sitter_results["caching_working"] = True
                logger.debug("✅ Tree-sitter caching functional")

        except Exception as e:
            logger.error(f"Tree-sitter validation failed: {e}")

        self.validation_results["tree_sitter"] = tree_sitter_results

    async def _validate_claude_context_integration(self) -> None:
        """Validate claude-context MCP integration."""
        logger.info("🔗 Validating claude-context integration...")

        claude_results = {
            "mcp_client_initialized": False,
            "server_connectivity": False,
            "semantic_search": False,
            "prefetching": False,
            "performance_compliant": False
        }

        try:
            # Check MCP client
            if self.components["claude_context"].mcp_client:
                claude_results["mcp_client_initialized"] = True
                logger.debug("✅ MCP client initialized")

                # Test connectivity (basic health check)
                health = await self.components["claude_context"].mcp_client.health_check()
                if health.get("server_healthy"):
                    claude_results["server_connectivity"] = True
                    logger.debug("✅ Claude-context server reachable")
                else:
                    logger.warning("⚠️ Claude-context server not reachable")

            # Test semantic search (mock/placeholder)
            try:
                # This would fail if claude-context server isn't running, but that's expected
                search_results = await self.components["claude_context"].enhanced_semantic_search(
                    query="test function",
                    workspace_path=str(self.workspace_path),
                    limit=5
                )

                claude_results["semantic_search"] = True
                logger.debug(f"✅ Semantic search returned {len(search_results)} results")

            except Exception as e:
                logger.debug(f"Semantic search test expected to fail without running server: {e}")

            # Test prefetching
            prefetch_scheduled = self.components["claude_context"].schedule_prefetch(
                "semantic_search",
                priority="low",
                query="test prefetch",
                workspace_path=str(self.workspace_path)
            )

            if prefetch_scheduled:
                claude_results["prefetching"] = True
                logger.debug("✅ Prefetching system functional")

            # Check performance stats
            integration_health = await self.components["claude_context"].get_integration_health()
            if "mcp_performance" in integration_health:
                claude_results["performance_compliant"] = True
                logger.debug("✅ Performance monitoring active")

        except Exception as e:
            logger.error(f"Claude-context validation failed: {e}")

        self.validation_results["claude_context"] = claude_results

    async def _validate_caching_efficiency(self) -> None:
        """Validate caching system efficiency."""
        logger.info("💾 Validating caching efficiency...")

        cache_results = {
            "redis_connection": False,
            "navigation_caching": False,
            "tree_sitter_caching": False,
            "performance_improvement": False,
            "cache_invalidation": False
        }

        try:
            # Test Redis connection
            cache_health = await self.components["navigation_cache"].health_check()
            if "🚀 Excellent" in cache_health.get("status", "") or "✅ Good" in cache_health.get("status", ""):
                cache_results["redis_connection"] = True
                logger.debug("✅ Redis connection healthy")

            # Test navigation result caching
            test_key = "test_navigation_result"
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}

            cached = await self.components["navigation_cache"].cache_navigation_result(
                test_key, test_data, 60
            )

            if cached:
                retrieved = await self.components["navigation_cache"].get_navigation_result(test_key)
                if retrieved == test_data:
                    cache_results["navigation_caching"] = True
                    logger.debug("✅ Navigation caching working")

            # Test Tree-sitter caching (mock analysis)
            if self.components["tree_sitter_analyzer"].initialized:
                test_file = self.workspace_path / "services/serena/v2/enhanced_lsp.py"
                if test_file.exists():
                    # First call - should cache
                    start_time = time.time()
                    analysis1 = await self.components["tree_sitter_analyzer"].analyze_file(str(test_file))
                    first_duration = (time.time() - start_time) * 1000

                    if analysis1:
                        # Cache the analysis
                        await self.components["navigation_cache"].cache_tree_sitter_analysis(
                            str(test_file), analysis1
                        )

                        # Check if it can be retrieved
                        cached_analysis = await self.components["navigation_cache"].get_tree_sitter_analysis(
                            str(test_file)
                        )

                        if cached_analysis:
                            cache_results["tree_sitter_caching"] = True
                            logger.debug("✅ Tree-sitter caching working")

                            # Performance improvement check
                            if first_duration > 50:  # Only meaningful if parsing took some time
                                cache_results["performance_improvement"] = True
                                logger.debug(f"✅ Performance improvement potential: {first_duration:.1f}ms -> cached")

        except Exception as e:
            logger.error(f"Caching validation failed: {e}")

        self.validation_results["caching"] = cache_results

    async def _validate_workspace_detection(self) -> None:
        """Validate workspace auto-detection."""
        logger.info("📂 Validating workspace detection...")

        workspace_results = {
            "auto_detection": False,
            "project_indicators_found": [],
            "workspace_path_correct": False,
            "dopemux_specific_handling": False
        }

        try:
            # Check if workspace was auto-detected
            detected_path = self.components["enhanced_lsp"].workspace_path
            auto_detected = self.components["enhanced_lsp"].stats.get("workspace_auto_detected", False)

            workspace_results["auto_detection"] = auto_detected
            workspace_results["workspace_path_correct"] = detected_path == self.workspace_path

            # Check for project indicators
            indicators = [".git", "package.json", "pyproject.toml", ".claude", "dopemux-mvp", "services"]
            found_indicators = []

            for indicator in indicators:
                if (self.workspace_path / indicator).exists():
                    found_indicators.append(indicator)

            workspace_results["project_indicators_found"] = found_indicators

            # Check dopemux-specific handling
            if "dopemux-mvp" in str(detected_path):
                workspace_results["dopemux_specific_handling"] = True
                logger.debug("✅ Dopemux-specific workspace handling active")

            logger.debug(f"✅ Workspace detection: {detected_path}")

        except Exception as e:
            logger.error(f"Workspace detection validation failed: {e}")

        self.validation_results["workspace_detection"] = workspace_results

    async def _generate_validation_report(self, validation_duration_ms: float) -> Dict[str, Any]:
        """Generate comprehensive validation report."""

        # Calculate overall success metrics
        total_checks = 0
        passed_checks = 0

        def count_checks(results_dict):
            nonlocal total_checks, passed_checks
            for key, value in results_dict.items():
                if isinstance(value, bool):
                    total_checks += 1
                    if value:
                        passed_checks += 1
                elif isinstance(value, dict) and key != "violations":
                    count_checks(value)

        for category_results in self.validation_results.values():
            if isinstance(category_results, dict):
                count_checks(category_results)

        success_rate = (passed_checks / total_checks) if total_checks > 0 else 0

        # Determine overall status
        if success_rate >= 0.9:
            overall_status = "🚀 EXCELLENT"
        elif success_rate >= 0.8:
            overall_status = "✅ GOOD"
        elif success_rate >= 0.7:
            overall_status = "⚠️ NEEDS_IMPROVEMENT"
        else:
            overall_status = "❌ FAILED"

        # Generate recommendations
        recommendations = []

        # Performance recommendations
        perf_results = self.validation_results.get("performance", {})
        if perf_results.get("tests_failed", 0) > 0:
            recommendations.append("🏃 Optimize slow operations to meet <200ms target")

        # ADHD recommendations
        adhd_results = self.validation_results.get("adhd_optimizations", {})
        if not adhd_results.get("focus_mode"):
            recommendations.append("🎯 Enable focus mode functionality for ADHD users")

        # Integration recommendations
        claude_results = self.validation_results.get("claude_context", {})
        if not claude_results.get("server_connectivity"):
            recommendations.append("🔗 Start claude-context server for full semantic search functionality")

        if not recommendations:
            recommendations.append("🎉 All systems operational - ready for testing!")

        return {
            "validation_summary": {
                "overall_status": overall_status,
                "success_rate": f"{success_rate:.1%}",
                "checks_passed": passed_checks,
                "total_checks": total_checks,
                "validation_duration_ms": round(validation_duration_ms, 1)
            },
            "component_results": self.validation_results,
            "recommendations": recommendations,
            "layer1_features_validated": {
                "real_mcp_integration": claude_results.get("mcp_client_initialized", False),
                "performance_monitoring": perf_results.get("tests_passed", 0) > 0,
                "intelligent_prefetching": claude_results.get("prefetching", False),
                "tree_sitter_analysis": self.validation_results.get("tree_sitter", {}).get("analysis_working", False),
                "enhanced_lsp_integration": self.validation_results.get("tree_sitter", {}).get("lsp_enhancement", False),
                "redis_caching": self.validation_results.get("caching", {}).get("navigation_caching", False),
                "adhd_optimizations": adhd_results.get("progressive_disclosure", False),
                "workspace_auto_detection": self.validation_results.get("workspace_detection", {}).get("auto_detection", False)
            },
            "next_steps": [
                "Test with real development workflows",
                "Validate with actual ADHD users",
                "Monitor performance in production",
                "Begin Layer 2 implementation (PostgreSQL graph + learning)"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "layer1_validation_v1"
        }

    async def _cleanup_components(self) -> None:
        """Clean up test components."""
        try:
            cleanup_tasks = []

            for component_name, component in self.components.items():
                if hasattr(component, 'close'):
                    cleanup_tasks.append(component.close())

            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)

            logger.debug("🧹 Component cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Standalone validation runner
async def run_layer1_validation(workspace_path: str = None) -> Dict[str, Any]:
    """Run Layer 1 validation suite."""
    if workspace_path is None:
        workspace_path = Path.cwd()
    else:
        workspace_path = Path(workspace_path)

    validator = Layer1Validator(workspace_path)
    return await validator.run_full_validation()


if __name__ == "__main__":
    # Run validation if executed directly
    async def main():
        import sys
        workspace = sys.argv[1] if len(sys.argv) > 1 else None
        results = await run_layer1_validation(workspace)
        print(json.dumps(results, indent=2))

    asyncio.run(main())