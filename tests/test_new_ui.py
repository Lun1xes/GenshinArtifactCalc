"""Tests for new UI features in ArtifactCalculatorApp (Genshin-style redesign)."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from decimal import Decimal

from test_calculator_state import FakeApp, FakeVar, FakeWidget, install_stub

install_stub()

import calculator
from good_adapter import ParsedArtifact


FOUR_STATS = ["Крит. урон", "Шанс крит. попадания", "Сила атаки %", "Восст. энергии"]
FOUR_VALS = ["7.77", "3.89", "5.83", "6.48"]


class TestNewUIFeatures(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        calculator.HISTORY_FILE = os.path.join(self._tmp.name, "hist.json")
        self.app = calculator.ArtifactCalculatorApp()

    def tearDown(self):
        self._tmp.cleanup()

    def fill_and_calculate(self):
        for i, (stat, val) in enumerate(zip(FOUR_STATS, FOUR_VALS)):
            self.app.stat_widgets[i]["stat_combo"].set(stat)
            self.app.stat_widgets[i]["entry"].delete(0, "end")
            self.app.stat_widgets[i]["entry"].insert(0, val)
        self.app.calculate()

    def test_slot_buttons_and_highlight(self):
        self.assertTrue(hasattr(self.app, "_slot_buttons"))
        self.assertEqual(len(self.app._slot_buttons), 5)
        for slot in calculator.ARTIFACT_SLOTS:
            self.assertIn(slot, self.app._slot_buttons)

        # Select a slot
        self.app._select_slot("Цветок жизни")
        self.assertEqual(self.app.slot_var.get(), "Цветок жизни")
        self.assertEqual(self.app.main_stat_var.get(), "HP")
        self.assertEqual(self.app._slot_buttons["Цветок жизни"].opts.get("fg_color"), calculator.C.CYAN_DIM)

    def test_preset_buttons_and_highlight(self):
        self.assertTrue(hasattr(self.app, "_preset_buttons"))
        self.assertIn("Main DPS (Криты / Атака)", self.app._preset_buttons)

        # Click preset button
        self.app._on_preset_click("EM Reactor (Кадзуха, Нахида)")
        self.assertEqual(self.app.preset_var.get(), "EM Reactor (Кадзуха, Нахида)")
        self.assertEqual(self.app._preset_buttons["EM Reactor (Кадзуха, Нахида)"].opts.get("border_width"), 2)

    def test_roll_bars_render_and_clear(self):
        self.fill_and_calculate()
        self.assertIsNotNone(self.app.last_calculation)
        self.assertGreater(len(self.app.roll_bars), 0)

        # Invalidate clears roll bars
        self.app._invalidate_calculation()
        self.assertEqual(len(self.app.roll_bars), 0)

    def test_compare_window_insufficient_history(self):
        # Empty history
        self.app.open_compare_window()
        self.assertIsNone(getattr(self.app, "_compare_win", None))
        self.assertIn("⚠️", self.app.result_textbox.get())

    def test_compare_window_with_history(self):
        # Save two artifacts to history
        self.fill_and_calculate()
        self.app.save_to_history()

        # Fill another
        self.app.slot_var.set("Перо смерти")
        self.app._select_slot("Перо смерти")
        self.fill_and_calculate()
        self.app.save_to_history()

        # Open compare window
        self.app.open_compare_window()
        self.assertIsNotNone(getattr(self.app, "_compare_win", None))
        self.assertTrue(self.app._compare_win.winfo_exists())

        # Opening again should reuse/lift
        first_win = self.app._compare_win
        self.app.open_compare_window()
        self.assertIs(self.app._compare_win, first_win)

    def test_get_rank_helper(self):
        self.assertEqual(calculator.get_rank(95.0)[0], "SSS")
        self.assertEqual(calculator.get_rank(85.0)[0], "SS")
        self.assertEqual(calculator.get_rank(75.0)[0], "S")
        self.assertEqual(calculator.get_rank(55.0)[0], "A")
        self.assertEqual(calculator.get_rank(35.0)[0], "B")
        self.assertEqual(calculator.get_rank(15.0)[0], "C")

    def test_character_selection_and_weights(self):
        furina_display = "Фурина (Sub-DPS / Буфер)"
        self.app.character_var.set(furina_display)
        self.app._on_character_change(furina_display)

        self.assertIn("Фурина", self.app.preset_var.get())
        self.assertIn("Фурина", self.app.char_tip_lbl.opts.get("text", ""))

        # Check weights for Furina: HP% has weight, ATK% has 0.0
        weights = self.app._collect_weights(self.app.preset_var.get())
        self.assertGreater(weights.get("HP %", 0.0), 1.0)
        self.assertEqual(weights.get("Сила атаки %", 0.0), 0.0)

    def test_character_build_preserves_substats_when_filled(self):
        # Fill stats with values
        self.app.stat_widgets[0]["stat_combo"].set("Крит. урон")
        self.app.stat_widgets[0]["entry"].insert(0, "14.0")
        self.app.stat_widgets[1]["stat_combo"].set("HP %")
        self.app.stat_widgets[1]["entry"].insert(0, "5.8")

        # Switch to Kokomi (who dislikes crits)
        kokomi_build = "Кокоми (Хиллер / Драйвер бутонов)"
        self.app.character_var.set(kokomi_build)
        self.app._on_character_change(kokomi_build)

        # Existing stat combo names should NOT be changed because entries have values
        self.assertEqual(self.app.stat_widgets[0]["stat_combo"].get(), "Крит. урон")
        self.assertEqual(self.app.stat_widgets[1]["stat_combo"].get(), "HP %")
        # But widget weights should reflect Kokomi (crit is 0.0 or negative, HP% is positive)
        self.assertIn("0.0", self.app.stat_widgets[0]["weight_combo"].get())

    def test_load_artifact_from_good_with_set_and_location(self):
        parsed = ParsedArtifact(
            slot="Пески времени",
            main_stat="HP %",
            level=0,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("7.77")),
                ("Шанс крит. попадания", Decimal("3.89")),
                ("Восст. энергии", Decimal("6.48")),
                ("HP", Decimal("299")),
            ],
            set_key="GoldenTroupe",
            location="Furina",
        )
        self.app.load_artifact_from_good(parsed)

        self.assertEqual(self.app.set_var.get(), "Золотая труппа")
        self.assertEqual(self.app.character_var.get(), "Фурина (Sub-DPS / Буфер)")
        self.assertIsNotNone(self.app.last_calculation)

    def test_export_current_artifact_to_good_with_set_and_location(self):
        self.app.slot_var.set("Пески времени")
        self.app.main_stat_var.set("HP %")
        self.app.level_var.set("+0")
        self.app.set_var.set("Золотая труппа")
        self.app.character_var.set("Фурина (Sub-DPS / Буфер)")
        self.fill_and_calculate()

        exported = self.app.export_current_artifact_to_good()
        self.assertEqual(exported["setKey"], "GoldenTroupe")
        self.assertEqual(exported["location"], "Furina")

    def test_copy_share_card_with_set_and_character(self):
        self.app.set_var.set("Золотая труппа")
        self.app.character_var.set("Фурина (Sub-DPS / Буфер)")
        self.fill_and_calculate()

        self.app.copy_share_card()
        clipboard_text = self.app.clipboard_get()
        self.assertIn("Золотая труппа", clipboard_text)
        self.assertIn("Фурина", clipboard_text)

    def test_apply_character_and_calculate_try_on(self):
        self.fill_and_calculate()
        import character_builds as cb
        neuv_build = cb.find_build_for_character("Neuvillette")
        self.assertIsNotNone(neuv_build)

        self.app._apply_character_and_calculate(neuv_build)
        self.assertEqual(self.app.character_var.get(), neuv_build.display_name)
        self.assertIsNotNone(self.app.last_calculation)
        self.assertIn("Невиллет", self.app.last_calculation["role"])

    def test_bulk_import_to_history_with_character_weights(self):
        parsed_furina = ParsedArtifact(
            slot="Пески времени",
            main_stat="HP %",
            level=0,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("7.77")),
                ("Шанс крит. попадания", Decimal("3.89")),
                ("Восст. энергии", Decimal("6.48")),
                ("HP", Decimal("299")),
            ],
            set_key="GoldenTroupe",
            location="Furina",
        )
        parsed_unassigned = ParsedArtifact(
            slot="Цветок жизни",
            main_stat="HP",
            level=0,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("7.77")),
                ("Шанс крит. попадания", Decimal("3.89")),
                ("Сила атаки %", Decimal("5.83")),
                ("Восст. энергии", Decimal("6.48")),
            ],
            set_key="GladiatorsFinale",
            location="",
        )
        self.app.bulk_import_to_history([parsed_furina, parsed_unassigned])

        with open(calculator.HISTORY_FILE, "r", encoding="utf-8") as f:
            hist = json.load(f)

        self.assertEqual(len(hist), 2)
        roles = [h["role"] for h in hist]
        self.assertTrue(any("Фурина" in r for r in roles))

    def test_navigation_views(self):
        self.assertTrue(hasattr(self.app, "show_view"))
        self.assertEqual(self.app._current_view, "calc")

        self.app.show_view("history")
        self.assertEqual(self.app._current_view, "history")
        self.assertEqual(self.app._nav_buttons["history"].opts.get("fg_color"), calculator.C.CYAN_DIM)

        self.app.show_view("compare")
        self.assertEqual(self.app._current_view, "compare")

        self.app.show_view("hub")
        self.assertEqual(self.app._current_view, "hub")

        self.app.show_view("calc")
        self.assertEqual(self.app._current_view, "calc")

    def test_feather_emoji_universal_glyph(self):
        self.assertEqual(calculator.SLOT_EMOJI["Перо смерти"], "✒️")
        self.assertNotIn("🪶", calculator.SLOT_EMOJI.values())

    def test_auto_switch_to_calc_on_load(self):
        self.app.show_view("hub")
        self.assertEqual(self.app._current_view, "hub")

        parsed = ParsedArtifact(
            slot="Перо смерти",
            main_stat="Сила атаки",
            level=20,
            rarity=5,
            substats=[
                ("Крит. урон", Decimal("14.0")),
                ("Шанс крит. попадания", Decimal("7.0")),
            ],
            set_key="GladiatorsFinale",
            location="",
        )
        self.app.load_artifact_from_good(parsed)
        self.assertEqual(self.app._current_view, "calc")

    def test_compare_view_slot_filter_and_current_source(self):
        # Save two artifacts
        self.fill_and_calculate()
        self.app.save_to_history()

        self.app.show_view("compare")
        self.assertEqual(self.app._current_view, "compare")

        # Slot filter
        self.app._on_compare_slot_filter_change("🌺 Цветок")
        self.assertEqual(self.app._compare_slot_filter.get(), "🌺 Цветок")

        # Current artifact source
        self.app._set_compare_source_a("current")
        self.assertEqual(self.app._compare_source_a.get(), "current")
        self.assertIsNotNone(self.app._compare_item_a)

        # Switch source A to history and refresh to exercise scroll_a and scroll_b row buttons
        self.app._set_compare_source_a("history")
        self.assertEqual(self.app._compare_source_a.get(), "history")
        self.app._refresh_compare_view()

        # Select items
        history = self.app._load_history()
        self.assertGreater(len(history), 0)
        self.app._select_compare_item_a(history[0])
        self.app._select_compare_item_b(history[0])
        self.app._refresh_compare_view()

    def test_lazy_loading_and_window_performance(self):
        # Fresh instance
        fresh_app = calculator.ArtifactCalculatorApp()
        self.assertFalse(fresh_app._history_built)
        self.assertFalse(fresh_app._compare_built)
        self.assertFalse(fresh_app._hub_built)

        # Open history -> builds history view
        fresh_app.show_view("history")
        self.assertTrue(fresh_app._history_built)
        self.assertFalse(fresh_app._compare_built)

        # Open compare -> builds compare view
        fresh_app.show_view("compare")
        self.assertTrue(fresh_app._compare_built)

        # Open hub -> builds hub view
        fresh_app.show_view("hub")
        self.assertTrue(fresh_app._hub_built)


if __name__ == "__main__":
    unittest.main()


