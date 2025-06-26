import unittest
from unittest.mock import Mock
import sys
import os

# Must mock py4godot before importing modules that depend on it
sys.modules["py4godot"] = Mock()
sys.modules["py4godot.classes"] = Mock()


# Create proper mocks for gdclass and Node
def mock_gdclass(cls):
    """Mock gdclass decorator that just returns the class unchanged."""
    return cls


mock_node_module = Mock()
mock_node_module.Node = type("MockNode", (), {"__init__": lambda self: None})

sys.modules["py4godot.classes"].gdclass = mock_gdclass
sys.modules["py4godot.classes.Node"] = mock_node_module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Import after mocking py4godot dependencies  # noqa: E402
from server.player.character_sheet import CharacterSheet  # noqa: E402
from data_models.client_character import ClientCharacter  # noqa: E402


class TestCharacterSheet(unittest.TestCase):
    """Test cases for CharacterSheet class."""

    def setUp(self):
        """Set up test fixtures."""
        self.character_sheet = CharacterSheet()

        # Create a mock ClientCharacter for testing
        self.mock_character_data = Mock(spec=ClientCharacter)
        self.mock_character_data.character_name = "TestCharacter"
        self.mock_character_data.player_index = 0x5000

    def test_initialization(self):
        """Test CharacterSheet initialization."""
        self.assertIsNotNone(self.character_sheet)
        self.assertIsNone(self.character_sheet.character_data)
        self.assertFalse(self.character_sheet.has_character_data())

    def test_set_character_data(self):
        """Test setting character data."""
        self.character_sheet.set_character_data(self.mock_character_data)

        self.assertEqual(self.character_sheet.character_data, self.mock_character_data)
        self.assertTrue(self.character_sheet.has_character_data())

    def test_get_character_data(self):
        """Test getting character data."""
        # Initially should return None
        result = self.character_sheet.get_character_data()
        self.assertIsNone(result)

        # After setting data, should return the data
        self.character_sheet.set_character_data(self.mock_character_data)
        result = self.character_sheet.get_character_data()
        self.assertEqual(result, self.mock_character_data)

    def test_has_character_data_false(self):
        """Test has_character_data returns False when no data is set."""
        self.assertFalse(self.character_sheet.has_character_data())

    def test_has_character_data_true(self):
        """Test has_character_data returns True when data is set."""
        self.character_sheet.set_character_data(self.mock_character_data)
        self.assertTrue(self.character_sheet.has_character_data())

    def test_set_character_data_none(self):
        """Test setting character data to None."""
        # First set some data
        self.character_sheet.set_character_data(self.mock_character_data)
        self.assertTrue(self.character_sheet.has_character_data())

        # Then set to None
        self.character_sheet.set_character_data(None)
        self.assertIsNone(self.character_sheet.character_data)
        self.assertFalse(self.character_sheet.has_character_data())

    def test_set_character_data_overwrite(self):
        """Test overwriting existing character data."""
        # Set initial data
        self.character_sheet.set_character_data(self.mock_character_data)

        # Create new mock data
        new_mock_data = Mock(spec=ClientCharacter)
        new_mock_data.character_name = "NewCharacter"
        new_mock_data.player_index = 0x5001

        # Overwrite with new data
        self.character_sheet.set_character_data(new_mock_data)

        self.assertEqual(self.character_sheet.character_data, new_mock_data)
        self.assertNotEqual(
            self.character_sheet.character_data, self.mock_character_data
        )
        self.assertTrue(self.character_sheet.has_character_data())

    def test_ready_method(self):
        """Test the _ready method doesn't raise errors."""
        # Should not raise any exceptions
        self.character_sheet._ready()


if __name__ == "__main__":
    unittest.main()
