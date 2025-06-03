import json
import os
from typing import Dict, Any


DEFAULT_CONFIG = {
    "server": {
        "host": "127.0.0.1",
        "port": 6500
    }
}


class ServerConfig:
    def __init__(self, config_path: str = "server_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_path):

            try:
                with open(self.config_path, 'r') as file:
                    return json.load(file)
            except Exception:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()
