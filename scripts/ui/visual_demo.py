#!/usr/bin/env python3
"""
Visual demonstration of MetaMCP tmux status bar
Shows what the interface looks like in actual usage
"""

import time

import logging

logger = logging.getLogger(__name__)

import os

def clear_screen():
    os.system('clear')

def show_tmux_interface():
    """Show simulated tmux interface with MetaMCP status bar."""

    scenarios = [
        {
            'title': 'Fresh Development Session',
            'status': '🧑‍💻 DEVELOPER | 💚 0.2k/10k ░░░░░ | 🟢 5m | ✅ 11 tools | 🧠 ADHD✓ | 09:15',
            'description': 'Starting fresh - all green indicators, low token usage, optimal focus time'
        },
        {
            'title': 'Active Research Phase',
            'status': '🔬 RESEARCHER | 💚 3.2k/10k ██░░░ | 🟢 18m | ✅ 3 tools | 🧠 ADHD✓ | 09:33',
            'description': 'Research role active, building token usage, still in good focus zone'
        },
        {
            'title': 'Approaching Break Time',
            'status': '🔬 RESEARCHER | 💛 6.0k/10k ███░░ | 🟡 28m | ✅ 3 tools | 🧠 ADHD✓ | 09:43',
            'description': 'Token usage increasing, 25+ minutes - yellow indicators suggest break soon'
        },
        {
            'title': 'Debugging Complex Issue',
            'status': '🐛 DEBUGGER | 🧡 8.2k/10k ████░ | 🔴 55m | ⚠️ 5 tools | 🧠 ADHD✓ | 10:10',
            'description': 'Switched to debugger role, high token usage, definitely time for a break!'
        },
        {
            'title': 'Emergency Operations',
            'status': '⚙️ OPS | ❤️ 9.8k/10k █████ | 🔴 1h35m | ❌ 2 tools | 🧠 ADHD✓ | 10:50',
            'description': 'Critical ops work - very high usage, long session, some tools offline'
        }
    ]

    for i, scenario in enumerate(scenarios):
        clear_screen()

        # Tmux window header
        logger.info("┌─────────────────────────────────────────────────────────────────────────────────────────────┐")
        logger.info("│ dopemux-session:0                                                      tmux 3.5a           │")
        logger.info("├─────────────────────────────────────────────────────────────────────────────────────────────┤")
        logger.info("│                                                                                             │")
        logger.info("│  ~ $ claude code                                                                            │")
        logger.info("│                                                                                             │")
        logger.info("│  🎯 MetaMCP ADHD-Optimized Development Environment                                          │")
        logger.info("│                                                                                             │")
        logger.info("│  Your intelligent development companion is active:                                          │")
        logger.info("│  • Role-based tool curation (no decision paralysis)                                        │")
        logger.info("│  • Token budget awareness (no surprise limits)                                             │")
        logger.info("│  • Break reminders (hyperfocus protection)                                                 │")
        logger.info("│  • Visual status feedback (no context switching)                                           │")
        logger.info("│                                                                                             │")
        logger.info("│  Quick commands:                                                                            │")
        logger.info("│  • C-b d = developer role    • C-b r = researcher role                                     │")
        logger.info("│  • C-b p = planner role      • C-b v = reviewer role                                       │")
        logger.info("│  • C-b B = break reminder    • C-b R = reload config                                       │")
        logger.info("│                                                                                             │")
        logger.info("│                                                                                             │")
        logger.info("│                                                                                             │")
        logger.info("│                                                                                             │")
        logger.info("│                                                                                             │")
        logger.info("│                                                                                             │")
        logger.info("├─────────────────────────────────────────────────────────────────────────────────────────────┤")

        # Status bar (this is where the magic happens!)
        logger.info(f"│ MetaMCP  {scenario['status']:<79} │")
        logger.info("└─────────────────────────────────────────────────────────────────────────────────────────────┘")

        # Description below
        logger.info(f"\n🎨 Scenario {i+1}/5: {scenario['title']}")
        logger.info(f"📝 {scenario['description']}")
        logger.info(f"\n⚡ Status Components:")
        logger.info(f"   Role: {scenario['status'].split('|')[0].strip()}")
        logger.info(f"   Tokens: {scenario['status'].split('|')[1].strip()}")
        logger.info(f"   Time: {scenario['status'].split('|')[2].strip()}")
        logger.info(f"   Health: {scenario['status'].split('|')[3].strip()}")
        logger.info(f"   ADHD: {scenario['status'].split('|')[4].strip()}")

        if i < len(scenarios) - 1:
            logger.info(f"\n⏱️  Press Enter to see next scenario...")
            input()
        else:
            logger.info(f"\n🎉 Demo complete! This is your new ADHD-friendly development interface.")

def main():
    logger.info("🚀 MetaMCP Tmux Visual Interface Demo")
    logger.info("=====================================")
    logger.info()
    logger.info("This demo shows how the MetaMCP status bar appears in actual tmux usage.")
    logger.info("You'll see 5 different development scenarios with ADHD-friendly visual feedback.")
    logger.info()
    logger.info("Each scenario demonstrates:")
    logger.info("• Role-specific color coding")
    logger.warning("• Progressive token usage warnings")
    logger.info("• Break time reminders")
    logger.info("• System health indicators")
    logger.info()
    input("Press Enter to start the demo...")

    show_tmux_interface()

if __name__ == '__main__':
    main()