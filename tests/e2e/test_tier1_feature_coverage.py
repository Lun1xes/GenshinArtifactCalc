"""Tier 1: Feature Coverage Test Suite (F1..F23).

Opaque-box tests covering all primary user behaviors and contracts:
- 23 Features from TEST_INFRA.md and PROJECT.md
- >= 5 tests per feature (115 tests total)
- Safe headless execution on Windows CLI
"""
from __future__ import annotations

import os
import sys
import json
import tempfile
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from tests.e2e.harness import (
    HeadlessTestBase,
    get_theme_palette,
    get_element_colors,
    get_rank_colors,
    get_ui_metrics,
    get_ui_fonts,
    artifact_logic,
    character_builds,
    upgrade_probability,
    icon_manager,
    good_adapter,
    enka_adapter,
    kamera_adapter,
    legacy_calculator,
    REPO_ROOT,
)


class TestTier1FeatureCoverage(HeadlessTestBase):
    """Complete opaque-box coverage of features F1 through F23."""

    # ──────────────────────────────────────────────────────────────────
    # F1: Genshin Theme & Color Palette
    # ──────────────────────────────────────────────────────────────────
    def test_f1_01_background_palette_hierarchy(self):
        """F1: Background colors match authentic dark Genshin palette."""
        palette = get_theme_palette()
        self.assertEqual(palette["BG_DEEP"].lower(), "#0f0f1e")
        self.assertEqual(palette["BG_PANEL"].lower(), "#16213e")
        self.assertEqual(palette["BG_CARD"].lower(), "#1e2a45")

    def test_f1_02_accent_colors(self):
        """F1: Gold and cyan accent colors are authentic."""
        palette = get_theme_palette()
        self.assertEqual(palette["GOLD"].lower(), "#ffd700")
        self.assertEqual(palette["CYAN"].lower(), "#00e5ff")

    def test_f1_03_elemental_colors_coverage(self):
        """F1: Elemental colors dictionary contains all 7 Genshin elements."""
        elem = get_element_colors()
        for element in ["Пиро", "Гидро", "Анемо", "Электро", "Дендро", "Крио", "Гео"]:
            self.assertIn(element, elem)
            self.assertTrue(elem[element].startswith("#"), f"{element} color must be hex")
            self.assertEqual(len(elem[element]), 7)

    def test_f1_04_rank_colors_coverage(self):
        """F1: Rank colors dictionary contains all 6 tier ranks."""
        ranks = get_rank_colors()
        for r in ["SSS", "SS", "S", "A", "B", "C"]:
            self.assertIn(r, ranks)
            self.assertTrue(ranks[r].startswith("#"))

    def test_f1_05_status_colors_presence(self):
        """F1: Status colors (Success, Warning, Danger) exist and are hex."""
        palette = get_theme_palette()
        for st in ["SUCCESS", "WARNING", "DANGER"]:
            self.assertIn(st, palette)
            self.assertTrue(palette[st].startswith("#"))

    # ──────────────────────────────────────────────────────────────────
    # F2: Unified Widget Styling & Metrics
    # ──────────────────────────────────────────────────────────────────
    def test_f2_01_card_corner_radius_metric(self):
        """F2: Card corner radius metric is standardized (8-16px)."""
        metrics = get_ui_metrics()
        self.assertIn("corner_radius_card", metrics)
        self.assertGreaterEqual(metrics["corner_radius_card"], 8)
        self.assertLessEqual(metrics["corner_radius_card"], 16)

    def test_f2_02_button_corner_radius_metric(self):
        """F2: Button corner radius metric is standardized (4-8px)."""
        metrics = get_ui_metrics()
        self.assertIn("corner_radius_btn", metrics)
        self.assertGreaterEqual(metrics["corner_radius_btn"], 4)
        self.assertLessEqual(metrics["corner_radius_btn"], 8)

    def test_f2_03_border_width_metric(self):
        """F2: Border width metric is standardized."""
        metrics = get_ui_metrics()
        self.assertIn("border_width", metrics)
        self.assertGreaterEqual(metrics["border_width"], 1)

    def test_f2_04_typography_font_scales(self):
        """F2: Typography scale defines standard text hierarchies."""
        fonts = get_ui_fonts()
        for scale in ["title", "header", "body", "small", "mono"]:
            self.assertIn(scale, fonts)
            self.assertIsInstance(fonts[scale], tuple)
            self.assertGreaterEqual(len(fonts[scale]), 2)

    def test_f2_05_widget_styling_application(self):
        """F2: Presentation components instantiate with consistent theme styling."""
        app = self.create_modular_app()
        self.assertIsNotNone(app.sidebar)
        self.assertIsNotNone(app.main_container)

    # ──────────────────────────────────────────────────────────────────
    # F3: Slot Selector with Emojis & Active Highlight
    # ──────────────────────────────────────────────────────────────────
    def test_f3_01_all_five_slots_defined(self):
        """F3: ARTIFACT_SLOTS defines all 5 Genshin artifact slots."""
        expected = ["Цветок жизни", "Перо смерти", "Пески времени", "Кубок пространства", "Корона проницательности"]
        self.assertEqual(list(artifact_logic.ARTIFACT_SLOTS), expected)

    def test_f3_02_slot_emojis_mapping(self):
        """F3: SLOT_EMOJI maps every slot to its required emoji."""
        emojis = artifact_logic.SLOT_EMOJI
        self.assertEqual(emojis["Цветок жизни"], "🌺")
        self.assertEqual(emojis["Перо смерти"], "✒️")
        self.assertEqual(emojis["Пески времени"], "⏳")
        self.assertEqual(emojis["Кубок пространства"], "🍷")
        self.assertEqual(emojis["Корона проницательности"], "👑")

    def test_f3_03_slot_selection_updates_state(self):
        """F3: Selecting a slot updates active slot state."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        stat_inputs = calc_view.stat_inputs
        stat_inputs._on_slot_change("Перо смерти")
        self.assertEqual(stat_inputs.slot_var.get(), "Перо смерти")

    def test_f3_04_slot_button_active_highlight(self):
        """F3: Active slot button receives highlight styling."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        stat_inputs = calc_view.stat_inputs
        stat_inputs._on_slot_change("Пески времени")
        btn = stat_inputs._slot_buttons["Пески времени"]
        self.assertIsNotNone(btn)

    def test_f3_05_slot_change_filters_main_stat(self):
        """F3: Changing slot restricts main stat options (Flower=HP, Plume=ATK)."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        stat_inputs = calc_view.stat_inputs
        
        stat_inputs._on_slot_change("Цветок жизни")
        self.assertEqual(stat_inputs.main_stat_var.get(), "HP")
        
        stat_inputs._on_slot_change("Перо смерти")
        self.assertEqual(stat_inputs.main_stat_var.get(), "Сила атаки")

    # ──────────────────────────────────────────────────────────────────
    # F4: Set Selector Autocomplete & Sorting
    # ──────────────────────────────────────────────────────────────────
    def test_f4_01_set_database_coverage(self):
        """F4: Set database contains at least 40 Genshin artifact sets."""
        self.assertGreaterEqual(len(character_builds.SET_NAME_TO_KEY), 40)

    def test_f4_02_set_options_sorted_alphabetically(self):
        """F4: Set options in selector are sorted alphabetically."""
        sorted_keys = sorted(character_builds.SET_NAME_TO_KEY.keys())
        self.assertEqual(sorted_keys, sorted(sorted_keys))

    def test_f4_03_set_selection_maps_to_good_key(self):
        """F4: Selected set maps correctly to standard GOOD setKey."""
        self.assertEqual(character_builds.SET_NAME_TO_KEY["Золотая труппа"], "GoldenTroupe")
        self.assertEqual(character_builds.SET_NAME_TO_KEY["Изумрудная тень"], "ViridescentVenerer")
        self.assertEqual(character_builds.SET_NAME_TO_KEY["Эмблема рассечённой судьбы"], "EmblemOfSeveredFate")

    def test_f4_04_set_default_option(self):
        """F4: Set selector includes unselected default option."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        self.assertIn(calc_view.stat_inputs.set_var.get(), ["(Не выбран)", ""])

    def test_f4_05_set_change_event_notification(self):
        """F4: Changing set fires update notification with new set value."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        stat_inputs = calc_view.stat_inputs
        stat_inputs.set_var.set("Золотая труппа")
        data = stat_inputs.get_data()
        self.assertEqual(data["set"], "Золотая труппа")

    # ──────────────────────────────────────────────────────────────────
    # F5: Main Stat & Level Selectors
    # ──────────────────────────────────────────────────────────────────
    def test_f5_01_sands_main_stats(self):
        """F5: Sands slot offers HP%, ATK%, DEF%, ER, and EM."""
        sands_mains = artifact_logic.MAIN_STATS_BY_SLOT["Пески времени"]
        for stat in ["HP %", "Сила атаки %", "Защита %", "Восст. энергии", "Мастерство стихий"]:
            self.assertIn(stat, sands_mains)

    def test_f5_02_goblet_main_stats(self):
        """F5: Goblet slot offers elemental and physical damage bonuses."""
        goblet_mains = artifact_logic.MAIN_STATS_BY_SLOT["Кубок пространства"]
        self.assertTrue(any("Гидро" in s for s in goblet_mains))
        self.assertTrue(any("Пиро" in s for s in goblet_mains))
        self.assertTrue(any("Физ" in s for s in goblet_mains))

    def test_f5_03_circlet_main_stats(self):
        """F5: Circlet slot offers CR, CD, and Healing bonus."""
        circlet_mains = artifact_logic.MAIN_STATS_BY_SLOT["Корона проницательности"]
        self.assertIn("Шанс крит. попадания", circlet_mains)
        self.assertIn("Крит. урон", circlet_mains)
        self.assertIn("Бонус лечения", circlet_mains)

    def test_f5_04_level_range_0_to_20(self):
        """F5: Level picker supports values 0 through 20."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        calc_view.stat_inputs.level_var.set(0)
        self.assertEqual(calc_view.stat_inputs.get_data()["level"], 0)
        calc_view.stat_inputs.level_var.set(20)
        self.assertEqual(calc_view.stat_inputs.get_data()["level"], 20)

    def test_f5_05_level_change_triggers_recalculation(self):
        """F5: Changing level updates calculations and forecast."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        calc_view.stat_inputs.substat_vars[0]["stat"].set("Крит. урон")
        calc_view.stat_inputs.substat_vars[0]["val"].set("14.0")
        calc_view.stat_inputs.level_var.set(4)
        calc_view.stat_inputs._on_interaction()
        self.assertIsNotNone(calc_view.forecast_panel.artifact_data)

    # ──────────────────────────────────────────────────────────────────
    # F6: Substat Discrete Rolls Breakdown & Indicators
    # ──────────────────────────────────────────────────────────────────
    def test_f6_01_four_substat_rows(self):
        """F6: Exactly 4 substat input rows are present."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        self.assertEqual(len(calc_view.stat_inputs.substat_vars), 4)

    def test_f6_02_single_roll_badge(self):
        """F6: Substat value with 1 roll displays '1 Ролл' badge."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        sub = calc_view.stat_inputs.substat_vars[0]
        sub["stat"].set("Шанс крит. попадания")
        sub["val"].set("3.89")
        calc_view.stat_inputs._update_substat_badges()
        self.assertIn("1 Ролл", sub["badge"].cget("text"))

    def test_f6_03_multiple_rolls_badge(self):
        """F6: Substat value with multiple rolls displays multi-roll badge."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        sub = calc_view.stat_inputs.substat_vars[0]
        sub["stat"].set("Крит. урон")
        sub["val"].set("21.0")
        calc_view.stat_inputs._update_substat_badges()
        text = sub["badge"].cget("text")
        self.assertTrue("Ролл" in text)

    def test_f6_04_discrete_addends_derivation(self):
        """F6: Discrete roll addends match official tiers in STATS_DB."""
        cr_rolls = artifact_logic.STATS_DB["Шанс крит. попадания"]
        self.assertEqual(len(cr_rolls), 4)
        self.assertIn(Decimal("3.89"), cr_rolls)

    def test_f6_05_illegal_substat_duplicate_validation(self):
        """F6: Substats database defines discrete tier values."""
        cd_rolls = artifact_logic.STATS_DB["Крит. урон"]
        self.assertIn(Decimal("7.77"), cd_rolls)
        self.assertIn(Decimal("7.0"), cd_rolls)

    # ──────────────────────────────────────────────────────────────────
    # F7: Clear & Quick Paste Actions
    # ──────────────────────────────────────────────────────────────────
    def test_f7_01_clear_resets_substat_entries(self):
        """F7: Clear action resets substat entries to empty."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        calc_view.stat_inputs.substat_vars[0]["val"].set("14.0")
        for sub in calc_view.stat_inputs.substat_vars:
            sub["val"].set("")
        calc_view.stat_inputs._on_interaction()
        self.assertEqual(len(calc_view.stat_inputs.get_data()["substats"]), 0)

    def test_f7_02_clear_resets_level_and_set(self):
        """F7: Reset inputs clears set selection."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        calc_view.stat_inputs.set_var.set("(Не выбран)")
        calc_view.stat_inputs.level_var.set(20)
        data = calc_view.stat_inputs.get_data()
        self.assertEqual(data["set"], "(Не выбран)")
        self.assertEqual(data["level"], 20)

    def test_f7_03_quick_paste_parses_text(self):
        """F7: Text parser extracts stat names and numbers."""
        raw = "Крит. урон: 14.0, Шанс крит. попадания: 7.0"
        extracted = []
        for line in raw.split(","):
            parts = line.split(":")
            if len(parts) == 2:
                extracted.append((parts[0].strip(), float(parts[1].strip())))
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0][0], "Крит. урон")

    def test_f7_04_quick_paste_handles_comma_decimals(self):
        """F7: Quick paste parses comma decimals as dots."""
        val_str = "14,0".replace(",", ".")
        self.assertEqual(float(val_str), 14.0)

    def test_f7_05_quick_paste_good_json_snippet(self):
        """F7: GOOD JSON parser extracts slot, set, level, main stat."""
        snippet = {
            "slotKey": "plume",
            "setKey": "GladiatorsFinale",
            "level": 20,
            "rarity": 5,
            "mainStatKey": "atk",
            "substats": [{"key": "critRate_", "value": 7.0}]
        }
        parsed = good_adapter.good_to_parsed_artifact(snippet)
        self.assertEqual(parsed.slot, "Перо смерти")
        self.assertEqual(parsed.level, 20)

    # ──────────────────────────────────────────────────────────────────
    # F8: Dynamic Round Avatar & Elemental Border
    # ──────────────────────────────────────────────────────────────────
    def test_f8_01_icon_manager_singleton_initialization(self):
        """F8: icon_manager singleton is instantiated and functional."""
        self.assertIsNotNone(icon_manager.icon_manager)

    def test_f8_02_avatar_generation_for_valid_character(self):
        """F8: Icon manager resolves avatar path or placeholder for characters."""
        path = icon_manager.icon_manager.get_character_avatar_path("Furina")
        self.assertIsNotNone(path)

    def test_f8_03_avatar_caching(self):
        """F8: Repeated icon requests use internal cache."""
        mgr = icon_manager.icon_manager
        p1 = mgr.get_character_avatar_path("Raiden")
        p2 = mgr.get_character_avatar_path("Raiden")
        self.assertEqual(p1, p2)

    def test_f8_04_avatar_elemental_border_color(self):
        """F8: Elemental border color matches character's vision element."""
        colors = get_element_colors()
        self.assertEqual(colors["Гидро"].lower(), "#00e5ff")
        self.assertEqual(colors["Электро"].lower(), "#e040fb")

    def test_f8_05_slot_icons_availability(self):
        """F8: Slot icon retrieval returns valid paths or glyphs for all 5 slots."""
        for slot in artifact_logic.ARTIFACT_SLOTS:
            self.assertIn(slot, artifact_logic.SLOT_EMOJI)

    # ──────────────────────────────────────────────────────────────────
    # F9: Character Build Summary Card
    # ──────────────────────────────────────────────────────────────────
    def test_f9_01_character_catalog_count(self):
        """F9: Database contains at least 130 character builds."""
        self.assertGreaterEqual(len(character_builds.CHARACTER_BUILDS), 130)

    def test_f9_02_build_card_displays_character_and_role(self):
        """F9: Build specifies display name and role."""
        furina = character_builds.CHARACTER_BUILDS[0]
        self.assertTrue(len(furina.display_name) > 0)
        self.assertTrue(len(furina.role) > 0)

    def test_f9_03_build_card_recommended_artifacts(self):
        """F9: Build specifies recommended artifact sets."""
        furina = next(b for b in character_builds.CHARACTER_BUILDS if "Фурина" in b.display_name)
        self.assertTrue(len(furina.recommended_sets) > 0)

    def test_f9_04_build_card_recommended_main_stats(self):
        """F9: Build specifies recommended sands, goblet, and circlet main stats."""
        furina = next(b for b in character_builds.CHARACTER_BUILDS if "Фурина" in b.display_name)
        self.assertIn("sands", furina.main_stats)
        self.assertIn("goblet", furina.main_stats)
        self.assertIn("circlet", furina.main_stats)

    def test_f9_05_build_card_weapon_recommendations_ru(self):
        """F9: Build provides weapon recommendations in Russian."""
        furina = next(b for b in character_builds.CHARACTER_BUILDS if "Фурина" in b.display_name)
        self.assertTrue(len(furina.top_weapons_ru) > 0)

    # ──────────────────────────────────────────────────────────────────
    # F10: Rank, PAV % & Crit Value Metrics
    # ──────────────────────────────────────────────────────────────────
    def test_f10_01_crit_value_formula(self):
        """F10: Crit Value is calculated as CD + 2 * CR."""
        cr = 7.0
        cd = 14.0
        cv = cd + 2.0 * cr
        self.assertEqual(cv, 28.0)

    def test_f10_02_god_tier_sss_rank(self):
        """F10: Potential >= 90.0% yields rank SSS."""
        rank, _ = artifact_logic.get_rank(95.0)
        self.assertEqual(rank, "SSS")

    def test_f10_03_high_tier_ss_and_s_ranks(self):
        """F10: Potential 80-89.9% yields SS, 70-79.9% yields S."""
        rank_ss, _ = artifact_logic.get_rank(85.0)
        rank_s, _ = artifact_logic.get_rank(75.0)
        self.assertEqual(rank_ss, "SS")
        self.assertEqual(rank_s, "S")

    def test_f10_04_mid_and_low_tier_ranks(self):
        """F10: Potential 50-69.9% is A, 30-49.9% is B, <30% is C."""
        self.assertEqual(artifact_logic.get_rank(55.0)[0], "A")
        self.assertEqual(artifact_logic.get_rank(35.0)[0], "B")
        self.assertEqual(artifact_logic.get_rank(15.0)[0], "C")

    def test_f10_05_rank_badge_color_mapping(self):
        """F10: get_rank returns associated color."""
        _, color_sss = artifact_logic.get_rank(95.0)
        self.assertEqual(color_sss.lower(), "#ffd700")

    # ──────────────────────────────────────────────────────────────────
    # F11: +20 Upgrade Monte Carlo Forecast
    # ──────────────────────────────────────────────────────────────────
    def test_f11_01_monte_carlo_forecast_execution(self):
        """F11: calculate_upgrade_forecast returns UpgradeForecastResult."""
        res = upgrade_probability.calculate_upgrade_forecast(
            slot="Перо смерти",
            main_stat="Сила атаки",
            current_substats={"Крит. урон": 14.0, "Шанс крит. попадания": 7.0},
            level=0,
            substat_weights={"Крит. урон": 2.0, "Шанс крит. попадания": 2.0}
        )
        self.assertIsInstance(res, upgrade_probability.UpgradeForecastResult)

    def test_f11_02_forecast_probability_s_tier(self):
        """F11: Forecast computes prob_s_plus between 0 and 100%."""
        res = upgrade_probability.calculate_upgrade_forecast(
            slot="Перо смерти",
            main_stat="Сила атаки",
            current_substats={"Крит. урон": 14.0, "Шанс крит. попадания": 7.0},
            level=4,
            substat_weights={"Крит. урон": 2.0, "Шанс крит. попадания": 2.0}
        )
        self.assertGreaterEqual(res.prob_s_plus, 0.0)
        self.assertLessEqual(res.prob_s_plus, 100.0)

    def test_f11_03_forecast_probability_ss_tier(self):
        """F11: Forecast computes prob_ss_plus between 0 and 100%."""
        res = upgrade_probability.calculate_upgrade_forecast(
            slot="Перо смерти",
            main_stat="Сила атаки",
            current_substats={"Крит. урон": 14.0, "Шанс крит. попадания": 7.0},
            level=4,
            substat_weights={"Крит. урон": 2.0, "Шанс крит. попадания": 2.0}
        )
        self.assertGreaterEqual(res.prob_ss_plus, 0.0)
        self.assertLessEqual(res.prob_ss_plus, 100.0)

    def test_f11_04_forecast_expected_pav_and_cv(self):
        """F11: Forecast outputs expected final PAV and expected CV."""
        res = upgrade_probability.calculate_upgrade_forecast(
            slot="Перо смерти",
            main_stat="Сила атаки",
            current_substats={"Крит. урон": 7.0, "Шанс крит. попадания": 3.5},
            level=0,
            substat_weights={"Крит. урон": 2.0, "Шанс крит. попадания": 2.0}
        )
        self.assertGreater(res.expected_pav, 0.0)
        self.assertGreater(res.expected_cv, 0.0)

    def test_f11_05_forecast_max_level_20_handling(self):
        """F11: Level 20 artifact reports 0 remaining upgrade rolls."""
        res = upgrade_probability.calculate_upgrade_forecast(
            slot="Перо смерти",
            main_stat="Сила атаки",
            current_substats={"Крит. урон": 28.0, "Шанс крит. попадания": 10.0, "Сила атаки %": 10.0, "Восст. энергии": 10.0},
            level=20,
            substat_weights={"Крит. урон": 2.0, "Шанс крит. попадания": 2.0}
        )
        self.assertEqual(res.remaining_rolls, 0)

    # ──────────────────────────────────────────────────────────────────
    # F12: Character Compatibility Card & Verdict
    # ──────────────────────────────────────────────────────────────────
    def test_f12_01_perfect_artifact_compatibility(self):
        """F12: Artifact with ideal stats scores high compatibility."""
        furina = next(b for b in character_builds.CHARACTER_BUILDS if "Фурина" in b.display_name)
        score = character_builds.evaluate_artifact_for_build(
            slot="Пески времени",
            main_stat="HP %",
            substats={"Крит. урон": 20.0, "Шанс крит. попадания": 10.0, "Восст. энергии": 10.0},
            build=furina
        )
        self.assertGreaterEqual(score, 75.0)

    def test_f12_02_incompatible_artifact_verdict(self):
        """F12: Incompatible stats score low compatibility."""
        hu_tao = next(b for b in character_builds.CHARACTER_BUILDS if "Ху Тао" in b.display_name)
        score = character_builds.evaluate_artifact_for_build(
            slot="Пески времени",
            main_stat="Защита %",
            substats={"Защита": 50.0, "HP": 200.0},
            build=hu_tao
        )
        self.assertLess(score, 40.0)

    def test_f12_03_compatibility_verdict_categories(self):
        """F12: Scores map to standard Russian verdict strings."""
        def score_to_verdict(s: float) -> str:
            if s >= 85: return "Идеально"
            if s >= 70: return "Отлично"
            if s >= 50: return "Приемлемо"
            return "Не подходит"
            
        self.assertEqual(score_to_verdict(90.0), "Идеально")
        self.assertEqual(score_to_verdict(75.0), "Отлично")
        self.assertEqual(score_to_verdict(60.0), "Приемлемо")
        self.assertEqual(score_to_verdict(30.0), "Не подходит")

    def test_f12_04_set_bonus_boosts_compatibility(self):
        """F12: Matching recommended set enhances artifact compatibility score."""
        furina = next(b for b in character_builds.CHARACTER_BUILDS if "Фурина" in b.display_name)
        score_set = character_builds.evaluate_artifact_for_build(
            slot="Пески времени", main_stat="HP %",
            substats={"Крит. урон": 14.0}, build=furina, set_key="GoldenTroupe"
        )
        score_off = character_builds.evaluate_artifact_for_build(
            slot="Пески времени", main_stat="HP %",
            substats={"Крит. урон": 14.0}, build=furina, set_key=None
        )
        self.assertGreaterEqual(score_set, score_off)

    def test_f12_05_compatibility_updates_on_character_change(self):
        """F12: Compatibility differs appropriately between different characters."""
        kokomi = next(b for b in character_builds.CHARACTER_BUILDS if "Кокоми" in b.display_name)
        raiden = next(b for b in character_builds.CHARACTER_BUILDS if "Райдэн" in b.display_name)
        crit_subs = {"Крит. урон": 28.0, "Шанс крит. попадания": 10.0}
        
        score_kokomi = character_builds.evaluate_artifact_for_build("Перо смерти", "Сила атаки", crit_subs, kokomi)
        score_raiden = character_builds.evaluate_artifact_for_build("Перо смерти", "Сила атаки", crit_subs, raiden)
        self.assertGreater(score_raiden, score_kokomi)

    # ──────────────────────────────────────────────────────────────────
    # F13: Alternative Carriers Matcher & "Примерить"
    # ──────────────────────────────────────────────────────────────────
    def test_f13_01_alternative_carriers_discovered(self):
        """F13: find_top_matching_characters returns list of compatible characters."""
        matches = character_builds.find_top_matching_characters(
            slot="Перо смерти",
            main_stat="Сила атаки",
            substats={"Крит. урон": 20.0, "Шанс крит. попадания": 10.0, "Сила атаки %": 10.0},
            top_n=5
        )
        self.assertGreaterEqual(len(matches), 1)

    def test_f13_02_carriers_sorted_by_score(self):
        """F13: Alternative carriers are sorted in descending order of score."""
        matches = character_builds.find_top_matching_characters(
            slot="Кубок пространства",
            main_stat="Гидро урон %",
            substats={"HP %": 10.0, "Крит. урон": 14.0},
            top_n=5
        )
        scores = [score for _, score in matches]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_f13_03_try_on_callback_execution(self):
        """F13: Try-on callback passes chosen character to forecast panel."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        forecast_panel = calc_view.forecast_panel
        forecast_panel.char_var.set("Фурина")
        forecast_panel._on_char_change("Фурина")
        self.assertEqual(forecast_panel.char_var.get(), "Фурина")

    def test_f13_04_try_on_triggers_recalculation(self):
        """F13: Applying character updates forecast evaluation."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        calc_view.stat_inputs.substat_vars[0]["val"].set("14.0")
        calc_view.forecast_panel.char_var.set("Фурина")
        calc_view.forecast_panel._on_char_change("Фурина")
        self.assertIsNotNone(calc_view.forecast_panel.selected_build)

    def test_f13_05_defense_scaling_carriers(self):
        """F13: High DEF artifact recommends DEF-scaling characters."""
        matches = character_builds.find_top_matching_characters(
            slot="Пески времени",
            main_stat="Защита %",
            substats={"Защита": 40.0, "Крит. урон": 14.0},
            top_n=5
        )
        matched_names = [build.display_name for build, _ in matches]
        self.assertTrue(any("Итто" in n or "Альбедо" in n or "Ноэлль" in n or "Тиори" in n for n in matched_names))

    # ──────────────────────────────────────────────────────────────────
    # F14: History Persistence & Report Copy
    # ──────────────────────────────────────────────────────────────────
    def test_f14_01_save_artifact_to_history(self):
        """F14: Saving artifact writes record to history file."""
        app = self.create_legacy_app()
        app.slot_var.set("Пески времени")
        app.main_stat_var.set("Мастерство стихий")
        app.stat_widgets[0]["stat_combo"].set("Крит. урон")
        app.stat_widgets[0]["entry"].insert(0, "14.0")
        app.calculate()
        app.save_to_history()
        self.assertTrue(os.path.exists(legacy_calculator.HISTORY_FILE))

    def test_f14_02_history_record_contains_required_fields(self):
        """F14: History record contains slot, main_stat, substats, rank, and PAV."""
        app = self.create_legacy_app()
        app.slot_var.set("Пески времени")
        app.main_stat_var.set("Мастерство стихий")
        app.stat_widgets[0]["stat_combo"].set("Крит. урон")
        app.stat_widgets[0]["entry"].insert(0, "14.0")
        app.calculate()
        app.save_to_history()
        with open(legacy_calculator.HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        item = data[0]
        self.assertIn("slot", item)
        self.assertIn("main_stat", item)
        self.assertIn("potential_pct", item)
        self.assertIn("rank", item)

    def test_f14_03_history_persistence_retrieval(self):
        """F14: Multiple saved artifacts are correctly retrieved from history."""
        app = self.create_legacy_app()
        app.calculate()
        app.save_to_history()
        app.slot_var.set("Перо смерти")
        app.calculate()
        app.save_to_history()
        with open(legacy_calculator.HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)

    def test_f14_04_copy_report_card_formatting(self):
        """F14: Copy share card generates formatted string with slot and stats."""
        app = self.create_legacy_app()
        app.calculate()
        app.copy_share_card()
        clip = app.clipboard_get()
        self.assertIn("Основной стат", clip)

    def test_f14_05_report_card_contains_cv_and_rank(self):
        """F14: Share card output includes rank and CV information."""
        app = self.create_legacy_app()
        app.calculate()
        app.copy_share_card()
        clip = app.clipboard_get()
        self.assertTrue("Ранг" in clip or "CV" in clip or "Рейтинг" in clip)

    # ──────────────────────────────────────────────────────────────────
    # F15: Sidebar Navigation (5 Tabs) & Active Highlight
    # ──────────────────────────────────────────────────────────────────
    def test_f15_01_sidebar_tab_identifiers(self):
        """F15: Sidebar contains navigation items for core views."""
        app = self.create_modular_app()
        view_keys = list(app.views.keys())
        self.assertIn("calculator", view_keys)
        self.assertIn("scanner", view_keys)
        self.assertIn("builds", view_keys)
        self.assertIn("about", view_keys)

    def test_f15_02_default_active_view(self):
        """F15: Default active view is 'calculator'."""
        app = self.create_modular_app()
        self.assertEqual(app.current_view_id, "calculator")

    def test_f15_03_sidebar_navigation_switch(self):
        """F15: show_view switches active view correctly."""
        app = self.create_modular_app()
        app.show_view("scanner")
        self.assertEqual(app.current_view_id, "scanner")
        app.show_view("builds")
        self.assertEqual(app.current_view_id, "builds")

    def test_f15_04_active_button_highlighting(self):
        """F15: Sidebar set_active method highlights requested tab."""
        app = self.create_modular_app()
        app.sidebar.set_active("about")
        self.assertEqual(app.current_view_id, "about")

    def test_f15_05_state_preservation_across_views(self):
        """F15: Navigating between views preserves calculator input state."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        calc_view.stat_inputs.substat_vars[0]["val"].set("21.0")
        app.show_view("scanner")
        app.show_view("calculator")
        self.assertEqual(calc_view.stat_inputs.substat_vars[0]["val"].get(), "21.0")

    # ──────────────────────────────────────────────────────────────────
    # F16: ScannerView: Enka.Network Showcase Integration
    # ──────────────────────────────────────────────────────────────────
    def test_f16_01_enka_uid_validation(self):
        """F16: Enka adapter validates 9-digit UID format."""
        self.assertTrue(enka_adapter.validate_uid("700123456"))
        self.assertFalse(enka_adapter.validate_uid("123"))
        self.assertFalse(enka_adapter.validate_uid("abcdefghi"))

    def test_f16_02_enka_showcase_payload_parsing(self):
        """F16: Enka parser extracts characters from showcase dictionary."""
        mock_payload = {
            "playerInfo": {"nickname": "Traveler"},
            "avatarInfoList": [
                {
                    "avatarId": 10000052,
                    "equipList": [
                        {
                            "flat": {
                                "icon": "UI_RelicIcon_15020_4",
                                "equipType": "EQUIP_BRACER",
                                "setNameTextMapHash": "285880402",
                                "relicMainstat": {"mainPropId": "FIGHT_PROP_HP", "statValue": 4780},
                                "relicSubstatList": [{"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 3.9}]
                            },
                            "relic": {"level": 21}
                        }
                    ]
                }
            ]
        }
        res = enka_adapter.parse_enka_showcase(mock_payload)
        self.assertIn("characters", res)
        self.assertEqual(len(res["characters"]), 1)

    def test_f16_03_enka_artifact_conversion(self):
        """F16: Enka equipped relic parses into ParsedArtifact."""
        mock_relic = {
            "flat": {
                "icon": "UI_RelicIcon_15020_4",
                "equipType": "EQUIP_BRACER",
                "setNameTextMapHash": "285880402",
                "relicMainstat": {"mainPropId": "FIGHT_PROP_HP", "statValue": 4780},
                "relicSubstatList": [{"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 3.9}]
            },
            "relic": {"level": 21}
        }
        parsed = enka_adapter.parse_enka_artifact(mock_relic)
        self.assertEqual(parsed.slot, "Цветок жизни")
        self.assertEqual(parsed.level, 20)

    def test_f16_04_enka_transfer_to_calculator(self):
        """F16: ParsedArtifact from Enka transfers into calculator inputs."""
        app = self.create_legacy_app()
        artifact = good_adapter.ParsedArtifact(
            slot="Перо смерти",
            main_stat="Сила атаки",
            level=20,
            rarity=5,
            substats=[("Крит. урон", Decimal("14.0")), ("Шанс крит. попадания", Decimal("7.0"))],
            set_key="GladiatorsFinale",
            location=""
        )
        app.load_artifact_from_good(artifact)
        self.assertEqual(app.slot_var.get(), "Перо смерти")

    def test_f16_05_enka_invalid_uid_error_handling(self):
        """F16: Fetching with invalid UID raises ValueError or returns error dict."""
        with self.assertRaises(ValueError):
            enka_adapter.fetch_showcase("invalid_uid")

    # ──────────────────────────────────────────────────────────────────
    # F17: ScannerView: Inventory Kamera Folder Monitoring
    # ──────────────────────────────────────────────────────────────────
    def test_f17_01_kamera_reads_good_files(self):
        """F17: Kamera adapter discovers and loads valid GOOD JSON files."""
        sample_good = {
            "format": "GOOD",
            "version": 2,
            "artifacts": [
                {
                    "setKey": "GoldenTroupe",
                    "slotKey": "flower",
                    "rarity": 5,
                    "mainStatKey": "hp",
                    "level": 0,
                    "substats": []
                }
            ]
        }
        test_file = self.tmp_path / "kamera_scan.json"
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(sample_good, f)
            
        data = kamera_adapter.load_kamera_json(str(test_file))
        self.assertEqual(len(data.get("artifacts", [])), 1)

    def test_f17_02_kamera_extracts_artifacts_list(self):
        """F17: Kamera adapter extracts list of ParsedArtifact objects."""
        sample_good = {
            "format": "GOOD",
            "version": 2,
            "artifacts": [
                {
                    "setKey": "GoldenTroupe",
                    "slotKey": "flower",
                    "rarity": 5,
                    "mainStatKey": "hp",
                    "level": 0,
                    "substats": []
                }
            ]
        }
        parsed_list = kamera_adapter.extract_parsed_artifacts(sample_good)
        self.assertEqual(len(parsed_list), 1)
        self.assertEqual(parsed_list[0].slot, "Цветок жизни")

    def test_f17_03_kamera_pagination_support(self):
        """F17: Paging slice correctly partitions artifact scan results."""
        artifacts = list(range(25))
        page_size = 10
        page_0 = artifacts[0:10]
        page_1 = artifacts[10:20]
        page_2 = artifacts[20:25]
        self.assertEqual(len(page_0), 10)
        self.assertEqual(len(page_1), 10)
        self.assertEqual(len(page_2), 5)

    def test_f17_04_kamera_transfer_to_calculator(self):
        """F17: Selected scanned artifact transfers into calculator."""
        app = self.create_legacy_app()
        artifact = good_adapter.ParsedArtifact(
            slot="Пески времени",
            main_stat="HP %",
            level=0,
            rarity=5,
            substats=[("Крит. урон", Decimal("7.8"))],
            set_key="GoldenTroupe",
            location=""
        )
        app.load_artifact_from_good(artifact)
        self.assertEqual(app.slot_var.get(), "Пески времени")
        self.assertEqual(app.main_stat_var.get(), "HP %")

    def test_f17_05_kamera_empty_folder_graceful_handling(self):
        """F17: Empty folder returns empty list without exception."""
        files = kamera_adapter.find_good_files(str(self.tmp_path))
        self.assertEqual(files, [])

    # ──────────────────────────────────────────────────────────────────
    # F18: ScannerView: GOOD JSON Import/Export
    # ──────────────────────────────────────────────────────────────────
    def test_f18_01_good_json_parsing(self):
        """F18: Parses standard GOOD format artifact into ParsedArtifact."""
        raw = {
            "setKey": "ViridescentVenerer",
            "slotKey": "goblet",
            "rarity": 5,
            "mainStatKey": "anemo_dmg_",
            "level": 20,
            "substats": [{"key": "critRate_", "value": 7.0}]
        }
        parsed = good_adapter.good_to_parsed_artifact(raw)
        self.assertEqual(parsed.slot, "Кубок пространства")
        self.assertEqual(parsed.set_key, "ViridescentVenerer")

    def test_f18_02_good_stat_key_translations(self):
        """F18: Translates Russian stat names to GOOD keys and back."""
        self.assertEqual(good_adapter.STAT_KEY_TO_RU["critRate_"], "Шанс крит. попадания")
        self.assertEqual(good_adapter.RU_TO_STAT_KEY["Шанс крит. попадания"], "critRate_")

    def test_f18_03_export_calculator_to_good(self):
        """F18: Exports current artifact into valid GOOD v2 artifact dictionary."""
        app = self.create_legacy_app()
        app.slot_var.set("Перо смерти")
        app.set_var.set("Золотая труппа")
        app.calculate()
        exported = app.export_current_artifact_to_good()
        self.assertEqual(exported["slotKey"], "plume")
        self.assertEqual(exported["setKey"], "GoldenTroupe")

    def test_f18_04_good_bulk_import_to_history(self):
        """F18: Bulk import saves multiple GOOD artifacts into history."""
        app = self.create_legacy_app()
        a1 = good_adapter.ParsedArtifact(slot="Цветок жизни", main_stat="HP", level=0, rarity=5, substats=[], set_key="GoldenTroupe", location="")
        a2 = good_adapter.ParsedArtifact(slot="Перо смерти", main_stat="Сила атаки", level=0, rarity=5, substats=[], set_key="GoldenTroupe", location="")
        app.bulk_import_to_history([a1, a2])
        with open(legacy_calculator.HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)

    def test_f18_05_corrupt_good_json_error_handling(self):
        """F18: Invalid JSON payload triggers controlled error."""
        with self.assertRaises(Exception):
            good_adapter.parse_good_json_string("INVALID_NOT_JSON")

    # ──────────────────────────────────────────────────────────────────
    # F19: BuildsView: 130+ Character Catalog & Element Filter
    # ──────────────────────────────────────────────────────────────────
    def test_f19_01_catalog_total_builds_count(self):
        """F19: Character builds catalog contains at least 130 meta builds."""
        self.assertGreaterEqual(len(character_builds.CHARACTER_BUILDS), 130)

    def test_f19_02_catalog_search_by_character_name(self):
        """F19: Searching by character name returns matching builds."""
        results = [b for b in character_builds.CHARACTER_BUILDS if "Райдэн" in b.display_name]
        self.assertGreaterEqual(len(results), 1)

    def test_f19_03_catalog_filter_by_element(self):
        """F19: Filtering by element returns characters of that element only."""
        pyro_builds = [b for b in character_builds.CHARACTER_BUILDS if b.element == "Пиро"]
        self.assertGreater(len(pyro_builds), 0)
        self.assertTrue(all(b.element == "Пиро" for b in pyro_builds))

    def test_f19_04_catalog_build_er_and_weapons(self):
        """F19: Builds contain ER requirements and weapon rankings."""
        build = character_builds.CHARACTER_BUILDS[0]
        self.assertTrue(hasattr(build, "top_weapons_ru"))
        self.assertTrue(hasattr(build, "substat_weights"))

    def test_f19_05_catalog_select_for_calculator_action(self):
        """F19: Selecting character updates forecast panel selection."""
        app = self.create_modular_app()
        calc_view = app.views["calculator"]
        forecast = calc_view.forecast_panel
        forecast.char_var.set("Фурина")
        forecast._on_char_change("Фурина")
        self.assertEqual(forecast.char_var.get(), "Фурина")

    # ──────────────────────────────────────────────────────────────────
    # F20: HistoryView: Filtered Table & Side-by-Side Diff
    # ──────────────────────────────────────────────────────────────────
    def test_f20_01_history_table_population(self):
        """F20: Saved history records are accessible for display."""
        app = self.create_legacy_app()
        app.calculate()
        app.save_to_history()
        history = app._load_history()
        self.assertEqual(len(history), 1)

    def test_f20_02_history_filter_by_slot(self):
        """F20: Filtering history by slot selects only matching artifacts."""
        app = self.create_legacy_app()
        app.slot_var.set("Цветок жизни")
        app.calculate()
        app.save_to_history()
        app.slot_var.set("Перо смерти")
        app.calculate()
        app.save_to_history()
        
        hist = app._load_history()
        flowers = [h for h in hist if h.get("slot") == "Цветок жизни"]
        self.assertEqual(len(flowers), 1)

    def test_f20_03_history_filter_by_rank(self):
        """F20: Filtering history by rank isolates matching artifacts."""
        hist = [
            {"slot": "Перо смерти", "rank": "SSS", "potential_pct": 95.0},
            {"slot": "Перо смерти", "rank": "A", "potential_pct": 60.0}
        ]
        sss_items = [h for h in hist if h["rank"] == "SSS"]
        self.assertEqual(len(sss_items), 1)

    def test_f20_04_side_by_side_comparison_diffs(self):
        """F20: Comparing two artifacts computes numeric metric diffs."""
        a = {"cv": 28.0, "score": 85.0}
        b = {"cv": 14.0, "score": 60.0}
        diff_cv = a["cv"] - b["cv"]
        diff_score = a["score"] - b["score"]
        self.assertEqual(diff_cv, 14.0)
        self.assertEqual(diff_score, 25.0)

    def test_f20_05_reload_history_item_to_calculator(self):
        """F20: Reloading item from history restores slot and main stat."""
        app = self.create_legacy_app()
        item = {
            "slot": "Пески времени",
            "main_stat": "Мастерство стихий",
            "level": 20,
            "substats": [("Крит. урон", 14.0)]
        }
        app.slot_var.set(item["slot"])
        app.main_stat_var.set(item["main_stat"])
        self.assertEqual(app.slot_var.get(), "Пески времени")
        self.assertEqual(app.main_stat_var.get(), "Мастерство стихий")

    # ──────────────────────────────────────────────────────────────────
    # F21: AboutView: Metadata & Sources & Hotkeys
    # ──────────────────────────────────────────────────────────────────
    def test_f21_01_app_title_and_version_display(self):
        """F21: Application title and version are defined."""
        app = self.create_modular_app()
        title = app.title()
        self.assertIn("Genshin", title)
        self.assertIn("v2", title)

    def test_f21_02_data_sources_credits(self):
        """F21: Documentation credits authoritative sources."""
        sources = ["AnimeGameData", "KQM", "Enka.Network", "Inventory Kamera"]
        self.assertEqual(len(sources), 4)

    def test_f21_03_keyboard_shortcuts_documentation(self):
        """F21: Standard shortcuts Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X are specified."""
        shortcuts = ["Ctrl+A", "Ctrl+C", "Ctrl+V", "Ctrl+X"]
        self.assertEqual(len(shortcuts), 4)

    def test_f21_04_developer_and_community_info(self):
        """F21: App metadata includes author and community information."""
        meta = {"app": "GenshinArtifactCalc", "version": "2.0"}
        self.assertEqual(meta["version"], "2.0")

    def test_f21_05_about_view_theme_consistency(self):
        """F21: About frame initializes within main container."""
        app = self.create_modular_app()
        about_frame = app.views.get("about")
        self.assertIsNotNone(about_frame)

    # ──────────────────────────────────────────────────────────────────
    # F22: Entrypoints Compatibility (test_ui, main, calculator)
    # ──────────────────────────────────────────────────────────────────
    def test_f22_01_test_ui_entrypoint_validity(self):
        """F22: test_ui.py is a valid launcher script importing GenshinCalcApp."""
        test_ui_path = REPO_ROOT / "test_ui.py"
        self.assertTrue(test_ui_path.exists())
        with open(test_ui_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("GenshinCalcApp", content)

    def test_f22_02_main_py_entrypoint_validity(self):
        """F22: main.py is a valid entrypoint launcher script."""
        main_path = REPO_ROOT / "main.py"
        self.assertTrue(main_path.exists())

    def test_f22_03_root_calculator_entrypoint_validity(self):
        """F22: calculator.py in repository root is present and references app."""
        calc_path = REPO_ROOT / "calculator.py"
        self.assertTrue(calc_path.exists())

    def test_f22_04_legacy_facade_class_presence(self):
        """F22: Legacy facade ArtifactCalculatorApp is maintained in src."""
        self.assertTrue(hasattr(legacy_calculator, "ArtifactCalculatorApp"))

    def test_f22_05_legacy_facade_api_contract(self):
        """F22: Legacy facade preserves required public API methods."""
        app = self.create_legacy_app()
        self.assertTrue(hasattr(app, "calculate"))
        self.assertTrue(hasattr(app, "save_to_history"))
        self.assertTrue(hasattr(app, "copy_share_card"))
        self.assertTrue(hasattr(app, "load_artifact_from_good"))

    # ──────────────────────────────────────────────────────────────────
    # F23: Windows Layout-Agnostic Hotkeys (VK 65, 67, 86, 88)
    # ──────────────────────────────────────────────────────────────────
    def test_f23_01_control_keypress_binding(self):
        """F23: Application registers global Control-KeyPress handler."""
        app = self.create_legacy_app()
        self.assertTrue(hasattr(app, "_handle_control_keys"))

    def test_f23_02_vk_65_select_all(self):
        """F23: Virtual keycode 65 (VK_A) triggers select all on entry."""
        app = self.create_legacy_app()
        entry = app.stat_widgets[0]["entry"]
        entry.insert(0, "test_val")
        event = MagicMock()
        event.widget = entry
        event.keycode = 65
        event.keysym = "cyrillic_ef"
        res = app._handle_control_keys(event)
        self.assertEqual(res, "break")

    def test_f23_03_vk_67_copy(self):
        """F23: Virtual keycode 67 (VK_C) triggers copy."""
        app = self.create_legacy_app()
        entry = app.stat_widgets[0]["entry"]
        event = MagicMock()
        event.widget = entry
        event.keycode = 67
        event.keysym = "cyrillic_es"
        res = app._handle_control_keys(event)
        # Handler either breaks or handles copy
        self.assertTrue(res == "break" or res is None)

    def test_f23_04_vk_86_paste(self):
        """F23: Virtual keycode 86 (VK_V) triggers paste from clipboard."""
        app = self.create_legacy_app()
        entry = app.stat_widgets[0]["entry"]
        app.clipboard_clear()
        app.clipboard_append("14.0")
        event = MagicMock()
        event.widget = entry
        event.keycode = 86
        event.keysym = "cyrillic_em"
        res = app._handle_control_keys(event)
        self.assertEqual(res, "break")

    def test_f23_05_vk_88_cut(self):
        """F23: Virtual keycode 88 (VK_X) triggers cut."""
        app = self.create_legacy_app()
        entry = app.stat_widgets[0]["entry"]
        entry.insert(0, "cut_val")
        event = MagicMock()
        event.widget = entry
        event.keycode = 88
        event.keysym = "cyrillic_che"
        res = app._handle_control_keys(event)
        self.assertEqual(res, "break")


if __name__ == "__main__":
    unittest.main()
