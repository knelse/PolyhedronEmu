import os
import json

DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 25860,
        "backlog": 5
    }
}

def load_config(config_path: str = "server_config.json") -> dict:
    """
    Load server configuration from a JSON file.
    Creates default config if file doesn't exist.
    Falls back to defaults if there's an error.
    """
    try:
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG
        
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config, using defaults: {str(e)}")
        return DEFAULT_CONFIG.copy() 