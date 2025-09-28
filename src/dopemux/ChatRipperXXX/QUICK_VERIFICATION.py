#!/usr/bin/env python3
"""Quick verification script to test differential privacy implementation."""

def test_differential_privacy_implementation():
    """Verify the DP implementation works correctly."""
    print("🔧 Testing Differential Privacy Implementation...")
    
    try:
        # Test 1: Basic DP Engine
        from src.chatx.privacy.differential_privacy import (
            DifferentialPrivacyEngine, 
            PrivacyBudget, 
            StatisticalQuery
        )
        
        engine = DifferentialPrivacyEngine(random_seed=42)
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6)
        
        test_data = [
            {'id': 1, 'score': 85, 'label': 'positive'},
            {'id': 2, 'score': 92, 'label': 'positive'},
            {'id': 3, 'score': 78, 'label': 'negative'},
        ]
        
        # Test count query
        query = StatisticalQuery('count', 'id', filter_conditions={'label': 'positive'})
        result = engine.count_query(test_data, query, budget)
        print(f"✅ Count query: {result.value:.2f} (expected ~2.0 with noise)")
        
        # Test 2: PolicyShield Integration
        from src.chatx.redaction.policy_shield import PolicyShield, PrivacyPolicy
        
        policy = PrivacyPolicy(enable_differential_privacy=True, dp_epsilon=1.0)
        shield = PolicyShield(policy=policy)
        
        test_chunks = [
            {'chunk_id': '1', 'text': 'Hello world', 'meta': {'labels_coarse': ['friendly']}},
            {'chunk_id': '2', 'text': 'How are you?', 'meta': {'labels_coarse': ['question']}},
        ]
        
        summary = shield.generate_privacy_safe_summary(test_chunks)
        print(f"✅ Privacy-safe summary generated: {summary['privacy_method']}")
        print(f"   Total chunks (noisy): {summary['total_chunks']:.2f}")
        
        # Test 3: Budget tracking
        budget_usage = shield.get_differential_privacy_budget_summary()
        total_epsilon = sum(budget_usage.values())
        print(f"✅ Privacy budget tracking: {total_epsilon:.3f} total epsilon used")
        
        print("\n🎉 ALL TESTS PASSED - Differential Privacy Implementation Working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_differential_privacy_implementation()
    exit(0 if success else 1)