import unittest
import json
import os
import tempfile
from unittest.mock import patch, mock_open
from server.config import load_config, DEFAULT_CONFIG

class TestConfig(unittest.TestCase):
    """Test configuration loading functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "server": {
                "host": "127.0.0.1",
                "port": 12345,
                "backlog": 10
            }
        }

    def test_load_config_with_existing_file(self):
        """Test loading configuration from an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            temp_file = f.name

        try:
            config = load_config(temp_file)
            self.assertEqual(config, self.test_config)
        finally:
            os.unlink(temp_file)

    def test_load_config_creates_default_when_missing(self):
        """Test that default configuration is created when file doesn't exist."""
        non_existent_file = "non_existent_config.json"
        
        # Ensure file doesn't exist
        if os.path.exists(non_existent_file):
            os.unlink(non_existent_file)

        try:
            config = load_config(non_existent_file)
            self.assertEqual(config, DEFAULT_CONFIG)
            
            # Verify file was created
            self.assertTrue(os.path.exists(non_existent_file))
            
            # Verify file contents
            with open(non_existent_file, 'r') as f:
                file_config = json.load(f)
            self.assertEqual(file_config, DEFAULT_CONFIG)
        finally:
            if os.path.exists(non_existent_file):
                os.unlink(non_existent_file)

    def test_load_config_handles_json_decode_error(self):
        """Test that configuration loading handles malformed JSON gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            temp_file = f.name

        try:
            with patch('builtins.print') as mock_print:
                config = load_config(temp_file)
                self.assertEqual(config, DEFAULT_CONFIG)
                mock_print.assert_called()
                # Verify error message was printed
                self.assertTrue(any("Error loading config" in str(call) for call in mock_print.call_args_list))
        finally:
            os.unlink(temp_file)

    def test_load_config_handles_file_permission_error(self):
        """Test that configuration loading handles file permission errors."""
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")
            
            with patch('builtins.print') as mock_print:
                config = load_config("restricted_file.json")
                self.assertEqual(config, DEFAULT_CONFIG)
                mock_print.assert_called()

    def test_default_config_structure(self):
        """Test that default configuration has the expected structure."""
        self.assertIn("server", DEFAULT_CONFIG)
        server_config = DEFAULT_CONFIG["server"]
        self.assertIn("host", server_config)
        self.assertIn("port", server_config)
        self.assertIn("backlog", server_config)
        
        # Verify default values
        self.assertEqual(server_config["host"], "0.0.0.0")
        self.assertEqual(server_config["port"], 25860)
        self.assertEqual(server_config["backlog"], 5)

    def test_load_config_default_path(self):
        """Test loading configuration with default path."""
        default_file = "server_config.json"
        
        # Clean up if exists
        if os.path.exists(default_file):
            os.unlink(default_file)

        try:
            config = load_config()  # Use default path
            self.assertEqual(config, DEFAULT_CONFIG)
            self.assertTrue(os.path.exists(default_file))
        finally:
            if os.path.exists(default_file):
                os.unlink(default_file)

if __name__ == '__main__':
    unittest.main() 