"""
Test character screen functionality.
"""

import unittest
from unittest.mock import MagicMock
from data_models.mongodb_models import CharacterDatabase, ClientCharacterMongo
from server.client_state_manager import ClientStateManager
from server.logger import ServerLogger


class TestCharacterScreen(unittest.TestCase):
    """Test character screen functionality including deletion and selection."""

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

    def test_character_selection_packet_parsing(self):
        """Test character selection packet parsing."""
        # Test the formula: character_slot_index = data[17] // 4 - 1

        # Test case 1: data[0] = 0x15, data[17] = 4 -> slot_index = 0
        test_data = bytearray(18)
        test_data[0] = 0x15  # Character selection packet
        test_data[17] = 4

        if test_data[0] == 0x15:
            character_slot_index = test_data[17] // 4 - 1
            self.assertEqual(character_slot_index, 0)

        # Test case 2: data[0] = 0x15, data[17] = 8 -> slot_index = 1
        test_data[17] = 8
        if test_data[0] == 0x15:
            character_slot_index = test_data[17] // 4 - 1
            self.assertEqual(character_slot_index, 1)

        # Test case 3: data[0] = 0x15, data[17] = 12 -> slot_index = 2
        test_data[17] = 12
        if test_data[0] == 0x15:
            character_slot_index = test_data[17] // 4 - 1
            self.assertEqual(character_slot_index, 2)

    def test_character_name_exists(self):
        """Test checking if character name exists."""
        from unittest.mock import patch

        with patch("data_models.mongodb_models.MongoClient"):
            db = CharacterDatabase()

            # Test name exists
            with patch.object(db.characters, "find_one") as mock_find_one:
                mock_find_one.return_value = {"name": "ExistingName"}

                result = db.character_name_exists("ExistingName")
                self.assertTrue(result)

                mock_find_one.assert_called_once_with(
                    {"name": "ExistingName", "is_not_queued_for_deletion": True}
                )

            # Test name doesn't exist
            with patch.object(db.characters, "find_one") as mock_find_one:
                mock_find_one.return_value = None

                result = db.character_name_exists("NewName")
                self.assertFalse(result)

    def test_create_character(self):
        """Test creating a new character."""
        from unittest.mock import patch

        with patch("data_models.mongodb_models.MongoClient"):
            db = CharacterDatabase()

            character_data = {
                "user_id": "testuser",
                "character_slot_index": 1,
                "name": "TestHero",
                "is_gender_female": False,
                "face_type": 10,
                "hair_style": 5,
                "hair_color": 3,
                "tattoo": 1,
                "level": 1,
                "experience": 0,
                "health": 100,
                "mana": 100,
                "strength": 10,
                "dexterity": 10,
                "intelligence": 10,
                "x_position": 0.0,
                "y_position": 0.0,
                "z_position": 0.0,
            }

            with patch.object(db, "_generate_unique_character_id") as mock_gen_id:
                with patch.object(db, "save_character") as mock_save:
                    mock_gen_id.return_value = 123
                    mock_save.return_value = True

                    result = db.create_character(character_data)

                    self.assertEqual(result, 123)
                    mock_gen_id.assert_called_once()
                    mock_save.assert_called_once()

    def test_character_creation_packet_parsing(self):
        """Test character creation packet structure validation."""
        # Test minimum packet size validation
        test_data = bytearray(30)  # Create packet with proper size
        test_data[0] = 30  # Packet length
        test_data[13] = 0x08
        test_data[14] = 0x40
        test_data[15] = 0x80
        test_data[16] = 0x05
        test_data[17] = 8  # Character slot (8 // 4 - 1 = 1)

        # Validate packet structure
        is_valid = (
            test_data[0] >= 0x1B
            and test_data[13] == 0x08
            and test_data[14] == 0x40
            and test_data[15] == 0x80
            and test_data[16] == 0x05
        )

        self.assertTrue(is_valid)

        # Test character slot calculation
        character_slot_index = test_data[17] // 4 - 1
        self.assertEqual(character_slot_index, 1)

    def test_character_appearance_parsing(self):
        """Test parsing character appearance data from packet."""
        # Create test packet with character data
        test_data = bytearray(30)
        test_data[0] = 30  # Packet length

        # Calculate character data bytes position
        char_data_bytes_start = test_data[0] - 5  # 25

        # Set up character data bytes at the calculated position
        char_data_bytes = bytearray(5)
        char_data_bytes[0] = 0b11000000  # Test data for face_type calculation
        char_data_bytes[1] = 0b00010000  # Gender bit + face_type bits
        char_data_bytes[2] = 0b00100000  # Hair style bits
        char_data_bytes[3] = 0b00110000  # Hair color bits
        char_data_bytes[4] = 0b01000000  # Tattoo bits

        # Place character data in the packet
        test_data[char_data_bytes_start : char_data_bytes_start + 5] = char_data_bytes

        # Parse appearance data (mimic the logic from the implementation)
        is_gender_female = (char_data_bytes[1] >> 4) % 2 == 1
        face_type = ((char_data_bytes[1] & 0b111111) << 2) + (char_data_bytes[0] >> 6)
        hair_style = ((char_data_bytes[2] & 0b111111) << 2) + (char_data_bytes[1] >> 6)
        hair_color = ((char_data_bytes[3] & 0b111111) << 2) + (char_data_bytes[2] >> 6)
        tattoo = ((char_data_bytes[4] & 0b111111) << 2) + (char_data_bytes[3] >> 6)

        # Verify parsing results
        self.assertTrue(is_gender_female)  # Bit 4 of byte[1] is set

        # Apply female adjustments
        if is_gender_female:
            face_type = 256 - face_type
            hair_style = 255 - hair_style
            hair_color = 255 - hair_color
            tattoo = 255 - tattoo

        # Values should be adjusted for female characters
        self.assertLess(face_type, 256)
        self.assertLess(hair_style, 256)
        self.assertLess(hair_color, 256)
        self.assertLess(tattoo, 256)


if __name__ == "__main__":
    unittest.main()
