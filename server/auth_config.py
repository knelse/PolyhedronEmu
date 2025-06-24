"""
Authentication configuration for the game server.
"""

import json
import os
from typing import Dict, Any


class AuthConfig:
    """Configuration class for authentication settings."""

    def __init__(self, config_path: str = "auth_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if not exists."""
        default_config = {
            "password_padding": "knelse_polyhedron_emu_",
            "hash_algorithm": "sha256",
            "max_login_length": 50,
            "max_password_length": 100,
            "min_password_length": 1,
            "case_sensitive_login": False,
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_config.update(loaded_config)
                    return default_config
            except (json.JSONDecodeError, IOError) as e:
                print(
                    f"Warning: Failed to load auth config from {self.config_path}: {e}"
                )
                print("Using default configuration")

        # Save default config
        self._save_config(default_config)
        return default_config

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Failed to save auth config to {self.config_path}: {e}")

    @property
    def password_padding(self) -> str:
        """Get the password padding string."""
        return self.config.get("password_padding", "knelse_polyhedron_emu_")

    @property
    def hash_algorithm(self) -> str:
        """Get the hash algorithm."""
        return self.config.get("hash_algorithm", "sha256")

    @property
    def max_login_length(self) -> int:
        """Get maximum login length."""
        return self.config.get("max_login_length", 50)

    @property
    def max_password_length(self) -> int:
        """Get maximum password length."""
        return self.config.get("max_password_length", 100)

    @property
    def min_password_length(self) -> int:
        """Get minimum password length."""
        return self.config.get("min_password_length", 1)

    @property
    def case_sensitive_login(self) -> bool:
        """Get whether login is case sensitive."""
        return self.config.get("case_sensitive_login", False)

    def update_config(self, **kwargs) -> None:
        """Update configuration values."""
        self.config.update(kwargs)
        self._save_config(self.config)


# Global instance
auth_config = AuthConfig()
