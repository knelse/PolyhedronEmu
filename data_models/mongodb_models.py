"""
MongoDB data models for the game server.
"""

from typing import Dict, Optional
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from .enums import (
    Guild,
    ClanRank,
    KarmaTypes,
    BelongingSlot,
    Clan,
    DEFAULT_CLAN,
)
from .client_character import ClientCharacter


class ClientCharacterMongo:
    """MongoDB data model for ClientCharacter with all persistent fields."""

    def __init__(self):
        # Core character data
        self.id: int = 0
        self.look_type: int = 0x7
        self.is_turned_off: int = 0x9

        # Level progression
        self.title_minus_one: int = 0
        self.degree_minus_one: int = 0

        # Stats - MP
        self.max_mp: int = 0
        self.current_mp: int = 0

        # Base and current stats
        self.base_strength: int = 0
        self.current_strength: int = 0
        self.base_agility: int = 0
        self.current_agility: int = 0
        self.base_accuracy: int = 0
        self.current_accuracy: int = 0
        self.base_endurance: int = 0
        self.current_endurance: int = 0

        # Elemental stats
        self.base_earth: int = 0
        self.current_earth: int = 0
        self.base_air: int = 0
        self.current_air: int = 0
        self.base_water: int = 0
        self.current_water: int = 0
        self.base_fire: int = 0
        self.current_fire: int = 0

        # Satiety and experience
        self.max_satiety: int = 100
        self.current_satiety: int = 100
        self.title_xp: int = 0
        self.degree_xp: int = 0
        self.available_title_stats: int = 0
        self.available_degree_stats: int = 0

        # Character identity
        self.is_gender_female: bool = False
        self.name: str = "<create new>"
        self.clan: Optional[Clan] = DEFAULT_CLAN

        # Appearance
        self.face_type: int = 0
        self.hair_style: int = 0
        self.hair_color: int = 0
        self.tattoo: int = 0

        # Equipment model IDs
        self.boot_model_id: int = 0
        self.pants_model_id: int = 0
        self.armor_model_id: int = 0
        self.helmet_model_id: int = 0
        self.gloves_model_id: int = 0

        # Character state
        self.is_not_queued_for_deletion: bool = True
        self.money: int = 0
        self.guild_level_minus_one: int = 0
        self.guild: Guild = Guild.NONE
        self.clan_rank: ClanRank = ClanRank.NEOPHYTE

        # Position and orientation
        self.x: float = 0.0
        self.y: float = 150.0
        self.z: float = 0.0
        self.angle: float = 0.0

        # Health and defense
        self.current_hp: int = 0
        self.max_hp: int = 0
        self.p_def: int = 0
        self.m_def: int = 0

        # Combat and karma
        self.karma: KarmaTypes = KarmaTypes.NEUTRAL
        self.items: Dict[BelongingSlot, int] = {}
        self.p_atk: int = 0
        self.m_atk: int = 0
        self.karma_count: int = 0

        # User linking
        self.user_id: Optional[str] = None  # Links character to user login
        self.character_slot_index: int = 0  # Character slot index (0, 1, 2, etc.)

        # Metadata
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)

    @classmethod
    def from_client_character(
        cls, character: ClientCharacter
    ) -> "ClientCharacterMongo":
        """Convert a ClientCharacter to ClientCharacterMongo."""
        mongo_char = cls()

        # Core character data
        mongo_char.id = character.id
        mongo_char.look_type = character.look_type
        mongo_char.is_turned_off = character.is_turned_off

        # Level progression
        mongo_char.title_minus_one = character.title_minus_one
        mongo_char.degree_minus_one = character.degree_minus_one

        # Stats
        mongo_char.max_mp = character.max_mp
        mongo_char.current_mp = character.current_mp

        # Base and current stats
        mongo_char.base_strength = character.base_strength
        mongo_char.current_strength = character.current_strength
        mongo_char.base_agility = character.base_agility
        mongo_char.current_agility = character.current_agility
        mongo_char.base_accuracy = character.base_accuracy
        mongo_char.current_accuracy = character.current_accuracy
        mongo_char.base_endurance = character.base_endurance
        mongo_char.current_endurance = character.current_endurance

        # Elemental stats
        mongo_char.base_earth = character.base_earth
        mongo_char.current_earth = character.current_earth
        mongo_char.base_air = character.base_air
        mongo_char.current_air = character.current_air
        mongo_char.base_water = character.base_water
        mongo_char.current_water = character.current_water
        mongo_char.base_fire = character.base_fire
        mongo_char.current_fire = character.current_fire

        # Satiety and experience
        mongo_char.max_satiety = character.max_satiety
        mongo_char.current_satiety = character.current_satiety
        mongo_char.title_xp = character.title_xp
        mongo_char.degree_xp = character.degree_xp
        mongo_char.available_title_stats = character.available_title_stats
        mongo_char.available_degree_stats = character.available_degree_stats

        # Character identity
        mongo_char.is_gender_female = character.is_gender_female
        mongo_char.name = character.name
        mongo_char.clan = character.clan

        # Appearance
        mongo_char.face_type = character.face_type
        mongo_char.hair_style = character.hair_style
        mongo_char.hair_color = character.hair_color
        mongo_char.tattoo = character.tattoo

        # Equipment model IDs
        mongo_char.boot_model_id = character.boot_model_id
        mongo_char.pants_model_id = character.pants_model_id
        mongo_char.armor_model_id = character.armor_model_id
        mongo_char.helmet_model_id = character.helmet_model_id
        mongo_char.gloves_model_id = character.gloves_model_id

        # Character state
        mongo_char.is_not_queued_for_deletion = character.is_not_queued_for_deletion
        mongo_char.money = character.money
        mongo_char.guild_level_minus_one = character.guild_level_minus_one
        mongo_char.guild = character.guild
        mongo_char.clan_rank = character.clan_rank

        # Position and orientation
        mongo_char.x = character.x
        mongo_char.y = character.y
        mongo_char.z = character.z
        mongo_char.angle = character.angle

        # Health and defense
        mongo_char.current_hp = character.current_hp
        mongo_char.max_hp = character.max_hp
        mongo_char.p_def = character.p_def
        mongo_char.m_def = character.m_def

        # Combat and karma
        mongo_char.karma = character.karma
        mongo_char.items = character.items.copy()
        mongo_char.p_atk = character.p_atk
        mongo_char.m_atk = character.m_atk
        mongo_char.karma_count = character.karma_count

        # Note: user_id is not copied from ClientCharacter as it's set separately

        return mongo_char

    def to_client_character(self) -> ClientCharacter:
        """Convert ClientCharacterMongo to ClientCharacter."""
        character = ClientCharacter()

        # Core character data
        character.id = self.id
        character.look_type = self.look_type
        character.is_turned_off = self.is_turned_off

        # Level progression
        character.title_minus_one = self.title_minus_one
        character.degree_minus_one = self.degree_minus_one

        # Stats
        character.max_mp = self.max_mp
        character.current_mp = self.current_mp

        # Base and current stats
        character.base_strength = self.base_strength
        character.current_strength = self.current_strength
        character.base_agility = self.base_agility
        character.current_agility = self.current_agility
        character.base_accuracy = self.base_accuracy
        character.current_accuracy = self.current_accuracy
        character.base_endurance = self.base_endurance
        character.current_endurance = self.current_endurance

        # Elemental stats
        character.base_earth = self.base_earth
        character.current_earth = self.current_earth
        character.base_air = self.base_air
        character.current_air = self.current_air
        character.base_water = self.base_water
        character.current_water = self.current_water
        character.base_fire = self.base_fire
        character.current_fire = self.current_fire

        # Satiety and experience
        character.max_satiety = self.max_satiety
        character.current_satiety = self.current_satiety
        character.title_xp = self.title_xp
        character.degree_xp = self.degree_xp
        character.available_title_stats = self.available_title_stats
        character.available_degree_stats = self.available_degree_stats

        # Character identity
        character.is_gender_female = self.is_gender_female
        character.name = self.name
        character.clan = self.clan

        # Appearance
        character.face_type = self.face_type
        character.hair_style = self.hair_style
        character.hair_color = self.hair_color
        character.tattoo = self.tattoo

        # Equipment model IDs
        character.boot_model_id = self.boot_model_id
        character.pants_model_id = self.pants_model_id
        character.armor_model_id = self.armor_model_id
        character.helmet_model_id = self.helmet_model_id
        character.gloves_model_id = self.gloves_model_id

        # Character state
        character.is_not_queued_for_deletion = self.is_not_queued_for_deletion
        character.money = self.money
        character.guild_level_minus_one = self.guild_level_minus_one
        character.guild = self.guild
        character.clan_rank = self.clan_rank

        # Position and orientation
        character.x = self.x
        character.y = self.y
        character.z = self.z
        character.angle = self.angle

        # Health and defense
        character.current_hp = self.current_hp
        character.max_hp = self.max_hp
        character.p_def = self.p_def
        character.m_def = self.m_def

        # Combat and karma
        character.karma = self.karma
        character.items = self.items.copy()
        character.p_atk = self.p_atk
        character.m_atk = self.m_atk
        character.karma_count = self.karma_count

        return character

    def to_dict(self) -> Dict:
        """Convert the model to a dictionary for MongoDB storage."""
        return {
            "id": self.id,
            "look_type": self.look_type,
            "is_turned_off": self.is_turned_off,
            "title_minus_one": self.title_minus_one,
            "degree_minus_one": self.degree_minus_one,
            "max_mp": self.max_mp,
            "current_mp": self.current_mp,
            "base_strength": self.base_strength,
            "current_strength": self.current_strength,
            "base_agility": self.base_agility,
            "current_agility": self.current_agility,
            "base_accuracy": self.base_accuracy,
            "current_accuracy": self.current_accuracy,
            "base_endurance": self.current_endurance,
            "current_endurance": self.current_endurance,
            "base_earth": self.base_earth,
            "current_earth": self.current_earth,
            "base_air": self.base_air,
            "current_air": self.current_air,
            "base_water": self.base_water,
            "current_water": self.current_water,
            "base_fire": self.base_fire,
            "current_fire": self.current_fire,
            "max_satiety": self.max_satiety,
            "current_satiety": self.current_satiety,
            "title_xp": self.title_xp,
            "degree_xp": self.degree_xp,
            "available_title_stats": self.available_title_stats,
            "available_degree_stats": self.available_degree_stats,
            "is_gender_female": self.is_gender_female,
            "name": self.name,
            "clan": (
                {"name": self.clan.name, "clan_id": self.clan.clan_id}
                if self.clan
                else None
            ),
            "face_type": self.face_type,
            "hair_style": self.hair_style,
            "hair_color": self.hair_color,
            "tattoo": self.tattoo,
            "boot_model_id": self.boot_model_id,
            "pants_model_id": self.pants_model_id,
            "armor_model_id": self.armor_model_id,
            "helmet_model_id": self.helmet_model_id,
            "gloves_model_id": self.gloves_model_id,
            "is_not_queued_for_deletion": self.is_not_queued_for_deletion,
            "money": self.money,
            "guild_level_minus_one": self.guild_level_minus_one,
            "guild": self.guild.value,
            "clan_rank": self.clan_rank.value,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "angle": self.angle,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "p_def": self.p_def,
            "m_def": self.m_def,
            "karma": self.karma.value,
            "items": {slot.value: item_id for slot, item_id in self.items.items()},
            "p_atk": self.p_atk,
            "m_atk": self.m_atk,
            "karma_count": self.karma_count,
            "user_id": self.user_id,
            "character_slot_index": self.character_slot_index,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ClientCharacterMongo":
        """Create a model instance from a dictionary."""
        instance = cls()

        # Core character data
        instance.id = data.get("id", 0)
        instance.look_type = data.get("look_type", 0x7)
        instance.is_turned_off = data.get("is_turned_off", 0x9)

        # Level progression
        instance.title_minus_one = data.get("title_minus_one", 0)
        instance.degree_minus_one = data.get("degree_minus_one", 0)

        # Stats
        instance.max_mp = data.get("max_mp", 0)
        instance.current_mp = data.get("current_mp", 0)

        # Base and current stats
        instance.base_strength = data.get("base_strength", 0)
        instance.current_strength = data.get("current_strength", 0)
        instance.base_agility = data.get("base_agility", 0)
        instance.current_agility = data.get("current_agility", 0)
        instance.base_accuracy = data.get("base_accuracy", 0)
        instance.current_accuracy = data.get("current_accuracy", 0)
        instance.base_endurance = data.get("base_endurance", 0)
        instance.current_endurance = data.get("current_endurance", 0)

        # Elemental stats
        instance.base_earth = data.get("base_earth", 0)
        instance.current_earth = data.get("current_earth", 0)
        instance.base_air = data.get("base_air", 0)
        instance.current_air = data.get("current_air", 0)
        instance.base_water = data.get("base_water", 0)
        instance.current_water = data.get("current_water", 0)
        instance.base_fire = data.get("base_fire", 0)
        instance.current_fire = data.get("current_fire", 0)

        # Satiety and experience
        instance.max_satiety = data.get("max_satiety", 100)
        instance.current_satiety = data.get("current_satiety", 100)
        instance.title_xp = data.get("title_xp", 0)
        instance.degree_xp = data.get("degree_xp", 0)
        instance.available_title_stats = data.get("available_title_stats", 0)
        instance.available_degree_stats = data.get("available_degree_stats", 0)

        # Character identity
        instance.is_gender_female = data.get("is_gender_female", False)
        instance.name = data.get("name", "Test")
        clan_data = data.get("clan")
        if clan_data:
            instance.clan = Clan(
                clan_data.get("name", "Default"), clan_data.get("clan_id", 0)
            )
        else:
            instance.clan = DEFAULT_CLAN

        # Appearance
        instance.face_type = data.get("face_type", 0)
        instance.hair_style = data.get("hair_style", 0)
        instance.hair_color = data.get("hair_color", 0)
        instance.tattoo = data.get("tattoo", 0)

        # Equipment model IDs
        instance.boot_model_id = data.get("boot_model_id", 0)
        instance.pants_model_id = data.get("pants_model_id", 0)
        instance.armor_model_id = data.get("armor_model_id", 0)
        instance.helmet_model_id = data.get("helmet_model_id", 0)
        instance.gloves_model_id = data.get("gloves_model_id", 0)

        # Character state
        instance.is_not_queued_for_deletion = data.get(
            "is_not_queued_for_deletion", True
        )
        instance.money = data.get("money", 0)
        instance.guild_level_minus_one = data.get("guild_level_minus_one", 0)
        instance.guild = Guild(data.get("guild", Guild.NONE.value))
        instance.clan_rank = ClanRank(data.get("clan_rank", ClanRank.NEOPHYTE.value))

        # Position and orientation
        instance.x = data.get("x", 0.0)
        instance.y = data.get("y", 150.0)
        instance.z = data.get("z", 0.0)
        instance.angle = data.get("angle", 0.0)

        # Health and defense
        instance.current_hp = data.get("current_hp", 0)
        instance.max_hp = data.get("max_hp", 0)
        instance.p_def = data.get("p_def", 0)
        instance.m_def = data.get("m_def", 0)

        # Combat and karma
        instance.karma = KarmaTypes(data.get("karma", KarmaTypes.NEUTRAL.value))
        items_data = data.get("items", {})
        instance.items = {
            BelongingSlot(int(slot)): item_id for slot, item_id in items_data.items()
        }
        instance.p_atk = data.get("p_atk", 0)
        instance.m_atk = data.get("m_atk", 0)
        instance.karma_count = data.get("karma_count", 0)

        # User linking
        instance.user_id = data.get("user_id")
        instance.character_slot_index = data.get("character_slot_index", 0)

        # Metadata
        instance.created_at = data.get("created_at", datetime.now(timezone.utc))
        instance.updated_at = data.get("updated_at", datetime.now(timezone.utc))

        return instance

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)


class CharacterDatabase:
    """Database manager for character operations."""

    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "polyhedron_emu",
    ):
        self.client = MongoClient(connection_string)
        self.db: Database = self.client[database_name]
        self.characters: Collection = self.db.characters

        # Create indexes
        self._create_indexes()

    def _create_indexes(self):
        """Create database indexes for optimal query performance."""
        # Unique index on character ID
        self.characters.create_index("id", unique=True)

        # Index on character name for lookups
        self.characters.create_index("name")

        # Index on deletion status for filtering
        self.characters.create_index("is_not_queued_for_deletion")

        # Index on user_id for fetching user's characters
        self.characters.create_index("user_id")

        # Compound index for guild queries
        self.characters.create_index([("guild", 1), ("guild_level_minus_one", -1)])

        # Compound index for user's active characters
        self.characters.create_index(
            [("user_id", 1), ("is_not_queued_for_deletion", 1)]
        )

        # Compound index for user's character slots
        self.characters.create_index([("user_id", 1), ("character_slot_index", 1)])

        # Index on creation date for time-based queries
        self.characters.create_index("created_at")

    def save_character(self, character: ClientCharacterMongo) -> bool:
        """Save a character to the database."""
        try:
            character.update_timestamp()
            character_dict = character.to_dict()

            # Use upsert to handle both insert and update
            result = self.characters.update_one(
                {"id": character.id}, {"$set": character_dict}, upsert=True
            )
            return result.acknowledged
        except Exception as e:
            print(f"Error saving character: {e}")
            return False

    def get_character_by_id(self, character_id: int) -> Optional[ClientCharacterMongo]:
        """Retrieve a character by ID."""
        try:
            character_data = self.characters.find_one({"id": character_id})
            if character_data:
                return ClientCharacterMongo.from_dict(character_data)
            return None
        except Exception as e:
            print(f"Error retrieving character: {e}")
            return None

    def get_character_by_name(self, name: str) -> Optional[ClientCharacterMongo]:
        """Retrieve a character by name."""
        try:
            character_data = self.characters.find_one({"name": name})
            if character_data:
                return ClientCharacterMongo.from_dict(character_data)
            return None
        except Exception as e:
            print(f"Error retrieving character by name: {e}")
            return None

    def get_characters_by_guild(self, guild: Guild) -> list[ClientCharacterMongo]:
        """Retrieve all characters in a specific guild."""
        try:
            characters_data = self.characters.find({"guild": guild.value})
            return [ClientCharacterMongo.from_dict(data) for data in characters_data]
        except Exception as e:
            print(f"Error retrieving characters by guild: {e}")
            return []

    def get_characters_by_user(self, user_id: str) -> list[ClientCharacterMongo]:
        """Retrieve all active characters belonging to a user."""
        try:
            characters_data = self.characters.find(
                {"user_id": user_id, "is_not_queued_for_deletion": True}
            ).sort(
                "character_slot_index", 1
            )  # Sort by character slot index
            return [ClientCharacterMongo.from_dict(data) for data in characters_data]
        except Exception as e:
            print(f"Error retrieving characters for user {user_id}: {e}")
            return []

    def get_active_characters(self) -> list[ClientCharacterMongo]:
        """Retrieve all characters not queued for deletion."""
        try:
            characters_data = self.characters.find({"is_not_queued_for_deletion": True})
            return [ClientCharacterMongo.from_dict(data) for data in characters_data]
        except Exception as e:
            print(f"Error retrieving active characters: {e}")
            return []

    def delete_character(self, character_id: int) -> bool:
        """Mark a character for deletion."""
        try:
            result = self.characters.update_one(
                {"id": character_id}, {"$set": {"is_not_queued_for_deletion": False}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error deleting character: {e}")
            return False

    def permanently_delete_character(self, character_id: int) -> bool:
        """Permanently remove a character from the database."""
        try:
            result = self.characters.delete_one({"id": character_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error permanently deleting character: {e}")
            return False

    def delete_character_by_user_index(
        self, user_id: str, character_slot_index: int
    ) -> bool:
        """Delete a character by user ID and character slot index."""
        try:
            character_data = self.characters.find_one(
                {
                    "user_id": user_id,
                    "character_slot_index": character_slot_index,
                    "is_not_queued_for_deletion": True,
                }
            )

            if not character_data:
                print(
                    f"No character found at slot {character_slot_index} for user {user_id}"
                )
                return False

            character = ClientCharacterMongo.from_dict(character_data)
            result = self.permanently_delete_character(character.id)

            if result:
                print(
                    f"Deleted character '{character.name}' (ID: {character.id}) "
                    f"from slot {character_slot_index} for user {user_id}"
                )

            return result
        except Exception as e:
            print(f"Error deleting character by user slot index: {e}")
            return False

    def get_character_count(self) -> int:
        """Get the total number of characters in the database."""
        try:
            return self.characters.count_documents({})
        except Exception as e:
            print(f"Error getting character count: {e}")
            return 0

    def get_active_character_count(self) -> int:
        """Get the number of active characters (not queued for deletion)."""
        try:
            return self.characters.count_documents({"is_not_queued_for_deletion": True})
        except Exception as e:
            print(f"Error getting active character count: {e}")
            return 0

    def get_next_available_slot_index(self, user_id: str, max_slots: int = 3) -> int:
        """Get the next available character slot index for a user."""
        try:
            # Get all character slot indices for this user
            used_slots = set()
            characters_data = self.characters.find(
                {"user_id": user_id, "is_not_queued_for_deletion": True},
                {"character_slot_index": 1},
            )

            for char_data in characters_data:
                used_slots.add(char_data.get("character_slot_index", 0))

            # Find the first available slot (0, 1, 2, ...)
            for slot_index in range(max_slots):
                if slot_index not in used_slots:
                    return slot_index

            # If all slots are taken, return -1
            return -1
        except Exception as e:
            print(f"Error getting next available slot index: {e}")
            return -1

    def character_name_exists(self, name: str) -> bool:
        """Check if a character name already exists in the database."""
        try:
            character_data = self.characters.find_one(
                {"name": name, "is_not_queued_for_deletion": True}
            )
            return character_data is not None
        except Exception as e:
            print(f"Error checking if character name exists: {e}")
            return True  # Return True on error to prevent duplicate names

    def create_character(self, character_data: dict) -> Optional[int]:
        """Create a new character from dictionary data."""
        try:
            # Create a new ClientCharacterMongo instance
            character = ClientCharacterMongo()

            # Set the character data
            character.user_id = character_data.get("user_id", "")
            character.character_slot_index = character_data.get(
                "character_slot_index", 0
            )
            character.name = character_data.get("name", "")
            character.is_gender_female = character_data.get("is_gender_female", False)
            character.face_type = character_data.get("face_type", 0)
            character.hair_style = character_data.get("hair_style", 0)
            character.hair_color = character_data.get("hair_color", 0)
            character.tattoo = character_data.get("tattoo", 0)
            character.x = character_data.get("x", 0.0)
            character.y = character_data.get("y", 150.0)
            character.z = character_data.get("z", 0.0)
            character.angle = character_data.get("angle", 0.0)

            # Generate a new unique ID
            character.id = self._generate_unique_character_id()

            # Save the character
            if self.save_character(character):
                return character.id
            else:
                return None

        except Exception as e:
            print(f"Error creating character: {e}")
            return None

    def _generate_unique_character_id(self) -> int:
        """Generate a unique character ID."""
        try:
            # Find the highest existing ID and add 1
            result = self.characters.find().sort("id", -1).limit(1)
            max_id = 0
            for doc in result:
                max_id = doc.get("id", 0)
            return max_id + 1
        except Exception as e:
            print(f"Error generating unique character ID: {e}")
            # Fallback to timestamp-based ID
            import time

            return int(time.time() * 1000) % 2147483647  # Keep within int32 range
