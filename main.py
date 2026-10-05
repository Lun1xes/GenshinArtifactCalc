import sys
from pathlib import Path
import customtkinter as ctk

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from genshin_calc.ui.theme import apply_app_theme
from genshin_calc.ui.app import GenshinCalcApp

# Backward compatibility alias
from genshin_calc.calculator import ArtifactCalculatorApp

if __name__ == "__main__":
    apply_app_theme()

    app = GenshinCalcApp()
    app.mainloop()

