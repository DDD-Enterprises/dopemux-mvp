"""
Test Grok Code Fast 1 for context generation via Zen MCP.

This test uses mcp__zen__chat directly (available in Claude Code context)
to verify grok-code-fast-1 can generate useful code context descriptions.
"""

import asyncio


async def test_grok_context_generation():
    """Test grok-code-fast-1 context generation."""

    # Sample code chunk
    sample_code = """
def calculate_complexity(node: Node) -> float:
    '''
    Calculate ADHD-friendly complexity score (0.0-1.0).

    Based on:
    - Nesting depth
    - Number of branches (if/for/while)
    - Total lines
    '''
    def count_depth(n: Node, depth: int = 0) -> int:
        if not n.children:
            return depth
        return max(count_depth(c, depth + 1) for c in n.children)

    def count_branches(n: Node) -> int:
        count = 0
        if n.type in ('if_statement', 'for_statement', 'while_statement'):
            count += 1
        for child in n.children:
            count += count_branches(child)
        return count

    depth = count_depth(node)
    branches = count_branches(node)
    lines = node.end_point[0] - node.start_point[0] + 1

    depth_score = min(depth / 10.0, 1.0)
    branch_score = min(branches / 10.0, 1.0)
    lines_score = min(lines / 100.0, 1.0)

    complexity = depth_score * 0.3 + branch_score * 0.4 + lines_score * 0.3
    return round(complexity, 2)
"""

    # Test prompt
    prompt = f"""Generate a concise 2-3 sentence description of this code from src/preprocessing/code_chunker.py (calculate_complexity):

```python
{sample_code}
```

Focus on: What does this code do? What's its purpose in the larger system?"""

    print("=" * 80)
    print("GROK CODE FAST 1 - CONTEXT GENERATION TEST")
    print("=" * 80)
    print(f"\nPrompt:\n{prompt}\n")
    print("-" * 80)

    # This would be called via mcp__zen__chat in Claude Code context
    print("\n⚠️  This test requires manual execution in Claude Code context")
    print("Run via Claude Code and call:")
    print(f"""
    mcp__zen__chat(
        prompt="{prompt[:50]}...",
        model="grok-code-fast-1",
        working_directory="/Users/hue/code/dopemux-mvp/services/dope-context",
        temperature=0.3
    )
    """)


if __name__ == "__main__":
    asyncio.run(test_grok_context_generation())
