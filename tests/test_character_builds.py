"""Unit tests for character_builds.py module."""
import unittest

import character_builds as cb


class TestCharacterBuilds(unittest.TestCase):
    def test_database_not_empty(self):
        self.assertGreater(len(cb.CHARACTER_BUILDS), 25)
        self.assertGreater(len(cb.ARTIFACT_SETS), 20)

    def test_get_build_by_display_name(self):
        furina = cb.get_build_by_display_name("Фурина (Sub-DPS / Буфер)")
        self.assertIsNotNone(furina)
        self.assertEqual(furina.name, "Фурина")
        self.assertIn("GoldenTroupe", furina.good_set_keys)
        self.assertIn("HP %", furina.main_stats["Пески времени"])

    def test_get_characters_for_set(self):
        # By Russian name
        troupe_users = cb.get_characters_for_set("Золотая труппа")
        self.assertTrue(any(u.name == "Фурина" for u in troupe_users))
        self.assertTrue(any(u.name == "Фишль" for u in troupe_users))

        # By GOOD setKey
        emblem_users = cb.get_characters_for_set("EmblemOfSeveredFate")
        self.assertTrue(any(u.name == "Райдэн" for u in emblem_users))
        self.assertTrue(any(u.name == "Е Лань" for u in emblem_users))
        self.assertTrue(any(u.name == "Сян Лин" for u in emblem_users))

    def test_evaluate_furina_ideal_artifact(self):
        furina = cb.get_build_by_display_name("Фурина (Sub-DPS / Буфер)")
        res = cb.evaluate_artifact_for_build(
            build=furina,
            slot="Пески времени",
            main_stat="HP %",
            substats={
                "Крит. урон": "21.0",
                "Шанс крит. попадания": "7.0",
                "Восст. энергии": "11.0",
                "HP": "299",
            },
            set_name_or_key="GoldenTroupe",
        )
        self.assertTrue(res.is_ideal)
        self.assertTrue(res.main_stat_matches)
        self.assertTrue(res.set_matches)
        self.assertGreaterEqual(res.score, 80.0)

    def test_evaluate_furina_bad_main_stat(self):
        furina = cb.get_build_by_display_name("Фурина (Sub-DPS / Буфер)")
        res = cb.evaluate_artifact_for_build(
            build=furina,
            slot="Пески времени",
            main_stat="Сила атаки %",
            substats={
                "Крит. урон": "21.0",
                "Шанс крит. попадания": "7.0",
            },
            set_name_or_key="GoldenTroupe",
        )
        self.assertFalse(res.is_ideal)
        self.assertFalse(res.main_stat_matches)
        self.assertIn("не подходит", res.verdict.lower())
        self.assertIn("HP", res.explanation)

    def test_kokomi_crit_penalty(self):
        kokomi = cb.get_build_by_display_name("Кокоми (Хиллер / Драйвер бутонов)")
        self.assertIsNotNone(kokomi)
        # Kokomi has negative crit weights
        self.assertLess(kokomi.substat_weights["Крит. урон"], 0.0)
        self.assertLess(kokomi.substat_weights["Шанс крит. попадания"], 0.0)

    def test_find_top_characters_for_artifact(self):
        # A Golden Troupe HP% Sands with Crit DMG and ER
        top = cb.find_top_characters_for_artifact(
            slot="Пески времени",
            main_stat="HP %",
            substats={"Крит. урон": "21.0", "Восст. энергии": "11.0", "Шанс крит. попадания": "7.0"},
            set_name_or_key="GoldenTroupe",
            limit=3,
        )
        self.assertGreater(len(top), 0)
        # Furina should be top 1
        self.assertEqual(top[0].build.name, "Фурина")

    def test_unique_character_names_and_builds(self):
        names = cb.get_unique_character_names()
        self.assertGreater(len(names), 25)
        self.assertIn("Фурина", names)
        self.assertIn("Невиллет", names)
        self.assertIn("Райдэн", names)

        furina_builds = cb.get_builds_for_character("Фурина")
        self.assertGreaterEqual(len(furina_builds), 2)
        self.assertTrue(all(b.name == "Фурина" for b in furina_builds))

    def test_weapon_names_and_formatting(self):
        self.assertEqual(cb.format_weapon_name("splendor_of_tranquil_waters"), "Блеск тихих вод")
        self.assertEqual(cb.format_weapon_name("favonius_sword"), "Меч Фавония")
        self.assertEqual(cb.format_weapon_name("unknown_new_spear"), "Unknown New Spear")

        furina = cb.get_build_by_display_name("Фурина (Sub-DPS / Буфер)")
        self.assertIsNotNone(furina)
        weapons = furina.top_weapon_names
        self.assertIsInstance(weapons, list)
        self.assertGreater(len(weapons), 0)


if __name__ == "__main__":
    unittest.main()
