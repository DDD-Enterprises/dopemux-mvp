#!/usr/bin/env python3
"""
ADHD Engine CLI

Command-line interface for ADHD Engine:
- Status checks
- Break triggers
- Focus session management
- Detector runs

Usage:
    adhd status              Show current ADHD state
    adhd break [--duration]  Suggest or start a break
    adhd focus [--task]      Start focus session
    adhd check               Run all detectors
    adhd voice [message]     Speak via TTS
    adhd context save        Save current context
    adhd context restore     Restore last context
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional

# Try to import httpx for async HTTP
try:
    import httpx
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    import urllib.request
    import urllib.error

# ANSI colors
class Colors:
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Configuration
ADHD_ENGINE_URL = os.getenv("ADHD_ENGINE_URL", "http://localhost:3333")


def http_get(path: str) -> Optional[dict]:
    """Make HTTP GET request."""
    url = f"{ADHD_ENGINE_URL}{path}"
    try:
        if HTTP_AVAILABLE:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                return response.json() if response.status_code == 200 else None
        else:
            with urllib.request.urlopen(url, timeout=5) as response:
                return json.loads(response.read().decode())
    except Exception as e:
        print(f"{Colors.RED}Error connecting to ADHD Engine: {e}{Colors.RESET}")
        return None


def http_post(path: str, data: dict) -> Optional[dict]:
    """Make HTTP POST request."""
    url = f"{ADHD_ENGINE_URL}{path}"
    try:
        if HTTP_AVAILABLE:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(url, json=data)
                return response.json() if response.status_code in [200, 201] else None
        else:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode())
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return None


def cmd_status(args):
    """Show current ADHD state."""
    state = http_get(f"/api/v1/state?user_id={args.user}")
    
    if not state:
        print(f"{Colors.RED}⚠️ ADHD Engine unreachable{Colors.RESET}")
        return 1
    
    energy = state.get("energy", "unknown")
    attention = state.get("attention", "unknown")
    session_min = state.get("session_minutes", 0)
    
    # Energy color
    energy_color = {
        "high": Colors.GREEN,
        "medium": Colors.YELLOW,
        "low": Colors.RED
    }.get(energy, Colors.RESET)
    
    # Attention icon
    attention_icons = {
        "hyperfocus": "🔥",
        "focused": "🎯",
        "distracted": "🌊",
        "fatigued": "😴",
        "overwhelmed": "😰"
    }
    attention_icon = attention_icons.get(attention, "🧠")
    
    print(f"\n{Colors.BOLD}ADHD State{Colors.RESET}")
    print(f"{'─' * 30}")
    print(f"⚡ Energy:     {energy_color}{energy.upper()}{Colors.RESET}")
    print(f"{attention_icon} Attention:  {attention}")
    print(f"⏱️  Session:    {session_min} minutes")
    
    # Warnings
    if session_min >= 90:
        print(f"\n{Colors.YELLOW}⚠️ Long session - consider a break{Colors.RESET}")
    if energy == "low":
        print(f"{Colors.YELLOW}⚠️ Low energy - switch to easier tasks{Colors.RESET}")
    if attention == "overwhelmed":
        print(f"{Colors.RED}🆘 Overwhelm detected - take a break NOW{Colors.RESET}")
    
    print()
    return 0



def cmd_break(args):
    """Suggest or start a break."""
    
    # Interactive mode
    if args.interactive:
        try:
            from break_guide import interactive_break_menu
            interactive_break_menu()
            return 0
        except ImportError:
            print(f"{Colors.YELLOW}Interactive mode requires 'rich' library.{Colors.RESET}")
            # Fallback to standard flow
    
    result = http_get(f"/api/v1/break-suggestion?user_id={args.user}")
    
    if not result:
        print(f"{Colors.YELLOW}☕ Take a 5-minute break{Colors.RESET}")
        return 0
    
    break_type = result.get("break_type", "short")
    duration = result.get("duration_minutes", 5)
    activities = result.get("activities", ["stretch", "hydrate"])
    
    print(f"\n{Colors.CYAN}☕ Break Suggestion{Colors.RESET}")
    print(f"{'─' * 30}")
    print(f"Type: {break_type}")
    print(f"Duration: {duration} minutes")
    print(f"Activities: {', '.join(activities)}")
    
    if args.start:
        # Log break start
        http_post("/api/v1/log-break", {
            "user_id": args.user,
            "break_type": break_type,
            "started_at": datetime.now().isoformat()
        })
        print(f"\n{Colors.GREEN}✅ Break started! Enjoy.{Colors.RESET}")
        
    if args.suggest:
        print(f"\n{Colors.BOLD}Break Recommended:{Colors.RESET}")
        print(f"  Start: 'adhd break --start'")
        print(f"  Guide: 'adhd break --interactive'")
    
    print()
    return 0

# ... (omitted) ...

    # break
    parser_break = subparsers.add_parser("break", help="Get break suggestion")
    parser_break.add_argument("--start", action="store_true", help="Start the break")
    parser_break.add_argument("--interactive", "-i", action="store_true", help="Interactive break menu")
    parser_break.add_argument("--suggest", action="store_true", help="Show suggestion prompt")
    parser_break.set_defaults(func=cmd_break)


def cmd_focus(args):
    """Start focus session."""
    task = args.task or "Unspecified task"
    
    result = http_post("/api/v1/focus-session", {
        "user_id": args.user,
        "task": task,
        "target_minutes": args.duration
    })
    
    if result:
        print(f"\n{Colors.GREEN}🎯 Focus session started{Colors.RESET}")
        print(f"Task: {task}")
        print(f"Target: {args.duration} minutes")
        print(f"\n{Colors.CYAN}Good luck! You've got this! 🚀{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}Starting focus session locally...{Colors.RESET}")
        print(f"Task: {task}")
    
    print()
    return 0


def cmd_check(args):
    """Run all detectors."""
    state = http_get(f"/api/v1/state?user_id={args.user}")
    
    if not state:
        print(f"{Colors.RED}Cannot run checks - engine unreachable{Colors.RESET}")
        return 1
    
    print(f"\n{Colors.BOLD}Running ADHD Detectors...{Colors.RESET}")
    print(f"{'─' * 40}")
    
    # Check hyperfocus
    session_min = state.get("session_minutes", 0)
    if session_min >= 120:
        print(f"{Colors.RED}🔥 HYPERFOCUS: {session_min}min - CRITICAL{Colors.RESET}")
    elif session_min >= 90:
        print(f"{Colors.YELLOW}🔥 HYPERFOCUS: {session_min}min - Warning{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}✓ Hyperfocus: OK ({session_min}min){Colors.RESET}")
    
    # Check energy
    energy = state.get("energy", "medium")
    if energy == "low":
        print(f"{Colors.YELLOW}⚡ ENERGY: Low - switch to easier tasks{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}✓ Energy: {energy}{Colors.RESET}")
    
    # Check attention
    attention = state.get("attention", "focused")
    if attention == "overwhelmed":
        print(f"{Colors.RED}😰 OVERWHELM: Detected - take break{Colors.RESET}")
    elif attention == "distracted":
        print(f"{Colors.YELLOW}🌊 Distraction: Detected{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}✓ Attention: {attention}{Colors.RESET}")
    
    print()
    return 0


def cmd_voice(args):
    """Speak message via TTS."""
    message = " ".join(args.message) if args.message else "Hello from ADHD Engine"
    
    # Try to use macOS say command directly
    import subprocess
    try:
        subprocess.run(["say", "-v", "Samantha", "-r", "180", message], check=True)
        print(f"{Colors.GREEN}🔊 Spoke: {message}{Colors.RESET}")
    except FileNotFoundError:
        print(f"{Colors.YELLOW}TTS not available (macOS 'say' command){Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}TTS error: {e}{Colors.RESET}")
    
    return 0


def cmd_context(args):
    """Context save/restore commands."""
    if args.action == "save":
        result = http_post("/api/v1/save-context", {
            "user_id": args.user,
            "reason": "cli_save",
            "prompt_hint": "Manual context save from CLI"
        })
        if result and result.get("saved"):
            print(f"{Colors.GREEN}📍 Context saved{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}Context save attempted (engine may be offline){Colors.RESET}")
    
    elif args.action == "restore":
        result = http_get(f"/api/v1/restore-context?user_id={args.user}")
        if result:
            print(f"\n{Colors.CYAN}📍 Last Context{Colors.RESET}")
            print(f"{'─' * 30}")
            if result.get("files"):
                print(f"Files: {', '.join(result['files'][:5])}")
            if result.get("task"):
                print(f"Task: {result['task']}")
            if result.get("reason"):
                print(f"Saved: {result['reason']}")
        else:
            print(f"{Colors.YELLOW}No saved context found{Colors.RESET}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="adhd",
        description="ADHD Engine CLI - Neurodivergent developer tools"
    )
    parser.add_argument("--user", default="default", help="User ID (default: default)")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # status
    parser_status = subparsers.add_parser("status", help="Show current ADHD state")
    parser_status.set_defaults(func=cmd_status)
    
    # break
    parser_break = subparsers.add_parser("break", help="Get break suggestion")
    parser_break.add_argument("--start", action="store_true", help="Start the break")
    parser_break.set_defaults(func=cmd_break)
    
    # focus
    parser_focus = subparsers.add_parser("focus", help="Start focus session")
    parser_focus.add_argument("--task", "-t", help="Task description")
    parser_focus.add_argument("--duration", "-d", type=int, default=25, help="Target minutes")
    parser_focus.set_defaults(func=cmd_focus)
    
    # check
    parser_check = subparsers.add_parser("check", help="Run all detectors")
    parser_check.set_defaults(func=cmd_check)
    
    # voice
    parser_voice = subparsers.add_parser("voice", help="Speak via TTS")
    parser_voice.add_argument("message", nargs="*", help="Message to speak")
    parser_voice.set_defaults(func=cmd_voice)
    
    # context
    parser_context = subparsers.add_parser("context", help="Context save/restore")
    parser_context.add_argument("action", choices=["save", "restore"])
    parser_context.set_defaults(func=cmd_context)
    
    args = parser.parse_args()
    
    try:
        sys.exit(args.func(args))
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted{Colors.RESET}")
        sys.exit(130)


if __name__ == "__main__":
    main()
