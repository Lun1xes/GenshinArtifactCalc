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
        parsed = ParsedArtifact(
            slot="Цветок жизни",
            main_stat="HP",
            level=0,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("7.8")),
            ],
            set_key="NoblesseOblige",
        )
        self.app.bulk_import_to_history([parsed])
        history = self.app._load_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["slot"], "Цветок жизни")
        self.assertEqual(history[0]["main_stat"], "HP")


if __name__ == "__main__":
    unittest.main()
