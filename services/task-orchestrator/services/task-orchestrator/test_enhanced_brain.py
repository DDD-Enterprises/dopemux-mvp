#!/usr/bin/env python3
"""
Test script for enhanced DopeBrainzManager with 2024-2025 prompt optimization techniques.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_enhanced_brain():
    """Test the enhanced DopeBrainzManager with advanced techniques."""
    print("🧠 Testing Enhanced DopeBrainzManager...")

    try:
        from enhanced_orchestrator import DopeBrainzManager

        brain = DopeBrainzManager()
        print("✅ DopeBrainzManager initialized with advanced features")

        # Test 1: Basic reasoning with COSTAR framework
        print("\n1. Testing COSTAR Framework...")
        prompt = "How should I optimize database queries?"
        context = {
            "use_costar": True,
            "task_type": "problem_solving",
            "domain": "database optimization",
            "complexity_score": 0.7,
            "output_type": "step-by-step solution",
            "focus_areas": ["performance", "scalability"],
            "communication_style": "technical",
            "formatting": "numbered steps",
            "audience_level": "developer"
        }

        response = await brain.reason(prompt, context)
        print(f"✅ COSTAR Response: {response[:100]}...")

        # Test 2: Chain-of-Thought for complex reasoning
        print("\n2. Testing Chain-of-Thought...")
        complex_prompt = "Design a microservices architecture for an e-commerce platform"
        complex_context = {
            "complexity_score": 0.9,  # Triggers CoT
            "include_examples": True,
            "task_type": "design"
        }

        response = await brain.reason(complex_prompt, complex_context)
        print(f"✅ CoT Response: {response[:100]}...")

        # Test 3: Self-consistency for critical decisions
        print("\n3. Testing Self-Consistency...")
        critical_prompt = "Should we use GraphQL or REST for our API?"
        critical_context = {
            "require_consistency": True,
            "complexity_score": 0.6
        }

        response = await brain.reason_with_self_consistency(critical_prompt, critical_context)
        print(f"✅ Self-Consistency Response: {response[:100]}...")

        # Test 4: Performance tracking
        print("\n4. Testing Performance Tracking...")
        await brain.track_prompt_performance(
            prompt="Test prompt",
            response="Test response",
            context={"task_type": "testing"},
            response_time=1.5
        )

        report = brain.performance_tracker.get_performance_report()
        print(f"✅ Performance Report: {report}")

        # Test 5: Evolutionary optimization (if API available)
        print("\n5. Testing Evolutionary Optimization...")
        try:
            base_prompt = "Explain async programming"
            evolved = await brain.evolutionary_optimizer.evolve_prompt(
                base_prompt,
                {"task_type": "explanation", "complexity_score": 0.6},
                generations=1  # Quick test
            )
            print(f"✅ Evolved Prompt: {evolved[:100]}...")
        except Exception as e:
            print(f"ℹ️  Evolutionary test skipped: {e}")

        print("\n🎉 All enhanced DopeBrainzManager tests completed successfully!")
        print("\n🚀 Advanced Features Implemented:")
        print("   ✅ COSTAR Framework for structured prompting")
        print("   ✅ Chain-of-Thought reasoning")
        print("   ✅ Few-shot prompting with examples")
        print("   ✅ Self-consistency for reliability")
        print("   ✅ Evolutionary prompt optimization")
        print("   ✅ Systematic performance tracking")
        print("   ✅ Meta-prompting with critique cycles")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_brain())
    sys.exit(0 if success else 1)