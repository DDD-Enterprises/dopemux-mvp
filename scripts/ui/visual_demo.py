#!/usr/bin/env python3
"""
Visual demonstration of MetaMCP tmux status bar
Shows what the interface looks like in actual usage
"""

import time
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
        print("┌─────────────────────────────────────────────────────────────────────────────────────────────┐")
        print("│ dopemux-session:0                                                      tmux 3.5a           │")
        print("├─────────────────────────────────────────────────────────────────────────────────────────────┤")
        print("│                                                                                             │")
        print("│  ~ $ claude code                                                                            │")
        print("│                                                                                             │")
        print("│  🎯 MetaMCP ADHD-Optimized Development Environment                                          │")
        print("│                                                                                             │")
        print("│  Your intelligent development companion is active:                                          │")
        print("│  • Role-based tool curation (no decision paralysis)                                        │")
        print("│  • Token budget awareness (no surprise limits)                                             │")
        print("│  • Break reminders (hyperfocus protection)                                                 │")
        print("│  • Visual status feedback (no context switching)                                           │")
        print("│                                                                                             │")
        print("│  Quick commands:                                                                            │")
        print("│  • C-b d = developer role    • C-b r = researcher role                                     │")
        print("│  • C-b p = planner role      • C-b v = reviewer role                                       │")
        print("│  • C-b B = break reminder    • C-b R = reload config                                       │")
        print("│                                                                                             │")
        print("│                                                                                             │")
        print("│                                                                                             │")
        print("│                                                                                             │")
        print("│                                                                                             │")
        print("│                                                                                             │")
        print("├─────────────────────────────────────────────────────────────────────────────────────────────┤")

        # Status bar (this is where the magic happens!)
        print(f"│ MetaMCP  {scenario['status']:<79} │")
        print("└─────────────────────────────────────────────────────────────────────────────────────────────┘")

        # Description below
        print(f"\n🎨 Scenario {i+1}/5: {scenario['title']}")
        print(f"📝 {scenario['description']}")
        print(f"\n⚡ Status Components:")
        print(f"   Role: {scenario['status'].split('|')[0].strip()}")
        print(f"   Tokens: {scenario['status'].split('|')[1].strip()}")
        print(f"   Time: {scenario['status'].split('|')[2].strip()}")
        print(f"   Health: {scenario['status'].split('|')[3].strip()}")
        print(f"   ADHD: {scenario['status'].split('|')[4].strip()}")

        if i < len(scenarios) - 1:
            print(f"\n⏱️  Press Enter to see next scenario...")
            input()
        else:
            print(f"\n🎉 Demo complete! This is your new ADHD-friendly development interface.")

def main():
    print("🚀 MetaMCP Tmux Visual Interface Demo")
    print("=====================================")
    print()
    print("This demo shows how the MetaMCP status bar appears in actual tmux usage.")
    print("You'll see 5 different development scenarios with ADHD-friendly visual feedback.")
    print()
    print("Each scenario demonstrates:")
    print("• Role-specific color coding")
    print("• Progressive token usage warnings")
    print("• Break time reminders")
    print("• System health indicators")
    print()
    input("Press Enter to start the demo...")

    show_tmux_interface()

if __name__ == '__main__':
    main()