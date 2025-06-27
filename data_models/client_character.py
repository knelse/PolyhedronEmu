"""
Client character data model.
"""

from typing import Dict, Optional
from data_models.enums import (
    guild,
    clan_rank,
    karma_types,
    belonging_slot,
    clan,
    DEFAULT_CLAN,
    HEALTH_AT_TITLE,
    HEALTH_AT_DEGREE,
    MP_AT_TITLE,
    MP_AT_DEGREE,
    AVAILABLE_STATS_PRIMARY,
    AVAILABLE_STATS_SECONDARY,
    STAT_BONUS_FOR_RESETS,
    XP_PER_LEVEL_BASE,
    XP_PER_LEVEL_DELTA,
)
from utils.bitstream_utils import simple_bit_stream


class client_character:
    """Represents a client character with all game-related attributes."""

    def __init__(self):
        # Core character data
        self.id: int = 0
        self.client_local_id: int = 0
        self.look_type: int = 0x7
        self.is_turned_off: int = 0x9

        # Level progression - must be set before HP/MP calculations
        self.title_minus_one: int = 0
        self.degree_minus_one: int = 0

        # Stats - MP (now that title/degree are initialized)
        self.max_mp: int = self.max_mp_base
        self.current_mp: int = self.max_mp_base

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
        self.available_title_stats: int = AVAILABLE_STATS_PRIMARY[0]
        self.available_degree_stats: int = AVAILABLE_STATS_PRIMARY[0]

        # Character identity
        self.is_gender_female: bool = False
        self.name: str = "Test"
        self.clan: Optional[clan] = DEFAULT_CLAN

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
        self.guild: guild = guild.NONE
        self.clan_rank: clan_rank = clan_rank.NEOPHYTE
        self.player_index: int = 0

        # Position and orientation
        self.x: float = 0.0
        self.y: float = 150.0
        self.z: float = 0.0
        self.angle: float = 0.0

        # Health and defense (now that title/degree are initialized)
        self.current_hp: int = self.max_hp_base
        self.max_hp: int = self.max_hp_base
        self.p_def: int = 0
        self.m_def: int = 0

        # Combat and karma
        self.karma: karma_types = karma_types.NEUTRAL
        self.items: Dict[belonging_slot, int] = {}
        self.p_atk: int = 0
        self.m_atk: int = 0
        self.karma_count: int = 0

    @property
    def max_hp_base(self) -> int:
        """Calculate base max HP from title and degree."""
        title_hp = HEALTH_AT_TITLE[self.title_minus_one % 60]
        degree_hp = HEALTH_AT_DEGREE[self.degree_minus_one % 60]
        return title_hp + degree_hp - 100

    @property
    def max_mp_base(self) -> int:
        """Calculate base max MP from title and degree."""
        title_mp = MP_AT_TITLE[self.title_minus_one % 60]
        degree_mp = MP_AT_DEGREE[self.degree_minus_one % 60]
        return title_mp + degree_mp - 100

    @property
    def xp_to_level_up(self) -> int:
        """Calculate XP needed to level up."""
        if self.title_minus_one % 60 == 59 and self.degree_minus_one % 60 == 59:
            return 1

        min_level = min(self.title_minus_one, self.degree_minus_one)
        max_level = max(self.title_minus_one, self.degree_minus_one)

        return int(
            XP_PER_LEVEL_BASE[max_level] + XP_PER_LEVEL_DELTA[max_level] * min_level
        )

    def level_up(self, new_title_level: int, new_degree_level: int):
        """Level up the character with new title and degree levels."""
        if new_title_level > self.title_minus_one:
            bonus_stats_from_reset = (
                self.title_minus_one // 60 * STAT_BONUS_FOR_RESETS[self.title_minus_one]
            )
            self.available_title_stats = (
                self.available_title_stats
                + AVAILABLE_STATS_PRIMARY[new_title_level]
                + bonus_stats_from_reset
            )
            self.available_degree_stats = (
                self.available_degree_stats + AVAILABLE_STATS_SECONDARY[new_title_level]
            )
        elif new_degree_level > self.degree_minus_one:
            bonus_stats_from_reset = (
                self.degree_minus_one
                // 60
                * STAT_BONUS_FOR_RESETS[self.degree_minus_one]
            )
            self.available_degree_stats = (
                self.available_degree_stats
                + AVAILABLE_STATS_PRIMARY[new_title_level]
                + bonus_stats_from_reset
            )
            self.available_title_stats = (
                self.available_title_stats + AVAILABLE_STATS_SECONDARY[new_title_level]
            )

    def to_character_list_bytearray(self) -> bytearray:
        """Convert character to bytearray for character list with padded name."""
        stream = simple_bit_stream()
        look_type = 0x79 if self.is_not_queued_for_deletion else 0x19
        stream.write_bytes(bytes([0x6C, 0x00, 0x2C, 0x01, 0x00, 0x00, 0x04]))
        stream.write_int(self.player_index, 16)
        stream.write_bytes(bytes([0x08, 0x40, 0x60]))
        stream.write_int(look_type, 8)
        stream.write_int(self.max_hp, 6)
        stream.write_int(1, 2)
        stream.write_int(self.max_hp >> 6, 8)
        stream.write_int(self.max_mp, 6)
        stream.write_int(self.max_hp >> 14, 2)
        stream.write_int(self.max_mp >> 6, 8)
        stream.write_int(self.current_strength, 6)
        stream.write_int(self.max_mp >> 14, 2)
        stream.write_int(self.current_strength >> 6, 8)
        stream.write_int(self.current_agility, 6)
        stream.write_int(self.current_strength >> 14, 2)
        stream.write_int(self.current_agility >> 6, 8)
        stream.write_int(self.current_accuracy, 6)
        stream.write_int(self.current_agility >> 14, 2)
        stream.write_int(self.current_accuracy >> 6, 8)
        stream.write_int(self.current_endurance, 6)
        stream.write_int(self.current_accuracy >> 14, 2)
        stream.write_int(self.current_endurance >> 6, 8)
        stream.write_int(self.current_earth, 6)
        stream.write_int(self.current_endurance >> 14, 2)
        stream.write_int(self.current_earth >> 6, 8)
        stream.write_int(self.current_air, 6)
        stream.write_int(self.current_earth >> 14, 2)
        stream.write_int(self.current_air >> 6, 8)
        stream.write_int(self.current_water, 6)
        stream.write_int(self.current_air >> 14, 2)
        stream.write_int(self.current_water >> 6, 8)
        stream.write_int(self.current_fire, 6)
        stream.write_int(self.current_water >> 14, 2)
        stream.write_int(self.current_fire >> 6, 8)
        stream.write_int(self.p_def, 6)
        stream.write_int(self.current_fire >> 14, 2)
        stream.write_int(self.p_def >> 6, 8)
        stream.write_int(self.m_def, 6)
        stream.write_int(self.p_def >> 14, 2)
        stream.write_int(self.m_def >> 6, 8)
        stream.write_int(self.karma, 6)
        stream.write_int(self.m_def >> 14, 2)
        stream.write_int(self.max_satiety, 6)
        stream.write_int(self.karma >> 6, 2)
        stream.write_int(self.max_satiety >> 6, 8)
        stream.write_int(self.title_minus_one, 6)
        stream.write_int(self.max_satiety >> 14, 2)
        stream.write_int(self.title_minus_one >> 6, 8)
        stream.write_int(self.degree_minus_one, 6)
        stream.write_int(self.title_minus_one >> 14, 2)
        stream.write_int(self.degree_minus_one >> 6, 8)
        stream.write_int(self.title_xp, 6)
        stream.write_int(self.degree_minus_one >> 14, 2)
        stream.write_int(self.title_xp >> 6, 24)
        stream.write_int(self.degree_xp, 6)
        stream.write_int(self.title_xp >> 30, 2)
        stream.write_int(self.degree_xp >> 6, 24)
        stream.write_int(self.current_satiety, 6)
        stream.write_int(self.degree_xp >> 30, 2)
        stream.write_int(self.current_satiety >> 6, 8)
        stream.write_int(self.current_hp, 6)
        stream.write_int(self.current_satiety >> 14, 2)
        stream.write_int(self.current_hp >> 6, 8)
        stream.write_int(self.current_mp, 6)
        stream.write_int(self.current_hp >> 14, 2)
        stream.write_int(self.current_mp >> 6, 8)
        stream.write_int(self.available_title_stats, 6)
        stream.write_int(self.current_mp >> 14, 2)
        stream.write_int(self.available_title_stats >> 6, 8)
        stream.write_int(self.available_degree_stats, 6)
        stream.write_int(self.available_title_stats >> 14, 2)
        stream.write_int(self.available_degree_stats >> 6, 8)
        stream.write_int(0b111010, 6)
        stream.write_int(self.available_degree_stats >> 14, 2)
        stream.write_bytes(bytes([0xC0, 0xC8, 0xC8]))
        name_encoded = self.name.encode("cp1251")[:19].ljust(19, b"\x00")
        stream.write_int(0b100 if self.is_gender_female else 0, 8)
        stream.write_int(name_encoded[0], 6)
        stream.write_int(0, 2)
        stream.write_int(name_encoded[1], 6)
        stream.write_int(name_encoded[0] >> 6, 2)
        stream.write_int(name_encoded[2], 6)
        stream.write_int(name_encoded[1] >> 6, 2)
        stream.write_int(name_encoded[3], 6)
        stream.write_int(name_encoded[2] >> 6, 2)
        stream.write_int(name_encoded[4], 6)
        stream.write_int(name_encoded[3] >> 6, 2)
        stream.write_int(name_encoded[5], 6)
        stream.write_int(name_encoded[4] >> 6, 2)
        stream.write_int(name_encoded[6], 6)
        stream.write_int(name_encoded[5] >> 6, 2)
        stream.write_int(name_encoded[7], 6)
        stream.write_int(name_encoded[6] >> 6, 2)
        stream.write_int(name_encoded[8], 6)
        stream.write_int(name_encoded[7] >> 6, 2)
        stream.write_int(name_encoded[9], 6)
        stream.write_int(name_encoded[8] >> 6, 2)
        stream.write_int(name_encoded[10], 6)
        stream.write_int(name_encoded[9] >> 6, 2)
        stream.write_int(name_encoded[11], 6)
        stream.write_int(name_encoded[10] >> 6, 2)
        stream.write_int(name_encoded[12], 6)
        stream.write_int(name_encoded[11] >> 6, 2)
        stream.write_int(name_encoded[13], 6)
        stream.write_int(name_encoded[12] >> 6, 2)
        stream.write_int(name_encoded[14], 6)
        stream.write_int(name_encoded[13] >> 6, 2)
        stream.write_int(name_encoded[15], 6)
        stream.write_int(name_encoded[14] >> 6, 2)
        stream.write_int(name_encoded[16], 6)
        stream.write_int(name_encoded[15] >> 6, 2)
        stream.write_int(name_encoded[17], 6)
        stream.write_int(name_encoded[16] >> 6, 2)
        stream.write_int(name_encoded[18], 6)
        stream.write_int(name_encoded[17] >> 6, 2)
        stream.write_int(self.face_type, 6)
        stream.write_int(name_encoded[18] >> 6, 2)
        stream.write_int(self.hair_style, 6)
        stream.write_int(self.face_type >> 6, 2)
        stream.write_int(self.hair_color, 6)
        stream.write_int(self.hair_style >> 6, 2)
        stream.write_int(self.tattoo, 6)
        stream.write_int(self.hair_color >> 6, 2)
        stream.write_int(self.boot_model_id, 6)
        stream.write_int(self.tattoo >> 6, 2)
        stream.write_int(self.pants_model_id, 6)
        stream.write_int(self.boot_model_id >> 6, 2)
        stream.write_int(self.armor_model_id, 6)
        stream.write_int(self.pants_model_id >> 6, 2)
        stream.write_int(self.helmet_model_id, 6)
        stream.write_int(self.armor_model_id >> 6, 2)
        stream.write_int(self.gloves_model_id, 6)
        stream.write_int(self.helmet_model_id >> 6, 2)
        stream.write_int(0, 6)
        stream.write_int(self.gloves_model_id >> 6, 2)
        stream.write_bytes(bytes([0xC0, 0xC0, 0x00, 0xFC, 0xFF, 0xFF, 0xFF]))
        stream.write_int(1 if self.is_not_queued_for_deletion else 0, 7)
        stream.write_int(1, 1)
        stream.write_bytes(
            bytes(
                [
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                ]
            )
        )
        return bytearray(stream.to_bytes())

    def to_game_data_bytearray(self) -> bytearray:
        """Convert character to bytearray for game data transmission."""
        from .world_coords import world_coords

        stream = simple_bit_stream()

        # Header
        stream.write_bytes(bytes([0x00, 0x01, 0x2C, 0x01, 0x00, 0x00, 0x04]))
        stream.write_int(self.player_index, 16)
        stream.write_bytes(bytes([0x08, 0x00]))

        # Character name encoding
        name_encoded = self.name.encode("cp1251")
        name_len = len(name_encoded) + 1

        stream.write_int(((name_len & 0b111) << 5) + 2, 8)
        stream.write_int(
            ((name_encoded[0] & 0b111) << 5) + ((name_len & 0b11111000) >> 3), 8
        )

        for i in range(1, len(name_encoded)):
            stream.write_int(
                ((name_encoded[i] & 0b111) << 5)
                + ((name_encoded[i - 1] & 0b11111000) >> 3),
                8,
            )

        stream.write_int((name_encoded[-1] & 0b11111000) >> 3, 8)

        # clan information
        if self.clan is None or self.clan.clan_id == DEFAULT_CLAN.clan_id:
            stream.write_bytes(bytes([0x00, 0x6E]))
        else:
            clan_name_encoded = self.clan.name.encode("cp1251")
            clan_name_length = len(clan_name_encoded)
            stream.write_int((clan_name_length & 0b111) << 5, 8)
            stream.write_int(
                ((clan_name_encoded[0] & 0b1111111) << 1)
                + ((clan_name_length & 0b1000) >> 3),
                8,
            )

            for i in range(1, clan_name_length):
                stream.write_int(
                    ((clan_name_encoded[i] & 0b1111111) << 1)
                    + ((clan_name_encoded[i - 1] & 0b10000000) >> 7),
                    8,
                )

            stream.write_int(
                0b01100000
                + (self.clan_rank.value << 1)
                + ((clan_name_encoded[-1] & 0b10000000) >> 7),
                8,
            )

        # Fixed bytes and coordinates
        stream.write_bytes(bytes([0x1A, 0x98, 0x18, 0x19]))

        # Encode and write coordinates
        x = world_coords.encode_server_coord(self.x)
        y = world_coords.encode_server_coord(self.y)
        z = world_coords.encode_server_coord(self.z)
        t = world_coords.encode_server_coord(self.angle)

        stream.write_bytes(bytes(x))
        stream.write_bytes(bytes(y))
        stream.write_bytes(bytes(z))
        stream.write_bytes(bytes(t))

        stream.write_bytes(bytes([0x37, 0x0D, 0x79, 0x00, 0xF0]))

        # Equipment slots
        equipment_slots = [
            belonging_slot.HELMET,
            belonging_slot.AMULET,
            belonging_slot.SHIELD,
            belonging_slot.CHESTPLATE,
            belonging_slot.GLOVES,
            belonging_slot.BELT,
            belonging_slot.BRACELET_LEFT,
            belonging_slot.BRACELET_RIGHT,
            belonging_slot.RING_1,
            belonging_slot.RING_2,
            belonging_slot.RING_3,
            belonging_slot.RING_4,
            belonging_slot.PANTS,
            belonging_slot.BOOTS,
            belonging_slot.GUILD,
            belonging_slot.MAP_BOOK,
            belonging_slot.RECIPE_BOOK,
            belonging_slot.MANTRA_BOOK,
        ]

        for slot in equipment_slots:
            stream.write_int(0x04 if not self._is_item_slot_empty(slot) else 0x00, 8)
            stream.write_int(0x00, 8)

        # Padding
        stream.write_bytes(bytes([0x00, 0x00, 0x00, 0x00]))

        # More equipment slots
        more_slots = [
            belonging_slot.INKPOT,
            belonging_slot.MONEY,
            belonging_slot.BACKPACK,
            belonging_slot.KEY_1,
            belonging_slot.KEY_2,
            belonging_slot.MISSION,
            belonging_slot.INVENTORY_1,
            belonging_slot.INVENTORY_2,
            belonging_slot.INVENTORY_3,
            belonging_slot.INVENTORY_4,
            belonging_slot.INVENTORY_5,
            belonging_slot.INVENTORY_6,
            belonging_slot.INVENTORY_7,
            belonging_slot.INVENTORY_8,
            belonging_slot.INVENTORY_9,
            belonging_slot.INVENTORY_10,
        ]

        for slot in more_slots:
            stream.write_int(0x04 if not self._is_item_slot_empty(slot) else 0x00, 8)
            stream.write_int(0x00, 8)

        # More padding
        stream.write_bytes(bytes([0x00] * 20))

        # Special slots
        special_slots = [
            belonging_slot.SPECIAL_1,
            belonging_slot.SPECIAL_2,
            belonging_slot.SPECIAL_3,
            belonging_slot.SPECIAL_4,
            belonging_slot.SPECIAL_5,
            belonging_slot.SPECIAL_6,
            belonging_slot.SPECIAL_7,
            belonging_slot.SPECIAL_8,
            belonging_slot.SPECIAL_9,
            belonging_slot.AMMO,
            belonging_slot.SPEEDHACK_MANTRA,
        ]

        for slot in special_slots:
            stream.write_int(0x04 if not self._is_item_slot_empty(slot) else 0x00, 8)
            stream.write_int(0x00, 8)

        # Final padding
        stream.write_bytes(bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0]))

        # 150 zero bytes
        stream.write_bytes(bytes([0x00] * 150))

        # Health and mana encoding
        stream.write_int(((self.current_hp & 0b111) << 5) + 0b10011, 8)
        stream.write_int((self.current_hp & 0b11111111000) >> 3, 8)
        stream.write_int(
            ((self.max_hp & 0b11) << 6)
            + (0b100 << 3)
            + ((self.current_hp & 0b11100000000000) >> 11),
            8,
        )
        stream.write_int((self.max_hp & 0b1111111100) >> 2, 8)
        stream.write_int(
            (self.karma.value << 4) + ((self.max_hp & 0b11110000000000) >> 10), 8
        )

        # Title and degree encoding
        to_encode = self.degree_minus_one * 100 + self.title_minus_one
        stream.write_int(((to_encode & 0b111111) << 2) + 2, 8)
        stream.write_int((to_encode & 0b11111111000000) >> 6, 8)

        stream.write_int(0x80, 8)

        # guild information
        if self.guild == guild.NONE:
            stream.write_int(0x00, 8)
        else:
            stream.write_int((1 << 7) + (self.guild.value << 1), 8)

        # Money encoding
        stream.write_int(((self.money & 0b1111) << 4) + self.guild_level_minus_one, 8)
        stream.write_int((self.money & 0b111111110000) >> 4, 8)
        stream.write_int((self.money & 0b11111111000000000000) >> 12, 8)
        stream.write_int((self.money & 0b1111111100000000000000000000) >> 20, 8)
        stream.write_int((self.money & 0b11110000000000000000000000000000) >> 28, 8)
        # Convert to bytearray and set packet length
        data = bytearray(stream.to_bytes())
        data[0] = len(data) % 256

        return data

    def _is_item_slot_empty(self, slot: belonging_slot) -> bool:
        """Check if an item slot is empty."""
        return slot not in self.items or self.items[slot] == 0
