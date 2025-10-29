#!/usr/bin/env python3
"""
Sound Alert System for DOPE Layout
Plays subtle audio cues for different events
"""

import os
import subprocess
from enum import Enum
from pathlib import Path

class AlertSound(Enum):
    """Available sound alerts"""
    SUCCESS = "/System/Library/Sounds/Glass.aiff"
    ERROR = "/System/Library/Sounds/Sosumi.aiff"
    WARNING = "/System/Library/Sounds/Funk.aiff"
    INFO = "/System/Library/Sounds/Pop.aiff"
    NOTIFICATION = "/System/Library/Sounds/Purr.aiff"
    UNTRACKED_WORK = "/System/Library/Sounds/Tink.aiff"
    CONTEXT_SWITCH = "/System/Library/Sounds/Blow.aiff"
    TASK_COMPLETE = "/System/Library/Sounds/Hero.aiff"

def play_sound(sound: AlertSound, volume: float = 0.5):
    """
    Play a sound alert
    
    Args:
        sound: AlertSound enum value
        volume: Volume level 0.0 to 1.0
    """
    try:
        # Check if sound file exists
        if not Path(sound.value).exists():
            return
        
        # Play with afplay (macOS)
        subprocess.run(
            ["afplay", "-v", str(volume), sound.value],
            check=False,
            capture_output=True
        )
    except Exception:
        pass  # Silently fail if can't play sound

# Convenience functions
def alert_success():
    """Tests passed, build successful"""
    play_sound(AlertSound.SUCCESS)

def alert_error():
    """Tests failed, build error"""
    play_sound(AlertSound.ERROR)

def alert_warning():
    """Warning condition"""
    play_sound(AlertSound.WARNING)

def alert_info():
    """Informational notification"""
    play_sound(AlertSound.INFO)

def alert_untracked_work():
    """Untracked work detected"""
    play_sound(AlertSound.UNTRACKED_WORK)

def alert_context_switch():
    """Context switch detected"""
    play_sound(AlertSound.CONTEXT_SWITCH)

def alert_task_complete():
    """Task completed"""
    play_sound(AlertSound.TASK_COMPLETE)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: sound_alerts.py <event>")
        print("Events: success, error, warning, info, untracked, context_switch, task_complete")
        sys.exit(1)
    
    event = sys.argv[1].lower()
    
    alerts = {
        "success": alert_success,
        "error": alert_error,
        "warning": alert_warning,
        "info": alert_info,
        "untracked": alert_untracked_work,
        "context_switch": alert_context_switch,
        "task_complete": alert_task_complete,
    }
    
    if event in alerts:
        alerts[event]()
        print(f"✅ Played {event} alert")
    else:
        print(f"❌ Unknown event: {event}")
        sys.exit(1)
