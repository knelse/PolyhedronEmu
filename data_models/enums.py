"""
Enums and supporting classes for data models.
"""

from enum import IntEnum
from typing import Dict


class GameObjectKind(IntEnum):
    """Game object kind enumeration."""

    ALCHEMY = 0
    CROSSBOW = 1
    CROSSBOW_NEW = 2
    ARMOR = 3
    ARMOR_NEW = 4
    ARMOR_OLD = 5
    AXE = 6
    AXE_NEW = 7
    POWDER = 8
    GUILD = 9
    MAGICAL = 10
    MAGICAL_NEW = 11
    MANTRA_BLACK = 12
    MANTRA_WHITE = 13
    MAP = 14
    MONSTER = 15
    QUEST = 16
    SWORD = 17
    SWORD_NEW = 18
    UNIQUE = 19
    PREF = 20
    CLIENT = 21
    UNKNOWN = 22
    LOOT_BAG = 23
    FOOD = 24
    BRUSHWOOD = 25
    FISTS = 26


class GameObjectType(IntEnum):
    """Game object type enumeration."""

    PREF_AXE_SWORD = 0
    PREF_CROSSBOW = 1
    PREF_CHESTPLATE = 2
    PREF_BELT_BOOTS_GLOVES_HELMET_PANTS = 3
    PREF_AMULET_BRACELET = 4
    PREF_RING = 5
    PREF_ROBE = 6
    PREF_CASTLE = 7
    PREF_SHIELD = 8
    PREF_QUEST = 9
    FLOWER = 10
    METAL = 11
    MINERAL = 12
    AMULET = 13
    AMULET_UNIQUE = 14
    CHESTPLATE = 15
    ROBE = 16
    ROBE_QUEST = 17
    ROBE_UNIQUE = 18
    CHESTPLATE_QUEST = 19
    CHESTPLATE_UNIQUE = 20
    BELT = 21
    BELT_QUEST = 22
    BELT_UNIQUE = 23
    BRACELET = 24
    BRACELET_UNIQUE = 25
    GLOVES = 26
    GLOVES_QUEST = 27
    GLOVES_UNIQUE = 28
    HELMET = 29
    HELMET_PREMIUM = 30
    HELMET_QUEST = 31
    HELMET_UNIQUE = 32
    PANTS = 33
    PANTS_QUEST = 34
    PANTS_UNIQUE = 35
    RING = 36
    RING_SPECIAL = 37
    RING_UNIQUE = 38
    SHIELD = 39
    SHIELD_QUEST = 40
    SHIELD_UNIQUE = 41
    BOOTS = 42
    BOOTS_QUEST = 43
    BOOTS_UNIQUE = 44
    CASTLE_CRYSTAL = 45
    CASTLE_STONE = 46
    GUILD_BAG = 47
    FLAG = 48
    GUILD = 49
    LETTER = 50
    LOTTERY = 51
    MANTRA_BLACK = 52
    MANTRA_WHITE = 53
    MONSTER = 54
    MONSTER_CASTLE_STONE = 55
    MONSTER_EVENT = 56
    MONSTER_EVENT_FLYING = 57
    MONSTER_FLYING = 58
    MONSTER_TOWER_SPIRIT = 59
    MONSTER_CASTLE_SPIRIT = 60
    ELIXIR_CASTLE = 61
    ELIXIR_TRAP = 62
    POWDER = 63
    POWDER_AREA = 64
    POWDER_EVENT = 65
    POWDER_GUILD = 66
    SCROLL = 67
    SPECIAL = 68
    SPECIAL_CRUSADER_GAPCLOSE = 69
    SPECIAL_INQUISITOR_TELEPORT = 70
    SPECIAL_ARCHMAGE_TELEPORT = 71
    SPECIAL_MASTER_OF_STEEL_WHIRLWIND = 72
    SPECIAL_DRUID_WOLF = 73
    SPECIAL_THIEF_STEAL = 74
    SPECIAL_MASTER_OF_STEEL_SUICIDE = 75
    SPECIAL_NECROMANCER_FLYER = 76
    SPECIAL_NECROMANCER_RESURRECTION = 77
    SPECIAL_NECROMANCER_ZOMBIE = 78
    SPECIAL_BANDIER_FLAG = 79
    SPECIAL_BANDIER_DISPEL_CONTROL = 80
    SPECIAL_BANDIER_FORTIFY = 81
    KEY = 82
    MAP = 83
    EAR_STRING = 84
    CRYSTAL = 85
    CROSSBOW_ITEM = 86
    CROSSBOW_QUEST = 87
    AXE_ITEM = 88
    AXE_QUEST = 89
    SWORD_ITEM = 90
    SWORD_QUEST = 91
    SWORD_UNIQUE = 92
    X2_DEGREE = 93
    X2_BOTH = 94
    X2_TITLE = 95
    EAR = 96
    BEAD = 97
    PACKET = 98
    UNKNOWN = 99
    CLIENT = 100
    LOOT_BAG = 101
    FOOD_APPLE = 102
    FOOD_PEAR = 103
    FOOD_MEAT = 104
    FOOD_BREAD = 105
    FOOD_FISH = 106
    ALCHEMY_BRUSHWOOD = 107
    FISTS = 108


class ItemSuffix(IntEnum):
    """Item suffix enumeration."""

    NONE = 0
    # ---- Rings ----
    HEALTH = 1
    ETHER = 2
    ACCURACY = 3
    AIR = 4
    DURABILITY = 5
    LIFE = 6
    PRECISION = 7
    ENDURANCE = 8
    FIRE = 9
    ABSORPTION = 10
    MEDITATION = 11
    STRENGTH = 12
    EARTH = 13
    VALUE = 14
    SAFETY = 15
    PRANA = 16
    AGILITY = 17
    WATER = 18
    # ---- Crossbows ----
    CRUELTY = 19
    CHAOS = 20
    RANGE = 21
    # ETHER,
    EXHAUSTION = 22
    HASTE = 23
    PENETRATION = 24
    DISTANCE = 25
    RADIANCE = 26
    VALOR = 27
    SPEED = 28
    INSTABILITY = 29
    MASTERY = 30
    DISEASE = 31
    DAMAGE = 32
    DISORDER = 33
    DECAY = 34
    FATIGUE = 35
    # VALUE,
    # ---- Other weapons ----
    # CRUELTY,
    # CHAOS,
    # INSTABILITY,
    DEVASTATION = 36
    # VALUE,
    # EXHAUSTION,
    # HASTE,
    # ETHER,
    # RANGE,
    WEAKNESS = 37
    # VALOR,
    # SPEED,
    # FATIGUE,
    # DISTANCE,
    # PENETRATION,
    # DAMAGE,
    # DISORDER,
    # DISEASE,
    # DECAY,
    INTERDICT = 38
    # ---- Robes ----
    # SAFETY,
    # PRANA,
    # FIRE,
    # DURABILITY,
    # LIFE,
    DRAGON = 39
    # VALUE,
    # HEALTH,
    # EARTH,
    # ETHER,
    DEFLECTION = 40
    # MEDITATION,
    DURABILITY_OLD = 41  # Different stat reqs
    LIFE_OLD = 42
    # WATER,
    ECLIPSE = 43
    SAFETY_OLD = 44
    PRANA_OLD = 45
    DEFLECTION_OLD = 46
    MEDITATION_OLD = 47
    # AIR,
    ARCHMAGE = 48
    HEALTH_OLD = 49
    ETHER_OLD = 50
    DRAGON_OTHER = 51
    # ---- Bracelets, Amulets ----
    # SAFETY,
    # ETHER,
    # DURABILITY,
    # HEALTH,
    # RADIANCE,
    # ABSORPTION,
    # MEDITATION,
    # VALUE,
    # DEFLECTION,
    # PRECISION,
    # DAMAGE,
    # ---- Helmets, Gloves, Belts, Pants, Boots ----
    # HEALTH,
    # VALUE,
    # DURABILITY,
    # MEDITATION,
    # ABSORPTION,
    # PRECISION,
    # SAFETY,
    # ETHER,
    # ---- Chestplates ----
    # DEFLECTION,
    # LIFE,
    # AGILITY,
    # WATER,
    # VALUE,
    CONCENTRATION = 52
    # VALOR,
    # SAFETY,
    # MEDITATION,
    MAJESTY_OLD = 53
    # AIR,
    # STRENGTH,
    INTEGRITY = 54
    # DURABILITY,
    INVINCIBILITY = 55
    # PRANA,
    CONCENTRATION_OLD = 56
    # FIRE,
    # AGILITY,
    # ABSORPTION,
    # HEALTH,
    # STRENGTH,
    # EARTH,
    ELEMENTS = 57
    MAJESTY = 58
    # ---- Shields ----
    # DEFLECTION,
    # LIFE,
    AGILITY_OLD = 59
    # WATER,
    # VALUE,
    # CONCENTRATION,
    # VALOR,
    # SAFETY,
    # MEDITATION,
    # MAJESTY_OLD,
    # AIR,
    # STRENGTH,
    INTEGRITY_OTHER = 60
    # DURABILITY,
    # INVINCIBILITY,
    # PRANA,
    # CONCENTRATION_OLD,
    # FIRE,
    # AGILITY,
    # ELEMENTS,
    # ABSORPTION,
    # HEALTH,
    STRENGTH_OLD = 61
    # EARTH,
    ELEMENTS_OLD = 62
    # MAJESTY,
    ELEMENTS_NEW = 63
    # ---- Quest ----
    SECRET = 64
    EXISTENCE = 65
    ADVENTURE = 66
    MYTH = 67
    LEGEND = 68
    SILENCE = 69
    BEING = 70
    PEACE = 71
    PROPHECY = 72
    HIKE = 73
    # ---- Crystal ----
    # STRENGTH,
    ENERGY = 74
    PERSISTENCE = 75
    # DEFLECTION,
    # ---- Castle ---- TODO: later
    INVINCIBILITY_CASTLE = 76
    RELIABILITY = 77
    BLINDING = 78
    PURIFICATION = 79
    CURSE = 80
    ERADICATION = 81
    LIFE_CASTLE = 82
    INVINCIBILITY_CASTLE_OLD = 83
    FRIGHT = 84
    PUNISHMENT = 85
    DEVASTATION_CASTLE = 86
    ERADICATION_OLD = 87
    LIFE_CASTLE_OLD = 88
    HALT = 89
    SHACKLE = 90
    RELIABILITY_OLD = 91
    DEVASTATION_CASTLE_OLD = 92
    RULE = 93
    DELIVERANCE = 94
    WHIRL = 95


class KarmaTypes(IntEnum):
    """Character karma types enumeration."""

    VERY_BAD = 0x1
    BAD = 0x2
    NEUTRAL = 0x3
    GOOD = 0x4
    BENIGN = 0x5


class Locale(IntEnum):
    """Locale enumeration."""

    RUSSIAN = 0
    ENGLISH = 1
    ITALIAN = 2
    PORTUGUESE = 3


class Guild(IntEnum):
    """Character guild enumeration."""

    NONE = 0
    Assasin = (0x1,)
    Crusader = (0x2,)
    Inquisitor = (0x3,)
    Hunter = (0x4,)
    Archmage = (0x5,)
    Barbarian = (0x6,)
    Druid = (0x7,)
    Thief = (0x8,)
    MasterOfSteel = (0x9,)
    Armorer = (0xA,)
    Blacksmith = (0xB,)
    Warlock = (0xC,)
    Necromancer = (0xD,)
    Bandier = (0xE,)
    ASSASIN = 1
    CRUSADER = 2
    INQUISITOR = 3
    HUNTER = 4
    ARCHMAGE = 5
    BARBARIAN = 6
    DRUID = 7
    THIEF = 8
    MASTER_OF_STEEL = 9
    ARMORER = 10
    BLACKSMITH = 11
    WARLOCK = 12
    NECROMANCER = 13
    BANDIER = 14


class ClanRank(IntEnum):
    """Character clan rank enumeration."""

    SENIOR = 0x0
    SENESCHAL = 0x1
    VASSAL = 0x2
    NEOPHYTE = 0x3
    # Not saved in game
    CANDIDATE = 0x4
    KICKED = 0x5
    # Breaks client if used after clan join
    ACCEPTED = 0x6


class BelongingSlot(IntEnum):
    """Equipment slot enumeration."""

    HELMET = 0
    AMULET = 1
    SHIELD = 2
    CHESTPLATE = 3
    GLOVES = 4
    BELT = 5
    BRACELET_LEFT = 6
    BRACELET_RIGHT = 7
    RING_1 = 8
    RING_2 = 9
    RING_3 = 10
    RING_4 = 11
    PANTS = 12
    BOOTS = 13
    GUILD = 14
    MAP_BOOK = 15
    RECIPE_BOOK = 16
    MANTRA_BOOK = 17
    INKPOT = 20
    INVENTORY_1 = 26
    INVENTORY_2 = 27
    INVENTORY_3 = 28
    INVENTORY_4 = 29
    INVENTORY_5 = 30
    INVENTORY_6 = 31
    INVENTORY_7 = 32
    INVENTORY_8 = 33
    INVENTORY_9 = 34
    INVENTORY_10 = 35
    MONEY = 1000
    BACKPACK = 1001
    KEY_1 = 1002
    KEY_2 = 1003
    MISSION = 1004
    SPECIAL_1 = 1005
    SPECIAL_2 = 1006
    SPECIAL_3 = 1007
    SPECIAL_4 = 1008
    SPECIAL_5 = 1009
    SPECIAL_6 = 1010
    SPECIAL_7 = 1011
    SPECIAL_8 = 1012
    SPECIAL_9 = 1013
    AMMO = 1014
    SPEEDHACK_MANTRA = 1015
    MAIN_HAND = 1016
    UNKNOWN = -1


class ChatType(IntEnum):
    """Chat type enumeration combining private and public chat types."""

    # Public chat types
    WHISPER = 1
    NORMAL = 2
    TRADE = 3
    GM = 5
    GM_OUTGOING = 999

    # Private chat types
    CLAN = 4
    GROUP = 5  # Note: conflicts with GM = 5
    SAY_CLAN = 11
    SAY_GROUP = 12
    SAY_ALLY = 13
    PM = 15

    def is_public(self) -> bool:
        """Check if this chat type is a public chat type."""
        return self.value in {1, 2, 3, 5, 999}


class MonsterType(IntEnum):
    """Monster type enumeration."""

    ПАЛОЧНИК = 0
    ПАЛОЧНИК_СТЕПНОЙ = 1
    ПАЛОЧНИК_ЛЕСНОЙ = 2
    ПАЛОЧНИК_ПЕЩЕРНЫЙ = 3
    ПСОГЛАВЕЦ = 4
    ПСОГЛАВЕЦ_СТЕПНОЙ = 5
    ПСОГЛАВЕЦ_ЛЕСНОЙ = 6
    ПСОГЛАВЕЦ_ПЕЩЕРНЫЙ = 7
    ТРУХЛЯВЫЙ_РЫЦАРЬ = 8
    РЖАВЫЙ_РЫЦАРЬ = 9
    НЕПРИКАЯННЫЙ_РЫЦАРЬ = 10
    ЗОЛОТОЙ_РЫЦАРЬ = 11
    ГИГАНТСКИЙ_РЫЦАРЬ = 12
    ВОЗДУШНЫЙ_РЫЦАРЬ = 13
    ЛЕТУН = 14
    ШТОРМОВОЙ_ЛЕТУН = 15
    ОГНЕННЫЙ_ЛЕТУН = 16
    ЯНТАРНЫЙ_ЛЕТУН = 17
    ГИГАНТСКИЙ_ЛЕТУН = 18
    ЗЕМЛЯНОЙ_ГОЛЕМ = 19
    ПЕСОЧНЫЙ_ГОЛЕМ = 20
    ГЛИНЯНЫЙ_ГОЛЕМ = 21
    СВОБОДНЫЙ_ГОЛЕМ = 22
    ГИГАНТСКИЙ_ГОЛЕМ = 23
    БАНГВИЛЬСКАЯ_СКОЛОПЕНДРА = 24
    ЦАРСКАЯ_СКОЛОПЕНДРА = 25
    СКЕЛЕТ = 26
    СКЕЛЕТ_ЛЕСНОЙ = 27
    СКЕЛЕТ_УМРАДСКИЙ = 28
    СКЕЛЕТ_ВОЗДУШНЫЙ = 29
    СКЕЛЕТ_ПЕЩЕРНЫЙ = 30
    ЛИЧ = 31
    ГИГАНТСКИЙ_СКЕЛЕТ = 32
    ВОЗДУШНЫЙ_ЛИЧ = 33
    АССАСИН2 = 34
    ВЕПРЬ = 35
    БЕШЕНЫЙ_ВЕПРЬ = 36
    СУХОЙ_ВЕПРЬ = 37
    ВОЗДУШНЫЙ_ВЕПРЬ = 38
    ЖЕЛЕЗНЫЙ_ВЕПРЬ = 39
    ОГНЕННЫЙ_ВЕПРЬ = 40
    ГИГАНТСКИЙ_ВЕПРЬ = 41
    ЦИАНОС = 42
    ЦИАНОС_ТЁМНЫЙ = 43
    ЦИАНОС_СУХОЙ = 44
    ЦИАНОС_ЖЕЛЕЗНЫЙ = 45
    ЦИАНОС_ВОЗДУШНЫЙ = 46
    ЦИАНОС_ГИГАНТСКИЙ = 47
    ВОЛК = 48
    СТЕПНОЙ_ВОЛК = 49
    ЛЕДЯНОЙ_ВОЛК = 50
    СУХОЙ_ВОЛК = 51
    ЖЕЛЕЗНЫЙ_ВОЛК = 52
    АДСКИЙ_ВОЛК = 53
    ПАУК = 54
    СЕРНЫЙ_ПАУК = 55
    СУХОЙ_ПАУК = 56
    ЖЕЛЕЗНЫЙ_ПАУК = 57
    ОГНЕННЫЙ_ПАУК = 58
    ЧЁРНАЯ_ВДОВА = 59
    ГИГАНТСКИЙ_ПАУК = 60
    ВОЗДУШНЫЙ_ПАУК = 61
    САЛАМАНДРА = 62
    НОМРАДСКАЯ_САЛАМАНДРА = 63
    ЗЕМЛЯНАЯ_САЛАМАНДРА = 64
    ЖЕЛЕЗНАЯ_САЛАМАНДРА = 65
    САЛАМАНДИГА = 66
    КРАСНЫЙ_СКОРПИОН = 67
    СКОРПИОН = 68
    СИНИЙ_СКОРПИОН = 69
    ОГНЕННЫЙ_СКОРПИОН = 70
    ТИФОН = 71
    ДЫМНЫЙ_ТИФОН = 72
    ВИЗЖАЩИЙ_ТИФОН = 73
    ЖЕЛЕЗНЫЙ_ТИФОН = 74
    ОГНЕННЫЙ_ТИФОН = 75
    ГИГАНТСКИЙ_ТИФОН = 76
    ЛЮДОЕД = 77
    СЕРНЫЙ_ЛЮДОЕД = 78
    ПЕЩЕРНЫЙ_ЛЮДОЕД = 79
    ГИГАНТСКИЙ_ЛЮДОЕД = 80
    НИФОН = 81
    ЗЕЛЁНЫЙ_ДРАКОН = 82
    СИНИЙ_ДРАКОН = 83
    КРАСНЫЙ_ДРАКОН = 84
    СТАЛЬНОЙ_ДРАКОН = 85
    ГИГАНТСКИЙ_ДРАКОН = 86
    КОШКА = 87
    БЫК = 88
    ТРОПОС = 89
    БЕШЕНЫЙ_ТРОПОС = 90
    ТОРФЯНОЙ_ТРОПОС = 91
    КОРОЛЕВСКИЙ_ТРОПОС = 92
    ВОЗДУШНЫЙ_ТРОПОС = 93
    МАМОНТ = 94
    ЖЕЛЕЗНЫЙ_МАМОНТ = 95
    СНЕЖНЫЙ_МАМОНТ = 96
    УГОЛЬНЫЙ_МАМОНТ = 97
    ЗОМБИ = 98
    СЕРЫЙ_ЗОМБИ = 99
    ЗОМБАДЕР = 100
    ГИГАНТСКИЙ_ЗОМБИ = 101
    ЗАЧАРОВАННОЕ_ДЕРЕВО = 102
    КРАСНОЕ_ДЕРЕВО = 103
    МЁРТВОЕ_ДЕРЕВО = 104
    ГРАНИТНЫЙ_КАМНЕЕД = 105
    ИЗУМРУДНЫЙ_КАМНЕЕД = 106
    САПФИРОВЫЙ_КАМНЕЕД = 107
    ХОЗЯИН_СКАЛ = 108
    ХОДЯЧИЙ_ТРУП = 109
    КАДАВР = 110
    КАДАВР_ПАУК = 111
    КОСТЯНОЙ_КАДАВР = 112
    ГИГАНТСКИЙ_КАДАВР = 113
    НЕТОПЫРЬ = 114
    СЕРЫЙ_НЕТОПЫРЬ = 115
    ОГНЕННЫЙ_НЕТОПЫРЬ = 116
    ГИГАНТСКИЙ_НЕТОПЫРЬ = 117
    ЛЕСНАЯ_МЕНАДА = 118
    СТЕПНАЯ_МЕНАДА = 119
    ПЕЩЕРНАЯ_МЕНАДА = 120
    МАГИЧЕСКАЯ_МЕНАДА = 121
    ВОЗДУШНАЯ_МЕНАДА = 122
    КАРЛИК = 123
    ЛЕСНОЙ_КАРЛИК = 124
    КРАТЕРНЫЙ_КАРЛИК = 125
    ВОЗДУШНЫЙ_КАРЛИК = 126
    ЗАМКОВЫЙ_КАМЕНЬ = 127
    ЗАЩИТНЫЙ_КАМЕНЬ = 128
    АССАСИН = 129
    СВОБОДНЫЙ_АССАСИН = 130
    ПРИЗРАЧНЫЙ_АССАСИН = 131
    ДРАКОСТ = 132
    ЗОЛОТОЙ_ДРАКОСТ = 133
    ЛЕДЯНОЙ_ДРАКОСТ = 134
    ГЛОТ = 135
    БОЛОТНЫЙ_ГЛОТ = 136
    ВЕСТНИК_СМЕРТИ = 137
    КУРГАННИК = 138
    РАЗБОЙНИК = 139
    ДУХ_БАШНИ = 140
    ЧЁРНЫЙ_ДРАКОН = 141
    БЕЛЫЙ_ДРАКОН = 142
    ЧЁРНЫЙ_ДРАКОН2 = 143
    БЕЛЫЙ_ДРАКОН2 = 144
    ЧЁРНЫЙ_ДРАКОН3 = 145
    БЕЛЫЙ_ДРАКОН3 = 146
    ВЕЛИКИЙ_ЧЁРНЫЙ_ДРАКОН = 147
    ВЕЛИКИЙ_БЕЛЫЙ_ДРАКОН = 148
    ЧЁРНЫЙ_РАНЕНЫЙ_ДРАКОН = 149
    ЧЁРНЫЙ_НАЕЗДНИК = 150
    БЕЛАЯ_НАЕЗДНИЦА = 151
    ПЛЫВУНЕЦ = 152
    ОГНЕННЫЙ_ЗМЕЙ = 153
    КОСТЯНОЙ_ЗМЕЙ = 154
    ЖЕЛЕЗНЫЙ_ЗМЕЙ = 155
    ПОДЗЕМНЫЙ_ЧЕРВЯК = 156
    РУСАЛКА = 157
    МЯСНОЙ_ЩУПАЛЬНИК = 158
    ЖЕЛЕЗНЫЙ_ЩУПАЛЬНИК = 159
    КОСТЯНАЯ_СОБАКА = 160
    ХАРОНСКИЙ_ОХОТНИК = 161
    ОГНЕННЫЙ_ОХОТНИК = 162
    ЖЕЛЕЗНЫЙ_ОХОТНИК = 163
    МЁРТВЫЙ_ОХОТНИК = 164
    ОГНЕННАЯ_ОХОТНИЦА = 165
    ЖЕЛЕЗНАЯ_ОХОТНИЦА = 166
    ХАРОНСКАЯ_ОХОТНИЦА = 167
    МЁРТВАЯ_ОХОТНИЦА = 168
    СТРАЖ_БЕЗДНЫ = 169
    ХИМЕРА = 170
    ЛЕТУН_НЕКРОМАНТА = 171
    ДЕМОН_ВОДЫ = 172
    ДЕМОН_ОГНЯ = 173
    ДЕМОН_ВОЗДУХА = 174
    ДЕМОН_ЗЕМЛИ = 175
    ЛЕТАЮЩИЙ_ДЕМОН = 176
    СВЕРХ_ДЕМОН = 177
    БАНГВИЛЬСКАЯ_СКОЛОПЕНДРА2 = 178
    ПАЛОЧНИК2 = 179
    ТРОПОС2 = 180
    РЖАВЫЙ_РЫЦАРЬ2 = 181
    ДУХ_ЗАМКА_ЛЬЕЖ = 182
    ДУХ_ЗАМКА_ФЬЕФ = 183
    ДУХ_ЗАМКА_АРИС = 184
    ДУХ_ЗАМКА_ЛАТОР = 185
    ДУХ_ЗАМКА_ЭЙКУМ_КАС = 186
    ДУХ_ЗАМКА_ГЕДЕОН = 187
    ДУХ_ЗАМКА_ШАТЕЛЬЕ = 188
    ДУХ_ЗАМКА_ТУАНОД = 189
    ДУХ_ЗАМКА_ПЕЛЬТЬЕ = 190
    ДУХ_ЗАМКА_КАРЕ_РОЯЛЬ = 191
    ДУХ_ЗАМКА_БЛЕССЕНДОР = 192
    ДУХ_ЗАМКА_ТЕРНОВАЛЬ = 193
    ДУХ_ЗАМКА_АММАЛАЭЛЬ = 194
    ДУХ_ЗАМКА_КАБЛАК = 195
    ДУХ_ЗАМКА_ДЭВАНАГАРИ = 196
    ДУХ_ЗАМКА_САБУЛАТ = 197
    ДУХ_ЗАМКА_ДЕФФЕНСАТ = 198
    ДУХ_ЗАМКА_АЙОНАТ = 199
    ДУХ_ЗАМКА_ТРИУМФАЛЕР = 200
    ДУХ_ЗАМКА_ХАНГААР = 201
    ДУХ_ЗАМКА_ДАБРАД = 202
    ДУХ_ЗАМКА_СЕД = 203
    ДУХ_ЗАМКА_ЛЕНДЕР = 204
    ДУХ_ЗАМКА_КЕЛЛОС = 205
    ДУХ_ЗАМКА_ШИБРОН = 206
    ДУХ_ЗАМКА_НИМЕД = 207
    ДУХ_ЗАМКА_КАНАКУН = 208
    ДУХ_ЗАМКА_ЭЛДУК = 209
    ДУХ_ЗАМКА_ЯНГ = 210
    ДУХ_ЗАМКА_ЭЛЕК = 211
    ДУХ_ЗАМКА_ГАВОТ = 212
    ДУХ_ЗАМКА_КАНДУР = 213
    ДУХ_ЗАМКА_ИММЕРТЕЛЬ = 214
    ДУХ_ЗАМКА_НАРЦИСС = 215
    ДУХ_ЗАМКА_РАНДЕН = 216
    ДУХ_ЗАМКА_НИРГУН = 217
    ДУХ_ЗАМКА_ГЕЛГИВИНН = 218
    ДУХ_ЗАМКА_ИЛЬ_СУИЛЬИ_РУА = 219


class MainhandSlotState(IntEnum):
    """Mainhand slot state enumeration."""

    FULL = 0
    FISTS = 22
    EMPTY = 255


class Stat(IntEnum):
    """Character stat enumeration."""

    HP_CURRENT = 0
    HP_MAX = 1
    MP_CURRENT = 2
    MP_MAX = 3
    SATIETY_CURRENT = 4
    SATIETY_MAX = 5
    PA = 6  # physical attack
    MA = 7  # magic attack
    PD = 8  # physical defense
    MD = 9  # magic defense
    STRENGTH = 10
    AGILITY = 11
    ACCURACY = 12
    ENDURANCE = 13
    EARTH = 14
    AIR = 15
    WATER = 16
    FIRE = 17
    TITLE_LEVEL = 18
    DEGREE_LEVEL = 19
    KARMA_TYPE = 20
    KARMA = 21
    TITLE_XP = 22
    DEGREE_XP = 23
    TITLE_STATS_AVAILABLE = 24
    DEGREE_STATS_AVAILABLE = 25
    CLAN_RANK_TYPE = 26
    MONEY = 27
    IS_INVISIBLE = 28


class Clan:
    """Character clan class."""

    def __init__(self, name: str = "Default", clan_id: int = 0):
        self.name = name
        self.clan_id = clan_id


# Create default clan instance as a module-level constant
DEFAULT_CLAN = Clan("Default", 0)


# Monster type mappings
MONSTER_NAME_TO_TYPE_MAPPING: Dict[MonsterType, int] = {
    MonsterType.ПАЛОЧНИК: 1000,
    MonsterType.ПАЛОЧНИК_СТЕПНОЙ: 1001,
    MonsterType.ПАЛОЧНИК_ЛЕСНОЙ: 1002,
    MonsterType.ПАЛОЧНИК_ПЕЩЕРНЫЙ: 1003,
    MonsterType.ПСОГЛАВЕЦ: 1010,
    MonsterType.ПСОГЛАВЕЦ_СТЕПНОЙ: 1011,
    MonsterType.ПСОГЛАВЕЦ_ЛЕСНОЙ: 1012,
    MonsterType.ПСОГЛАВЕЦ_ПЕЩЕРНЫЙ: 1013,
    MonsterType.ТРУХЛЯВЫЙ_РЫЦАРЬ: 1020,
    MonsterType.РЖАВЫЙ_РЫЦАРЬ: 1021,
    MonsterType.НЕПРИКАЯННЫЙ_РЫЦАРЬ: 1022,
    MonsterType.ЗОЛОТОЙ_РЫЦАРЬ: 1023,
    MonsterType.ГИГАНТСКИЙ_РЫЦАРЬ: 1024,
    MonsterType.ВОЗДУШНЫЙ_РЫЦАРЬ: 1025,
    MonsterType.ЛЕТУН: 1030,
    MonsterType.ШТОРМОВОЙ_ЛЕТУН: 1031,
    MonsterType.ОГНЕННЫЙ_ЛЕТУН: 1032,
    MonsterType.ЯНТАРНЫЙ_ЛЕТУН: 1033,
    MonsterType.ГИГАНТСКИЙ_ЛЕТУН: 1034,
    MonsterType.ЗЕМЛЯНОЙ_ГОЛЕМ: 1040,
    MonsterType.ПЕСОЧНЫЙ_ГОЛЕМ: 1041,
    MonsterType.ГЛИНЯНЫЙ_ГОЛЕМ: 1042,
    MonsterType.СВОБОДНЫЙ_ГОЛЕМ: 1043,
    MonsterType.ГИГАНТСКИЙ_ГОЛЕМ: 1044,
    MonsterType.БАНГВИЛЬСКАЯ_СКОЛОПЕНДРА: 1050,
    MonsterType.ЦАРСКАЯ_СКОЛОПЕНДРА: 1051,
    MonsterType.СКЕЛЕТ: 1060,
    MonsterType.СКЕЛЕТ_ЛЕСНОЙ: 1061,
    MonsterType.СКЕЛЕТ_УМРАДСКИЙ: 1062,
    MonsterType.СКЕЛЕТ_ВОЗДУШНЫЙ: 1063,
    MonsterType.СКЕЛЕТ_ПЕЩЕРНЫЙ: 1064,
    MonsterType.ЛИЧ: 1065,
    MonsterType.ГИГАНТСКИЙ_СКЕЛЕТ: 1066,
    MonsterType.ВОЗДУШНЫЙ_ЛИЧ: 1067,
    MonsterType.АССАСИН2: 1069,
    MonsterType.ВЕПРЬ: 1070,
    MonsterType.БЕШЕНЫЙ_ВЕПРЬ: 1071,
    MonsterType.СУХОЙ_ВЕПРЬ: 1072,
    MonsterType.ВОЗДУШНЫЙ_ВЕПРЬ: 1073,
    MonsterType.ЖЕЛЕЗНЫЙ_ВЕПРЬ: 1074,
    MonsterType.ОГНЕННЫЙ_ВЕПРЬ: 1075,
    MonsterType.ГИГАНТСКИЙ_ВЕПРЬ: 1076,
    MonsterType.ЦИАНОС: 1080,
    MonsterType.ЦИАНОС_ТЁМНЫЙ: 1081,
    MonsterType.ЦИАНОС_СУХОЙ: 1082,
    MonsterType.ЦИАНОС_ЖЕЛЕЗНЫЙ: 1083,
    MonsterType.ЦИАНОС_ВОЗДУШНЫЙ: 1084,
    MonsterType.ЦИАНОС_ГИГАНТСКИЙ: 1085,
    MonsterType.ВОЛК: 1090,
    MonsterType.СТЕПНОЙ_ВОЛК: 1091,
    MonsterType.ЛЕДЯНОЙ_ВОЛК: 1092,
    MonsterType.СУХОЙ_ВОЛК: 1093,
    MonsterType.ЖЕЛЕЗНЫЙ_ВОЛК: 1094,
    MonsterType.АДСКИЙ_ВОЛК: 1095,
    MonsterType.ПАУК: 1100,
    MonsterType.СЕРНЫЙ_ПАУК: 1101,
    MonsterType.СУХОЙ_ПАУК: 1102,
    MonsterType.ЖЕЛЕЗНЫЙ_ПАУК: 1103,
    MonsterType.ОГНЕННЫЙ_ПАУК: 1104,
    MonsterType.ЧЁРНАЯ_ВДОВА: 1105,
    MonsterType.ГИГАНТСКИЙ_ПАУК: 1106,
    MonsterType.ВОЗДУШНЫЙ_ПАУК: 1107,
    MonsterType.САЛАМАНДРА: 1110,
    MonsterType.НОМРАДСКАЯ_САЛАМАНДРА: 1111,
    MonsterType.ЗЕМЛЯНАЯ_САЛАМАНДРА: 1112,
    MonsterType.ЖЕЛЕЗНАЯ_САЛАМАНДРА: 1113,
    MonsterType.САЛАМАНДИГА: 1114,
    MonsterType.КРАСНЫЙ_СКОРПИОН: 1120,
    MonsterType.СКОРПИОН: 1121,
    MonsterType.СИНИЙ_СКОРПИОН: 1122,
    MonsterType.ОГНЕННЫЙ_СКОРПИОН: 1123,
    MonsterType.ТИФОН: 1130,
    MonsterType.ДЫМНЫЙ_ТИФОН: 1131,
    MonsterType.ВИЗЖАЩИЙ_ТИФОН: 1132,
    MonsterType.ЖЕЛЕЗНЫЙ_ТИФОН: 1133,
    MonsterType.ОГНЕННЫЙ_ТИФОН: 1134,
    MonsterType.ГИГАНТСКИЙ_ТИФОН: 1135,
    MonsterType.ЛЮДОЕД: 1140,
    MonsterType.СЕРНЫЙ_ЛЮДОЕД: 1141,
    MonsterType.ПЕЩЕРНЫЙ_ЛЮДОЕД: 1142,
    MonsterType.ГИГАНТСКИЙ_ЛЮДОЕД: 1143,
    MonsterType.НИФОН: 1150,
    MonsterType.ЗЕЛЁНЫЙ_ДРАКОН: 1160,
    MonsterType.СИНИЙ_ДРАКОН: 1161,
    MonsterType.КРАСНЫЙ_ДРАКОН: 1162,
    MonsterType.СТАЛЬНОЙ_ДРАКОН: 1163,
    MonsterType.ГИГАНТСКИЙ_ДРАКОН: 1164,
    MonsterType.КОШКА: 1170,
    MonsterType.БЫК: 1180,
    MonsterType.ТРОПОС: 1190,
    MonsterType.БЕШЕНЫЙ_ТРОПОС: 1191,
    MonsterType.ТОРФЯНОЙ_ТРОПОС: 1192,
    MonsterType.КОРОЛЕВСКИЙ_ТРОПОС: 1193,
    MonsterType.ВОЗДУШНЫЙ_ТРОПОС: 1194,
    MonsterType.МАМОНТ: 1200,
    MonsterType.ЖЕЛЕЗНЫЙ_МАМОНТ: 1201,
    MonsterType.СНЕЖНЫЙ_МАМОНТ: 1202,
    MonsterType.УГОЛЬНЫЙ_МАМОНТ: 1203,
    MonsterType.ЗОМБИ: 1210,
    MonsterType.СЕРЫЙ_ЗОМБИ: 1211,
    MonsterType.ЗОМБАДЕР: 1212,
    MonsterType.ГИГАНТСКИЙ_ЗОМБИ: 1213,
    MonsterType.ЗАЧАРОВАННОЕ_ДЕРЕВО: 1220,
    MonsterType.КРАСНОЕ_ДЕРЕВО: 1221,
    MonsterType.МЁРТВОЕ_ДЕРЕВО: 1222,
    MonsterType.ГРАНИТНЫЙ_КАМНЕЕД: 1230,
    MonsterType.ИЗУМРУДНЫЙ_КАМНЕЕД: 1231,
    MonsterType.САПФИРОВЫЙ_КАМНЕЕД: 1232,
    MonsterType.ХОЗЯИН_СКАЛ: 1233,
    MonsterType.ХОДЯЧИЙ_ТРУП: 1240,
    MonsterType.КАДАВР: 1241,
    MonsterType.КАДАВР_ПАУК: 1242,
    MonsterType.КОСТЯНОЙ_КАДАВР: 1243,
    MonsterType.ГИГАНТСКИЙ_КАДАВР: 1244,
    MonsterType.НЕТОПЫРЬ: 1250,
    MonsterType.СЕРЫЙ_НЕТОПЫРЬ: 1251,
    MonsterType.ОГНЕННЫЙ_НЕТОПЫРЬ: 1252,
    MonsterType.ГИГАНТСКИЙ_НЕТОПЫРЬ: 1253,
    MonsterType.ЛЕСНАЯ_МЕНАДА: 1260,
    MonsterType.СТЕПНАЯ_МЕНАДА: 1261,
    MonsterType.ПЕЩЕРНАЯ_МЕНАДА: 1262,
    MonsterType.МАГИЧЕСКАЯ_МЕНАДА: 1263,
    MonsterType.ВОЗДУШНАЯ_МЕНАДА: 1264,
    MonsterType.КАРЛИК: 1270,
    MonsterType.ЛЕСНОЙ_КАРЛИК: 1271,
    MonsterType.КРАТЕРНЫЙ_КАРЛИК: 1272,
    MonsterType.ВОЗДУШНЫЙ_КАРЛИК: 1273,
    MonsterType.ЗАМКОВЫЙ_КАМЕНЬ: 1280,
    MonsterType.ЗАЩИТНЫЙ_КАМЕНЬ: 1281,
    MonsterType.АССАСИН: 1290,
    MonsterType.СВОБОДНЫЙ_АССАСИН: 1291,
    MonsterType.ПРИЗРАЧНЫЙ_АССАСИН: 1292,
    MonsterType.ДРАКОСТ: 1300,
    MonsterType.ЗОЛОТОЙ_ДРАКОСТ: 1301,
    MonsterType.ЛЕДЯНОЙ_ДРАКОСТ: 1302,
    MonsterType.ГЛОТ: 1310,
    MonsterType.БОЛОТНЫЙ_ГЛОТ: 1311,
    MonsterType.ВЕСТНИК_СМЕРТИ: 1320,
    MonsterType.КУРГАННИК: 1330,
    MonsterType.РАЗБОЙНИК: 1340,
    MonsterType.ДУХ_БАШНИ: 1350,
    MonsterType.ЧЁРНЫЙ_ДРАКОН: 1360,
    MonsterType.БЕЛЫЙ_ДРАКОН: 1361,
    MonsterType.ЧЁРНЫЙ_ДРАКОН2: 1362,
    MonsterType.БЕЛЫЙ_ДРАКОН2: 1363,
    MonsterType.ЧЁРНЫЙ_ДРАКОН3: 1364,
    MonsterType.БЕЛЫЙ_ДРАКОН3: 1365,
    MonsterType.ВЕЛИКИЙ_ЧЁРНЫЙ_ДРАКОН: 1366,
    MonsterType.ВЕЛИКИЙ_БЕЛЫЙ_ДРАКОН: 1367,
    MonsterType.ЧЁРНЫЙ_РАНЕНЫЙ_ДРАКОН: 1368,
    MonsterType.ЧЁРНЫЙ_НАЕЗДНИК: 1370,
    MonsterType.БЕЛАЯ_НАЕЗДНИЦА: 1371,
    MonsterType.ПЛЫВУНЕЦ: 1380,
    MonsterType.ОГНЕННЫЙ_ЗМЕЙ: 1400,
    MonsterType.КОСТЯНОЙ_ЗМЕЙ: 1401,
    MonsterType.ЖЕЛЕЗНЫЙ_ЗМЕЙ: 1402,
    MonsterType.ПОДЗЕМНЫЙ_ЧЕРВЯК: 1410,
    MonsterType.РУСАЛКА: 1420,
    MonsterType.МЯСНОЙ_ЩУПАЛЬНИК: 1430,
    MonsterType.ЖЕЛЕЗНЫЙ_ЩУПАЛЬНИК: 1431,
    MonsterType.КОСТЯНАЯ_СОБАКА: 1440,
    MonsterType.ХАРОНСКИЙ_ОХОТНИК: 1450,
    MonsterType.ОГНЕННЫЙ_ОХОТНИК: 1451,
    MonsterType.ЖЕЛЕЗНЫЙ_ОХОТНИК: 1452,
    MonsterType.МЁРТВЫЙ_ОХОТНИК: 1453,
    MonsterType.ОГНЕННАЯ_ОХОТНИЦА: 1460,
    MonsterType.ЖЕЛЕЗНАЯ_ОХОТНИЦА: 1461,
    MonsterType.ХАРОНСКАЯ_ОХОТНИЦА: 1462,
    MonsterType.МЁРТВАЯ_ОХОТНИЦА: 1463,
    MonsterType.СТРАЖ_БЕЗДНЫ: 1470,
    MonsterType.ХИМЕРА: 1480,
    MonsterType.ЛЕТУН_НЕКРОМАНТА: 1850,
    MonsterType.ДЕМОН_ВОДЫ: 1870,
    MonsterType.ДЕМОН_ОГНЯ: 1871,
    MonsterType.ДЕМОН_ВОЗДУХА: 1872,
    MonsterType.ДЕМОН_ЗЕМЛИ: 1873,
    MonsterType.ЛЕТАЮЩИЙ_ДЕМОН: 1874,
    MonsterType.СВЕРХ_ДЕМОН: 1875,
    MonsterType.БАНГВИЛЬСКАЯ_СКОЛОПЕНДРА2: 1880,
    MonsterType.ПАЛОЧНИК2: 1881,
    MonsterType.ТРОПОС2: 1882,
    MonsterType.РЖАВЫЙ_РЫЦАРЬ2: 1883,
    MonsterType.ДУХ_ЗАМКА_ЛЬЕЖ: 1900,
    MonsterType.ДУХ_ЗАМКА_ФЬЕФ: 1901,
    MonsterType.ДУХ_ЗАМКА_АРИС: 1902,
    MonsterType.ДУХ_ЗАМКА_ЛАТОР: 1903,
    MonsterType.ДУХ_ЗАМКА_ЭЙКУМ_КАС: 1904,
    MonsterType.ДУХ_ЗАМКА_ГЕДЕОН: 1905,
    MonsterType.ДУХ_ЗАМКА_ШАТЕЛЬЕ: 1906,
    MonsterType.ДУХ_ЗАМКА_ТУАНОД: 1907,
    MonsterType.ДУХ_ЗАМКА_ПЕЛЬТЬЕ: 1908,
    MonsterType.ДУХ_ЗАМКА_КАРЕ_РОЯЛЬ: 1909,
    MonsterType.ДУХ_ЗАМКА_БЛЕССЕНДОР: 1910,
    MonsterType.ДУХ_ЗАМКА_ТЕРНОВАЛЬ: 1911,
    MonsterType.ДУХ_ЗАМКА_АММАЛАЭЛЬ: 1912,
    MonsterType.ДУХ_ЗАМКА_КАБЛАК: 1913,
    MonsterType.ДУХ_ЗАМКА_ДЭВАНАГАРИ: 1914,
    MonsterType.ДУХ_ЗАМКА_САБУЛАТ: 1915,
    MonsterType.ДУХ_ЗАМКА_ДЕФФЕНСАТ: 1916,
    MonsterType.ДУХ_ЗАМКА_АЙОНАТ: 1917,
    MonsterType.ДУХ_ЗАМКА_ТРИУМФАЛЕР: 1918,
    MonsterType.ДУХ_ЗАМКА_ХАНГААР: 1919,
    MonsterType.ДУХ_ЗАМКА_ДАБРАД: 1920,
    MonsterType.ДУХ_ЗАМКА_СЕД: 1921,
    MonsterType.ДУХ_ЗАМКА_ЛЕНДЕР: 1922,
    MonsterType.ДУХ_ЗАМКА_КЕЛЛОС: 1923,
    MonsterType.ДУХ_ЗАМКА_ШИБРОН: 1924,
    MonsterType.ДУХ_ЗАМКА_НИМЕД: 1925,
    MonsterType.ДУХ_ЗАМКА_КАНАКУН: 1926,
    MonsterType.ДУХ_ЗАМКА_ЭЛДУК: 1927,
    MonsterType.ДУХ_ЗАМКА_ЯНГ: 1928,
    MonsterType.ДУХ_ЗАМКА_ЭЛЕК: 1929,
    MonsterType.ДУХ_ЗАМКА_ГАВОТ: 1930,
    MonsterType.ДУХ_ЗАМКА_КАНДУР: 1931,
    MonsterType.ДУХ_ЗАМКА_ИММЕРТЕЛЬ: 1932,
    MonsterType.ДУХ_ЗАМКА_НАРЦИСС: 1933,
    MonsterType.ДУХ_ЗАМКА_РАНДЕН: 1934,
    MonsterType.ДУХ_ЗАМКА_НИРГУН: 1935,
    MonsterType.ДУХ_ЗАМКА_ГЕЛГИВИНН: 1936,
    MonsterType.ДУХ_ЗАМКА_ИЛЬ_СУИЛЬИ_РУА: 1937,
}

# Reverse mapping: int -> MonsterType
MONSTER_TYPE_TO_NAME_MAPPING: Dict[int, MonsterType] = {
    v: k for k, v in MONSTER_NAME_TO_TYPE_MAPPING.items()
}

# Static data for health and MP calculations
HEALTH_AT_TITLE = [
    100,
    150,
    200,
    250,
    300,
    350,
    400,
    450,
    500,
    550,
    600,
    650,
    700,
    750,
    800,
    850,
    900,
    950,
    1000,
    1050,
    1100,
    1150,
    1200,
    1250,
    1300,
    1350,
    1400,
    1450,
    1500,
    1550,
    1600,
    1650,
    1700,
    1750,
    1800,
    1850,
    1900,
    1950,
    2000,
    2050,
    2100,
    2150,
    2200,
    2250,
    2300,
    2350,
    2400,
    2450,
    2500,
    2550,
    2600,
    2650,
    2700,
    2750,
    2800,
    2850,
    2900,
    2950,
    3000,
    3200,
]

HEALTH_AT_DEGREE = [
    100,
    110,
    120,
    130,
    150,
    160,
    170,
    180,
    190,
    210,
    220,
    230,
    240,
    250,
    270,
    280,
    290,
    300,
    310,
    330,
    340,
    350,
    360,
    370,
    390,
    400,
    410,
    420,
    430,
    450,
    460,
    470,
    480,
    490,
    510,
    520,
    530,
    540,
    550,
    570,
    580,
    590,
    600,
    610,
    630,
    640,
    650,
    660,
    670,
    690,
    700,
    710,
    720,
    730,
    750,
    760,
    770,
    780,
    790,
    800,
]

MP_AT_TITLE = [
    100,
    100,
    100,
    100,
    125,
    125,
    125,
    125,
    125,
    150,
    150,
    150,
    150,
    150,
    175,
    175,
    175,
    175,
    175,
    200,
    200,
    200,
    200,
    200,
    225,
    225,
    225,
    225,
    225,
    250,
    250,
    250,
    250,
    250,
    275,
    275,
    275,
    275,
    275,
    300,
    300,
    300,
    300,
    300,
    325,
    325,
    325,
    325,
    325,
    350,
    350,
    350,
    350,
    350,
    375,
    375,
    375,
    375,
    375,
    400,
]

MP_AT_DEGREE = [
    100,
    175,
    250,
    325,
    400,
    475,
    550,
    625,
    700,
    775,
    850,
    925,
    1000,
    1075,
    1150,
    1225,
    1300,
    1375,
    1450,
    1525,
    1600,
    1675,
    1750,
    1825,
    1900,
    1975,
    2050,
    2125,
    2200,
    2275,
    2350,
    2425,
    2500,
    2575,
    2650,
    2725,
    2800,
    2875,
    2950,
    3025,
    3100,
    3175,
    3250,
    3325,
    3400,
    3475,
    3550,
    3625,
    3700,
    3775,
    3850,
    3925,
    4000,
    4075,
    4150,
    4225,
    4300,
    4375,
    4450,
    4650,
]

AVAILABLE_STATS_PRIMARY = [
    4,
    4,
    4,
    4,
    6,
    6,
    6,
    6,
    6,
    8,
    8,
    8,
    8,
    8,
    8,
    8,
    8,
    8,
    8,
    10,
    10,
    10,
    10,
    10,
    10,
    10,
    10,
    10,
    10,
    12,
    12,
    12,
    12,
    12,
    12,
    12,
    12,
    12,
    12,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    18,
    18,
    20,
]

AVAILABLE_STATS_SECONDARY = [
    0,
    0,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    2,
    0,
    0,
    0,
    0,
    2,
    0,
    0,
    0,
    0,
    4,
    0,
    0,
    0,
    0,
    4,
    0,
    0,
    0,
    0,
    6,
    0,
    0,
    0,
    0,
    6,
    0,
    0,
    0,
    0,
    8,
    0,
    0,
    0,
    0,
    8,
    0,
    0,
    0,
    0,
    10,
    0,
    0,
    0,
    0,
    10,
]

STAT_BONUS_FOR_RESETS = [
    1,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
]

XP_PER_LEVEL_BASE = [
    50,
    320,
    1080,
    2880,
    7000,
    10800,
    15680,
    22080,
    29570,
    39500,
    50820,
    64800,
    81120,
    100940,
    123750,
    151040,
    182070,
    218700,
    259920,
    310000,
    363800,
    428300,
    499900,
    584600,
    678100,
    784200,
    904000,
    1038800,
    1194200,
    1368000,
    1561600,
    1781800,
    2025500,
    2300400,
    2609300,
    2954900,
    3340400,
    3768800,
    4251200,
    4808000,
    5430000,
    6121000,
    6897000,
    7763000,
    8809000,
    9988000,
    11321000,
    12810000,
    14478000,
    16513000,
    18805000,
    21416000,
    24354000,
    27687000,
    33895000,
    41458000,
    50684000,
    61931000,
    75607000,
    92268000,
]

XP_PER_LEVEL_DELTA = [
    0,
    40,
    90,
    180,
    350,
    450,
    560,
    690,
    821.2,
    987.4,
    1155,
    1350,
    1560,
    1802.5,
    2062.5,
    2360,
    2677.5,
    3037.5,
    3420,
    3875,
    5067.2,
    6521.9,
    8204.9,
    10230.5,
    12544.8,
    15231.6,
    18331.1,
    21889,
    26045.9,
    30780,
    36143.5,
    42317.7,
    49256.5,
    57171.7,
    66164.4,
    76334.9,
    87798.4,
    100666.6,
    115272.9,
    132220,
    151311.6,
    172699.7,
    196885.3,
    224068.4,
    256929.2,
    294211.7,
    336619.1,
    384300,
    438033.4,
    503646.5,
    577977.2,
    663072.4,
    759339.3,
    869064.2,
    1070773.9,
    1317772.2,
    1620554.1,
    1991402,
    2444412.8,
    2998709.8,
]
