"""
Checkpoint Manager - Step 5 of Phase 1
Auto-save system for ADHD context preservation

Saves to ConPort every 30 seconds to prevent context loss.
Research shows ADHD interruptions occur every 3-6 minutes,
so 30s ensures max 30s of lost work.

Complexity: 0.40 (Medium)
Effort: 4 focus blocks (100 minutes)
"""

from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import time
import json
import subprocess
from .conport_client import get_conport_client


@dataclass
class Checkpoint:
    """
    Complete session state snapshot.

    Everything needed to restore session after interruption.
    """

    session_id: str
    timestamp: datetime
    mode: str  # Current workflow mode (research, plan, implement)
    energy_level: str  # Current energy state
    active_agents: list[dict]  # Which agents running + their state
    chat_history: list[dict]  # Recent conversation (last 15 messages)
    open_files: list[str]  # Files being worked on
    cursor_positions: dict[str, dict]  # File -> line/column
    pending_tasks: list[dict]  # Unfinished tasks
    session_duration_seconds: int  # How long session has been active
    last_activity: datetime  # Last user interaction


class CheckpointManager:
    """
    ADHD-optimized auto-save system.

    Saves complete session state to ConPort every 30 seconds.
    Enables instant recovery after interruptions.
    """

    def __init__(
        self,
        workspace_id: str,
        session_id: str,
        checkpoint_interval: int = 30,
    ):
        """
        Initialize checkpoint manager.

        Args:
            workspace_id: ConPort workspace ID
            session_id: Unique session identifier
            checkpoint_interval: Seconds between auto-saves (default: 30)
        """
        self.workspace_id = workspace_id
        self.session_id = session_id
        self.checkpoint_interval = checkpoint_interval

        self.session_start = datetime.now()
        self.checkpoint_count = 0
        self.auto_save_thread: Optional[threading.Thread] = None
        self.running = False

        # State to checkpoint
        self.current_mode = "chat"
        self.current_energy = "medium"
        self.active_agents: list[dict] = []
        self.chat_history: list[dict] = []
        self.open_files: list[str] = []
        self.cursor_positions: dict = {}
        self.pending_tasks: list[dict] = []

    def start_auto_save(self) -> None:
        """Start auto-save background thread."""
        if self.auto_save_thread and self.auto_save_thread.is_alive():
            print("⚠️ Auto-save already running")
            return

        self.running = True
        self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self.auto_save_thread.start()

        print(f"💾 Auto-save started (every {self.checkpoint_interval}s)")

    def stop_auto_save(self) -> None:
        """Stop auto-save thread."""
        self.running = False
        if self.auto_save_thread:
            self.auto_save_thread.join(timeout=2)

        print("🛑 Auto-save stopped")

    def _auto_save_loop(self) -> None:
        """Background auto-save loop."""
        while self.running:
            time.sleep(self.checkpoint_interval)

            try:
                self.save_checkpoint()
            except Exception as e:
                print(f"⚠️ Checkpoint failed: {e}")

    def save_checkpoint(self, verbose: bool = False) -> str:
        """
        Save current state to ConPort.

        Args:
            verbose: Print detailed save message

        Returns:
            Checkpoint ID

        ADHD Benefit:
            Prevents 23-minute context recovery cost.
            Max 30s of work lost vs 23+ minutes to rebuild mental model.
        """
        # Create checkpoint
        session_duration = (datetime.now() - self.session_start).total_seconds()

        checkpoint = Checkpoint(
            session_id=self.session_id,
            timestamp=datetime.now(),
            mode=self.current_mode,
            energy_level=self.current_energy,
            active_agents=self.active_agents.copy(),
            chat_history=self.chat_history[-15:],  # Last 15 messages
            open_files=self.open_files.copy(),
            cursor_positions=self.cursor_positions.copy(),
            pending_tasks=self.pending_tasks.copy(),
            session_duration_seconds=int(session_duration),
            last_activity=datetime.now(),
        )

        # Save to ConPort
        checkpoint_id = self._save_to_conport(checkpoint)

        self.checkpoint_count += 1

        if verbose:
            print(
                f"💾 Checkpoint #{self.checkpoint_count} saved "
                f"(session: {int(session_duration / 60)}m)"
            )
        else:
            # Subtle feedback - just icon
            print("💾", end="", flush=True)

        return checkpoint_id

    def _save_to_conport(self, checkpoint: Checkpoint) -> str:
        """
        Save checkpoint to ConPort custom_data.

        Args:
            checkpoint: Checkpoint to save

        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"checkpoint_{self.session_id}_{checkpoint.timestamp.timestamp()}"

        try:
            # Use ConPort MCP for persistent storage
            # Note: This requires ConPort MCP to be available
            # For MVP, we'll try ConPort first, fall back to JSON

            # Attempt ConPort save (will implement MCP call when integrated)
            # For now, keep JSON as reliable fallback

            checkpoint_file = f"/tmp/dopemux_checkpoint_{self.session_id}_latest.json"
            with open(checkpoint_file, "w") as f:
                json.dump(asdict(checkpoint), f, indent=2, default=str)

            # Real ConPort MCP integration
            # Save to ConPort for persistence across sessions
            self._save_to_conport_mcp(checkpoint_id, checkpoint)

        except Exception as e:
            print(f"⚠️ Checkpoint save error: {e}")
            # Fail gracefully - ADHD accommodation (don't break flow)

        return checkpoint_id

    def _save_to_conport_mcp(self, checkpoint_id: str, checkpoint: Checkpoint) -> None:
        """
        Save checkpoint to ConPort via MCP.

        Uses mcp__conport__log_custom_data for persistent storage.

        Args:
            checkpoint_id: Unique checkpoint identifier
            checkpoint: Checkpoint data to save
        """
        try:
            # Prepare checkpoint data
            checkpoint_data = asdict(checkpoint)

            # Convert datetime objects to ISO strings for JSON serialization
            checkpoint_data["timestamp"] = checkpoint.timestamp.isoformat()
            checkpoint_data["last_activity"] = checkpoint.last_activity.isoformat()

            # Use ConPort client (supports both HTTP and MCP modes)
            client = get_conport_client(self.workspace_id)
            result = client.log_custom_data(
                category="adhd_checkpoints",
                key=checkpoint_id,
                value=checkpoint_data
            )

            if result.get("success"):
                print(f"✅ Checkpoint saved to ConPort ({result.get('mode', 'unknown')} mode)")
            else:
                print(f"⚠️ ConPort save failed: {result.get('error', 'unknown')}")

        except Exception as e:
            # Silent failure - JSON file is already saved as fallback
            print(f"⚠️ ConPort integration error: {e}")

    def load_latest_checkpoint(self) -> Optional[Checkpoint]:
        """
        Load most recent checkpoint for this session.

        Returns:
            Latest checkpoint or None if no checkpoints exist

        ADHD Benefit:
            Instant session restoration - no "what was I doing?" anxiety
        """
        # Try ConPort first, fall back to JSON
        checkpoint = self._load_from_conport_mcp()

        if checkpoint:
            return checkpoint

        # Fallback to JSON file
        checkpoint_file = f"/tmp/dopemux_checkpoint_{self.session_id}_latest.json"

        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)

            # Reconstruct checkpoint
            checkpoint = Checkpoint(
                session_id=data["session_id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                mode=data["mode"],
                energy_level=data["energy_level"],
                active_agents=data["active_agents"],
                chat_history=data["chat_history"],
                open_files=data["open_files"],
                cursor_positions=data["cursor_positions"],
                pending_tasks=data["pending_tasks"],
                session_duration_seconds=data["session_duration_seconds"],
                last_activity=datetime.fromisoformat(data["last_activity"]),
            )

            return checkpoint

        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"⚠️ Failed to load checkpoint: {e}")
            return None

    def _load_from_conport_mcp(self) -> Optional[Checkpoint]:
        """
        Load checkpoint from ConPort via MCP.

        Returns:
            Checkpoint if found, None otherwise
        """
        try:
            # Use ConPort client
            client = get_conport_client(self.workspace_id)
            checkpoints = client.get_custom_data(
                category="adhd_checkpoints",
                limit=1
            )

            if checkpoints and len(checkpoints) > 0:
                data = checkpoints[0]
                # Reconstruct checkpoint with datetime parsing
                checkpoint = Checkpoint(
                    session_id=data["session_id"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    mode=data["mode"],
                    energy_level=data["energy_level"],
                    active_agents=data["active_agents"],
                    chat_history=data["chat_history"],
                    open_files=data["open_files"],
                    cursor_positions=data["cursor_positions"],
                    pending_tasks=data["pending_tasks"],
                    session_duration_seconds=data["session_duration_seconds"],
                    last_activity=datetime.fromisoformat(data["last_activity"]),
                )
                print(f"✅ Checkpoint loaded from ConPort")
                return checkpoint

            return None

        except Exception as e:
            # Silent failure - fall back to JSON
            print(f"⚠️ ConPort load failed: {e}")
            return None

    def update_state(
        self,
        mode: Optional[str] = None,
        energy: Optional[str] = None,
        agents: Optional[list] = None,
        message: Optional[dict] = None,
        files: Optional[list] = None,
    ) -> None:
        """
        Update checkpoint state (called as session progresses).

        Args:
            mode: New mode if changed
            energy: New energy level if changed
            agents: Updated agent list if changed
            message: New chat message to add
            files: Updated file list if changed
        """
        if mode:
            self.current_mode = mode

        if energy:
            self.current_energy = energy

        if agents is not None:
            self.active_agents = agents

        if message:
            self.chat_history.append(message)
            # Keep only last 50 messages
            if len(self.chat_history) > 50:
                self.chat_history = self.chat_history[-50:]

        if files is not None:
            self.open_files = files


if __name__ == "__main__":
    """Test checkpoint manager."""

    print("Testing Checkpoint Manager:")
    print("=" * 60)

    manager = CheckpointManager(
        workspace_id="/Users/hue/code/ui-build",
        session_id="test-session-123",
    )

    # Update state
    manager.update_state(
        mode="implement",
        energy="high",
        agents=[{"name": "claude", "status": "running"}],
        message={"role": "user", "content": "Implement JWT tokens"},
    )

    # Save checkpoint
    checkpoint_id = manager.save_checkpoint(verbose=True)
    print(f"✅ Saved: {checkpoint_id}")

    # Load checkpoint
    loaded = manager.load_latest_checkpoint()
    if loaded:
        print(f"\n✅ Loaded checkpoint:")
        print(f"  Mode: {loaded.mode}")
        print(f"  Energy: {loaded.energy_level}")
        print(f"  Agents: {len(loaded.active_agents)}")
        print(f"  Messages: {len(loaded.chat_history)}")
        print(f"  Duration: {loaded.session_duration_seconds}s")

    # Test auto-save
    print(f"\nStarting auto-save (will save in {manager.checkpoint_interval}s)...")
    manager.start_auto_save()

    print("Simulating work for 65 seconds...")
    for i in range(13):
        time.sleep(5)
        manager.update_state(
            message={"role": "assistant", "content": f"Working... step {i+1}"}
        )
        print(".", end="", flush=True)

    print("\n")
    manager.stop_auto_save()

    print(f"✅ Auto-save test complete ({manager.checkpoint_count} checkpoints saved)")
