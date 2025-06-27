import json
import os
import logging
from typing import Dict, Any


DEFAULT_CONFIG = {"server": {"host": "0.0.0.0", "port": 25860, "backlog": 5}}


def load_config(config_path: str = "server_config.json") -> dict:
    """
    Load server configuration from a JSON file.
    Creates default config if file doesn't exist.
    Falls back to defaults if there's an error.
    """
    try:
        if not os.path.exists(config_path):
            with open(config_path, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG

        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger = logging.getLogger("config")
        logger.error(f"Error loading config, using defaults: {str(e)}")
        return DEFAULT_CONFIG.copy()


class server_config:
    def __init__(self, config_path: str = "server_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_path):

            try:
                with open(self.config_path, "r") as file:
                    return json.load(file)
            except Exception:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()
