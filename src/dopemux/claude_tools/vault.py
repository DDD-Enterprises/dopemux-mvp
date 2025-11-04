"""
Vault Integration for Claude-Code-Tools

Provides encrypted environment backup and sync functionality using SOPS.

Based on Claude-Code-Tools vault patterns.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# For SOPS integration, we need to install sops
try:
    from sops import SOPSFile
    SOPS_AVAILABLE = True
except ImportError:
    SOPS_AVAILABLE = False
    logging.warning("SOPS not available. Vault encryption disabled.")

logger = logging.getLogger(__name__)


class VaultError(Exception):
    """Raised when vault operations fail."""
    pass


class Vault:
    """
    Encrypted environment vault management.

    Provides backup and sync functionality for .env files using SOPS.
    """

    def __init__(self, vault_dir: str = ".vault", sops_config: Optional[str] = None):
        """
        Initialize vault.

        Args:
            vault_dir: Directory for vault files
            sops_config: Path to SOPS configuration file
        """
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(exist_ok=True)
        self.sops_config = sops_config or "~/.sops.yaml"

        if not SOPS_AVAILABLE:
            logger.warning("SOPS not available. Vault functionality limited.")

    def encrypt_env(self, env_file: str = ".env") -> bool:
        """
        Encrypt .env file to vault.

        Args:
            env_file: Path to .env file

        Returns:
            True if successful, False otherwise
        """
        if not SOPS_AVAILABLE:
            logger.error("SOPS not available for encryption")
            return False

        try:
            env_path = Path(env_file)
            if not env_path.exists():
                logger.error(f"Environment file not found: {env_file}")
                return False

            vault_file = self.vault_dir / f"{env_path.stem}.yaml"

            # Load SOPS configuration
            sops_file = SOPSFile.load(self.sops_config)

            # Read .env file
            with open(env_path, 'r') as f:
                env_content = f.read()

            # Create SOPS data
            sops_data = {
                'env_content': env_content,
                'timestamp': str(datetime.now()),
                'vault_version': '1.0.0'
            }

            # Encrypt and write to vault
            sops_file.load_data(sops_data)
            sops_file.to_file(str(vault_file))

            logger.info(f"Encrypted {env_file} to {vault_file}")

            # Remove original .env file for security
            env_path.unlink()

            return True

        except Exception as e:
            logger.error(f"Failed to encrypt env file: {e}")
            return False

    def decrypt_env(self, vault_file: str = None) -> Optional[str]:
        """
        Decrypt vault file to .env.

        Args:
            vault_file: Path to vault file (default: .vault/.env.yaml)

        Returns:
            Decrypted content or None if failed
        """
        if not SOPS_AVAILABLE:
            logger.error("SOPS not available for decryption")
            return None

        try:
            if vault_file is None:
                vault_path = self.vault_dir / ".env.yaml"
            else:
                vault_path = Path(vault_file)

            if not vault_path.exists():
                logger.error(f"Vault file not found: {vault_path}")
                return None

            # Load and decrypt SOPS file
            sops_file = SOPSFile.load(str(vault_path))
            decrypted_data = sops_file.decrypted_data

            # Extract env content
            env_content = decrypted_data.get('env_content')

            if env_content:
                # Write to .env file
                env_path = Path(".env")
                with open(env_path, 'w') as f:
                    f.write(env_content)

                logger.info(f"Decrypted {vault_path} to {env_path}")
                return env_content

            return None

        except Exception as e:
            logger.error(f"Failed to decrypt vault file: {e}")
            return None

    def sync_env(self, env_file: str = ".env") -> bool:
        """
        Sync environment file to vault (encrypt if changed).

        Args:
            env_file: Path to .env file

        Returns:
            True if synced, False otherwise
        """
        try:
            env_path = Path(env_file)
            vault_file = self.vault_dir / f"{env_path.stem}.yaml"

            if not env_path.exists():
                logger.warning(f"Environment file not found: {env_file}")
                return False

            # Check if needs sync (simple timestamp check)
            if vault_file.exists() and env_path.stat().st_mtime < vault_file.stat().st_mtime:
                logger.info("Environment file up to date")
                return True

            # Encrypt and update vault
            return self.encrypt_env(env_file)

        except Exception as e:
            logger.error(f"Failed to sync env file: {e}")
            return False

    def list_vaults(self) -> List[str]:
        """
        List all vault files.

        Returns:
            List of vault file paths
        """
        vaults = []

        if self.vault_dir.exists():
            for vault_file in self.vault_dir.glob("*.yaml"):
                vaults.append(str(vault_file))

        return vaults