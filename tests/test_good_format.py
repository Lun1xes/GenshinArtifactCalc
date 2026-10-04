from __future__ import annotations

import unittest
from decimal import Decimal

from good_adapter import (
    GoodFormatError,
    ParsedArtifact,
    from_good_artifact,
    from_good_json,
    slot_good_to_internal,
    slot_internal_to_good,
    stat_good_to_internal,
    stat_internal_to_good,
    to_good_artifact,
    to_good_json,
)
from artifact_logic import ArtifactInputError, evaluate_artifact


class TestGoodFormatMapping(unittest.TestCase):
    def test_slot_mappings_bidirectional(self):
        cases = [
            ("flower", "Цветок жизни"),
            ("plume", "Перо смерти"),
            ("sands", "Пески времени"),
            ("goblet", "Кубок пространства"),
            ("circlet", "Корона проницательности"),
        ]
        for good_key, internal_name in cases:
            self.assertEqual(slot_good_to_internal(good_key), internal_name)
            self.assertEqual(slot_internal_to_good(internal_name), good_key)

    def test_stat_mappings_bidirectional(self):
        cases = [
            ("hp", "HP"),
            ("hp_", "HP %"),
            ("atk", "Сила атаки"),
            ("atk_", "Сила атаки %"),
            ("def", "Защита"),
            ("def_", "Защита %"),
            ("eleMas", "Мастерство стихий"),
            ("enerRech_", "Восст. энергии"),
            ("critRate_", "Шанс крит. попадания"),
            ("critDMG_", "Крит. урон"),
            ("heal_", "Бонус лечения"),
            ("physical_dmg_", "Физ. урон %"),
            ("pyro_dmg_", "Пиро урон %"),
            ("hydro_dmg_", "Гидро урон %"),
            ("cryo_dmg_", "Крио урон %"),
            ("electro_dmg_", "Электро урон %"),
            ("anemo_dmg_", "Анемо урон %"),
            ("geo_dmg_", "Гео урон %"),
            ("dendro_dmg_", "Дендро урон %"),
        ]
        for good_key, internal_name in cases:
            self.assertEqual(stat_good_to_internal(good_key), internal_name)
            self.assertEqual(stat_internal_to_good(internal_name), good_key)

    def test_unknown_slot_or_stat_raises_error(self):
        with self.assertRaises(GoodFormatError):
            slot_good_to_internal("unknown_slot")
        with self.assertRaises(GoodFormatError):
            stat_good_to_internal("unknown_stat")


class TestGoodSerialization(unittest.TestCase):
    def test_single_artifact_to_good(self):
        artifact = {
            "slot": "Перо смерти",
            "main_stat": "Сила атаки",
            "level": 20,
            "rarity": 5,
            "set_key": "GladiatorsFinale",
            "substats": [
                {"stat": "Крит. урон", "value": Decimal("21.0")},
                {"stat": "Шанс крит. попадания", "value": Decimal("7.0")},
                {"stat": "Сила атаки %", "value": Decimal("9.9")},
                {"stat": "Восст. энергии", "value": Decimal("5.2")},
            ],
        }
        good_dict = to_good_artifact(artifact)
        self.assertEqual(good_dict["slotKey"], "plume")
        self.assertEqual(good_dict["mainStatKey"], "atk")
        self.assertEqual(good_dict["level"], 20)
        self.assertEqual(good_dict["rarity"], 5)
        self.assertEqual(good_dict["setKey"], "GladiatorsFinale")
        self.assertEqual(len(good_dict["substats"]), 4)
        self.assertEqual(good_dict["substats"][0], {"key": "critDMG_", "value": 21.0})
        self.assertEqual(good_dict["substats"][1], {"key": "critRate_", "value": 7.0})

    def test_collection_to_good_json(self):
        artifacts = [
            {
                "slot": "Цветок жизни",
                "main_stat": "HP",
                "level": 0,
                "rarity": 5,
                "substats": [
                    {"stat": "Крит. урон", "value": Decimal("7.8")},
                ],
            }
        ]
        json_str = to_good_json(artifacts)
        self.assertIn('"format": "GOOD"', json_str)
        self.assertIn('"version": 2', json_str)
        self.assertIn('"flower"', json_str)


class TestGoodDeserialization(unittest.TestCase):
    def test_single_artifact_deserialization(self):
        good_obj = {
            "setKey": "GladiatorsFinale",
            "slotKey": "plume",
            "rarity": 5,
            "mainStatKey": "atk",
            "level": 20,
            "substats": [
                {"key": "critDMG_", "value": 21.0},
                {"key": "critRate_", "value": 7.0},
            ],
        }
        parsed: ParsedArtifact = from_good_artifact(good_obj)
        self.assertEqual(parsed.slot, "Перо смерти")
        self.assertEqual(parsed.main_stat, "Сила атаки")
        self.assertEqual(parsed.level, 20)
        self.assertEqual(parsed.rarity, 5)
        self.assertEqual(parsed.set_key, "GladiatorsFinale")
        self.assertEqual(len(parsed.substats), 2)
        self.assertEqual(parsed.substats[0], ("Крит. урон", Decimal("21.0")))
        self.assertEqual(parsed.substats[1], ("Шанс крит. попадания", Decimal("7.0")))

    def test_from_good_json_single_or_root(self):
        raw_root = """{
            "format": "GOOD",
            "version": 2,
            "source": "Test",
            "artifacts": [
                {
                    "setKey": "NoblesseOblige",
                    "slotKey": "sands",
                    "rarity": 5,
                    "mainStatKey": "atk_",
                    "level": 16,
                    "substats": [
                        {"key": "critRate_", "value": 3.9}
                    ]
                }
            ]
        }"""
        artifacts = from_good_json(raw_root)
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].slot, "Пески времени")
        self.assertEqual(artifacts[0].main_stat, "Сила атаки %")
        self.assertEqual(artifacts[0].level, 16)
        self.assertEqual(artifacts[0].substats[0], ("Шанс крит. попадания", Decimal("3.9")))

    def test_invalid_json_or_missing_keys_raises_good_format_error(self):
        with self.assertRaises(GoodFormatError):
            from_good_json("not valid json")
        with self.assertRaises(GoodFormatError):
            from_good_artifact({"invalid": "structure"})


class TestGoodEndToEndRoundTrip(unittest.TestCase):
    def test_round_trip_artifact_reachability_preserved(self):
        # 1. Evaluate original artifact
        slot = "Пески времени"
        main_stat = "Сила атаки %"
        substats = {
            "Крит. урон": Decimal("14.0"),
            "Шанс крит. попадания": Decimal("7.0"),
            "Восст. энергии": Decimal("5.2"),
            "Мастерство стихий": Decimal("23.0"),
        }
        weights = {s: 1.0 for s in substats}
        entries1 = [(i, stat, str(val)) for i, (stat, val) in enumerate(substats.items())]
        ev1 = evaluate_artifact(
            8,
            False,
            entries1,
            weights,
            slot=slot,
            main_stat=main_stat,
        )

        # 2. Export to GOOD
        raw_art = {
            "slot": slot,
            "main_stat": main_stat,
            "level": 8,
            "substats": [{"stat": k, "value": v} for k, v in substats.items()],
        }
        good_json_str = to_good_json(raw_art)

        # 3. Import from GOOD JSON
        parsed_list = from_good_json(good_json_str)
        self.assertEqual(len(parsed_list), 1)
        imported = parsed_list[0]
        self.assertEqual(imported.slot, slot)
        self.assertEqual(imported.main_stat, main_stat)
        self.assertEqual(imported.level, 8)

        # 4. Evaluate imported artifact
        entries2 = [(i, stat, str(val)) for i, (stat, val) in enumerate(imported.substats)]
        ev2 = evaluate_artifact(
            imported.level,
            False,
            entries2,
            weights,
            slot=imported.slot,
            main_stat=imported.main_stat,
        )

        # 5. Check exact match
        self.assertEqual(ev1.current_pct, ev2.current_pct)
        self.assertEqual(ev1.potential_pct, ev2.potential_pct)
        self.assertEqual(ev1.expected_pct, ev2.expected_pct)

    def test_unreachable_roll_diagnostics(self):
        # Substat with an impossible roll value (e.g. 50.0% crit rate)
        good_art = {
            "slotKey": "plume",
            "mainStatKey": "atk",
            "level": 0,
            "rarity": 5,
            "substats": [
                {"key": "critRate_", "value": 50.0},
            ],
        }
        parsed = from_good_artifact(good_art)
        self.assertEqual(parsed.slot, "Перо смерти")
        entries = [(0, "Шанс крит. попадания", "50.0")]
        # ArtifactInputError should be raised cleanly when evaluate is run
        with self.assertRaises(ArtifactInputError):
            evaluate_artifact(
                0,
                True,
                entries,
                {"Шанс крит. попадания": 1.0},
                slot=parsed.slot,
                main_stat=parsed.main_stat,
            )


if __name__ == "__main__":
    unittest.main()
