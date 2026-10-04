import os
import sys

def get_project_root() -> str:
    """
    Get the absolute path to the project root directory.
    Works for both local development and PyInstaller bundled executables.
    """
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (PyInstaller)
        # sys.executable is the path to the .exe file
        return os.path.dirname(sys.executable)
    else:
        # If run from Python interpreter
        # Go up from src/genshin_calc/utils.py -> src/genshin_calc -> src -> root
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
