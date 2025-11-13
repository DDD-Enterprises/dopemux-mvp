#!/usr/bin/env python3
"""
Workspace Selector Widget for Dopemux Dashboard
Allows switching between workspaces with hotkeys
"""

import os
from typing import List, Optional

class WorkspaceSelector:
    """Interactive workspace selector for TMUX dashboard"""
    
    def __init__(self):
        self.workspaces = self._load_workspaces()
        self.current_workspace = os.getenv("DOPEMUX_WORKSPACE_ID") or os.getcwd()
        self.current_index = self._find_current_index()
    
    def _load_workspaces(self) -> List[str]:
        """Load all configured workspaces"""
        default = os.getenv("DEFAULT_WORKSPACE_PATH", os.getcwd())
        additional = os.getenv("WORKSPACE_PATHS", "").split(",")
        
        workspaces = [default]
        workspaces.extend([w.strip() for w in additional if w.strip()])
        
        return list(dict.fromkeys(workspaces))  # Remove duplicates
    
    def _find_current_index(self) -> int:
        """Find index of current workspace"""
        try:
            return self.workspaces.index(self.current_workspace)
        except ValueError:
            return 0
    
    def next_workspace(self) -> str:
        """Switch to next workspace (circular)"""
        self.current_index = (self.current_index + 1) % len(self.workspaces)
        self.current_workspace = self.workspaces[self.current_index]
        return self.current_workspace
    
    def prev_workspace(self) -> str:
        """Switch to previous workspace (circular)"""
        self.current_index = (self.current_index - 1) % len(self.workspaces)
        self.current_workspace = self.workspaces[self.current_index]
        return self.current_workspace
    
    def select_workspace(self, index: int) -> Optional[str]:
        """Select workspace by index"""
        if 0 <= index < len(self.workspaces):
            self.current_index = index
            self.current_workspace = self.workspaces[index]
            return self.current_workspace
        return None
    
    def get_workspace_display(self) -> str:
        """Get formatted workspace display for dashboard"""
        workspace_name = os.path.basename(self.current_workspace)
        total = len(self.workspaces)
        current_num = self.current_index + 1
        
        # Show navigation hint if multiple workspaces
        if total > 1:
            return f"[{current_num}/{total}] {workspace_name} (←/→ to switch)"
        else:
            return workspace_name
    
    def get_all_workspaces_status(self) -> List[dict]:
        """Get status for all workspaces (for multi-workspace view)"""
        status = []
        for i, workspace in enumerate(self.workspaces):
            name = os.path.basename(workspace)
            is_current = (i == self.current_index)
            status.append({
                "index": i,
                "name": name,
                "path": workspace,
                "current": is_current,
                "exists": os.path.exists(workspace)
            })
        return status
