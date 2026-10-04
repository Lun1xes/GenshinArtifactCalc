from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from decimal import Decimal

# Install customtkinter stub before importing calculator
from test_calculator_state import FakeApp, FakeVar, FakeWidget, install_stub

install_stub()

import calculator  # noqa: E402
from good_adapter import ParsedArtifact  # noqa: E402


class TestGoodUIIntegration(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        calculator.HISTORY_FILE = os.path.join(self._tmp.name, "hist.json")
        self.app = calculator.ArtifactCalculatorApp()

    def tearDown(self):
        self._tmp.cleanup()

    def test_load_artifact_from_good(self):
        parsed = ParsedArtifact(
            slot="Перо смерти",
            main_stat="Сила атаки",
            level=20,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("21.0")),
                ("Шанс крит. попадания", Decimal("7.0")),
                ("Сила атаки %", Decimal("9.9")),
                ("Восст. энергии", Decimal("5.2")),
            ],
            set_key="GladiatorsFinale",
        )
        self.app.load_artifact_from_good(parsed)

        self.assertEqual(self.app.slot_var.get(), "Перо смерти")
        self.assertEqual(self.app.main_stat_var.get(), "Сила атаки")
        self.assertEqual(self.app.level_var.get(), "+20")

        # Verify substat rows populated
        self.assertEqual(self.app.stat_widgets[0]["stat_combo"].get(), "Крит. урон")
        self.assertEqual(self.app.stat_widgets[0]["entry"].get(), "21.0")
        self.assertEqual(self.app.stat_widgets[1]["stat_combo"].get(), "Шанс крит. попадания")
        self.assertEqual(self.app.stat_widgets[1]["entry"].get(), "7.0")

        # Verify calculation was executed automatically
        self.assertIsNotNone(self.app.last_calculation)
        self.assertEqual(self.app.last_calculation["slot"], "Перо смерти")
        self.assertEqual(self.app.last_calculation["level"], "+20")

        # Verify calculate_artifact alias exists and callable
        self.assertTrue(callable(self.app.calculate_artifact))

    def test_load_artifact_from_good_4_initial_stats(self):
        parsed = ParsedArtifact(
            slot="Перо смерти",
            main_stat="Сила атаки",
            level=20,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("21.0")),
                ("Шанс крит. попадания", Decimal("7.0")),
                ("Сила атаки %", Decimal("14.6")),
                ("Восст. энергии", Decimal("5.2")),
            ],
            set_key="GladiatorsFinale",
        )
        self.app.load_artifact_from_good(parsed)
        self.assertEqual(self.app.initial_stats_var.get(), "4 сабстата")
        self.assertIsNotNone(self.app.last_calculation)
        self.assertEqual(self.app.last_calculation["slot"], "Перо смерти")
        self.assertEqual(self.app.last_calculation["level"], "+20")

    def test_load_goblet_cryo_dmg(self):
        parsed = ParsedArtifact(
            slot="Кубок пространства",
            main_stat="Крио урон %",
            level=20,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("21.0")),
                ("Шанс крит. попадания", Decimal("7.0")),
                ("Сила атаки %", Decimal("14.6")),
                ("Восст. энергии", Decimal("5.2")),
            ],
            set_key="BlizzardStrayer",
        )
        self.app.load_artifact_from_good(parsed)
        self.assertEqual(self.app.slot_var.get(), "Кубок пространства")
        self.assertEqual(self.app.main_stat_var.get(), "Крио урон %")
        self.assertIsNotNone(self.app.last_calculation)
        self.assertEqual(self.app.last_calculation["main_stat"], "Крио урон %")

    def test_load_circlet_synonym(self):
        parsed = ParsedArtifact(
            slot="Корона проницательности",
            main_stat="Крит. урон",
            level=20,
            rarity=5,
            substats=[
                ("Шанс крит. попадания", Decimal("10.5")),
                ("Сила атаки %", Decimal("14.6")),
                ("Восст. энергии", Decimal("11.0")),
                ("Мастерство стихий", Decimal("21")),
            ],
            set_key="NoblesseOblige",
        )
        self.app.load_artifact_from_good(parsed)
        self.assertEqual(self.app.slot_var.get(), "Корона разума")
        self.assertEqual(self.app.main_stat_var.get(), "Крит. урон")
        self.assertIsNotNone(self.app.last_calculation)

    def test_export_current_artifact_to_good(self):
        # Configure calculator inputs
        self.app.slot_var.set("Перо смерти")
        self.app._on_slot_change("Перо смерти")
        self.app.main_stat_var.set("Сила атаки")
        self.app.level_var.set("+20")
        self.app.stat_widgets[0]["stat_combo"].set("Крит. урон")
        self.app.stat_widgets[0]["entry"].delete(0, "end")
        self.app.stat_widgets[0]["entry"].insert(0, "21.0")
        self.app.stat_widgets[1]["stat_combo"].set("Шанс крит. попадания")
        self.app.stat_widgets[1]["entry"].delete(0, "end")
        self.app.stat_widgets[1]["entry"].insert(0, "7.0")
        self.app.stat_widgets[2]["stat_combo"].set("Сила атаки %")
        self.app.stat_widgets[2]["entry"].delete(0, "end")
        self.app.stat_widgets[2]["entry"].insert(0, "9.9")
        self.app.stat_widgets[3]["stat_combo"].set("Восст. энергии")
        self.app.stat_widgets[3]["entry"].delete(0, "end")
        self.app.stat_widgets[3]["entry"].insert(0, "5.2")

        good_art = self.app.export_current_artifact_to_good()
        self.assertEqual(good_art["slotKey"], "plume")
        self.assertEqual(good_art["mainStatKey"], "atk")
        self.assertEqual(good_art["level"], 20)
        self.assertEqual(len(good_art["substats"]), 4)

    def test_bulk_import_to_history(self):
        parsed1 = ParsedArtifact(
            slot="Цветок жизни",
            main_stat="HP",
            level=0,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("7.8")),
            ],
            set_key="NoblesseOblige",
            location="RaidenShogun",
        )
        parsed2 = ParsedArtifact(
            slot="Перо смерти",
            main_stat="Сила атаки",
            level=20,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("21.0")),
                ("Шанс крит. попадания", Decimal("7.0")),
                ("Сила атаки %", Decimal("14.6")),
                ("Восст. энергии", Decimal("5.2")),
            ],
            set_key="GladiatorsFinale",
            location="",
        )
        self.app.bulk_import_to_history([parsed1, parsed2])
        history = self.app._load_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["location"], "Инвентарь")
        self.assertEqual(history[0]["rank"], "S")
        self.assertEqual(history[1]["location"], "RaidenShogun")

    def test_open_history_window(self):
        try:
            self.app.open_history_window()
            opened = True
        except Exception:
            opened = False
        self.assertTrue(opened)

    def test_open_good_transfer_dialog(self):
        # Verify dialog opens without exceptions under CTk stub
        try:
            self.app.open_good_transfer_dialog()
            opened = True
        except Exception:
            opened = False
        self.assertTrue(opened)

    def test_good_dialog_modeless_and_single_instance(self):
        self.app.open_good_transfer_dialog()
        first_dialog = self.app._good_dialog
        self.assertIsNotNone(first_dialog)
        # Verify opening again reuses existing instance without exception
        self.app.open_good_transfer_dialog()
        self.assertIs(self.app._good_dialog, first_dialog)

    def test_handle_control_keys_russian_paste(self):
        # Setup clipboard
        self.app.clipboard_clear()
        self.app.clipboard_append("718285856")

        entry = self.app.stat_widgets[0]["entry"]
        entry.delete(0, "end")

        class FakeKeyEvent:
            widget = entry
            keycode = 86  # 'V'
            keysym = "Cyrillic_em"
            state = 4

        res = self.app._handle_control_keys(FakeKeyEvent())
        self.assertEqual(res, "break")
        self.assertIn("718285856", entry.get())

    def test_handle_control_keys_latin_passthrough(self):
        class FakeKeyEvent:
            widget = self.app.stat_widgets[0]["entry"]
            keycode = 86
            keysym = "v"
            state = 4

        res = self.app._handle_control_keys(FakeKeyEvent())
        # Should not intercept Latin 'v', returning None
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
