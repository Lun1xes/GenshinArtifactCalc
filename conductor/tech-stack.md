# Technology Stack: Genshin Impact 5★ Artifact Calculator (v2)

## Core Technologies
- **Language:** Python 3.10+
  - Rationale: High-level language with built-in precision math (`decimal.Decimal`), efficient combinatorics (`itertools`), and caching (`functools.lru_cache`).
- **GUI Framework:** CustomTkinter (`customtkinter`)
  - Rationale: Modern dark-mode themed desktop UI wrapper around Tkinter, lightweight and cross-platform without heavy external runtimes.
- **Testing:** Standard Library `unittest`
  - Rationale: Zero-dependency test runner executing unit tests (`test_artifact_logic.py`) and GUI state tests (`test_calculator_state.py`).
- **Persistence:** JSON (`artifact_history.json`)
  - Rationale: Simple, human-readable, schema-free local storage for user artifact evaluation history.

## Architecture and Key Design Patterns
- **Separation of Concerns:**
  - `artifact_logic.py`: Pure domain logic, mathematical combinatorics, validation, and rating heuristics. Zero GUI dependencies.
  - `calculator.py`: Presentation layer managing event handlers, user input widgets, dynamic dropdown updating, and state synchronization.
- **Precision Arithmetic:**
  - Mandatory use of `decimal.Decimal` with configured step quantization to avoid IEEE-754 floating-point drift.
- **Discrete Solver & Caching:**
  - Precomputed and LRU-cached roll combination lookups to ensure sub-millisecond calculation response during real-time typing.
- **Test-Driven State Verification:**
  - Decoupled testing using CustomTkinter stubs to verify widget state transitions and validation guards without opening physical OS windows.
