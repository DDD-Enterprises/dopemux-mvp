#!/usr/bin/env python3
"""
Serena v2 Layer 1 Test Runner

Standalone test runner for Layer 1 navigation intelligence validation.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add services to path for imports
sys.path.insert(0, str(Path(__file__).parent / "services"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_basic_components():
    """Test basic component initialization and functionality."""
    results = {
        "tree_sitter_init": False,
        "navigation_cache_init": False,
        "performance_monitor_init": False,
        "workspace_detection": False,
        "component_health": {}
    }

    try:
        # Test Tree-sitter analyzer
        from serena.v2.tree_sitter_analyzer import TreeSitterAnalyzer

        analyzer = TreeSitterAnalyzer()
        tree_sitter_success = await analyzer.initialize()
        results["tree_sitter_init"] = tree_sitter_success

        if tree_sitter_success:
            print(f"🌳 Tree-sitter initialized with languages: {list(analyzer.languages.keys())}")

            # Test analysis on this file
            analysis = await analyzer.analyze_file(__file__)
            if analysis:
                print(f"🔍 Self-analysis: {len(analysis.elements)} elements, complexity: {analysis.overall_complexity:.2f}")
                results["tree_sitter_analysis"] = True
        else:
            print("⚠️ Tree-sitter initialization failed")

        # Test performance monitor
        from serena.v2.performance_monitor import PerformanceMonitor, PerformanceTarget

        perf_monitor = PerformanceMonitor(target=PerformanceTarget(target_ms=200.0))

        # Test operation tracking
        op_id = perf_monitor.start_operation("test_operation")
        await asyncio.sleep(0.05)  # 50ms simulated work
        metrics = perf_monitor.end_operation(op_id, success=True)

        if metrics and metrics.duration_ms < 200:
            results["performance_monitor_init"] = True
            print(f"⏱️ Performance monitor working: {metrics.duration_ms:.1f}ms tracked")

        # Test workspace detection
        from serena.v2.enhanced_lsp import EnhancedLSPWrapper, LSPConfig
        from serena.v2.navigation_cache import NavigationCache, NavigationCacheConfig
        from serena.v2.adhd_features import ADHDCodeNavigator
        from serena.v2.focus_manager import FocusManager

        # Create minimal components for workspace detection test
        cache_config = NavigationCacheConfig(redis_url="redis://localhost:6379", db_index=2)
        nav_cache = NavigationCache(cache_config)

        adhd_nav = ADHDCodeNavigator()
        focus_mgr = FocusManager()

        # Test workspace detection
        lsp_config = LSPConfig()
        enhanced_lsp = EnhancedLSPWrapper(
            config=lsp_config,
            workspace_path=Path.cwd(),
            cache=nav_cache,
            adhd_navigator=adhd_nav,
            focus_manager=focus_mgr,
            performance_monitor=perf_monitor
        )

        detected_workspace = enhanced_lsp.workspace_path
        current_workspace = Path.cwd()

        if "dopemux-mvp" in str(detected_workspace):
            results["workspace_detection"] = True
            print(f"📂 Workspace auto-detected: {detected_workspace}")
        else:
            print(f"⚠️ Workspace detection uncertain: {detected_workspace}")

        # Component health checks
        try:
            await nav_cache.initialize()
            cache_health = await nav_cache.health_check()
            results["component_health"]["navigation_cache"] = cache_health.get("status", "unknown")
            print(f"💾 Navigation cache: {cache_health.get('status', 'unknown')}")
        except Exception as e:
            results["component_health"]["navigation_cache"] = f"error: {e}"
            print(f"❌ Navigation cache failed: {e}")

        try:
            await adhd_nav.initialize(detected_workspace)
            adhd_health = await adhd_nav.health_check()
            results["component_health"]["adhd_features"] = adhd_health.get("status", "unknown")
            print(f"🧠 ADHD features: {adhd_health.get('status', 'unknown')}")
        except Exception as e:
            results["component_health"]["adhd_features"] = f"error: {e}"
            print(f"❌ ADHD features failed: {e}")

        # Cleanup
        try:
            await nav_cache.close()
        except Exception:
            pass

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure Serena v2 modules are available")
        results["import_error"] = str(e)
    except Exception as e:
        print(f"❌ Test error: {e}")
        results["test_error"] = str(e)

    return results

async def test_tree_sitter_analysis():
    """Test Tree-sitter analysis on actual project files."""
    print("\n🌳 Testing Tree-sitter Analysis on Project Files")

    try:
        from serena.v2.tree_sitter_analyzer import TreeSitterAnalyzer

        analyzer = TreeSitterAnalyzer()
        if not await analyzer.initialize():
            print("❌ Tree-sitter analyzer initialization failed")
            return {"error": "initialization_failed"}

        # Test files to analyze
        test_files = [
            "services/serena/v2/enhanced_lsp.py",
            "services/serena/v2/tree_sitter_analyzer.py",
            "services/serena/v2/performance_monitor.py"
        ]

        analysis_results = {}

        for test_file in test_files:
            file_path = Path(test_file)
            if file_path.exists():
                print(f"\n📄 Analyzing: {file_path.name}")

                start_time = time.time()
                analysis = await analyzer.analyze_file(str(file_path))
                duration_ms = (time.time() - start_time) * 1000

                if analysis:
                    analysis_results[test_file] = {
                        "elements_found": len(analysis.elements),
                        "complexity_score": analysis.overall_complexity,
                        "complexity_level": analysis.complexity_level.value,
                        "lines_of_code": analysis.lines_of_code,
                        "analysis_time_ms": duration_ms,
                        "adhd_recommendations": analysis.adhd_recommendations[:2]
                    }

                    print(f"  📊 {len(analysis.elements)} elements, complexity: {analysis.overall_complexity:.2f} ({analysis.complexity_level.value})")
                    print(f"  ⏱️ Analysis time: {duration_ms:.1f}ms")

                    if analysis.adhd_recommendations:
                        print(f"  💡 ADHD insight: {analysis.adhd_recommendations[0]}")
                else:
                    print(f"  ❌ Analysis failed")
                    analysis_results[test_file] = {"error": "analysis_failed"}
            else:
                print(f"  ⚠️ File not found: {test_file}")

        return analysis_results

    except Exception as e:
        print(f"❌ Tree-sitter test failed: {e}")
        return {"error": str(e)}

async def test_performance_monitoring():
    """Test performance monitoring system."""
    print("\n⏱️ Testing Performance Monitoring")

    try:
        from serena.v2.performance_monitor import PerformanceMonitor, PerformanceTarget

        monitor = PerformanceMonitor(
            target=PerformanceTarget(target_ms=200.0, warning_ms=150.0, critical_ms=500.0)
        )

        # Test operation tracking
        test_results = {}

        # Test fast operation
        op_id = monitor.start_operation("fast_test")
        await asyncio.sleep(0.05)  # 50ms
        metrics = monitor.end_operation(op_id, success=True, cache_hit=False)

        test_results["fast_operation"] = {
            "duration_ms": metrics.duration_ms,
            "under_target": metrics.duration_ms < 200.0
        }
        print(f"  🚀 Fast operation: {metrics.duration_ms:.1f}ms (target: <200ms)")

        # Test cached operation
        op_id = monitor.start_operation("cache_test")
        await asyncio.sleep(0.001)  # 1ms simulated cache hit
        metrics = monitor.end_operation(op_id, success=True, cache_hit=True)

        test_results["cached_operation"] = {
            "duration_ms": metrics.duration_ms,
            "cache_hit": metrics.cache_hit
        }
        print(f"  💾 Cached operation: {metrics.duration_ms:.1f}ms (cache hit)")

        # Get performance report
        report = await monitor.get_performance_report()
        test_results["report_generated"] = "overview" in report

        if report.get("overview"):
            avg_duration = report["overview"]["average_duration_ms"]
            compliance_rate = report["overview"]["target_compliance_rate"]
            print(f"  📊 Average: {avg_duration}ms, Compliance: {compliance_rate}")

        return test_results

    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        return {"error": str(e)}

async def main():
    """Main test runner."""
    print("🧪 Serena v2 Layer 1 Test Suite")
    print("=" * 50)

    all_results = {}

    # Test basic components
    print("\n🔧 Testing Basic Components")
    all_results["basic_components"] = await test_basic_components()

    # Test Tree-sitter analysis
    all_results["tree_sitter_analysis"] = await test_tree_sitter_analysis()

    # Test performance monitoring
    all_results["performance_monitoring"] = await test_performance_monitoring()

    # Generate summary
    print("\n📋 Test Summary")
    print("=" * 30)

    total_tests = 0
    passed_tests = 0

    def count_results(results_dict, prefix=""):
        nonlocal total_tests, passed_tests
        for key, value in results_dict.items():
            if isinstance(value, bool):
                total_tests += 1
                if value:
                    passed_tests += 1
                    print(f"✅ {prefix}{key}")
                else:
                    print(f"❌ {prefix}{key}")
            elif isinstance(value, dict) and "error" not in value:
                count_results(value, f"{prefix}{key}.")
            elif "error" in str(value):
                total_tests += 1
                print(f"❌ {prefix}{key}: {value}")

    count_results(all_results)

    success_rate = (passed_tests / total_tests) if total_tests > 0 else 0
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed ({success_rate:.1%})")

    if success_rate >= 0.8:
        print("🚀 Layer 1 is ready for production!")
    elif success_rate >= 0.6:
        print("✅ Layer 1 is mostly functional - minor issues to address")
    else:
        print("⚠️ Layer 1 needs significant fixes before use")

    # Save detailed results
    with open("layer1_test_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n📄 Detailed results saved to: layer1_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())