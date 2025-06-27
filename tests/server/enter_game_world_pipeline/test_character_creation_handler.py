import sys
import unittest
from unittest.mock import MagicMock, patch
from server.enter_game_world_pipeline.character_creation_handler import (
    character_creation_handler,
)
from server.enter_game_world_pipeline.exceptions import character_creation_exception
from server.logger import server_logger
from data_models.mongodb_models import character_database

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()


class TestCharacterCreationHandler(unittest.TestCase):
    """Test character_creation_handler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_character_db = MagicMock(spec=character_database)
        self.handler = character_creation_handler(self.mock_character_db)
        self.mock_logger = MagicMock(spec=server_logger)
        self.player_index = 0x5000

    def test_create_character_from_packet_success(self):
        """Test successful character creation."""
        test_packet = bytearray(50)
        test_packet[0] = 30

        with patch.object(
            self.handler, "_decode_character_name", return_value="TestChar"
        ):
            self.mock_character_db.character_name_exists.return_value = False
            self.mock_character_db.create_character.return_value = "char_id_123"

            # Should not raise an exception
            self.handler.create_character_from_packet(
                test_packet, "testuser", 1, self.player_index, self.mock_logger
            )

            self.mock_character_db.create_character.assert_called_once()
            self.mock_logger.info.assert_called_once()

    def test_create_character_from_packet_name_exists(self):
        """Test character creation when name already exists."""
        test_packet = bytearray(50)
        test_packet[0] = 30

        with patch.object(
            self.handler, "_decode_character_name", return_value="ExistingChar"
        ):
            self.mock_character_db.character_name_exists.return_value = True

            with self.assertRaises(character_creation_exception) as cm:
                self.handler.create_character_from_packet(
                    test_packet, "testuser", 1, self.player_index, self.mock_logger
                )

            self.assertIn(
                "tried to create character with existing name", str(cm.exception)
            )
            self.mock_character_db.create_character.assert_not_called()

    def test_create_character_from_packet_db_failure(self):
        """Test character creation when database save fails."""
        test_packet = bytearray(50)
        test_packet[0] = 30

        with patch.object(
            self.handler, "_decode_character_name", return_value="TestChar"
        ):
            self.mock_character_db.character_name_exists.return_value = False
            self.mock_character_db.create_character.return_value = None  # DB failure

            with self.assertRaises(character_creation_exception) as cm:
                self.handler.create_character_from_packet(
                    test_packet, "testuser", 1, self.player_index, self.mock_logger
                )

            self.assertIn("failed to save character", str(cm.exception))

    def test_create_character_from_packet_exception(self):
        """Test character creation with exception."""
        test_packet = bytearray(50)
        test_packet[0] = 30

        with patch.object(
            self.handler, "_decode_character_name", side_effect=Exception("Test error")
        ):
            with self.assertRaises(character_creation_exception) as cm:
                self.handler.create_character_from_packet(
                    test_packet, "testuser", 1, self.player_index, self.mock_logger
                )

            self.assertIn("Error creating character", str(cm.exception))
            self.assertIn("Test error", str(cm.exception))

    def test_decode_character_name(self):
        """Test character name decoding."""
        # This test verifies the actual name decoding logic
        test_packet = bytearray(50)
        test_packet[0] = 30
        # Set up some test data for name decoding
        test_packet[20] = 0x40  # Example character data
        test_packet[21] = 0x80

        result = self.handler._decode_character_name(test_packet)
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
