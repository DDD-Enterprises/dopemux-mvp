
import sys
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

# Setup path
src_path = str(Path.cwd() / "src")
sys.path.append(src_path)

# Import from NEW location
orch_src = str(Path.cwd() / "services/session-manager/src")
sys.path.append(orch_src)

# Import the renamed adapter
# The refactor renamed tmux_manager.py -> layout_adapter.py (which contains TmuxLayoutManager class)
# We need to check if the CLASS name was changed. My plan didn't specify class rename, just file rename.
# So it should still be TmuxLayoutManager inside layout_adapter.py
try:
    from layout_adapter import TmuxLayoutManager
    print("✅ Successfully imported TmuxLayoutManager from services/session-manager/src/layout_adapter.py")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

def test_manager():
    session_name = "test-session-manager-session"
    print(f"Creating session: {session_name}")
    
    manager = TmuxLayoutManager(session_name=session_name)
    manager.create_session(energy_level="medium")
    
    # Verify session exists using Core utilities
    from dopemux.mobile import tmux_utils
    if session_name in tmux_utils.list_sessions():
        print("✅ Session created successfully")
    else:
        print("❌ Session creation failed")
        sys.exit(1)
        
    # Verify panes (Medium energy = 3 panes)
    panes = manager.controller.list_panes(session=session_name)
    print(f"Pane count: {len(panes)} (Expected ~3)")
    
    # Clean up
    manager.destroy_session()
    print("✅ Session destroyed")

if __name__ == "__main__":
    test_manager()
