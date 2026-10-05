"""Entry point for Genshin Artifact Calculator.

This file serves as a convenience launcher from the repository root,
running the modular application from src/genshin_calc/ui/app.py.
"""
import sys
from pathlib import Path
import customtkinter as ctk

# Add src to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import genshin_calc.calculator as _backend
from genshin_calc.ui.app import GenshinCalcApp

# Re-export all symbols from genshin_calc.calculator
for _k, _v in _backend.__dict__.items():
    if not _k.startswith("__"):
        globals()[_k] = _v

class _CalculatorModule(sys.modules[__name__].__class__):
    def __getattr__(self, item):
        return getattr(_backend, item)

    def __setattr__(self, item, value):
        super().__setattr__(item, value)
        if hasattr(_backend, item) or item in ("HISTORY_FILE",):
            setattr(_backend, item, value)

sys.modules[__name__].__class__ = _CalculatorModule

from genshin_calc.ui.theme import apply_app_theme

if __name__ == "__main__":
    apply_app_theme()

    app = GenshinCalcApp()
    app.mainloop()

