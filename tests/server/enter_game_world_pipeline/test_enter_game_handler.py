import sys
import unittest
from unittest.mock import MagicMock, patch
from server.enter_game_world_pipeline.enter_game_handler import EnterGameHandler
from server.enter_game_world_pipeline.exceptions import EnterGameException
from server.logger import ServerLogger
from server.client_state_manager import ClientStateManager
from data_models.mongodb_models import CharacterDatabase

sys.modules["py4godot"] = MagicMock()
sys.modules["py4godot.classes"] = MagicMock()
sys.modules["py4godot.classes.Node3D"] = MagicMock()


class TestEnterGameHandler(unittest.TestCase):
    """Test EnterGameHandler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock(spec=ServerLogger)
        self.mock_state_manager = MagicMock(spec=ClientStateManager)
        self.mock_character_db = MagicMock(spec=CharacterDatabase)
        self.handler = EnterGameHandler(self.mock_character_db)
        self.player_index = 0x5000
        self.mock_socket = MagicMock()

    @patch(
        "server.enter_game_world_pipeline.enter_game_handler."
        "ServerSocketUtils.send_packet_with_logging"
    )
    @patch("data_models.mongodb_models.ClientCharacterMongo")
    def test_send_enter_game_data_success(self, mock_char_mongo, mock_send_packet):
        """Test successful enter game data sending."""
        mock_send_packet.return_value = True

        # Mock state manager to return user_id
        self.mock_state_manager.get_user_id.return_value = "testuser"

        # Mock database to return character
        mock_character_data = {
            "name": "TestChar",
            "user_id": "testuser",
            "character_slot_index": 1,
            "is_not_queued_for_deletion": True,
        }
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = mock_character_data
        self.mock_character_db.characters = mock_collection

        # Mock character creation
        mock_character = MagicMock()
        mock_character.name = "TestChar"
        mock_character.to_game_data_bytearray.return_value = b"game_data"
        mock_char_mongo.from_dict.return_value.to_client_character.return_value = (
            mock_character
        )

        # Should not raise an exception
        self.handler.send_enter_game_data(
            1,  # character_slot_index
            self.player_index,
            self.mock_socket,
            self.mock_logger,
            self.mock_state_manager,
        )

        # Verify packets were sent
        mock_send_packet.assert_called_once()
        self.mock_logger.info.assert_called_once()

    def test_send_enter_game_data_no_user_id(self):
        """Test when user_id is None."""
        # Mock state manager to return None user_id
        self.mock_state_manager.get_user_id.return_value = None

        with self.assertRaises(EnterGameException) as cm:
            self.handler.send_enter_game_data(
                1,  # character_slot_index
                self.player_index,
                self.mock_socket,
                self.mock_logger,
                self.mock_state_manager,
            )

        self.assertIn("Cannot send enter game data for player", str(cm.exception))
        self.assertIn("no user_id found", str(cm.exception))

    def test_send_enter_game_data_character_not_found(self):
        """Test when character is not found."""
        # Mock state manager to return user_id
        self.mock_state_manager.get_user_id.return_value = "testuser"

        # Mock database to return None (character not found)
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        self.mock_character_db.characters = mock_collection

        with self.assertRaises(EnterGameException) as cm:
            self.handler.send_enter_game_data(
                1,  # character_slot_index
                self.player_index,
                self.mock_socket,
                self.mock_logger,
                self.mock_state_manager,
            )

        self.assertIn("character not found at slot", str(cm.exception))

    @patch(
        "server.enter_game_world_pipeline.enter_game_handler."
        "ServerSocketUtils.send_packet_with_logging"
    )
    @patch("data_models.mongodb_models.ClientCharacterMongo")
    def test_send_enter_game_data_packet_send_failure(
        self, mock_char_mongo, mock_send_packet
    ):
        """Test when packet sending fails."""
        mock_send_packet.return_value = False

        # Mock state manager to return user_id
        self.mock_state_manager.get_user_id.return_value = "testuser"

        # Mock database to return character
        mock_character_data = {
            "name": "TestChar",
            "user_id": "testuser",
            "character_slot_index": 1,
            "is_not_queued_for_deletion": True,
        }
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = mock_character_data
        self.mock_character_db.characters = mock_collection

        # Mock character creation
        mock_character = MagicMock()
        mock_character.name = "TestChar"
        mock_character.to_game_data_bytearray.return_value = b"game_data"
        mock_char_mongo.from_dict.return_value.to_client_character.return_value = (
            mock_character
        )

        with self.assertRaises(EnterGameException) as cm:
            self.handler.send_enter_game_data(
                1,  # character_slot_index
                self.player_index,
                self.mock_socket,
                self.mock_logger,
                self.mock_state_manager,
            )

        self.assertIn("Failed to send enter game data", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
