#!/usr/bin/env python3
"""
Basic GPT-Researcher usage examples for Dopemux integration testing
"""

import asyncio
import os
from gpt_researcher import GPTResearcher

# Set up environment variables
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["TAVILY_API_KEY"] = "your-tavily-api-key"


async def quick_research_example():
    """Quick research for immediate insights (5-10 minutes)"""
    print("🔍 Starting quick research...")

    researcher = GPTResearcher(
        query="What are the latest AI coding assistant trends in 2024?",
        report_type="basic",
        report_source="web"
    )

    # Conduct research
    context = await researcher.conduct_research()
    print(f"📊 Research completed. Found {len(context)} sources.")

    # Generate report
    report = await researcher.write_report()
    print("📝 Report generated!")
    print("="*50)
    print(report[:500] + "...")

    return report


async def deep_research_example():
    """Deep research with tree exploration (25-30 minutes)"""
    print("🌳 Starting deep research...")

    def progress_callback(progress):
        print(f"📈 Progress: Depth {progress.current_depth}/{progress.total_depth}, "
              f"Queries {progress.completed_queries}/{progress.total_queries}")
        if progress.current_query:
            print(f"🔍 Current: {progress.current_query}")

    researcher = GPTResearcher(
        query="How are AI agents transforming software development workflows?",
        report_type="deep",  # Enables deep research
        verbose=True
    )

    # Conduct deep research with progress tracking
    context = await researcher.conduct_research(on_progress=progress_callback)
    print(f"📊 Deep research completed. Context length: {len(context)}")

    # Generate comprehensive report
    report = await researcher.write_report()

    # Get research metadata
    sources = researcher.get_source_urls()
    costs = researcher.get_costs()

    print(f"💰 Research cost: ${costs:.2f}")
    print(f"🔗 Sources used: {len(sources)}")

    return report, sources, costs


async def mcp_research_example():
    """Research using MCP servers for hybrid data access"""
    print("🔌 Starting MCP-enhanced research...")

    # Configure MCP servers
    mcp_configs = [
        {
            "name": "github",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")}
        }
    ]

    researcher = GPTResearcher(
        query="What are the most popular open source AI research tools?",
        report_type="detailed",
        mcp_configs=mcp_configs,
        mcp_strategy="fast"  # or "deep" for more thorough MCP usage
    )

    # Enable hybrid retrieval (web + MCP)
    os.environ["RETRIEVER"] = "tavily,mcp"

    context = await researcher.conduct_research()
    report = await researcher.write_report()

    print("🔗 MCP-enhanced research completed!")
    return report


async def adhd_friendly_research():
    """ADHD-optimized research pattern (chunked execution)"""
    print("🧠 Starting ADHD-friendly research...")

    # Simulate ADHD-optimized chunking
    query = "Best practices for building AI-powered developer tools"

    # Chunk 1: Quick overview (10 minutes)
    print("📋 Chunk 1: Getting overview...")
    researcher1 = GPTResearcher(
        query=f"Overview: {query}",
        report_type="basic",
        verbose=False
    )
    overview = await researcher1.conduct_research()

    # Simulated break
    print("☕ Break time! (5 minutes)")
    await asyncio.sleep(1)  # Simulate break

    # Chunk 2: Deep dive (20 minutes)
    print("📋 Chunk 2: Deep analysis...")
    researcher2 = GPTResearcher(
        query=f"Detailed analysis: {query}",
        report_type="detailed",
        context=overview,  # Use previous context
        verbose=False
    )
    detailed_context = await researcher2.conduct_research()

    # Generate combined report
    final_report = await researcher2.write_report()

    print("✅ ADHD-friendly research completed!")
    print(f"📊 Total context: {len(detailed_context)} sources")

    return final_report


async def competitive_analysis_example():
    """Multi-target competitive research"""
    print("⚔️ Starting competitive analysis...")

    companies = ["OpenAI", "Anthropic", "Google AI"]
    reports = {}

    for company in companies:
        print(f"🔍 Researching {company}...")

        researcher = GPTResearcher(
            query=f"{company} AI development tools and APIs 2024",
            report_type="detailed",
            verbose=False
        )

        context = await researcher.conduct_research()
        report = await researcher.write_report()
        reports[company] = {
            'report': report,
            'sources': len(context),
            'cost': researcher.get_costs()
        }

    # Generate comparative analysis
    print("📊 Generating comparative analysis...")
    comparative_researcher = GPTResearcher(
        query="Compare AI development platforms: OpenAI vs Anthropic vs Google AI",
        report_type="detailed"
    )

    # Use combined context from all company research
    all_context = []
    for company, data in reports.items():
        all_context.extend([f"Research on {company}: {data['report'][:1000]}"])

    comparative_report = await comparative_researcher.write_report(ext_context=all_context)

    print("✅ Competitive analysis completed!")
    return comparative_report, reports


async def session_persistence_example():
    """Demonstrate session persistence for ADHD context preservation"""
    print("💾 Testing session persistence...")

    # Start research session
    researcher = GPTResearcher(
        query="Future of AI in software engineering",
        report_type="deep",
        verbose=True
    )

    # Simulate interrupted research
    print("🔍 Starting research (will be interrupted)...")

    # Partial research
    context = await researcher.conduct_research()

    # Save session state (simulate)
    session_data = {
        'query': researcher.query,
        'context': researcher.get_research_context(),
        'sources': researcher.get_source_urls(),
        'progress': len(context),
        'costs': researcher.get_costs()
    }

    print("💾 Session saved due to interruption...")
    print(f"📊 Progress: {session_data['progress']} sources, ${session_data['costs']:.2f}")

    # Simulate resuming session
    print("🔄 Resuming research session...")

    resumed_researcher = GPTResearcher(
        query=session_data['query'],
        context=session_data['context'],  # Restore context
        visited_urls=set(session_data['sources']),  # Avoid duplicate sources
        report_type="deep"
    )

    # Continue research
    final_context = await resumed_researcher.conduct_research()
    final_report = await resumed_researcher.write_report()

    print("✅ Session successfully resumed and completed!")
    print(f"📊 Final: {len(final_context)} total sources")

    return final_report


async def main():
    """Run all examples"""
    print("🚀 GPT-Researcher Dopemux Integration Examples")
    print("=" * 60)

    # Run examples (uncomment the ones you want to test)

    # 1. Quick research (5-10 minutes)
    await quick_research_example()

    # 2. Deep research (25-30 minutes) - Uncomment to test
    # await deep_research_example()

    # 3. MCP-enhanced research - Uncomment to test
    # await mcp_research_example()

    # 4. ADHD-friendly chunked research
    # await adhd_friendly_research()

    # 5. Competitive analysis - Uncomment to test
    # await competitive_analysis_example()

    # 6. Session persistence demo
    # await session_persistence_example()

    print("\n✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())