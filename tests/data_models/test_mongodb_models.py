"""
Tests for MongoDB data models.
"""

import unittest
from data_models.mongodb_models import client_character_mongo, character_database
from data_models.client_character import client_character
from data_models.enums import guild, clan_rank, karma_types, belonging_slot


class TestClientCharacterMongo(unittest.TestCase):
    """Test cases for client_character_mongo class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mongo_char = client_character_mongo()

    def test_character_initialization(self):
        """Test that character initializes with correct default values."""
        self.assertEqual(self.mongo_char.id, 0)
        self.assertEqual(self.mongo_char.name, "<create new>")
        self.assertEqual(self.mongo_char.current_hp, 0)
        self.assertEqual(self.mongo_char.max_hp, 0)
        self.assertEqual(self.mongo_char.y, 150.0)
        self.assertTrue(self.mongo_char.is_not_queued_for_deletion)
        self.assertFalse(self.mongo_char.is_gender_female)
        self.assertEqual(self.mongo_char.guild, guild.NONE)
        self.assertEqual(self.mongo_char.clan_rank, clan_rank.NEOPHYTE)
        self.assertEqual(self.mongo_char.karma, karma_types.NEUTRAL)

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        self.mongo_char.id = 123
        self.mongo_char.name = "TestCharacter"
        self.mongo_char.money = 1000

        char_dict = self.mongo_char.to_dict()

        self.assertEqual(char_dict["id"], 123)
        self.assertEqual(char_dict["name"], "TestCharacter")
        self.assertEqual(char_dict["money"], 1000)
        self.assertEqual(char_dict["guild"], guild.NONE.value)
        self.assertEqual(char_dict["clan_rank"], clan_rank.NEOPHYTE.value)
        self.assertEqual(char_dict["karma"], karma_types.NEUTRAL.value)

    def test_from_dict_conversion(self):
        """Test conversion from dictionary."""
        char_dict = {
            "id": 456,
            "name": "TestFromDict",
            "money": 2000,
            "guild": guild.NONE.value,
            "clan_rank": clan_rank.NEOPHYTE.value,
            "karma": karma_types.NEUTRAL.value,
            "is_gender_female": True,
            "current_hp": 100,
            "max_hp": 150,
        }

        mongo_char = client_character_mongo.from_dict(char_dict)

        self.assertEqual(mongo_char.id, 456)
        self.assertEqual(mongo_char.name, "TestFromDict")
        self.assertEqual(mongo_char.money, 2000)
        self.assertEqual(mongo_char.guild, guild.NONE)
        self.assertEqual(mongo_char.clan_rank, clan_rank.NEOPHYTE)
        self.assertEqual(mongo_char.karma, karma_types.NEUTRAL)
        self.assertTrue(mongo_char.is_gender_female)
        self.assertEqual(mongo_char.current_hp, 100)
        self.assertEqual(mongo_char.max_hp, 150)

    def test_from_client_character_conversion(self):
        """Test conversion from client_character."""
        client_char = client_character()
        client_char.id = 789
        client_char.name = "TestConversion"
        client_char.money = 3000
        client_char.guild = guild.NONE
        client_char.clan_rank = clan_rank.NEOPHYTE
        client_char.karma = karma_types.NEUTRAL
        client_char.is_gender_female = True
        client_char.current_hp = 200
        client_char.max_hp = 250

        mongo_char = client_character_mongo.from_client_character(client_char)

        self.assertEqual(mongo_char.id, 789)
        self.assertEqual(mongo_char.name, "TestConversion")
        self.assertEqual(mongo_char.money, 3000)
        self.assertEqual(mongo_char.guild, guild.NONE)
        self.assertEqual(mongo_char.clan_rank, clan_rank.NEOPHYTE)
        self.assertEqual(mongo_char.karma, karma_types.NEUTRAL)
        self.assertTrue(mongo_char.is_gender_female)
        self.assertEqual(mongo_char.current_hp, 200)
        self.assertEqual(mongo_char.max_hp, 250)

    def test_to_client_character_conversion(self):
        """Test conversion to client_character."""
        self.mongo_char.id = 999
        self.mongo_char.name = "TestToClient"
        self.mongo_char.money = 4000
        self.mongo_char.guild = guild.NONE
        self.mongo_char.clan_rank = clan_rank.NEOPHYTE
        self.mongo_char.karma = karma_types.NEUTRAL
        self.mongo_char.is_gender_female = False
        self.mongo_char.current_hp = 300
        self.mongo_char.max_hp = 350

        client_char = self.mongo_char.to_client_character()

        self.assertEqual(client_char.id, 999)
        self.assertEqual(client_char.name, "TestToClient")
        self.assertEqual(client_char.money, 4000)
        self.assertEqual(client_char.guild, guild.NONE)
        self.assertEqual(client_char.clan_rank, clan_rank.NEOPHYTE)
        self.assertEqual(client_char.karma, karma_types.NEUTRAL)
        self.assertFalse(client_char.is_gender_female)
        self.assertEqual(client_char.current_hp, 300)
        self.assertEqual(client_char.max_hp, 350)

    def test_items_conversion(self):
        """Test items dictionary conversion."""
        self.mongo_char.items = {
            belonging_slot.HELMET: 1,
            belonging_slot.CHESTPLATE: 2,
        }

        char_dict = self.mongo_char.to_dict()
        self.assertEqual(
            char_dict["items"],
            {belonging_slot.HELMET.value: 1, belonging_slot.CHESTPLATE.value: 2},
        )

        # Test conversion back
        mongo_char_from_dict = client_character_mongo.from_dict(char_dict)
        self.assertEqual(mongo_char_from_dict.items, self.mongo_char.items)

    def test_timestamp_update(self):
        """Test timestamp update functionality."""
        original_timestamp = self.mongo_char.updated_at
        self.mongo_char.update_timestamp()
        self.assertGreater(self.mongo_char.updated_at, original_timestamp)


class TestCharacterDatabase(unittest.TestCase):
    """Test cases for character_database class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a test database
        self.db = character_database(
            connection_string="mongodb://localhost:27017/",
            database_name="polyhedron_emu_test",
        )
        # Clean the test database before each test
        self.db.characters.delete_many({})

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean the test database after each test
        self.db.characters.delete_many({})

    def test_database_initialization(self):
        """Test database initialization."""
        self.assertIsNotNone(self.db.client)
        self.assertIsNotNone(self.db.db)
        self.assertIsNotNone(self.db.characters)

    def test_save_and_retrieve_character(self):
        """Test saving and retrieving a character."""
        mongo_char = client_character_mongo()
        mongo_char.id = 1001
        mongo_char.name = "TestSaveRetrieve"
        mongo_char.money = 5000

        # Save character
        save_result = self.db.save_character(mongo_char)
        self.assertTrue(save_result)

        # Retrieve character
        retrieved_char = self.db.get_character_by_id(1001)
        self.assertIsNotNone(retrieved_char)
        self.assertEqual(retrieved_char.id, 1001)
        self.assertEqual(retrieved_char.name, "TestSaveRetrieve")
        self.assertEqual(retrieved_char.money, 5000)

    def test_get_character_by_name(self):
        """Test retrieving character by name."""
        mongo_char = client_character_mongo()
        mongo_char.id = 1002
        mongo_char.name = "TestNameLookup"

        # Save character
        self.db.save_character(mongo_char)

        # Retrieve by name
        retrieved_char = self.db.get_character_by_name("TestNameLookup")
        self.assertIsNotNone(retrieved_char)
        self.assertEqual(retrieved_char.id, 1002)
        self.assertEqual(retrieved_char.name, "TestNameLookup")

    def test_get_characters_by_guild(self):
        """Test retrieving characters by guild."""
        # Create characters in different guilds
        char1 = client_character_mongo()
        char1.id = 1003
        char1.name = "GuildChar1"
        char1.guild = guild.NONE

        char2 = client_character_mongo()
        char2.id = 1004
        char2.name = "GuildChar2"
        char2.guild = guild.NONE

        char3 = client_character_mongo()
        char3.id = 1005
        char3.name = "OtherGuildChar"
        char3.guild = guild.ASSASIN

        # Save characters
        self.db.save_character(char1)
        self.db.save_character(char2)
        self.db.save_character(char3)

        # Get characters by guild
        guild_chars = self.db.get_characters_by_guild(guild.NONE)
        self.assertEqual(len(guild_chars), 2)
        char_names = [char.name for char in guild_chars]
        self.assertIn("GuildChar1", char_names)
        self.assertIn("GuildChar2", char_names)

    def test_delete_character(self):
        """Test character deletion."""
        mongo_char = client_character_mongo()
        mongo_char.id = 1006
        mongo_char.name = "TestDelete"

        # Save character
        self.db.save_character(mongo_char)

        # Verify it exists
        retrieved_char = self.db.get_character_by_id(1006)
        self.assertIsNotNone(retrieved_char)

        # Delete character
        delete_result = self.db.delete_character(1006)
        self.assertTrue(delete_result)

        # Verify it's marked for deletion
        deleted_char = self.db.get_character_by_id(1006)
        self.assertIsNotNone(deleted_char)
        self.assertFalse(deleted_char.is_not_queued_for_deletion)

    def test_character_count(self):
        """Test character counting."""
        # Get initial count
        initial_count = self.db.get_character_count()

        # Add a character
        mongo_char = client_character_mongo()
        mongo_char.id = 1007
        mongo_char.name = "TestCount"
        self.db.save_character(mongo_char)

        # Check new count
        new_count = self.db.get_character_count()
        self.assertEqual(new_count, initial_count + 1)

        # Check active count
        active_count = self.db.get_active_character_count()
        self.assertEqual(active_count, initial_count + 1)

    def test_get_characters_by_user(self):
        """Test retrieving characters by user ID."""
        # Create characters for different users
        char1 = client_character_mongo()
        char1.id = 1
        char1.name = "UserChar1"
        char1.user_id = "testuser1"

        char2 = client_character_mongo()
        char2.id = 2
        char2.name = "UserChar2"
        char2.user_id = "testuser1"

        char3 = client_character_mongo()
        char3.id = 3
        char3.name = "OtherChar"
        char3.user_id = "testuser2"

        # Save characters
        self.assertTrue(self.db.save_character(char1))
        self.assertTrue(self.db.save_character(char2))
        self.assertTrue(self.db.save_character(char3))

        # Get characters for testuser1
        user1_chars = self.db.get_characters_by_user("testuser1")
        self.assertEqual(len(user1_chars), 2)

        # Verify character names
        char_names = {char.name for char in user1_chars}
        self.assertEqual(char_names, {"UserChar1", "UserChar2"})

        # Get characters for testuser2
        user2_chars = self.db.get_characters_by_user("testuser2")
        self.assertEqual(len(user2_chars), 1)
        self.assertEqual(user2_chars[0].name, "OtherChar")

        # Get characters for non-existent user
        no_chars = self.db.get_characters_by_user("nonexistent")
        self.assertEqual(len(no_chars), 0)


if __name__ == "__main__":
    unittest.main()
