"""
Test character deletion functionality.
"""

import unittest
from unittest.mock import MagicMock
from data_models.mongodb_models import CharacterDatabase, ClientCharacterMongo
from server.client_state_manager import ClientStateManager
from server.logger import ServerLogger


class TestCharacterDelete(unittest.TestCase):
    """Test character deletion by user and index."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = MagicMock(spec=ServerLogger)
        self.state_manager = ClientStateManager(self.logger)

        # Mock database for testing
        self.mock_db = MagicMock(spec=CharacterDatabase)

    def test_delete_character_by_user_index(self):
        """Test deleting character by user ID and index."""
        # Create a real CharacterDatabase instance for testing
        from unittest.mock import patch

        with patch("data_models.mongodb_models.MongoClient"):
            db = CharacterDatabase()

            # Create mock characters
            char1 = ClientCharacterMongo()
            char1.id = 1
            char1.name = "TestChar1"
            char1.user_id = "testuser"
            char1.character_slot_index = 0

            char2 = ClientCharacterMongo()
            char2.id = 2
            char2.name = "TestChar2"
            char2.user_id = "testuser"
            char2.character_slot_index = 1

            char3 = ClientCharacterMongo()
            char3.id = 3
            char3.name = "TestChar3"
            char3.user_id = "testuser"
            char3.character_slot_index = 2

            # Mock the database methods
            with patch.object(db.characters, "find_one") as mock_find_one:
                with patch.object(db, "permanently_delete_character") as mock_delete:
                    # Mock finding character at slot 1
                    mock_find_one.return_value = char2.to_dict()
                    mock_delete.return_value = True

                    # Test deleting character at slot 1 (second character)
                    result = db.delete_character_by_user_index("testuser", 1)

                    # Verify the method was called correctly
                    mock_find_one.assert_called_once_with(
                        {
                            "user_id": "testuser",
                            "character_slot_index": 1,
                            "is_not_queued_for_deletion": True,
                        }
                    )
                    mock_delete.assert_called_once_with(2)
                    self.assertTrue(result)

    def test_delete_character_invalid_index(self):
        """Test deleting character with invalid index."""
        from unittest.mock import patch

        with patch("data_models.mongodb_models.MongoClient"):
            db = CharacterDatabase()

            # Mock the database methods
            with patch.object(db.characters, "find_one") as mock_find_one:
                # Mock no character found at slot 5
                mock_find_one.return_value = None

                # Test deleting character at invalid slot
                result = db.delete_character_by_user_index("testuser", 5)

                # Should return False for invalid slot
                self.assertFalse(result)

    def test_character_slot_index_calculation(self):
        """Test character slot index calculation from packet data."""
        # Test the formula: character_slot_index = data[17] // 4 - 1

        # Test case 1: data[17] = 4 -> slot_index = 0
        test_data = bytearray(18)
        test_data[17] = 4
        character_slot_index = test_data[17] // 4 - 1
        self.assertEqual(character_slot_index, 0)

        # Test case 2: data[17] = 8 -> slot_index = 1
        test_data[17] = 8
        character_slot_index = test_data[17] // 4 - 1
        self.assertEqual(character_slot_index, 1)

        # Test case 3: data[17] = 12 -> slot_index = 2
        test_data[17] = 12
        character_slot_index = test_data[17] // 4 - 1
        self.assertEqual(character_slot_index, 2)

    def test_state_manager_user_id_tracking(self):
        """Test state manager user_id tracking."""
        player_index = 0x5000
        user_id = "testuser"

        # Add client
        self.state_manager.add_client(player_index)

        # Set user_id
        result = self.state_manager.set_user_id(player_index, user_id)
        self.assertTrue(result)

        # Get user_id
        retrieved_user_id = self.state_manager.get_user_id(player_index)
        self.assertEqual(retrieved_user_id, user_id)

        # Remove client
        self.state_manager.remove_client(player_index)

        # User_id should be gone
        retrieved_user_id = self.state_manager.get_user_id(player_index)
        self.assertIsNone(retrieved_user_id)

    def test_set_user_id_unknown_client(self):
        """Test setting user_id for unknown client."""
        player_index = 0x9999
        user_id = "testuser"

        # Try to set user_id for non-existent client
        result = self.state_manager.set_user_id(player_index, user_id)
        self.assertFalse(result)

    def test_get_next_available_slot_index(self):
        """Test getting next available character slot index."""
        from unittest.mock import patch

        with patch("data_models.mongodb_models.MongoClient"):
            db = CharacterDatabase()

            # Mock characters data - slots 0 and 2 are taken
            mock_characters_data = [
                {"character_slot_index": 0},
                {"character_slot_index": 2},
            ]

            with patch.object(db.characters, "find") as mock_find:
                mock_find.return_value = mock_characters_data

                # Should return slot 1 (the available slot)
                next_slot = db.get_next_available_slot_index("testuser")
                self.assertEqual(next_slot, 1)

                # Verify the query was correct
                mock_find.assert_called_once_with(
                    {"user_id": "testuser", "is_not_queued_for_deletion": True},
                    {"character_slot_index": 1},
                )


if __name__ == "__main__":
    unittest.main()
