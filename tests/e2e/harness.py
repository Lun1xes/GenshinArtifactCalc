"""E2E Test Harness: Headless Execution & Fixtures for Genshin Artifact Calculator.

Provides headless execution safety, dialogue interceptors, mock fixtures,
and interface bridges across presentation, logic, and adapters.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import MagicMock
from decimal import Decimal

# Ensure src and repo root are in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src"
GENSHIN_CALC_DIR = SRC_DIR / "genshin_calc"

for path_entry in [str(REPO_ROOT), str(SRC_DIR), str(GENSHIN_CALC_DIR)]:
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)

# Import domain and adapter modules safely
import genshin_calc.artifact_logic as artifact_logic
import genshin_calc.character_builds as character_builds
import genshin_calc.upgrade_probability as upgrade_probability
import genshin_calc.icon_manager as icon_manager
import genshin_calc.good_adapter as good_adapter
import genshin_calc.enka_adapter as enka_adapter
import genshin_calc.kamera_adapter as kamera_adapter
import genshin_calc.calculator as legacy_calculator

# Headless / Mock Tkinter safety
import tkinter as tk
from tkinter import messagebox, filedialog

# Intercept modal popups so CLI never blocks
_DIALOG_LOG: list[tuple[str, str, str]] = []

def _mock_dialog(dialog_type: str, title: str = "", message: str = "", **kwargs):
    _DIALOG_LOG.append((dialog_type, str(title), str(message)))
    if "ask" in dialog_type:
        return True
    return "ok"

messagebox.showinfo = lambda title="", message="", **kw: _mock_dialog("showinfo", title, message, **kw)
messagebox.showwarning = lambda title="", message="", **kw: _mock_dialog("showwarning", title, message, **kw)
messagebox.showerror = lambda title="", message="", **kw: _mock_dialog("showerror", title, message, **kw)
messagebox.askyesno = lambda title="", message="", **kw: _mock_dialog("askyesno", title, message, **kw)
messagebox.askokcancel = lambda title="", message="", **kw: _mock_dialog("askokcancel", title, message, **kw)
filedialog.askopenfilename = lambda **kw: ""
filedialog.askdirectory = lambda **kw: ""
filedialog.asksaveasfilename = lambda **kw: ""


class HeadlessTestBase(unittest.TestCase):
    """Base class for all E2E test cases, guaranteeing clean headless teardown."""
    
    def setUp(self):
        super().setUp()
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp_dir.name)
        
        # Isolate history file to temporary folder
        self._orig_history_file = getattr(legacy_calculator, "HISTORY_FILE", None)
        legacy_calculator.HISTORY_FILE = str(self.tmp_path / "test_history.json")
        
        # Clear dialog logs
        _DIALOG_LOG.clear()
        
        # Track apps for cleanup
        self._created_apps = []

    def tearDown(self):
        for app in self._created_apps:
            try:
                app.destroy()
            except Exception:
                pass
        self._created_apps.clear()
        
        if self._orig_history_file:
            legacy_calculator.HISTORY_FILE = self._orig_history_file
            
        try:
            self._tmp_dir.cleanup()
        except Exception:
            pass
        super().tearDown()

    def create_legacy_app(self):
        """Creates an instance of legacy ArtifactCalculatorApp safely withdrawn."""
        app = legacy_calculator.ArtifactCalculatorApp()
        try:
            app.withdraw()
        except Exception:
            pass
        self._created_apps.append(app)
        return app

    def create_modular_app(self):
        """Creates an instance of GenshinCalcApp safely withdrawn."""
        from genshin_calc.ui.app import GenshinCalcApp
        app = GenshinCalcApp()
        try:
            app.withdraw()
        except Exception:
            pass
        self._created_apps.append(app)
        return app

    def get_dialog_log(self):
        return list(_DIALOG_LOG)


# Helper functions providing uniform contract access

def get_theme_palette() -> dict[str, str]:
    """Retrieves theme palette either from theme module or legacy calculator.C."""
    try:
        from genshin_calc.ui.theme import ThemeColors
        return {
            "BG_DEEP": ThemeColors.BG_DEEP,
            "BG_PANEL": ThemeColors.BG_PANEL,
            "BG_CARD": ThemeColors.BG_CARD,
            "BG_INPUT": getattr(ThemeColors, "BG_INPUT", "#0e1a30"),
            "GOLD": ThemeColors.GOLD,
            "CYAN": ThemeColors.CYAN,
            "TEXT_PRIMARY": getattr(ThemeColors, "TEXT_PRIMARY", "#e0e0e0"),
            "TEXT_MUTED": getattr(ThemeColors, "TEXT_MUTED", "#90a4ae"),
            "BORDER": getattr(ThemeColors, "BORDER", "#243555"),
            "SUCCESS": getattr(ThemeColors, "SUCCESS", "#69f0ae"),
            "WARNING": getattr(ThemeColors, "WARNING", "#ffd54f"),
            "DANGER": getattr(ThemeColors, "DANGER", "#ff5252"),
        }
    except Exception:
        C = legacy_calculator.C
        return {
            "BG_DEEP": C.BG_DEEP,
            "BG_PANEL": C.BG_PANEL,
            "BG_CARD": C.BG_CARD,
            "BG_INPUT": getattr(C, "BG_INPUT", "#0e1a30"),
            "GOLD": C.GOLD,
            "CYAN": C.CYAN,
            "TEXT_PRIMARY": getattr(C, "TEXT_PRIMARY", "#e0e0e0"),
            "TEXT_MUTED": getattr(C, "TEXT_MUTED", "#90a4ae"),
            "BORDER": getattr(C, "BORDER", "#243555"),
            "SUCCESS": getattr(C, "GREEN", "#69f0ae"),
            "WARNING": getattr(C, "YELLOW_WARN", "#ffd54f"),
            "DANGER": getattr(C, "RED", "#ff5252"),
        }


def get_element_colors() -> dict[str, str]:
    """Retrieves standard elemental colors mapping."""
    try:
        from genshin_calc.ui.theme import ELEMENT_COLORS
        return dict(ELEMENT_COLORS)
    except Exception:
        # Canonical elemental colors from Genshin Impact design specification
        return {
            "Пиро": "#ff5252",
            "Гидро": "#00e5ff",
            "Анемо": "#69f0ae",
            "Электро": "#e040fb",
            "Дендро": "#76ff03",
            "Крио": "#81d4fa",
            "Гео": "#ffd700",
        }


def get_rank_colors() -> dict[str, str]:
    """Retrieves rank badge colors mapping."""
    try:
        from genshin_calc.ui.theme import RANK_COLORS
        return dict(RANK_COLORS)
    except Exception:
        return {
            "SSS": "#ffd700",
            "SS": "#e040fb",
            "S": "#00e5ff",
            "A": "#69f0ae",
            "B": "#64b5f6",
            "C": "#90a4ae",
        }


def get_ui_metrics() -> dict[str, int]:
    """Retrieves widget styling metrics (corner radii, border widths)."""
    try:
        from genshin_calc.ui.theme import METRICS
        return dict(METRICS)
    except Exception:
        return {
            "corner_radius_card": 10,
            "corner_radius_btn": 6,
            "border_width": 1,
        }


def get_ui_fonts() -> dict[str, tuple]:
    """Retrieves typography scale."""
    try:
        from genshin_calc.ui.theme import FONTS
        return dict(FONTS)
    except Exception:
        return {
            "title": ("Segoe UI", 18, "bold"),
            "header": ("Segoe UI", 14, "bold"),
            "body": ("Segoe UI", 12),
            "small": ("Segoe UI", 10),
            "mono": ("Consolas", 11),
        }
