"""
Tests for the client_character data model.
"""

import unittest
from data_models.client_character import client_character
from data_models.enums import guild, clan_rank, karma_types, belonging_slot


class TestClientCharacter(unittest.TestCase):
    """Test cases for client_character class."""

    def setUp(self):
        """Set up test fixtures."""
        self.character = client_character()

    def test_character_initialization(self):
        """Test that character initializes with correct default values."""
        self.assertEqual(self.character.id, 0)
        self.assertEqual(self.character.name, "Test")
        self.assertEqual(self.character.current_hp, 100)
        self.assertEqual(self.character.max_hp, 100)
        self.assertEqual(self.character.y, 150.0)
        self.assertTrue(self.character.is_not_queued_for_deletion)
        self.assertFalse(self.character.is_gender_female)
        self.assertEqual(self.character.guild, guild.NONE)
        self.assertEqual(self.character.clan_rank, clan_rank.NEOPHYTE)
        self.assertEqual(self.character.karma, karma_types.NEUTRAL)

    def test_character_properties(self):
        """Test character property calculations."""
        # Test default base HP/MP calculations
        base_hp = self.character.max_hp_base
        base_mp = self.character.max_mp_base
        self.assertIsInstance(base_hp, int)
        self.assertIsInstance(base_mp, int)

        # Test XP calculation
        xp_needed = self.character.xp_to_level_up
        self.assertIsInstance(xp_needed, int)
        self.assertGreater(xp_needed, 0)

    def test_character_stats_modification(self):
        """Test modifying character stats."""
        self.character.base_strength = 50
        self.character.current_strength = 45
        self.character.name = "TestCharacter"
        self.character.money = 1000

        self.assertEqual(self.character.base_strength, 50)
        self.assertEqual(self.character.current_strength, 45)
        self.assertEqual(self.character.name, "TestCharacter")
        self.assertEqual(self.character.money, 1000)

    def test_equipment_items(self):
        """Test equipment items dictionary."""
        self.assertIsInstance(self.character.items, dict)
        self.assertEqual(len(self.character.items), 0)

        # Add some equipment
        self.character.items[belonging_slot.HELMET] = 1
        self.character.items[belonging_slot.CHESTPLATE] = 2

        self.assertEqual(self.character.items[belonging_slot.HELMET], 1)
        self.assertEqual(self.character.items[belonging_slot.CHESTPLATE], 2)

    def test_position_and_orientation(self):
        """Test position and orientation fields."""
        self.character.x = 100.5
        self.character.y = 200.7
        self.character.z = 300.1
        self.character.angle = 45.0

        self.assertEqual(self.character.x, 100.5)
        self.assertEqual(self.character.y, 200.7)
        self.assertEqual(self.character.z, 300.1)
        self.assertEqual(self.character.angle, 45.0)

    def test_elemental_stats(self):
        """Test elemental stat fields."""
        self.character.base_earth = 10
        self.character.current_earth = 12
        self.character.base_fire = 15
        self.character.current_fire = 18

        self.assertEqual(self.character.base_earth, 10)
        self.assertEqual(self.character.current_earth, 12)
        self.assertEqual(self.character.base_fire, 15)
        self.assertEqual(self.character.current_fire, 18)


if __name__ == "__main__":
    unittest.main()
