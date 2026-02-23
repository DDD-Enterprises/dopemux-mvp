"""
Proactive Context Preservation

Auto-saves mental model state before breaks to enable quick context restoration.
Integrates with Serena (code navigation) and ConPort (knowledge graph).

ADHD Benefit: Eliminates "what was I doing?" frustration after breaks
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class PreservedContext:
    """Snapshot of development context at a moment in time."""
    # Code context
    active_files: List[str] = field(default_factory=list)
    cursor_positions: Dict[str, int] = field(default_factory=dict)  # file -> line number
    recent_symbols: List[str] = field(default_factory=list)  # Recently accessed functions/classes
    
    # Mental model
    mental_model_summary: str = ""  # AI-generated summary of what user was working on
    task_description: Optional[str] = None  # Current task from Leantime/ConPort
    
    # Temporal context
    timestamp: datetime = field(default_factory=datetime.now)
    session_duration: int = 0  # Minutes in current session
    
    # Decision trail
    recent_decisions: List[Dict[str, Any]] = field(default_factory=list)  # Last 3 decisions from ConPort
    
    # Workspace
    workspace_path: Optional[str] = None
    git_branch: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreservedContext':
        """Restore from dict."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ContextPreserver:
    """
    Preserve and restore development context around breaks.
    
    Integration points:
    - Serena: Active files, cursor positions, symbol navigation
    - ConPort: Recent decisions, task context
    - Desktop Commander: Window state (optional)
    """
    
    def __init__(
        self,
        conport_client,
        serena_client=None,
        storage_path: str = ".context_snapshots"
    ):
        """
        Initialize context preserver.
        
        Args:
            conport_client: ConPort/DopeconBridge client
            serena_client: Optional Serena MCP client for code context
            storage_path: Directory for saved contexts
        """
        self.conport = conport_client
        self.serena = serena_client
        self.storage_path = storage_path
        
        # Create storage directory
        import os
        os.makedirs(storage_path, exist_ok=True)
    
    async def capture_current_context(
        self,
        user_id: str,
        workspace_path: Optional[str] = None
    ) -> PreservedContext:
        """
        Capture current development context.
        
        Args:
            user_id: User identifier
            workspace_path: Optional workspace path
        
        Returns:
            PreservedContext snapshot
        """
        logger.info(f"📸 Capturing context for {user_id}")
        
        context = PreservedContext(workspace_path=workspace_path)
        
        try:
            # Get recent decisions from ConPort
            if self.conport:
                decisions = await self._get_recent_decisions(user_id, limit=3)
                context.recent_decisions = decisions
                
                # Extract task description from most recent decision
                if decisions:
                    context.task_description = decisions[0].get('summary', '')
            
            # Get active files from Serena (if available)
            if self.serena:
                active_files = await self._get_active_files()
                context.active_files = active_files
                
                # Get cursor positions
                cursor_positions = await self._get_cursor_positions()
                context.cursor_positions = cursor_positions
                
                # Get recent symbols
                recent_symbols = await self._get_recent_symbols()
                context.recent_symbols = recent_symbols
            
            # Get git context
            if workspace_path:
                git_branch = await self._get_git_branch(workspace_path)
                context.git_branch = git_branch
            
            # Generate mental model summary using AI
            context.mental_model_summary = await self._generate_mental_model(context)
            
            # Save snapshot
            await self._save_snapshot(user_id, context)
            
            logger.info(f"✅ Context captured: {len(context.active_files)} files, {len(context.recent_decisions)} decisions")
            return context
            
        except Exception as e:
            logger.error(f"Failed to capture context: {e}")
            return context
    
    async def restore_context(
        self,
        user_id: str,
        context: Optional[PreservedContext] = None
    ) -> Dict[str, Any]:
        """
        Restore context after break.
        
        Args:
            user_id: User identifier
            context: Optional specific context to restore (default: most recent)
        
        Returns:
            Summary for user display
        """
        logger.info(f"🔄 Restoring context for {user_id}")
        
        try:
            # Load context if not provided
            if context is None:
                context = await self._load_latest_snapshot(user_id)
            
            if context is None:
                return {"error": "No saved context found"}
            
            # Build restoration summary
            time_since = (datetime.now() - context.timestamp).total_seconds() / 60
            
            summary = {
                "time_since_save": f"{int(time_since)} minutes ago",
                "task": context.task_description or "Unknown task",
                "mental_model": context.mental_model_summary,
                "active_files": context.active_files,
                "git_branch": context.git_branch,
                "recent_decisions": [d.get('summary', '') for d in context.recent_decisions],
                "restoration_tips": self._generate_restoration_tips(context)
            }
            
            logger.info(f"✅ Context restored from {int(time_since)} minutes ago")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to restore context: {e}")
            return {"error": str(e)}
    
    async def _get_recent_decisions(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Fetch recent decisions from ConPort."""
        try:
            # Mock implementation - replace with actual ConPort API call
            decisions = await self.conport.recent_decisions(limit=limit)
            return decisions if decisions else []
        except Exception as e:
            logger.warning(f"Failed to fetch decisions: {e}")
            return []
    
    async def _get_active_files(self) -> List[str]:
        """Get currently active files from Serena."""
        # Mock implementation - replace with actual Serena MCP call
        return []
    
    async def _get_cursor_positions(self) -> Dict[str, int]:
        """Get cursor positions for active files."""
        # Mock implementation
        return {}
    
    async def _get_recent_symbols(self) -> List[str]:
        """Get recently accessed symbols (functions, classes)."""
        # Mock implementation
        return []
    
    async def _get_git_branch(self, workspace_path: str) -> Optional[str]:
        """Get current git branch."""
        try:
            process = await asyncio.create_subprocess_exec(
                'git', 'branch', '--show-current',
                cwd=workspace_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=2.0)
                if process.returncode == 0:
                    return stdout.decode().strip()
            except asyncio.TimeoutError:
                process.kill()
                logger.warning("Git branch command timed out")
        except Exception as e:
            logger.warning(f"Failed to get git branch: {e}")
        return None
    
    async def _generate_mental_model(self, context: PreservedContext) -> str:
        """
        Generate AI summary of what user was working on.
        
        Uses recent decisions + active files to create human-readable summary.
        """
        # Simple heuristic implementation
        parts = []
        
        if context.task_description:
            parts.append(f"Working on: {context.task_description}")
        
        if context.active_files:
            parts.append(f"Editing {len(context.active_files)} files: {', '.join(context.active_files[:3])}")
        
        if context.git_branch:
            parts.append(f"On branch: {context.git_branch}")
        
        if not parts:
            return "No clear task context captured"
        
        return " | ".join(parts)
    
    async def _save_snapshot(self, user_id: str, context: PreservedContext) -> bool:
        """Save context snapshot to disk."""
        try:
            filename = f"{self.storage_path}/{user_id}_latest.json"
            with open(filename, 'w') as f:
                json.dump(context.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False
    
    async def _load_latest_snapshot(self, user_id: str) -> Optional[PreservedContext]:
        """Load most recent context snapshot."""
        try:
            filename = f"{self.storage_path}/{user_id}_latest.json"
            with open(filename, 'r') as f:
                data = json.load(f)
            return PreservedContext.from_dict(data)
        except FileNotFoundError:
            logger.warning(f"No saved context for {user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return None
    
    def _generate_restoration_tips(self, context: PreservedContext) -> List[str]:
        """Generate helpful tips for getting back into flow."""
        tips = []
        
        if context.active_files:
            tips.append(f"💡 Resume editing {context.active_files[0]}")
        
        if context.recent_decisions:
            tips.append(f"📋 Review your last decision: {context.recent_decisions[0].get('summary', '')[:50]}...")
        
        if context.git_branch:
            tips.append(f"🌿 You're on branch: {context.git_branch}")
        
        tips.append("🧘 Take 2 minutes to review your mental model before diving back in")
        
        return tips
