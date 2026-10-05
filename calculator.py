"""Entry point for Genshin Artifact Calculator.

This file serves as a convenience launcher from the repository root,
running the main application from src/genshin_calc/calculator.py.
"""
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from genshin_calc.calculator import ArtifactCalculatorApp

if __name__ == "__main__":
    app = ArtifactCalculatorApp()
    app.mainloop()
