import sys
import unittest
from unittest.mock import MagicMock, patch
from server.enter_game_world_pipeline.character_screen_handler import (
    CharacterScreenHandler,
)
from server.enter_game_world_pipeline.exceptions import CharacterScreenException
from server.logger import ServerLogger
from server.client_state_manager import ClientStateManager
from data_models.mongodb_models import CharacterDatabase
from server.packets import ServerPackets

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()


class TestCharacterScreenHandler(unittest.TestCase):
    """Test CharacterScreenHandler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=ServerLogger)
        self.mock_state_manager = MagicMock(spec=ClientStateManager)
        self.mock_character_db = MagicMock(spec=CharacterDatabase)
        self.handler = CharacterScreenHandler(self.mock_character_db)
        self.player_index = 0x5000
        self.mock_socket = MagicMock()

    def test_wait_for_character_screen_interaction_select_character(self):
        """Test character selection interaction."""
        select_packet = bytearray(50)
        select_packet[0] = 0x15  # Character select packet
        select_packet[17] = 0x04  # Character slot (4//4 - 1 = 0)

        self.mock_state_manager.get_user_id.return_value = "testuser"

        # Mock database to return existing character
        mock_character = {"name": "TestChar", "user_id": "testuser"}
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = mock_character
        self.mock_character_db.characters = mock_collection

        patch_path = (
            "server.enter_game_world_pipeline.character_screen_handler."
            "ServerSocketUtils.receive_packet_with_logging"
        )
        with patch(patch_path, return_value=select_packet):
            result = self.handler.wait_for_character_screen_interaction(
                self.mock_socket,
                self.player_index,
                self.mock_logger,
                self.mock_state_manager,
            )

            self.assertEqual(
                result, 0
            )  # Should return character slot index (4//4 - 1 = 0)
            self.mock_logger.info.assert_called()

            # Verify the database was queried correctly
            mock_collection.find_one.assert_called_once_with(
                {
                    "user_id": "testuser",
                    "character_slot_index": 0,
                    "is_not_queued_for_deletion": True,
                }
            )

    def test_wait_for_character_screen_interaction_select_nonexistent_character(self):
        """Test character selection when character doesn't exist."""
        select_packet = bytearray(50)
        select_packet[0] = 0x15  # Character select packet
        select_packet[17] = 0x08  # Character slot (8//4 - 1 = 1)

        self.mock_state_manager.get_user_id.return_value = "testuser"

        # Mock database to return None (character doesn't exist)
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        self.mock_character_db.characters = mock_collection

        patch_path = (
            "server.enter_game_world_pipeline.character_screen_handler."
            "ServerSocketUtils.receive_packet_with_logging"
        )
        with patch(patch_path, return_value=select_packet):
            with self.assertRaises(CharacterScreenException) as cm:
                self.handler.wait_for_character_screen_interaction(
                    self.mock_socket,
                    self.player_index,
                    self.mock_logger,
                    self.mock_state_manager,
                )

            self.assertIn("tried to select non-existent character", str(cm.exception))
            self.assertIn("slot 1", str(cm.exception))

    def test_wait_for_character_screen_interaction_create_character(self):
        """Test character creation interaction."""
        create_packet = bytearray(50)
        create_packet[0] = 30  # Packet length
        create_packet[13] = 0x08  # Required byte
        create_packet[14] = 0x40  # Required byte
        create_packet[15] = 0x80  # Required byte
        create_packet[16] = 0x05  # Required byte
        create_packet[17] = 0x04  # Character slot (4//4 - 1 = 0)

        self.mock_state_manager.get_user_id.return_value = "testuser"

        patch_path = (
            "server.enter_game_world_pipeline.character_screen_handler."
            "ServerSocketUtils.receive_packet_with_logging"
        )
        with patch(patch_path, return_value=create_packet):
            with patch.object(
                self.handler.character_creator,
                "create_character_from_packet",
                return_value=None,  # Success (no exception)
            ):
                with patch(
                    "server.enter_game_world_pipeline.character_screen_handler."
                    "ServerSocketUtils.send_packet_or_cleanup",
                    return_value=True,
                ) as mock_send:
                    result = self.handler.wait_for_character_screen_interaction(
                        self.mock_socket,
                        self.player_index,
                        self.mock_logger,
                        self.mock_state_manager,
                    )

                    self.assertEqual(result, 0)  # Should return character slot index
                    self.mock_logger.info.assert_called()

                    # Verify the actual packet sent is the character name check success
                    mock_send.assert_called_once()
                    sent_packet = mock_send.call_args[0][1]
                    expected_packet = ServerPackets.character_name_check_success(
                        self.player_index
                    )
                    self.assertEqual(sent_packet, expected_packet)

    def test_wait_for_character_screen_interaction_create_character_name_taken(self):
        """Test character creation when name is already taken."""
        create_packet = bytearray(50)
        create_packet[0] = 30  # Packet length
        create_packet[13] = 0x08  # Required byte
        create_packet[14] = 0x40  # Required byte
        create_packet[15] = 0x80  # Required byte
        create_packet[16] = 0x05  # Required byte
        create_packet[17] = 0x04  # Character slot (4//4 - 1 = 0)

        self.mock_state_manager.get_user_id.return_value = "testuser"

        patch_path = (
            "server.enter_game_world_pipeline.character_screen_handler."
            "ServerSocketUtils.receive_packet_with_logging"
        )
        with patch(patch_path, return_value=create_packet):
            with patch.object(
                self.handler.character_creator,
                "create_character_from_packet",
                side_effect=Exception("Name already taken"),  # Character creation fails
            ):
                with patch(
                    "server.enter_game_world_pipeline.character_screen_handler."
                    "ServerSocketUtils.send_packet_or_cleanup",
                    return_value=True,
                ) as mock_send:
                    with self.assertRaises(CharacterScreenException) as cm:
                        self.handler.wait_for_character_screen_interaction(
                            self.mock_socket,
                            self.player_index,
                            self.mock_logger,
                            self.mock_state_manager,
                        )

                    self.assertIn("Character creation failed", str(cm.exception))

                    # Verify the actual packet sent is the character name already taken
                    mock_send.assert_called_once()
                    sent_packet = mock_send.call_args[0][1]
                    expected_packet = ServerPackets.character_name_already_taken(
                        self.player_index
                    )
                    self.assertEqual(sent_packet, expected_packet)

    def test_wait_for_character_screen_interaction_invalid_packet(self):
        """Test invalid packet handling."""
        invalid_packet = bytearray(10)  # Too short
        invalid_packet[0] = 0x99  # Invalid packet type

        patch_path = (
            "server.enter_game_world_pipeline.character_screen_handler."
            "ServerSocketUtils.receive_packet_with_logging"
        )
        with patch(patch_path, side_effect=[invalid_packet, None]):  # Invalid then None
            with self.assertRaises(CharacterScreenException) as cm:
                self.handler.wait_for_character_screen_interaction(
                    self.mock_socket,
                    self.player_index,
                    self.mock_logger,
                    self.mock_state_manager,
                )

            self.assertIn("Failed to receive character screen data", str(cm.exception))

    def test_wait_for_character_screen_interaction_no_data(self):
        """Test when no data is received."""
        patch_path = (
            "server.enter_game_world_pipeline.character_screen_handler."
            "ServerSocketUtils.receive_packet_with_logging"
        )
        with patch(patch_path, return_value=None):
            with self.assertRaises(CharacterScreenException) as cm:
                self.handler.wait_for_character_screen_interaction(
                    self.mock_socket,
                    self.player_index,
                    self.mock_logger,
                    self.mock_state_manager,
                )

            self.assertIn("Failed to receive character screen data", str(cm.exception))

    def test_wait_for_character_screen_interaction_exception(self):
        """Test exception during character screen interaction."""
        patch_path = (
            "server.enter_game_world_pipeline.character_screen_handler."
            "ServerSocketUtils.receive_packet_with_logging"
        )
        with patch(patch_path, side_effect=Exception("Test error")):
            with self.assertRaises(CharacterScreenException) as cm:
                self.handler.wait_for_character_screen_interaction(
                    self.mock_socket,
                    self.player_index,
                    self.mock_logger,
                    self.mock_state_manager,
                )

            self.assertIn(
                "Error waiting for character screen interaction", str(cm.exception)
            )
            self.assertIn("Test error", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
