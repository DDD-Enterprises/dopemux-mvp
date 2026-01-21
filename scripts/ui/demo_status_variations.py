#!/usr/bin/env python3
"""
Demo script to show different MetaMCP status bar variations
for ADHD-friendly visual feedback testing.
"""

import time

import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path

# Add parent directory to path to import the status bar
sys.path.insert(0, str(Path(__file__).parent))
from metamcp_status import MetaMCPStatusBar


def demo_role_variations():
    """Demo different role indicators."""
    logger.info("\n🎨 MetaMCP Status Bar Demo - Role Variations\n")

    status_bar = MetaMCPStatusBar()

    roles = ['developer', 'researcher', 'planner', 'reviewer', 'ops', 'architect', 'debugger']

    for role in roles:
        logger.info(f"Role: {role}")
        formatted = status_bar.format_role_indicator(role)
        logger.info(f"  Status: {formatted}")
        logger.info()

def demo_token_usage_progression():
    """Demo token usage at different levels."""
    logger.info("\n💚 Token Usage Progression Demo\n")

    status_bar = MetaMCPStatusBar()
    budget = 10000

    usage_levels = [0, 1500, 4000, 6000, 8000, 9500, 10000]

    for usage in usage_levels:
        percentage = (usage / budget) * 100
        formatted = status_bar.format_token_usage(usage, budget)
        logger.info(f"Usage: {usage:,} tokens ({percentage:.1f}%)")
        logger.info(f"  Status: {formatted}")
        logger.info()

def demo_session_duration_warnings():
    """Demo session duration with break reminders."""
    logger.info("\n⏰ Session Duration & Break Reminders Demo\n")

    status_bar = MetaMCPStatusBar()

    durations = [5, 15, 25, 35, 50, 75, 120]

    for duration in durations:
        formatted = status_bar.format_session_duration(duration)
        logger.info(f"Duration: {duration} minutes")
        logger.info(f"  Status: {formatted}")
        logger.info()

def demo_health_indicators():
    """Demo health status indicators."""
    logger.info("\n🏥 Health Status Demo\n")

    status_bar = MetaMCPStatusBar()

    health_states = [
        ('healthy', 11),
        ('warning', 8),
        ('error', 3),
        ('unknown', 0)
    ]

    for health, tools in health_states:
        formatted = status_bar.format_health_status(health, tools)
        logger.info(f"Health: {health}, Tools: {tools}")
        logger.info(f"  Status: {formatted}")
        logger.info()

def demo_full_status_bar():
    """Demo complete status bar in different scenarios."""
    logger.info("\n🎯 Complete Status Bar Scenarios\n")

    status_bar = MetaMCPStatusBar()

    scenarios = [
        {
            'name': 'Fresh Start (Developer)',
            'role': 'developer',
            'tools_count': 4,
            'token_usage': 150,
            'token_budget': 10000,
            'session_duration': 5,
            'health': 'healthy',
            'adhd_features': True
        },
        {
            'name': 'Mid Session (Researcher)',
            'role': 'researcher',
            'tools_count': 3,
            'token_usage': 4500,
            'token_budget': 10000,
            'session_duration': 28,
            'health': 'healthy',
            'adhd_features': True
        },
        {
            'name': 'Break Time! (Debugger)',
            'role': 'debugger',
            'tools_count': 5,
            'token_usage': 8200,
            'token_budget': 10000,
            'session_duration': 55,
            'health': 'warning',
            'adhd_features': True
        },
        {
            'name': 'Emergency Mode (Ops)',
            'role': 'ops',
            'tools_count': 2,
            'token_usage': 9800,
            'token_budget': 10000,
            'session_duration': 95,
            'health': 'error',
            'adhd_features': True
        }
    ]

    for scenario in scenarios:
        logger.info(f"Scenario: {scenario['name']}")

        # Override the get_metamcp_status method temporarily
        original_method = status_bar.get_metamcp_status
        status_bar.get_metamcp_status = lambda: scenario

        full_status = status_bar.generate_status_bar()
        logger.info(f"  Status: {full_status}")
        logger.info()

        # Restore original method
        status_bar.get_metamcp_status = original_method

def interactive_demo():
    """Interactive demo with live updates."""
    logger.info("\n🚀 Interactive Live Demo (Press Ctrl+C to stop)\n")

    status_bar = MetaMCPStatusBar()

    try:
        while True:
            full_status = status_bar.generate_status_bar()
            logger.info(f"\r{full_status}", end='', flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n\nDemo stopped.")

def main():
    """Run all demos."""
    logger.info("🎨 MetaMCP ADHD-Friendly Status Bar Demo")
    logger.info("=" * 50)

    demo_role_variations()
    demo_token_usage_progression()
    demo_session_duration_warnings()
    demo_health_indicators()
    demo_full_status_bar()

    response = input("Run interactive live demo? (y/n): ")
    if response.lower().startswith('y'):
        interactive_demo()

if __name__ == '__main__':
    main()