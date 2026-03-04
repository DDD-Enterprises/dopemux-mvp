"""LiteLLM process management for Dopemux.

Centralized manager for direct LiteLLM process control, replacing Docker-based
management with native subprocess handling.
"""

from __future__ import annotations

import logging
import os
import secrets
import signal
import socket
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import yaml

logger = logging.getLogger(__name__)


class LiteLLMManagerError(RuntimeError):
    """Raised when LiteLLM process management fails."""


class LiteLLMProcessInfo:
    """Holds information about a running LiteLLM process."""
    
    def __init__(
        self,
        instance_id: str,
        port: int,
        config_path: Path,
        log_path: Path,
        master_key: str,
        process: subprocess.Popen,
        db_enabled: bool = False,
        db_url: Optional[str] = None,
    ):
        self.instance_id = instance_id
        self.port = port
        self.config_path = config_path
        self.log_path = log_path
        self.master_key = master_key
        self.process = process
        self.db_enabled = db_enabled
        self.db_url = db_url
        self.start_time = datetime.now()
        self.last_health_check = datetime.now()
        self.healthy = False
        
    @property
    def base_url(self) -> str:
        """Return the HTTP base URL for the proxy."""
        return f"http://127.0.0.1:{self.port}"
    
    def update_health(self, is_healthy: bool) -> None:
        """Update the health status of this process."""
        self.healthy = is_healthy
        self.last_health_check = datetime.now()


class LiteLLMHealthMonitor:
    """Background health monitoring for LiteLLM processes."""
    
    def __init__(self, manager: LiteLLMManager):
        self.manager = manager
        self._stop_event = threading.Event()
        self._monitor_interval = 30.0  # seconds
        self._thread = self._create_thread()

    def _create_thread(self) -> threading.Thread:
        """Create a fresh monitor thread for each start cycle."""
        return threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="LiteLLMHealthMonitor"
        )
        
    def start(self) -> None:
        """Start the health monitoring thread."""
        if self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = self._create_thread()
        self._thread.start()
        logger.info("🔄 LiteLLM health monitor started")
    
    def stop(self) -> None:
        """Stop the health monitoring thread."""
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("⏹️  LiteLLM health monitor stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                self._check_all_processes()
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
            
            # Sleep for interval or until stop event
            for _ in range(int(self._monitor_interval * 2)):  # Check every 0.5s
                if self._stop_event.is_set():
                    break
                time.sleep(0.5)
    
    def _check_all_processes(self) -> None:
        """Check health of all managed LiteLLM processes."""
        processes = []
        with self.manager._lock:
            processes = list(self.manager._processes.items())
            
        for instance_id, process_info in processes:
            try:
                is_healthy = self._check_process_health(process_info)
                process_info.update_health(is_healthy)
                
                if not is_healthy:
                    logger.warning(f"⚠️  LiteLLM instance {instance_id} unhealthy")
                    self._attempt_recovery(process_info)
            except Exception as e:
                logger.error(f"Error checking health for {instance_id}: {e}")
    
    def _check_process_health(self, process_info: LiteLLMProcessInfo) -> bool:
        """Check if a LiteLLM process is healthy."""
        try:
            # First check if process is still running
            if process_info.process.poll() is not None:
                return False
            
            # Check HTTP health endpoint
            import urllib.request
            url = f"{process_info.base_url}/health/readiness"
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    def _attempt_recovery(self, process_info: LiteLLMProcessInfo) -> None:
        """Attempt to recover an unhealthy process."""
        try:
            logger.info(f"🔄 Attempting recovery for LiteLLM instance {process_info.instance_id}")
            
            # Terminate the unhealthy process
            if process_info.process.poll() is None:
                try:
                    process_info.process.terminate()
                    process_info.process.wait(timeout=5)
                except Exception as te:
                    logger.warning(f"Error terminating process during recovery: {te}")
            
            # Use manager's lock for consistent state
            with self.manager._lock:
                # Remove from active processes if still there
                if self.manager._processes.get(process_info.instance_id) is process_info:
                    del self.manager._processes[process_info.instance_id]
                
                # Load configuration data back from the file if we want to restart
                # But wait, start_instance handles everything including config preparation.
                # However, start_instance expects config_data (dict), not config_path.
                # Let's read the existing config file back into a dict.
                try:
                    with open(process_info.config_path, 'r') as f:
                        config_data = yaml.safe_load(f)
                except Exception as ce:
                    logger.error(f"Failed to load config for recovery: {ce}")
                    return

                # Attempt to restart - we must not hold the lock while calling start_instance
                # because start_instance will try to acquire it.
            
            # Restart outside the lock
            self.manager.start_instance(
                instance_id=process_info.instance_id,
                port=process_info.port,
                config_data=config_data,
                db_enabled=process_info.db_enabled,
                db_url=process_info.db_url
            )
            
        except Exception as e:
            logger.error(f"Recovery failed for {process_info.instance_id}: {e}")


class LiteLLMManager:
    """Centralized manager for LiteLLM processes.
    
    Replaces Docker-based management with direct subprocess control.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self._processes: Dict[str, LiteLLMProcessInfo] = {}
        self._health_monitor = LiteLLMHealthMonitor(self)
        self._lock = threading.Lock()
        
    def start(self) -> None:
        """Start the health monitoring system."""
        self._health_monitor.start()
    
    def stop(self) -> None:
        """Stop all managed processes and monitoring."""
        self._health_monitor.stop()
        self.stop_all_instances()
    
    def start_instance(
        self,
        instance_id: str,
        port: int,
        config_data: Dict[str, Any],
        db_enabled: bool = False,
        db_url: Optional[str] = None,
    ) -> LiteLLMProcessInfo:
        """Start a LiteLLM instance with the given configuration.
        
        Args:
            instance_id: Identifier for this instance
            port: Port to run the LiteLLM proxy on
            config_data: LiteLLM configuration dictionary
            db_enabled: Whether to enable database support
            db_url: Database URL if db_enabled is True
            
        Returns:
            LiteLLMProcessInfo object with process details
            
        Raises:
            LiteLLMManagerError: If the instance cannot be started
        """
        with self._lock:
            # Check if instance already exists
            if instance_id in self._processes:
                existing = self._processes[instance_id]
                if existing.process.poll() is None:
                    raise LiteLLMManagerError(f"Instance {instance_id} already running")
                else:
                    # Clean up dead process
                    del self._processes[instance_id]
            
            # Prepare instance directory
            instance_dir = self._get_instance_dir(instance_id)
            instance_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate/load master key
            master_key = self._ensure_master_key(instance_dir)
            
            # Prepare configuration
            config_path = self._prepare_config(instance_dir, config_data, master_key, db_enabled, db_url)
            
            # Set up logging
            log_path = instance_dir / "litellm.log"
            
            # Check if port is available
            if self._is_port_in_use(port):
                raise LiteLLMManagerError(f"Port {port} is already in use")
            
            # Launch the process
            process = self._launch_process(config_path, log_path, port, master_key, db_enabled, db_url)
            
            # Create process info object
            process_info = LiteLLMProcessInfo(
                instance_id=instance_id,
                port=port,
                config_path=config_path,
                log_path=log_path,
                master_key=master_key,
                process=process,
                db_enabled=db_enabled,
                db_url=db_url,
            )
            
            # Wait for health
            if not self._wait_for_health(process_info, timeout=30.0):
                process.terminate()
                raise LiteLLMManagerError(f"LiteLLM instance {instance_id} failed to become healthy")
            
            # Add to active processes
            self._processes[instance_id] = process_info
            
            return process_info
    
    def stop_instance(self, instance_id: str) -> bool:
        """Stop a running LiteLLM instance.
        
        Args:
            instance_id: Identifier for the instance to stop
            
        Returns:
            True if instance was stopped, False if it wasn't running
        """
        with self._lock:
            if instance_id not in self._processes:
                return False
            
            process_info = self._processes[instance_id]
            
            try:
                # Terminate process
                if process_info.process.poll() is None:
                    process_info.process.terminate()
                    process_info.process.wait(timeout=10)
                
                # Remove from active processes
                del self._processes[instance_id]
                
                return True
            except Exception as e:
                logger.error(f"Error stopping instance {instance_id}: {e}")
                return False
    
    def stop_all_instances(self) -> None:
        """Stop all running LiteLLM instances."""
        with self._lock:
            instance_ids = list(self._processes.keys())

        for instance_id in instance_ids:
            self.stop_instance(instance_id)
    
    def get_instance(self, instance_id: str) -> Optional[LiteLLMProcessInfo]:
        """Get information about a running instance.
        
        Args:
            instance_id: Identifier for the instance
            
        Returns:
            LiteLLMProcessInfo if instance is running, None otherwise
        """
        with self._lock:
            return self._processes.get(instance_id)
    
    def get_all_instances(self) -> List[LiteLLMProcessInfo]:
        """Get information about all running instances.
        
        Returns:
            List of all running LiteLLMProcessInfo objects
        """
        with self._lock:
            return list(self._processes.values())
    
    def build_client_environment(self, instance_id: str) -> Dict[str, str]:
        """Build environment variables for a client to use a specific instance.
        
        Args:
            instance_id: Identifier for the instance
            
        Returns:
            Dictionary of environment variables
            
        Raises:
            LiteLLMManagerError: If instance is not running
        """
        with self._lock:
            if instance_id not in self._processes:
                raise LiteLLMManagerError(f"Instance {instance_id} is not running")
            
            process_info = self._processes[instance_id]
            
            env_vars = {
                "OPENAI_API_BASE": process_info.base_url,
                "OPENAI_BASE_URL": process_info.base_url,
                "OPENAI_API_KEY": process_info.master_key,
                "ANTHROPIC_API_BASE": process_info.base_url,
                "ANTHROPIC_BASE_URL": process_info.base_url,
                "ANTHROPIC_API_KEY": process_info.master_key,
                "DOPEMUX_CLAUDE_VIA_LITELLM": "1",
                "DOPEMUX_LITELLM_MASTER_KEY": process_info.master_key,
                "DOPEMUX_LITELLM_PORT": str(process_info.port),
                "LITELLM_PROXY_URL": process_info.base_url,
                "LITELLM_MASTER_KEY": process_info.master_key,
            }
            
            if process_info.db_enabled and process_info.db_url:
                env_vars["DOPEMUX_LITELLM_DB_URL"] = process_info.db_url
                env_vars["LITELLM_DATABASE_URL"] = process_info.db_url
                env_vars["DATABASE_URL"] = process_info.db_url
            
            # Preserve provider keys
            provider_keys = ["ANTHROPIC_API_KEY", "XAI_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY"]
            for key in provider_keys:
                if key in os.environ:
                    env_vars[f"DOPEMUX_PROVIDER_{key}"] = os.environ[key]
            
            return env_vars
    
    def _get_instance_dir(self, instance_id: str) -> Path:
        """Get the directory for a LiteLLM instance."""
        return self.project_root / ".dopemux" / "litellm" / instance_id
    
    def _ensure_master_key(self, instance_dir: Path) -> str:
        """Ensure a master key exists for the instance."""
        key_path = instance_dir / "master.key"
        
        # Check existing key
        if key_path.exists():
            try:
                existing_key = key_path.read_text().strip()
                if existing_key.startswith("sk-"):
                    return existing_key
            except Exception as e:
                logger.warning(f"Error reading existing master key: {e}")
        
        # Generate new key
        random_part = secrets.token_urlsafe(24).replace("-", "").replace("_", "")[:24]
        new_key = f"sk-master-dopemux-local-{random_part}"
        
        try:
            key_path.write_text(new_key)
        except Exception as e:
            logger.warning(f"Error writing master key: {e}")
        
        return new_key
    
    def _prepare_config(
        self,
        instance_dir: Path,
        config_data: Dict[str, Any],
        master_key: str,
        db_enabled: bool,
        db_url: Optional[str],
    ) -> Path:
        """Prepare the LiteLLM configuration file."""
        config_path = instance_dir / "litellm.config.yaml"
        
        # Set master key
        general_settings = config_data.setdefault("general_settings", {})
        general_settings["master_key"] = master_key
        
        # Handle database configuration
        if db_enabled and db_url:
            general_settings["database_url"] = db_url
        else:
            general_settings.pop("database_url", None)
        
        # Write configuration
        try:
            config_path.write_text(
                yaml.safe_dump(config_data, sort_keys=False, default_flow_style=False)
            )
            return config_path
        except Exception as e:
            raise LiteLLMManagerError(f"Failed to write configuration: {e}")
    
    def _launch_process(
        self,
        config_path: Path,
        log_path: Path,
        port: int,
        master_key: str,
        db_enabled: bool,
        db_url: Optional[str],
    ) -> subprocess.Popen:
        """Launch the LiteLLM process."""
        # Prepare environment
        env = os.environ.copy()
        env["LITELLM_MASTER_KEY"] = master_key
        
        if db_enabled and db_url:
            env["DATABASE_URL"] = db_url
        else:
            env["LITELLM_DISABLE_DB"] = "true"
            env["LITELLM_DISABLE_SPEND_LOGGING"] = "true"
        
        # Prepare command
        cmd = [
            "litellm",
            "--config", str(config_path),
            "--port", str(port),
            "--host", "127.0.0.1",
        ]
        
        # Open log file
        log_file = open(log_path, "a", encoding="utf-8")
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            
            return process
        except Exception as e:
            log_file.close()
            raise LiteLLMManagerError(f"Failed to launch LiteLLM process: {e}")
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.bind(("127.0.0.1", port))
                return False
        except (OSError, socket.error):
            return True
    
    def _wait_for_health(self, process_info: LiteLLMProcessInfo, timeout: float = 30.0) -> bool:
        """Wait for a LiteLLM process to become healthy."""
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            try:
                import urllib.request
                url = f"{process_info.base_url}/health/readiness"
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status == 200:
                        process_info.update_health(True)
                        return True
            except Exception:
                pass
            
            time.sleep(0.5)
        
        return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all managed instances."""
        status = {}
        
        with self._lock:
            for instance_id, process_info in self._processes.items():
                status[instance_id] = {
                    "port": process_info.port,
                    "healthy": process_info.healthy,
                    "last_health_check": process_info.last_health_check.isoformat(),
                    "start_time": process_info.start_time.isoformat(),
                    "db_enabled": process_info.db_enabled,
                }
        
        return status


# Global singleton instance
_litellm_manager: Optional[LiteLLMManager] = None
_manager_lock = threading.Lock()


def get_litellm_manager(project_root: Optional[Path] = None) -> LiteLLMManager:
    """Get the global LiteLLM manager instance.
    
    Args:
        project_root: Optional project root path. If None, uses current working directory.
        
    Returns:
        The global LiteLLMManager instance
    """
    global _litellm_manager
    
    with _manager_lock:
        if _litellm_manager is None:
            if project_root is None:
                project_root = Path.cwd()
            _litellm_manager = LiteLLMManager(project_root)
    
    return _litellm_manager
