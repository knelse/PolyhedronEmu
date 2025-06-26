import sys
import unittest
from unittest.mock import MagicMock, patch
from server.enter_game_world_pipeline.character_data_handler import CharacterDataHandler
from server.enter_game_world_pipeline.exceptions import CharacterDataException
from server.logger import ServerLogger
from data_models.mongodb_models import CharacterDatabase
from server.packets import ServerPackets

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()


class TestCharacterDataHandler(unittest.TestCase):
    """Test CharacterDataHandler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=ServerLogger)
        self.mock_character_db = MagicMock(spec=CharacterDatabase)
        self.player_index = 0x5000
        self.mock_socket = MagicMock()
        self.handler = CharacterDataHandler(self.mock_character_db)

    @patch(
        "server.enter_game_world_pipeline.character_data_handler."
        "ServerSocketUtils.send_packet_or_cleanup"
    )
    def test_send_character_select_and_data_success(self, mock_send_packet):
        """Test successful character select data sending."""
        mock_send_packet.return_value = True

        # Should not raise an exception
        self.handler.send_character_select_and_data(
            self.player_index,
            "testuser",
            self.mock_socket,
            self.mock_logger,
        )

        # Verify both packets were sent
        self.assertEqual(mock_send_packet.call_count, 2)

        # Verify the actual packets sent are the expected ones
        first_call = mock_send_packet.call_args_list[0]
        second_call = mock_send_packet.call_args_list[1]

        # First call should be character select start data
        expected_char_select = ServerPackets.get_character_select_start_data(
            self.player_index
        )
        self.assertEqual(first_call[0][1], expected_char_select)

        # Second call should be triple character data (contains new character data)
        expected_new_char_data = ServerPackets.get_new_character_data(self.player_index)
        self.assertIn(expected_new_char_data, second_call[0][1])

    @patch(
        "server.enter_game_world_pipeline.character_data_handler."
        "ServerSocketUtils.send_packet_or_cleanup"
    )
    def test_send_character_select_and_data_first_packet_fails(self, mock_send_packet):
        """Test when first packet sending fails."""
        mock_send_packet.return_value = False

        with self.assertRaises(CharacterDataException) as cm:
            self.handler.send_character_select_and_data(
                self.player_index,
                "testuser",
                self.mock_socket,
                self.mock_logger,
            )

        self.assertIn("Failed to send character select packet", str(cm.exception))
        # Should only be called once since first packet failed
        self.assertEqual(mock_send_packet.call_count, 1)

    @patch(
        "server.enter_game_world_pipeline.character_data_handler."
        "ServerSocketUtils.send_packet_or_cleanup"
    )
    def test_send_character_select_and_data_second_packet_fails(self, mock_send_packet):
        """Test when second packet sending fails."""
        mock_send_packet.side_effect = [True, False]  # First succeeds, second fails

        with self.assertRaises(CharacterDataException) as cm:
            self.handler.send_character_select_and_data(
                self.player_index,
                "testuser",
                self.mock_socket,
                self.mock_logger,
            )

        self.assertIn("Failed to send character data packet", str(cm.exception))
        # Should be called twice
        self.assertEqual(mock_send_packet.call_count, 2)

    def test_create_triple_character_data(self):
        """Test triple character data creation."""
        result = self.handler._create_triple_character_data(
            self.player_index, "testuser", self.mock_logger
        )

        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

        # Verify it contains the expected new character data
        expected_packet = ServerPackets.get_new_character_data(self.player_index)
        self.assertIn(expected_packet, result)


if __name__ == "__main__":
    unittest.main()
