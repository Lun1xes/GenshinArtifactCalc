import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src" / "genshin_calc"))

from genshin_calc.calculator import ArtifactCalculatorApp

if __name__ == "__main__":
    app = ArtifactCalculatorApp()
    app.mainloop()
