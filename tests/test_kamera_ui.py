"""Tests for Inventory Kamera UI integration in ArtifactCalculatorApp."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from test_calculator_state import FakeApp, FakeVar, FakeWidget, install_stub

install_stub()

import calculator
import kamera_adapter
from good_adapter import ParsedArtifact


SAMPLE_GOOD_DATA = {
    "format": "GOOD",
    "version": 2,
    "source": "InventoryKamera",
    "artifacts": [
        {
            "setKey": "GladiatorsFinale",
            "slotKey": "flower",
            "rarity": 5,
            "mainStatKey": "hp",
            "level": 20,
            "substats": [
                {"key": "critRate_", "value": 10.5},
                {"key": "critDMG_", "value": 21.0},
                {"key": "atk_", "value": 9.9},
                {"key": "enerRech_", "value": 5.8},
            ],
            "location": "Diluc",
            "lock": True,
        },
        {
            "setKey": "EmblemOfSeveredFate",
            "slotKey": "sands",
            "rarity": 5,
            "mainStatKey": "enerRech_",
            "level": 20,
            "substats": [
                {"key": "critRate_", "value": 7.0},
                {"key": "critDMG_", "value": 14.0},
                {"key": "atk_", "value": 14.6},
                {"key": "hp_", "value": 4.1},
            ],
            "location": "RaidenShogun",
            "lock": True,
        },
        {
            "setKey": "DeepwoodMemories",
            "slotKey": "goblet",
            "rarity": 5,
            "mainStatKey": "dendro_dmg_",
            "level": 16,
            "substats": [
                {"key": "critRate_", "value": 3.9},
                {"key": "critDMG_", "value": 15.5},
                {"key": "eleMas", "value": 35.0},
                {"key": "atk_", "value": 4.7},
            ],
            "location": "",
            "lock": False,
        },
    ],
    "characters": [
        {"key": "Diluc", "level": 90},
        {"key": "RaidenShogun", "level": 90},
    ],
}


class TestKameraUIIntegration(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        calculator.HISTORY_FILE = os.path.join(self._tmp.name, "hist.json")
        self.app = calculator.ArtifactCalculatorApp()

    def tearDown(self):
        self._tmp.cleanup()

    def test_kamera_button_and_dialog_open(self):
        self.assertTrue(hasattr(self.app, "kamera_btn"))
        self.assertTrue(callable(self.app.open_kamera_dialog))

        # Open Kamera dialog
        self.app.open_kamera_dialog()
        self.assertIsNotNone(getattr(self.app, "_good_dialog", None))
        self.assertTrue(self.app._good_dialog.winfo_exists())

    def test_load_kamera_artifact_into_calculator(self):
        art = ParsedArtifact(
            slot="Пески времени",
            main_stat="Восст. энергии",
            level=20,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("14.0")),
                ("Шанс крит. попадания", Decimal("7.0")),
                ("Сила атаки %", Decimal("14.6")),
                ("HP %", Decimal("4.1")),
            ],
            set_key="EmblemOfSeveredFate",
            location="RaidenShogun",
        )
        self.app.load_artifact_from_good(art)

        self.assertEqual(self.app.slot_var.get(), "Пески времени")
        self.assertEqual(self.app.main_stat_var.get(), "Восст. энергии")
        self.assertEqual(self.app.level_var.get(), "+20")
        self.assertIsNotNone(self.app.last_calculation)
        self.assertEqual(self.app.last_calculation["slot"], "Пески времени")

    def test_bulk_save_kamera_scan_to_history(self):
        raw_artifacts = SAMPLE_GOOD_DATA["artifacts"]
        parsed_list = [kamera_adapter.from_good_artifact(r) for r in raw_artifacts]

        self.app.bulk_import_to_history(parsed_list)
        history = self.app._load_history()

        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["slot"], "Кубок пространства")
        self.assertEqual(history[1]["slot"], "Пески времени")
        self.assertEqual(history[1]["location"], "RaidenShogun")
        self.assertEqual(history[2]["slot"], "Цветок жизни")
        self.assertEqual(history[2]["location"], "Diluc")

    def test_kamera_tabview_initial_tab(self):
        # Open via open_kamera_dialog
        self.app.open_kamera_dialog()
        self.assertIsNotNone(self.app._good_dialog)
        # Check that subsequent call lifts dialog
        self.app.open_kamera_dialog()
        self.assertTrue(self.app._good_dialog.winfo_exists())

    def test_kamera_parsing_with_mixed_levels_and_sets(self):
        # Generate 45 items to test pagination boundary
        items = []
        for i in range(45):
            items.append({
                "setKey": f"Set_{i % 5}",
                "slotKey": "flower" if i % 2 == 0 else "plume",
                "rarity": 5,
                "mainStatKey": "hp",
                "level": 20 if i < 30 else 12,
                "substats": [
                    {"key": "critRate_", "value": 7.0},
                    {"key": "critDMG_", "value": 14.0},
                    {"key": "atk_", "value": 9.0},
                    {"key": "hp_", "value": 4.0},
                ],
                "location": "Diluc" if i % 3 == 0 else "",
                "lock": False,
            })
        scan_payload = {
            "format": "GOOD",
            "version": 2,
            "source": "InventoryKamera",
            "artifacts": items,
        }
        test_file = Path(self._tmp.name) / "test_scan_45.json"
        test_file.write_text(json.dumps(scan_payload), encoding="utf-8")

        parsed_list, meta = kamera_adapter.load_kamera_good_file(str(test_file))
        self.assertEqual(len(parsed_list), 45)
        self.assertEqual(meta["source"], "InventoryKamera")

        # Test bulk import to history
        self.app.bulk_import_to_history(parsed_list)
        hist = self.app._load_history()
        self.assertEqual(len(hist), 45)


if __name__ == "__main__":
    unittest.main()
