import sys
from pathlib import Path
import customtkinter as ctk

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from genshin_calc.ui.app import GenshinCalcApp

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = GenshinCalcApp()
    app.mainloop()
