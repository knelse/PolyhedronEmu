"""
Client character data model.
"""

from typing import Dict, Optional
from .enums import (
    Guild,
    ClanRank,
    KarmaTypes,
    BelongingSlot,
    Clan,
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
from utils.bitstream_utils import SimpleBitStream


class ClientCharacter:
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
        self.karma: KarmaTypes = KarmaTypes.NEUTRAL
        self.items: Dict[BelongingSlot, int] = {}
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
        stream = SimpleBitStream()
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
        for char in name_encoded:
            print(char)
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
