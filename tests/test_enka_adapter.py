from __future__ import annotations

import unittest
from decimal import Decimal
import json

from good_adapter import ParsedArtifact
from enka_adapter import (
    EnkaError,
    EnkaNetworkError,
    EnkaPrivateShowcaseError,
    EnkaRateLimitError,
    EnkaUserNotFoundError,
    ENKA_SLOT_MAP,
    ENKA_PROP_MAP,
    ENKA_SET_MAP,
    get_avatar_name,
    parse_enka_relic,
    parse_showcase,
    enka_profile_to_good_json,
    EnkaProfile,
    EnkaCharacter,
    clear_enka_cache,
    fetch_enka_profile,
    _CACHE,
)


SAMPLE_ENKA_PAYLOAD = {
    "playerInfo": {
        "nickname": "TravelerTest",
        "level": 60,
        "worldLevel": 8,
        "signature": "Testing Enka Integration",
    },
    "avatarInfoList": [
        {
            "avatarId": 10000046,  # Hu Tao
            "propMap": {},
            "equipList": [
                {
                    "itemId": 82543,
                    "reliquary": {
                        "level": 21,
                        "mainPropId": 14001,
                        "appendPropIdList": [501082, 501063, 501221, 501242],
                    },
                    "flat": {
                        "nameTextMapHash": "513291572",
                        "rankLevel": 5,
                        "itemType": "ITEM_RELIQUARY",
                        "icon": "UI_RelicIcon_15008_4",
                        "equipType": "EQUIP_BRACER",
                        "setId": 15008,
                        "reliquarySubstats": [
                            {"appendPropId": "FIGHT_PROP_DEFENSE", "statValue": 37},
                            {"appendPropId": "FIGHT_PROP_ATTACK_PERCENT", "statValue": 11.1},
                            {"appendPropId": "FIGHT_PROP_CRITICAL_HURT", "statValue": 18.7},
                            {"appendPropId": "FIGHT_PROP_ELEMENT_MASTERY", "statValue": 19},
                        ],
                        "reliquaryMainstat": {
                            "mainPropId": "FIGHT_PROP_HP",
                            "statValue": 4780,
                        },
                    },
                },
                {
                    "itemId": 82523,
                    "reliquary": {
                        "level": 21,
                        "mainPropId": 12001,
                        "appendPropIdList": [501082],
                    },
                    "flat": {
                        "rankLevel": 5,
                        "itemType": "ITEM_RELIQUARY",
                        "icon": "UI_RelicIcon_15008_2",
                        "equipType": "EQUIP_NECKLACE",
                        "setId": 15008,
                        "reliquarySubstats": [
                            {"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 10.5},
                            {"appendPropId": "FIGHT_PROP_CRITICAL_HURT", "statValue": 21.0},
                            {"appendPropId": "FIGHT_PROP_HP_PERCENT", "statValue": 9.9},
                            {"appendPropId": "FIGHT_PROP_ELEMENT_MASTERY", "statValue": 42},
                        ],
                        "reliquaryMainstat": {
                            "mainPropId": "FIGHT_PROP_ATTACK",
                            "statValue": 311,
                        },
                    },
                },
                {
                    # Weapon (should be ignored by relic parser)
                    "itemId": 13501,
                    "weapon": {"level": 90, "promoteLevel": 6},
                    "flat": {"itemType": "ITEM_WEAPON", "rankLevel": 5},
                },
            ],
        },
        {
            "avatarId": 10000052,  # Raiden Shogun
            "equipList": [],
        },
    ],
    "ttl": 60,
    "uid": "700000042",
}


class TestEnkaAdapter(unittest.TestCase):
    def setUp(self):
        clear_enka_cache()

    def test_mappings_completeness(self):
        # Verify 5 standard slots
        self.assertEqual(len(ENKA_SLOT_MAP), 5)
        self.assertEqual(ENKA_SLOT_MAP["EQUIP_BRACER"], "Цветок жизни")
        self.assertEqual(ENKA_SLOT_MAP["EQUIP_NECKLACE"], "Перо смерти")
        self.assertEqual(ENKA_SLOT_MAP["EQUIP_SHOES"], "Пески времени")
        self.assertEqual(ENKA_SLOT_MAP["EQUIP_RING"], "Кубок пространства")
        self.assertEqual(ENKA_SLOT_MAP["EQUIP_DRESS"], "Корона проницательности")

        # Verify key stats
        self.assertEqual(ENKA_PROP_MAP["FIGHT_PROP_CRITICAL"], "Шанс крит. попадания")
        self.assertEqual(ENKA_PROP_MAP["FIGHT_PROP_CRITICAL_HURT"], "Крит. урон")
        self.assertEqual(ENKA_PROP_MAP["FIGHT_PROP_CHARGE_EFFICIENCY"], "Восст. энергии")
        self.assertEqual(ENKA_PROP_MAP["FIGHT_PROP_ELEMENT_MASTERY"], "Мастерство стихий")
        self.assertEqual(ENKA_PROP_MAP["FIGHT_PROP_FIRE_ADD_HURT"], "Пиро урон %")

    def test_avatar_name_lookup(self):
        self.assertEqual(get_avatar_name(10000046), "Hu Tao")
        self.assertEqual(get_avatar_name(10000052), "Raiden Shogun")
        self.assertEqual(get_avatar_name(10000089), "Furina")
        self.assertEqual(get_avatar_name(99999999), "Character_99999999")

    def test_parse_single_enka_relic(self):
        relic_raw = SAMPLE_ENKA_PAYLOAD["avatarInfoList"][0]["equipList"][0]
        parsed = parse_enka_relic(relic_raw, character_name="Hu Tao")

        self.assertIsInstance(parsed, ParsedArtifact)
        self.assertEqual(parsed.slot, "Цветок жизни")
        self.assertEqual(parsed.main_stat, "HP")
        self.assertEqual(parsed.level, 20)  # 21 - 1
        self.assertEqual(parsed.rarity, 5)
        self.assertEqual(parsed.set_key, "CrimsonWitchOfFlames")
        self.assertEqual(parsed.location, "Hu Tao")

        expected_subs = [
            ("Защита", Decimal("37")),
            ("Сила атаки %", Decimal("11.1")),
            ("Крит. урон", Decimal("18.7")),
            ("Мастерство стихий", Decimal("19")),
        ]
        self.assertEqual(parsed.substats, expected_subs)

    def test_parse_showcase_profile(self):
        profile = parse_showcase(SAMPLE_ENKA_PAYLOAD)
        self.assertEqual(profile.uid, "700000042")
        self.assertEqual(profile.nickname, "TravelerTest")
        self.assertEqual(profile.level, 60)
        self.assertEqual(profile.world_level, 8)
        self.assertEqual(len(profile.characters), 2)

        hu_tao = profile.characters[0]
        self.assertEqual(hu_tao.name, "Hu Tao")
        self.assertEqual(len(hu_tao.artifacts), 2)

        raiden = profile.characters[1]
        self.assertEqual(raiden.name, "Raiden Shogun")
        self.assertEqual(len(raiden.artifacts), 0)

    def test_private_showcase_raises_exception(self):
        private_payload = {
            "playerInfo": {"nickname": "HiddenPlayer", "level": 10},
            "uid": "123456789",
        }
        with self.assertRaises(EnkaPrivateShowcaseError):
            parse_showcase(private_payload)

        empty_showcase = {
            "playerInfo": {"nickname": "EmptyPlayer"},
            "avatarInfoList": [],
            "uid": "123456789",
        }
        with self.assertRaises(EnkaPrivateShowcaseError):
            parse_showcase(empty_showcase)

    def test_enka_to_good_json_export(self):
        profile = parse_showcase(SAMPLE_ENKA_PAYLOAD)
        good_json_str = enka_profile_to_good_json(profile)

        data = json.loads(good_json_str)
        self.assertEqual(data["format"], "GOOD")
        self.assertEqual(data["version"], 2)
        self.assertIn("artifacts", data)
        self.assertEqual(len(data["artifacts"]), 2)

        art0 = data["artifacts"][0]
        self.assertEqual(art0["slotKey"], "flower")
        self.assertEqual(art0["mainStatKey"], "hp")
        self.assertEqual(art0["level"], 20)
        self.assertEqual(art0["setKey"], "CrimsonWitchOfFlames")
        self.assertEqual(art0["location"], "Hu Tao")

    def test_caching_mechanism(self):
        profile = parse_showcase(SAMPLE_ENKA_PAYLOAD)
        _CACHE["700000042"] = (9999999999.0, profile)

        # Mocking or calling fetch with cache should return cached profile immediately
        cached_result = fetch_enka_profile("700000042", use_cache=True)
        self.assertEqual(cached_result.nickname, "TravelerTest")
        self.assertEqual(cached_result.uid, "700000042")


if __name__ == "__main__":
    unittest.main()
