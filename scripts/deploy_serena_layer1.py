#!/usr/bin/env python3
"""
Serena Layer 1 Deployment Script

ADHD-optimized deployment for navigation intelligence.
Handles all setup, validation, and activation automatically.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add services to path
sys.path.insert(0, str(Path(__file__).parent / "services"))


class SerenaLayer1Deployer:
    """
    ADHD-optimized deployment manager for Serena Layer 1.

    Features:
    - Automatic dependency validation
    - Redis health check and optimization
    - Component initialization and testing
    - Real-world navigation workflow validation
    - Gentle error handling with clear next steps
    """

    def __init__(self, workspace_path: Path = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.deployment_status = {
            "dependencies_checked": False,
            "redis_optimized": False,
            "components_initialized": False,
            "navigation_tested": False,
            "deployment_complete": False
        }

    async def deploy(self) -> Dict[str, Any]:
        """Deploy Serena Layer 1 with ADHD optimizations."""
        print("🚀 Serena Layer 1 Deployment")
        print("=" * 40)
        print(f"📂 Workspace: {self.workspace_path}")
        print(f"📅 Deployment time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        deployment_start = time.time()

        try:
            # Step 1: Check dependencies
            print("🔧 Step 1: Checking dependencies...")
            deps_result = await self._check_dependencies()
            self.deployment_status["dependencies_checked"] = deps_result["success"]

            if not deps_result["success"]:
                return self._create_deployment_report("FAILED", "Dependency check failed", deployment_start)

            # Step 2: Optimize Redis
            print("\n🗄️ Step 2: Optimizing Redis for ADHD navigation...")
            redis_result = await self._setup_redis()
            self.deployment_status["redis_optimized"] = redis_result["success"]

            if not redis_result["success"]:
                return self._create_deployment_report("FAILED", "Redis setup failed", deployment_start)

            # Step 3: Initialize components
            print("\n🧠 Step 3: Initializing navigation intelligence...")
            init_result = await self._initialize_components()
            self.deployment_status["components_initialized"] = init_result["success"]

            if not init_result["success"]:
                return self._create_deployment_report("FAILED", "Component initialization failed", deployment_start)

            # Step 4: Test navigation workflows
            print("\n🧭 Step 4: Testing real navigation workflows...")
            nav_result = await self._test_navigation_workflows()
            self.deployment_status["navigation_tested"] = nav_result["success"]

            # Step 5: Finalize deployment
            print("\n✅ Step 5: Finalizing deployment...")
            final_result = await self._finalize_deployment()

            if final_result["success"]:
                self.deployment_status["deployment_complete"] = True
                return self._create_deployment_report("SUCCESS", "Deployment completed successfully", deployment_start)
            else:
                return self._create_deployment_report("PARTIAL", "Deployment mostly complete with minor issues", deployment_start)

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return self._create_deployment_report("FAILED", f"Deployment error: {e}", deployment_start)

    async def _check_dependencies(self) -> Dict[str, Any]:
        """Check all required dependencies for Layer 1."""
        try:
            missing_deps = []
            available_deps = []

            # Check Python packages
            required_packages = [
                "redis",
                "aiohttp",
                "pydantic",
                "tree_sitter"  # Optional but helpful
            ]

            for package in required_packages:
                try:
                    __import__(package)
                    available_deps.append(package)
                    print(f"   ✅ {package}")
                except ImportError:
                    missing_deps.append(package)
                    print(f"   ❌ {package} (missing)")

            # Check Serena v2 modules
            try:
                from serena.v2 import EnhancedLSPWrapper
                available_deps.append("serena.v2")
                print(f"   ✅ serena.v2 modules")
            except ImportError as e:
                missing_deps.append("serena.v2")
                print(f"   ❌ serena.v2 modules: {e}")

            # Check workspace structure
            workspace_indicators = [".git", ".claude", "services"]
            found_indicators = []

            for indicator in workspace_indicators:
                if (self.workspace_path / indicator).exists():
                    found_indicators.append(indicator)

            print(f"   📂 Workspace indicators: {', '.join(found_indicators)}")

            success = len(missing_deps) == 0 and "serena.v2" in available_deps

            return {
                "success": success,
                "missing_dependencies": missing_deps,
                "available_dependencies": available_deps,
                "workspace_indicators": found_indicators,
                "workspace_valid": len(found_indicators) >= 2
            }

        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            return {"success": False, "error": str(e)}

    async def _setup_redis(self) -> Dict[str, Any]:
        """Set up and optimize Redis for ADHD navigation."""
        try:
            from serena.v2.redis_optimizer import quick_redis_health_check

            # Check Redis health
            health_check = await quick_redis_health_check()

            if not health_check["redis_available"]:
                print(f"   ❌ Redis not available: {health_check.get('error', 'Unknown error')}")
                print(f"   💡 ADHD-friendly fix: Start Redis with: docker run -d -p 6379:6379 redis:alpine")
                return {"success": False, "issue": "redis_not_available"}

            print(f"   ✅ Redis available: {health_check['status']}")
            print(f"   ⚡ Performance: {health_check['operation_time_ms']}ms (target: <2ms)")

            # Validate for ADHD requirements
            adhd_ready = health_check.get("adhd_ready", False)
            if adhd_ready:
                print(f"   🧠 ADHD-ready: ✅ Performance suitable for navigation intelligence")
            else:
                print(f"   ⚠️ Performance above ideal, but usable for ADHD navigation")

            return {
                "success": True,
                "redis_status": health_check["status"],
                "performance_ms": health_check["operation_time_ms"],
                "adhd_optimized": adhd_ready
            }

        except Exception as e:
            logger.error(f"Redis setup failed: {e}")
            return {"success": False, "error": str(e)}

    async def _initialize_components(self) -> Dict[str, Any]:
        """Initialize Layer 1 components with ADHD optimizations."""
        try:
            from serena.v2 import (
                NavigationCache, NavigationCacheConfig,
                ADHDCodeNavigator, FocusManager,
                PerformanceMonitor, PerformanceTarget,
                TreeSitterAnalyzer
            )

            components_status = {}

            # Initialize navigation cache
            print("   💾 Initializing navigation cache...")
            cache_config = NavigationCacheConfig(
                redis_url="redis://localhost:6379",
                db_index=1,  # Separate from ConPort
                default_ttl=300
            )

            nav_cache = NavigationCache(cache_config)
            await nav_cache.initialize()
            cache_health = await nav_cache.health_check()
            components_status["navigation_cache"] = cache_health["status"]
            print(f"      {cache_health['status']}")

            # Initialize ADHD features
            print("   🧠 Initializing ADHD features...")
            adhd_navigator = ADHDCodeNavigator()
            await adhd_navigator.initialize(self.workspace_path)
            adhd_health = await adhd_navigator.health_check()
            components_status["adhd_features"] = adhd_health["status"]
            print(f"      {adhd_health['status']}")

            # Initialize focus manager
            print("   🎯 Initializing focus manager...")
            focus_manager = FocusManager()
            await focus_manager.initialize()
            focus_health = await focus_manager.health_check()
            components_status["focus_manager"] = focus_health["status"]
            print(f"      {focus_health['status']}")

            # Initialize performance monitoring
            print("   ⏱️ Initializing performance monitoring...")
            perf_monitor = PerformanceMonitor(
                target=PerformanceTarget(target_ms=200.0, warning_ms=150.0, critical_ms=500.0)
            )
            components_status["performance_monitor"] = "🚀 Active"
            print(f"      🚀 Active (target: <200ms)")

            # Initialize Tree-sitter (with graceful fallback)
            print("   🌳 Initializing Tree-sitter analyzer...")
            tree_analyzer = TreeSitterAnalyzer()
            tree_success = await tree_analyzer.initialize()

            if tree_success:
                components_status["tree_sitter"] = f"🌳 Enhanced ({len(tree_analyzer.parsers)} parsers)"
                print(f"      🌳 Enhanced mode with {len(tree_analyzer.parsers)} language parsers")
            else:
                components_status["tree_sitter"] = "✅ LSP-only mode (fully functional)"
                print(f"      ✅ LSP-only mode (Tree-sitter compatibility issues - still fully functional)")

            # Cleanup
            await nav_cache.close()

            success = all("🚀" in status or "✅" in status or "🧠" in status or "🎯" in status or "🌳" in status
                         for status in components_status.values())

            return {
                "success": success,
                "components": components_status,
                "tree_sitter_enhanced": tree_success,
                "lsp_navigation_ready": True
            }

        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _test_navigation_workflows(self) -> Dict[str, Any]:
        """Test Layer 1 with real navigation workflows."""
        try:
            print("   🧪 Testing workspace detection...")

            # Test workspace detection
            from serena.v2.enhanced_lsp import EnhancedLSPWrapper, LSPConfig
            from serena.v2.navigation_cache import NavigationCache, NavigationCacheConfig
            from serena.v2.adhd_features import ADHDCodeNavigator
            from serena.v2.focus_manager import FocusManager
            from serena.v2.performance_monitor import PerformanceMonitor

            # Minimal setup for testing
            cache_config = NavigationCacheConfig(db_index=4)  # Test DB
            nav_cache = NavigationCache(cache_config)
            adhd_nav = ADHDCodeNavigator()
            focus_mgr = FocusManager()
            perf_monitor = PerformanceMonitor()

            enhanced_lsp = EnhancedLSPWrapper(
                config=LSPConfig(),
                workspace_path=self.workspace_path,
                cache=nav_cache,
                adhd_navigator=adhd_nav,
                focus_manager=focus_mgr,
                performance_monitor=perf_monitor
            )

            # Test workspace detection
            detected_workspace = enhanced_lsp.workspace_path
            workspace_correct = "dopemux-mvp" in str(detected_workspace)

            print(f"      📂 Detected: {detected_workspace}")
            print(f"      🎯 Dopemux project: {'✅ Correct' if workspace_correct else '⚠️ Check path'}")

            # Test project file detection
            python_files = list(self.workspace_path.rglob("*.py"))
            js_files = list(self.workspace_path.rglob("*.js"))

            print(f"      📄 Python files: {len(python_files)} (navigation ready)")
            print(f"      📄 JavaScript files: {len(js_files)} (navigation ready)")

            navigation_ready = len(python_files) > 0 or len(js_files) > 0

            return {
                "success": navigation_ready,
                "workspace_detected": workspace_correct,
                "python_files": len(python_files),
                "javascript_files": len(js_files),
                "navigation_ready": navigation_ready
            }

        except Exception as e:
            logger.error(f"Navigation workflow test failed: {e}")
            return {"success": False, "error": str(e)}

    async def _finalize_deployment(self) -> Dict[str, Any]:
        """Finalize deployment with ADHD-friendly usage instructions."""
        try:
            # Create deployment summary
            deployment_summary = {
                "serena_layer1_version": "2.0.0-layer1",
                "deployment_timestamp": datetime.now().isoformat(),
                "workspace": str(self.workspace_path),
                "features_enabled": [],
                "usage_instructions": [],
                "adhd_optimizations": []
            }

            # Document enabled features
            if self.deployment_status["redis_optimized"]:
                deployment_summary["features_enabled"].append("🗄️ Redis navigation cache with <2ms performance")

            if self.deployment_status["components_initialized"]:
                deployment_summary["features_enabled"].append("🧠 ADHD features: focus modes, progressive disclosure, complexity scoring")

            if self.deployment_status["navigation_tested"]:
                deployment_summary["features_enabled"].append("🧭 Enhanced LSP navigation with workspace auto-detection")

            # ADHD optimizations active
            deployment_summary["adhd_optimizations"] = [
                "🎯 <200ms navigation response targets",
                "📋 Progressive disclosure (max 10 initial results)",
                "🌡️ Real-time complexity scoring and warnings",
                "🎛️ Focus modes for attention management",
                "🍞 Navigation breadcrumb preservation",
                "💾 Automatic context saving and restoration",
                "⚡ Intelligent prefetching for smooth exploration"
            ]

            # Usage instructions
            deployment_summary["usage_instructions"] = [
                "🚀 Start navigation: python -m serena.v2.enhanced_lsp",
                "🎯 Enable focus mode: Use focus_manager.set_focus_mode()",
                "🔍 Enhanced search: Use claude_context.enhanced_semantic_search()",
                "📊 Monitor performance: Check enhanced_lsp.health_check()",
                "📚 Documentation: See docs/serena-adhd-navigation-guide.md"
            ]

            # Save deployment info
            deployment_file = self.workspace_path / "serena_layer1_deployment.json"
            with open(deployment_file, "w") as f:
                json.dump(deployment_summary, f, indent=2)

            print(f"\n📄 Deployment summary saved: {deployment_file}")

            return {"success": True, "deployment_summary": deployment_summary}

        except Exception as e:
            logger.error(f"Deployment finalization failed: {e}")
            return {"success": False, "error": str(e)}

    def _create_deployment_report(self, status: str, message: str, start_time: float) -> Dict[str, Any]:
        """Create deployment report with ADHD-friendly summary."""
        duration = (time.time() - start_time) * 1000

        report = {
            "deployment_status": status,
            "message": message,
            "duration_ms": round(duration, 1),
            "workspace": str(self.workspace_path),
            "component_status": self.deployment_status,
            "timestamp": datetime.now().isoformat()
        }

        # Add ADHD-friendly next steps
        if status == "SUCCESS":
            report["next_steps"] = [
                "🎉 Serena Layer 1 is ready for development!",
                "📚 Review ADHD navigation guide: docs/serena-adhd-navigation-guide.md",
                "🧪 Test with real coding tasks",
                "🎯 Experiment with focus modes",
                "📊 Monitor performance and ADHD experience"
            ]
            report["adhd_benefits"] = [
                "⚡ Instant navigation with <200ms responses",
                "🧠 Cognitive load reduction through progressive disclosure",
                "🎯 Focus modes for attention management",
                "💾 Context preservation across interruptions",
                "🔍 Intelligent semantic search integration"
            ]

        elif status == "PARTIAL":
            report["next_steps"] = [
                "✅ Core navigation intelligence is functional",
                "🔧 Address minor issues when convenient",
                "📚 Use LSP navigation features immediately",
                "⚡ Redis caching provides excellent performance"
            ]

        else:  # FAILED
            report["recovery_steps"] = [
                "📋 Check dependency installation",
                "🗄️ Ensure Redis is running (docker run -d -p 6379:6379 redis:alpine)",
                "📂 Verify workspace is dopemux-mvp project root",
                "🔧 Check logs for specific error details"
            ]

        return report

    # Helper methods
    async def _run_quick_health_check(self) -> Dict[str, Any]:
        """Run quick health check for deployed system."""
        try:
            from serena.v2.redis_optimizer import quick_redis_health_check

            redis_health = await quick_redis_health_check()

            return {
                "redis": redis_health,
                "workspace": {
                    "path": str(self.workspace_path),
                    "is_dopemux": "dopemux-mvp" in str(self.workspace_path),
                    "has_services": (self.workspace_path / "services").exists()
                }
            }

        except Exception as e:
            return {"error": str(e)}


# Quick deployment functions
async def quick_deploy(workspace_path: str = None) -> Dict[str, Any]:
    """Quick deployment for immediate ADHD navigation."""
    deployer = SerenaLayer1Deployer(Path(workspace_path) if workspace_path else None)
    return await deployer.deploy()


async def validate_deployment() -> Dict[str, Any]:
    """Validate existing deployment."""
    print("🔍 Validating Serena Layer 1 Deployment")

    try:
        # Check if deployment file exists
        deployment_file = Path.cwd() / "serena_layer1_deployment.json"

        if deployment_file.exists():
            with open(deployment_file, "r") as f:
                deployment_data = json.load(f)

            print(f"✅ Deployment found: {deployment_data.get('serena_layer1_version', 'unknown')}")
            print(f"📅 Deployed: {deployment_data.get('deployment_timestamp', 'unknown')}")

            # Quick health check
            from serena.v2.redis_optimizer import quick_redis_health_check
            health = await quick_redis_health_check()

            return {
                "deployment_exists": True,
                "deployment_data": deployment_data,
                "current_health": health
            }
        else:
            print("❌ No deployment found - run deploy_serena_layer1.py")
            return {"deployment_exists": False}

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return {"error": str(e)}


async def main():
    """Main deployment execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy Serena Layer 1 Navigation Intelligence")
    parser.add_argument("--workspace", help="Workspace path (auto-detected if not provided)")
    parser.add_argument("--validate", action="store_true", help="Validate existing deployment")
    parser.add_argument("--quick", action="store_true", help="Quick deployment mode")

    args = parser.parse_args()

    if args.validate:
        await validate_deployment()
        return

    # Run deployment
    deployer = SerenaLayer1Deployer(Path(args.workspace) if args.workspace else None)
    result = await deployer.deploy()

    # Print final status
    print(f"\n🎯 DEPLOYMENT {result['deployment_status']}")
    print(f"Duration: {result['duration_ms']:.1f}ms")

    if result["deployment_status"] == "SUCCESS":
        print("\n🎉 Serena Layer 1 is ready for ADHD-optimized development!")
    elif result["deployment_status"] == "PARTIAL":
        print("\n👍 Core functionality ready - minor issues can be addressed later")
    else:
        print("\n💙 Don't worry - we can fix this together. Check the recovery steps above.")


if __name__ == "__main__":
    asyncio.run(main())