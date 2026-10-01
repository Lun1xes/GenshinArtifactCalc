Genshin Artifact Calculator — v2

Files
-----
calculator.py          GUI
artifact_logic.py      pure validation/calculation logic
 test_artifact_logic.py      logic/regression tests
 test_calculator_state.py    GUI-state tests using a lightweight customtkinter stub

Install/runtime
---------------
Python 3.10+ recommended.
Install dependency on Windows:
    py -m pip install customtkinter

Run:
    py calculator.py

Run tests:
    py -m unittest discover -p "test_*.py"

Important
---------
The implementation adds:
- Artifact Slot selection.
- Main Stat selection with slot-specific valid options.
- Main Stat cannot also be a Substat.
- Main Stat is excluded from potential revealed-substat pool.
- Discrete roll reachability instead of round(value / avg).
- Exact total-roll validation for 3/4-stat artifacts.
- Decimal-based parsing and stale-result protection.
- PAV explicitly treated as a project heuristic, not an in-game formula.

Source note
-----------
The Genshin data in this package follows the reference values and sources supplied
in the working conversation (KQM/Fandom/community technical references). Live web
verification was not available in the build environment used to create these files,
so treat the source list as the supplied reference set rather than a fresh 2026
verification.
