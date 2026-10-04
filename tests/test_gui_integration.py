"""Unit tests for GUI integration of Paimon.moe, AnimeGameData, and Genshin-DB features."""
import os
import sys
import tempfile
import types
import unittest

# Reuse the fake customtkinter stub pattern from test_calculator_state
from test_calculator_state import FakeApp, FakeVar, FakeWidget, install_stub

install_stub()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import calculator
import character_builds as cb
import upgrade_probability as up


class GuiIntegrationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        calculator.HISTORY_FILE = os.path.join(self._tmp.name, "hist.json")
        self.app = calculator.ArtifactCalculatorApp()

    def tearDown(self):
        self._tmp.cleanup()

    def _fill_valid_artifact(self, level="+0", slot="Пески времени", main_stat="HP %"):
        a = self.app
        a.slot_var.set(slot)
        a._on_slot_change(slot)
        a.main_stat_var.set(main_stat)
        a.level_var.set(level)
        a.initial_stats_var.set("4 сабстата")

        subs = [
            ("Крит. урон", "7.77"),
            ("Шанс крит. попадания", "3.89"),
            ("Восст. энергии", "6.48"),
            ("HP", "299"),
        ]
        for i, (name, val) in enumerate(subs):
            a.stat_widgets[i]["stat_combo"].set(name)
            a.stat_widgets[i]["entry"].delete(0, "end")
            a.stat_widgets[i]["entry"].insert(0, val)

    def test_two_level_character_selection(self):
        a = self.app
        # 1. Select character Furina
        a._on_char_name_change("Фурина")
        self.assertEqual(a.char_name_var.get(), "Фурина")
        self.assertIn("Фурина", a.character_var.get())
        self.assertTrue(len(a.role_name_menu.opts.get("values", [])) >= 2)

        # 2. Check info card updated
        tip = a.char_tip_lbl._text
        self.assertIn("Фурина", tip)
        self.assertIn("Золотая труппа", tip)
        self.assertIn("Оружие", tip)

        # 3. Select second role
        roles = a.role_name_menu.opts.get("values", [])
        second_role = roles[1]
        a._on_role_name_change(second_role)
        self.assertEqual(a.role_name_var.get(), second_role)
        self.assertIn(second_role, a.character_var.get())

        # 4. Preset resets character selection
        a._on_preset_click("Main DPS (Криты / Атака)")
        self.assertEqual(a.char_name_var.get(), "(Выбрать героя...)")
        self.assertEqual(a.role_name_var.get(), "(Роль / Билд)")
        self.assertEqual(a.character_var.get(), "(Выбрать персонажа...)")

    def test_backwards_compatible_character_change(self):
        a = self.app
        # Calling legacy _on_character_change with full string
        a._on_character_change("Фурина (Sub-DPS / Буфер)")
        self.assertEqual(a.char_name_var.get(), "Фурина")
        self.assertEqual(a.role_name_var.get(), "Sub-DPS / Буфер")
        self.assertEqual(a.character_var.get(), "Фурина (Sub-DPS / Буфер)")

    def test_upgrade_forecast_at_level_0(self):
        self._fill_valid_artifact(level="+0")
        self.app.calculate()

        self.assertIsNotNone(self.app.last_calculation)
        fc = self.app.last_calculation.get("forecast")
        self.assertIsNotNone(fc)
        self.assertTrue(len(fc["verdict"]) > 0)
        self.assertGreaterEqual(fc["prob_s_plus"], 0.0)

        # Check textbox report includes AnimeGameData section
        report = self.app.result_textbox._text
        self.assertIn("ПРОГНОЗ УЛУЧШЕНИЙ ДО +20", report)
        self.assertIn("Шанс S+", report)

        # Check forecast card labels
        verdict_text = self.app.forecast_verdict_lbl._text
        self.assertTrue(len(verdict_text) > 0)
        self.assertIn("Шанс", self.app.forecast_stats_lbl._text)

    def test_upgrade_forecast_at_level_20(self):
        self._fill_valid_artifact(level="+20")
        # In level 20 with 4 stats, total rolls must match +20 logic
        # 4 initial stats + 5 upgrades = 9 total rolls
        self.app.stat_widgets[0]["entry"].delete(0, "end")
        self.app.stat_widgets[0]["entry"].insert(0, "38.85") # 5 extra rolls
        self.app.calculate()

        self.assertIsNotNone(self.app.last_calculation)
        self.assertIn("+20", self.app.forecast_verdict_lbl._text)

    def test_share_card_includes_forecast(self):
        self._fill_valid_artifact(level="+0")
        self.app.calculate()
        self.app.copy_share_card()
        clipboard_content = "".join(self.app.clipboard)
        self.assertIn("Прогноз (+20):", clipboard_content)

    def test_artifact_icon_update(self):
        a = self.app
        # Should not throw any exception when updating slot or set
        a._update_artifact_icon("Кубок пространства", "GoldenTroupe")
        a._on_set_change("Золотая труппа")
        self.assertEqual(a.set_var.get(), "(Без сета / Любой)")


if __name__ == "__main__":
    unittest.main()
