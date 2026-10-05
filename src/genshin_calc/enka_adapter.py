"""Adapter module for Enka.Network API.

Fetches player character showcase data and translates raw Enka reliquary properties
into Genshin Open Object Data (GOOD) and internal calculator representations.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

try:
    from .good_adapter import ParsedArtifact, to_good_artifact
except (ImportError, ValueError):
    from good_adapter import ParsedArtifact, to_good_artifact

D = Decimal


class EnkaError(Exception):
    """Base exception for all Enka adapter operations."""


class EnkaNetworkError(EnkaError):
    """Raised when network requests fail due to HTTP or connectivity issues."""


class EnkaPrivateShowcaseError(EnkaError):
    """Raised when the player's character showcase is hidden or empty."""


class EnkaRateLimitError(EnkaError):
    """Raised when HTTP 429 Too Many Requests is encountered."""


class EnkaUserNotFoundError(EnkaError):
    """Raised when the requested UID does not exist (HTTP 404)."""


@dataclass(frozen=True)
class EnkaCharacter:
    avatar_id: int
    name: str
    element: str
    level: int
    artifacts: list[ParsedArtifact]


@dataclass(frozen=True)
class EnkaProfile:
    uid: str
    nickname: str
    level: int
    world_level: int
    characters: list[EnkaCharacter]

    @property
    def player_name(self) -> str:
        return self.nickname


# Enka slot identifier to internal Russian slot name
ENKA_SLOT_MAP: dict[str, str] = {
    "EQUIP_BRACER": "Цветок жизни",
    "EQUIP_NECKLACE": "Перо смерти",
    "EQUIP_SHOES": "Пески времени",
    "EQUIP_RING": "Кубок пространства",
    "EQUIP_DRESS": "Корона проницательности",
}

# Enka fight property identifiers to internal Russian stat names
ENKA_PROP_MAP: dict[str, str] = {
    "FIGHT_PROP_BASE_ATTACK": "Базовая атака",
    "FIGHT_PROP_HP": "HP",
    "FIGHT_PROP_HP_PERCENT": "HP %",
    "FIGHT_PROP_ATTACK": "Сила атаки",
    "FIGHT_PROP_ATTACK_PERCENT": "Сила атаки %",
    "FIGHT_PROP_DEFENSE": "Защита",
    "FIGHT_PROP_DEFENSE_PERCENT": "Защита %",
    "FIGHT_PROP_CRITICAL": "Шанс крит. попадания",
    "FIGHT_PROP_CRITICAL_HURT": "Крит. урон",
    "FIGHT_PROP_CHARGE_EFFICIENCY": "Восст. энергии",
    "FIGHT_PROP_HEAL_ADD": "Бонус лечения",
    "FIGHT_PROP_ELEMENT_MASTERY": "Мастерство стихий",
    "FIGHT_PROP_PHYSICAL_ADD_HURT": "Физ. урон %",
    "FIGHT_PROP_FIRE_ADD_HURT": "Пиро урон %",
    "FIGHT_PROP_ELEC_ADD_HURT": "Электро урон %",
    "FIGHT_PROP_WATER_ADD_HURT": "Гидро урон %",
    "FIGHT_PROP_WIND_ADD_HURT": "Анемо урон %",
    "FIGHT_PROP_ICE_ADD_HURT": "Крио урон %",
    "FIGHT_PROP_ROCK_ADD_HURT": "Гео урон %",
    "FIGHT_PROP_GRASS_ADD_HURT": "Дендро урон %",
}

# Artifact Set IDs from Genshin game data mapped to standard GOOD setKey names
ENKA_SET_MAP: dict[int, str] = {
    15001: "GladiatorsFinale",
    15002: "WanderersTroupe",
    15003: "NoblesseOblige",
    15004: "BloodstainedChivalry",
    15005: "MaidenBeloved",
    15006: "ViridescentVenerer",
    15007: "ArchaicPetra",
    15008: "CrimsonWitchOfFlames",
    15009: "ThunderingFury",
    15010: "Lavawalker",
    15011: "Thundersoother",
    15012: "RetracingBolide",
    15013: "BlizzardStrayer",
    15014: "HeartOfDepth",
    15015: "TenacityOfTheMillelith",
    15016: "PaleFlame",
    15017: "ShimenawasReminiscence",
    15018: "EmblemOfSeveredFate",
    15019: "HuskOfOpulentDreams",
    15020: "OceanHuedClam",
    15021: "VermillionHereafter",
    15022: "EchoesOfAnOffering",
    15023: "DeepwoodMemories",
    15024: "GildedDreams",
    15025: "DesertPavilionChronicle",
    15026: "FlowerOfParadiseLost",
    15027: "NymphsDream",
    15028: "VourukashasGlow",
    15029: "MarechausseeHunter",
    15030: "GoldenTroupe",
    15031: "SongOfDaysPast",
    15032: "NighttimeWhispersInTheEchoingWoods",
    15033: "FragmentOfHarmonicWhimsy",
    15034: "UnfinishedReverie",
    15035: "ScrollOfTheHeroOfCinderCity",
    15036: "ObsidianCodex",
}

# Mapping of character Avatar IDs to human-readable names
AVATAR_ID_MAP: dict[int, str] = {
    10000002: "Kamisato Ayaka",
    10000003: "Jean",
    10000005: "Aether",
    10000007: "Lumine",
    10000014: "Barbara",
    10000015: "Kaeya",
    10000016: "Diluc",
    10000020: "Razor",
    10000021: "Amber",
    10000022: "Venti",
    10000023: "Xiangling",
    10000024: "Beidou",
    10000025: "Xingqiu",
    10000026: "Xiao",
    10000027: "Ningguang",
    10000029: "Klee",
    10000030: "Zhongli",
    10000031: "Fischl",
    10000032: "Bennett",
    10000033: "Tartaglia",
    10000034: "Noelle",
    10000035: "Qiqi",
    10000036: "Chongyun",
    10000037: "Ganyu",
    10000038: "Albedo",
    10000039: "Diona",
    10000041: "Mona",
    10000042: "Keqing",
    10000043: "Sucrose",
    10000044: "Xinyan",
    10000045: "Rosaria",
    10000046: "Hu Tao",
    10000047: "Kaedehara Kazuha",
    10000048: "Yanfei",
    10000049: "Yoimiya",
    10000050: "Thoma",
    10000051: "Eula",
    10000052: "Raiden Shogun",
    10000053: "Sayu",
    10000054: "Sangonomiya Kokomi",
    10000055: "Gorou",
    10000056: "Kujou Sara",
    10000057: "Arataki Itto",
    10000058: "Yae Miko",
    10000059: "Shikanoin Heizou",
    10000060: "Yelan",
    10000061: "Kirara",
    10000062: "Aloy",
    10000063: "Shenhe",
    10000064: "Yun Jin",
    10000065: "Kuki Shinobu",
    10000066: "Kamisato Ayato",
    10000067: "Collei",
    10000068: "Dori",
    10000069: "Tighnari",
    10000070: "Nilou",
    10000071: "Cyno",
    10000072: "Candace",
    10000073: "Nahida",
    10000074: "Layla",
    10000075: "Wanderer",
    10000076: "Faruzan",
    10000077: "Yaoyao",
    10000078: "Alhaitham",
    10000079: "Dehya",
    10000080: "Mika",
    10000081: "Kaveh",
    10000082: "Baizhu",
    10000083: "Lynette",
    10000084: "Lyney",
    10000085: "Freminet",
    10000086: "Wriothesley",
    10000087: "Neuvillette",
    10000088: "Charlotte",
    10000089: "Furina",
    10000090: "Chevreuse",
    10000091: "Navia",
    10000092: "Gaming",
    10000093: "Xianyun",
    10000094: "Chiori",
    10000095: "Arlecchino",
    10000096: "Sethos",
    10000097: "Clorinde",
    10000098: "Sigewinne",
    10000099: "Emilie",
    10000100: "Kachina",
    10000101: "Kinich",
    10000102: "Mualani",
    10000103: "Xilonen",
    10000104: "Chasca",
    10000105: "Ororon",
    10000106: "Mavuika",
    10000107: "Citlali",
    10000108: "Lan Yan",
    10000109: "Yumemizuki Mizuki",
}

# In-memory TTL cache: {uid: (expire_timestamp, EnkaProfile)}
_CACHE: dict[str, tuple[float, EnkaProfile]] = {}


def clear_enka_cache() -> None:
    """Clears all cached Enka profiles."""
    _CACHE.clear()


def get_avatar_name(avatar_id: int) -> str:
    """Returns the human-readable character name or a fallback identifier."""
    return AVATAR_ID_MAP.get(avatar_id, f"Character_{avatar_id}")


def parse_enka_relic(item: Mapping[str, Any], character_name: str = "") -> ParsedArtifact:
    """Converts a raw Enka equipList item into a ParsedArtifact dataclass."""
    flat = item.get("flat", {})
    item_type = flat.get("itemType")

    if item_type != "ITEM_RELIQUARY" and "reliquary" not in item and "relic" not in item and "equipType" not in flat:
        raise EnkaError("Item is not a reliquary artifact.")

    equip_type = flat.get("equipType", "")
    if equip_type not in ENKA_SLOT_MAP:
        raise EnkaError(f"Unrecognized artifact equipType: {equip_type}")
    slot = ENKA_SLOT_MAP[equip_type]

    mainstat_data = flat.get("reliquaryMainstat") or flat.get("relicMainstat", {})
    main_prop_id = mainstat_data.get("mainPropId", "")
    if main_prop_id not in ENKA_PROP_MAP:
        raise EnkaError(f"Unrecognized mainPropId: {main_prop_id}")
    main_stat = ENKA_PROP_MAP[main_prop_id]

    relic_info = item.get("reliquary") or item.get("relic", {})
    raw_level = int(relic_info.get("level", 1))
    level = max(0, min(20, raw_level - 1))
    rarity = int(flat.get("rankLevel", 5))

    substats: list[tuple[str, Decimal]] = []
    substats_raw = flat.get("reliquarySubstats") or flat.get("relicSubstatList", [])
    for sub in substats_raw:
        sub_prop = sub.get("appendPropId", "")
        if sub_prop in ENKA_PROP_MAP:
            s_name = ENKA_PROP_MAP[sub_prop]
            s_val = D(str(sub.get("statValue", 0)))
            substats.append((s_name, s_val))

    set_id = flat.get("setId")
    set_key = ENKA_SET_MAP.get(set_id, "")

    return ParsedArtifact(
        slot=slot,
        main_stat=main_stat,
        level=level,
        rarity=rarity,
        substats=substats,
        set_key=set_key,
        location=character_name,
        lock=False,
    )


def parse_showcase(payload: Mapping[str, Any]) -> EnkaProfile:
    """Parses a full Enka.Network API response into an EnkaProfile model."""
    if not isinstance(payload, Mapping):
        raise EnkaError("Invalid response payload from Enka API.")

    avatar_info_list = payload.get("avatarInfoList")
    if not avatar_info_list or not isinstance(avatar_info_list, list) or len(avatar_info_list) == 0:
        raise EnkaPrivateShowcaseError(
            "Витрина персонажей закрыта или пуста. "
            "Откройте детали персонажей в профиле игры (Настройки витрины)."
        )

    player_info = payload.get("playerInfo", {})
    nickname = str(player_info.get("nickname", "Путешественник"))
    level = int(player_info.get("level", 0))
    world_level = int(player_info.get("worldLevel", 0))
    uid = str(payload.get("uid", ""))

    characters: list[EnkaCharacter] = []
    for av in avatar_info_list:
        if not isinstance(av, Mapping):
            continue
        avatar_id = int(av.get("avatarId", 0))
        char_name = get_avatar_name(avatar_id)
        char_lvl = int(av.get("propMap", {}).get("4001", {}).get("val", 0))

        artifacts: list[ParsedArtifact] = []
        for eq in av.get("equipList", []):
            if isinstance(eq, Mapping) and eq.get("flat", {}).get("itemType") == "ITEM_RELIQUARY":
                try:
                    art = parse_enka_relic(eq, character_name=char_name)
                    if art.rarity == 5:
                        artifacts.append(art)
                except Exception:
                    continue

        characters.append(
            EnkaCharacter(
                avatar_id=avatar_id,
                name=char_name,
                element="",
                level=char_lvl,
                artifacts=artifacts,
            )
        )

    return EnkaProfile(
        uid=uid,
        nickname=nickname,
        level=level,
        world_level=world_level,
        characters=characters,
    )


def enka_profile_to_good_json(profile: EnkaProfile, indent: int = 2) -> str:
    """Serializes all 5-star artifacts from an EnkaProfile into a standard GOOD v2 JSON string."""
    all_artifacts = []
    for char in profile.characters:
        for art in char.artifacts:
            raw_art = {
                "slot": art.slot,
                "main_stat": art.main_stat,
                "level": art.level,
                "rarity": art.rarity,
                "substats": art.substats,
                "set_key": art.set_key,
                "location": char.name,
            }
            all_artifacts.append(to_good_artifact(raw_art))

    doc = {
        "format": "GOOD",
        "version": 2,
        "source": "Enka.Network via Genshin Artifact Calc v2",
        "artifacts": all_artifacts,
    }
    return json.dumps(doc, indent=indent, ensure_ascii=False)


def fetch_enka_profile(uid: str, timeout: int = 8, use_cache: bool = True) -> EnkaProfile:
    """Fetches player showcase from Enka.Network API by UID with TTL caching."""
    clean_uid = uid.strip()
    if not clean_uid.isdigit() or len(clean_uid) not in (9, 10):
        raise EnkaError(f"Некорректный UID: '{uid}'. UID должен содержать 9 или 10 цифр.")

    now = time.time()
    if use_cache and clean_uid in _CACHE:
        expiry, cached_profile = _CACHE[clean_uid]
        if now < expiry:
            return cached_profile

    url = f"https://enka.network/api/uid/{clean_uid}/"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GenshinArtifactCalc/2.0 (PairProgrammer Desktop)",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        if err.code == 404:
            raise EnkaUserNotFoundError(f"Игрок с UID {clean_uid} не найден на серверах Enka.") from err
        elif err.code == 429:
            raise EnkaRateLimitError("Слишком много запросов к Enka.Network (429). Подождите минуту.") from err
        raise EnkaNetworkError(f"Ошибка Enka API: HTTP {err.code}") from err
    except urllib.error.URLError as err:
        raise EnkaNetworkError(f"Не удалось подключиться к Enka.Network: {err.reason}") from err
    except Exception as err:
        raise EnkaNetworkError(f"Сетевая ошибка: {err}") from err

    profile = parse_showcase(data)
    ttl = int(data.get("ttl", 60))
    _CACHE[clean_uid] = (now + ttl, profile)
    return profile


def validate_uid(uid: str) -> bool:
    """Validate 9 or 10 digit UID format."""
    clean = uid.strip()
    return clean.isdigit() and len(clean) in (9, 10)


def parse_enka_showcase(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Parse raw showcase dict into characters and artifacts list."""
    profile = parse_showcase(payload)
    chars = []
    for c in profile.characters:
        chars.append({
            "name": c.name,
            "element": c.element,
            "artifacts": c.artifacts,
        })
    return {"player": profile.player_name, "characters": chars}


def parse_enka_artifact(relic: Mapping[str, Any]) -> ParsedArtifact:
    """Convert raw relic dictionary to ParsedArtifact."""
    return parse_enka_relic(relic)


def fetch_showcase(uid: str) -> dict[str, Any]:
    """Fetch raw showcase JSON payload by UID."""
    if not validate_uid(uid):
        raise ValueError(f"Invalid UID: {uid}")
    clean_uid = uid.strip()
    url = f"https://enka.network/api/uid/{clean_uid}/"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GenshinArtifactCalc/2.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))
