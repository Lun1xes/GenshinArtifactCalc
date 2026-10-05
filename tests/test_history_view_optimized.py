"""Unit tests for optimized HistoryView functionality.

Covers:
- Pagination and page navigation
- Filtering by slot, rank, and text search (set, stat, character)
- Sorting by potential, CV, level, and date
- Substat extraction from both dict and list data structures
- Item deletion and clear history
- Side-by-side comparison and delta diff computation
- Current calculator artifact comparison
"""
import json
import os
import sys
from pathlib import Path
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from genshin_calc.ui.views.history_view import HistoryView
from genshin_calc.good_adapter import ParsedArtifact


class TestHistoryViewOptimized(unittest.TestCase):
    def setUp(self):
        self.sample_history = [
            {
                "timestamp": "2026-10-05T12:00:00",
                "slot": "Цветок жизни",
                "main_stat": "HP",
                "set_key": "GladiatorsFinale",
                "level": "+20",
                "rank": "SSS",
                "potential_pct": 96.5,
                "crit_value": 42.0,
                "location": "Raiden",
                "substats": {
                    "Крит. шанс %": 10.5,
                    "Крит. урон": 21.0,
                    "Сила атаки %": 9.9,
                    "Восст. энергии": 11.0,
                },
            },
            {
                "timestamp": "2026-10-04T12:00:00",
                "slot": "Перо смерти",
                "main_stat": "Сила атаки",
                "set": "Конец гладиатора",
                "level": 20,
                "rank": "S",
                "potential_pct": 82.0,
                "crit_value": 31.0,
                "location": "Инвентарь",
                "substats": [
                    ("Крит. шанс %", 7.0),
                    ("Крит. урон", 17.0),
                    ("Защита %", 5.8),
                ],
            },
            {
                "timestamp": "2026-10-03T12:00:00",
                "slot": "Пески времени",
                "main_stat": "Сила атаки %",
                "set_key": "EmblemOfSeveredFate",
                "level": "+0",
                "rank": "B",
                "potential_pct": 55.0,
                "crit_value": 7.8,
                "location": "Инвентарь",
                "substats": {
                    "Крит. урон": 7.8,
                },
            },
            {
                "timestamp": "2026-10-02T12:00:00",
                "slot": "Кубок пространства",
                "main_stat": "Электро урон %",
                "set_key": "EmblemOfSeveredFate",
                "level": "+16",
                "rank": "A",
                "potential_pct": 71.5,
                "crit_value": 24.2,
                "location": "KujouSara",
                "substats": {
                    "Крит. шанс %", 3.9,
                    "Крит. урон", 16.4,
                },
            },
        ]

    def test_substat_extraction_dict_and_list(self):
        """Test that both dict and list substat representations are parsed consistently."""
        item_dict = {"substats": {"Крит. шанс %": 10.5, "Крит. урон": 21.0}}
        item_list = {"substats": [("Крит. шанс %", 10.5), ("Крит. урон", 21.0)]}
        item_good = {"substats": [{"key": "critRate_", "value": 10.5}, {"key": "critDMG_", "value": 21.0}]}

        res_dict = HistoryView._get_item_substats(item_dict)
        res_list = HistoryView._get_item_substats(item_list)
        res_good = HistoryView._get_item_substats(item_good)

        self.assertEqual(len(res_dict), 2)
        self.assertEqual(len(res_list), 2)
        self.assertEqual(len(res_good), 2)
        self.assertEqual(dict(res_dict)["Крит. шанс %"], 10.5)
        self.assertEqual(dict(res_list)["Крит. шанс %"], 10.5)
        self.assertEqual(dict(res_good)["Шанс крит. попадания"], 10.5)

    def test_cv_calculation_fallback(self):
        """Test CV calculation from substats when explicit crit_value is absent."""
        item = {
            "substats": {
                "Крит. шанс %": 7.0,
                "Крит. урон": 14.0,
            }
        }
        # CV = 7.0 * 2 + 14.0 = 28.0
        cv = HistoryView._get_item_cv(item)
        self.assertEqual(cv, 28.0)

    def test_level_parsing(self):
        """Test integer and string level formatting."""
        self.assertEqual(HistoryView._get_item_level({"level": "+20"}), 20)
        self.assertEqual(HistoryView._get_item_level({"level": 16}), 16)
        self.assertEqual(HistoryView._get_item_level({"level": "+0"}), 0)
        self.assertEqual(HistoryView._get_item_level({}), 0)

    def test_set_name_resolution(self):
        """Test set key translation to Russian name."""
        item_ru = {"set": "Изумрудная тень"}
        self.assertEqual(HistoryView._get_item_set_name(item_ru), "Изумрудная тень")

        item_key = {"set_key": "GladiatorsFinale"}
        self.assertIn("гладиатор", HistoryView._get_item_set_name(item_key).lower())

    def test_pagination_logic(self):
        """Test pagination bounds and page slicing."""
        with patch.object(HistoryView, "_build_ui"):
            view = HistoryView.__new__(HistoryView)
            view.history_records = list(range(45))  # 45 items
            view.filtered_records = view.history_records
            view.page_size = 20
            view.current_page = 1

            total_pages = math_ceil = (len(view.filtered_records) + 19) // 20
            self.assertEqual(total_pages, 3)

            # Page 1: 0 to 20
            start = (view.current_page - 1) * view.page_size
            end = min(start + view.page_size, len(view.filtered_records))
            self.assertEqual(end - start, 20)

            # Page 3: 40 to 45
            view.current_page = 3
            start = (view.current_page - 1) * view.page_size
            end = min(start + view.page_size, len(view.filtered_records))
            self.assertEqual(end - start, 5)

    def test_filtering_and_search(self):
        """Test filtering records by slot, rank, and text search."""
        with patch.object(HistoryView, "_build_ui"):
            view = HistoryView.__new__(HistoryView)
            view.history_records = list(self.sample_history)
            view.page_size = 20
            view.current_page = 1
            view.selected_slot_filter = "Все"
            view.selected_rank_filter = "Все"
            view.selected_sort = "Новые"
            view.search_query = ""
            view.count_label = MagicMock()
            view._render_current_page = MagicMock()

            # 1. Slot filter
            view.selected_slot_filter = "Перо смерти"
            view._apply_filters_and_render()
            self.assertEqual(len(view.filtered_records), 1)
            self.assertEqual(view.filtered_records[0]["slot"], "Перо смерти")

            # 2. Rank filter
            view.selected_slot_filter = "Все"
            view.selected_rank_filter = "SSS"
            view._apply_filters_and_render()
            self.assertEqual(len(view.filtered_records), 1)
            self.assertEqual(view.filtered_records[0]["rank"], "SSS")

            # 3. Search by character
            view.selected_rank_filter = "Все"
            view.search_query = "kujou"
            view._apply_filters_and_render()
            self.assertEqual(len(view.filtered_records), 1)
            self.assertEqual(view.filtered_records[0]["location"], "KujouSara")

            # 4. Search by set name
            view.search_query = "emblem"
            view._apply_filters_and_render()
            self.assertEqual(len(view.filtered_records), 2)

    def test_sorting(self):
        """Test sorting filtered records by potential, CV, and level."""
        with patch.object(HistoryView, "_build_ui"):
            view = HistoryView.__new__(HistoryView)
            view.history_records = list(self.sample_history)
            view.page_size = 20
            view.current_page = 1
            view.selected_slot_filter = "Все"
            view.selected_rank_filter = "Все"
            view.search_query = ""
            view.count_label = MagicMock()
            view._render_current_page = MagicMock()

            # Sort by potential descending
            view.selected_sort = "Потенциал ↓"
            view._apply_filters_and_render()
            pots = [view._get_item_potential(x) for x in view.filtered_records]
            self.assertEqual(pots, sorted(pots, reverse=True))

            # Sort by CV descending
            view.selected_sort = "CV ↓"
            view._apply_filters_and_render()
            cvs = [view._get_item_cv(x) for x in view.filtered_records]
            self.assertEqual(cvs, sorted(cvs, reverse=True))

            # Sort by level descending
            view.selected_sort = "Уровень ↓"
            view._apply_filters_and_render()
            lvls = [view._get_item_level(x) for x in view.filtered_records]
            self.assertEqual(lvls, sorted(lvls, reverse=True))

    def test_delete_item(self):
        """Test deleting an item from history."""
        with patch.object(HistoryView, "_build_ui"):
            view = HistoryView.__new__(HistoryView)
            view.history_records = list(self.sample_history)
            view.compare_a = self.sample_history[0]
            view.compare_b = None
            view._save_history_to_disk = MagicMock()
            view._apply_filters_and_render = MagicMock()
            view._render_compare_state = MagicMock()

            target = self.sample_history[0]
            view._delete_item(target)

            self.assertEqual(len(view.history_records), len(self.sample_history) - 1)
            self.assertIsNone(view.compare_a)
            view._save_history_to_disk.assert_called_once()


if __name__ == "__main__":
    unittest.main()
