# Project: Genshin Impact Modular Artifact Calculator UI Modernization

## Architecture
The application is structured into a modular presentation tier (`src/genshin_calc/ui/`) layered on top of core calculation, data, and adapter services:
- **Presentation Layer (`src/genshin_calc/ui/`)**:
  - `theme.py`: Centralized design system (Genshin palette, elemental colors, typography, card and button metrics).
  - `app.py` (`GenshinCalcApp`): Master Tkinter window, grid container, view registry, navigation coordinator, and cross-view artifact transfer broker.
  - `hotkeys.py`: Global Windows layout-agnostic hotkey handler (VK_A=65, VK_C=67, VK_V=86, VK_X=88).
  - `components/`: Reusable UI modules (`sidebar.py`, `stat_inputs.py`, `forecast_panel.py`).
  - `views/`: Standalone views (`calculator_view.py`, `scanner_view.py`, `builds_view.py`, `history_view.py`, `about_view.py`).
- **Domain & Adapter Layer (`src/genshin_calc/`)**:
  - `artifact_logic.py`: Substat definitions (`Decimal`), discrete roll combinations, roll limits.
  - `upgrade_probability.py`: Monte Carlo simulation for +20 upgrade forecasting, expected PAV% & CV, tier odds.
  - `character_builds.py`: 134 meta-builds, 83 characters, weapon translations, compatibility scoring (`evaluate_artifact_for_build`), top character matcher.
  - `icon_manager.py`: Singleton avatar and icon service with caching, circular masking, and 2px elemental borders.
  - `enka_adapter.py`, `kamera_adapter.py`, `good_adapter.py`: Data ingestion and standard GOOD v2 import/export.
- **Entrypoints**:
  - `test_ui.py`, `main.py`, `calculator.py`: Unified entrypoints launching `GenshinCalcApp`.
  - `src/genshin_calc/calculator.py`: Backwards-compatibility facade (`ArtifactCalculatorApp`) maintaining API contracts for existing test suites.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Genshin Theme & Palette | #0f0f1e, #16213e, #1e2a45, #ffd700, #00e5ff, elemental colors | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Unified Widget Styling | Standard cards, buttons, corner radii, typography in theme.py | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Icon Manager Slot Support | Add `get_artifact_slot_icon()` to icon_manager.py | M1 | Survey Explorer 2 |
| 4 | Slot Selector with Emojis | Buttons (🌺, ✒️, ⏳, 🍷, 👑) with active slot highlight | M2 | ORIGINAL_REQUEST §R2 |
| 5 | Set Selector with Search/Autocomplete | Searchable/sorted artifact set dropdown | M2 | ORIGINAL_REQUEST §R2 |
| 6 | Main Stat & Level Selectors | Slot-filtered main stats and 0-20 level picker | M2 | ORIGINAL_REQUEST §R2 |
| 7 | Discrete Rolls & Progress Bars | 4 substat rows with roll count badges, discrete addends, and progress indicators | M2 | ORIGINAL_REQUEST §R2 |
| 8 | Clear & Quick Paste Actions | "Очистить" and "Быстрая вставка" buttons in StatInputs | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Dynamic Avatar with Elemental Border | Dynamic round avatar and 2px elemental border via icon_manager | M2 | ORIGINAL_REQUEST §R2 |
| 10 | Build Recommendation Card | Recommended sets, main stats for sands/goblet/circlet, top weapons (RU) | M2 | ORIGINAL_REQUEST §R2 |
| 11 | Rank, PAV & CV Display | SSS..C rank badge, PAV % scale (current vs expected vs max), CV | M2 | ORIGINAL_REQUEST §R2 |
| 12 | +20 Upgrade Forecast Block | Monte Carlo expected PAV bar, S+/SS+ chances, investment verdict | M2 | ORIGINAL_REQUEST §R2 |
| 13 | Character Compatibility Card | Verdict (⭐ Идеально, ✅ Отлично, ⚠️ Приемлемо, ❌ Не подходит) | M2 | ORIGINAL_REQUEST §R2 |
| 14 | Alternative Carriers & "Примерить" | Top compatible alternative characters with 1-click fit to calc | M2 | ORIGINAL_REQUEST §R2 |
| 15 | Save History & Copy Report | "💾 Сохранить в историю" and "📋 Скопировать отчёт" buttons | M2 | ORIGINAL_REQUEST §R2 |
| 16 | Modern Sidebar Navigation | Gold logo, 5 tabs ("Калькулятор", "Импорт / Скан", "Билды героев", "История и Сравнение", "О программе"), active highlight | M3 | ORIGINAL_REQUEST §R3 |
| 17 | ScannerView: Enka.Network | UID fetch, character showcase selector, 1-click transfer to calc | M3 | ORIGINAL_REQUEST §R3 |
| 18 | ScannerView: Inventory Kamera | Folder watcher, scanned GOOD artifacts list, pagination, 1-click transfer | M3 | ORIGINAL_REQUEST §R3 |
| 19 | ScannerView: GOOD JSON | File import, paste JSON, export to JSON | M3 | ORIGINAL_REQUEST §R3 |
| 20 | BuildsView: 130+ Meta-Builds | Search by name, element filter pills, weapons, ER requirements, "Выбрать для калькулятора" | M3 | ORIGINAL_REQUEST §R3 |
| 21 | HistoryView: Filtered Table | Saved artifact table with slot and rank filters, reload into calc | M3 | ORIGINAL_REQUEST §R3 |
| 22 | HistoryView: Side-by-Side Diff | 2-artifact comparison with +diff / -diff indicators | M3 | ORIGINAL_REQUEST §R3 |
| 23 | AboutView | App info, version 2.0+, data sources (AnimeGameData, KQM, Enka, Kamera), hotkey reference | M3 | ORIGINAL_REQUEST §R3 |
| 24 | App View Coordination | `app.py` dynamic switching and `transfer_artifact_to_calculator` broker | M3 | ORIGINAL_REQUEST §R3 |
| 25 | Unified Entrypoints | `test_ui.py`, `main.py`, `calculator.py` launch `GenshinCalcApp` | M4 | ORIGINAL_REQUEST §R4 |
| 26 | Layout-Agnostic Hotkeys | Global Windows Ctrl+C, Ctrl+V, Ctrl+A, Ctrl+X handler (`hotkeys.py`) | M4 | ORIGINAL_REQUEST §R4 |
| 27 | Legacy Facade Compatibility | Backwards compatibility facade in `src/genshin_calc/calculator.py` | M4 | Survey Explorer 1 |
| 28 | E2E Testing Suite | Opaque-box automated test suite (Tiers 1-4) published via `TEST_READY.md` | E2E | ORIGINAL_REQUEST & Strategy |
| 29 | 100% E2E Pass & Adversarial Hardening | Verification of all tiers + Tier 5 white-box stress coverage | M5 | Strategy Final Milestone |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Harness, runner, Tiers 1-4 opaque-box tests, `TEST_READY.md` | none (Parallel) | IN_PROGRESS |
| M1 | Centralized Theme & Styling | `theme.py`, color palette, standard widget styles, icon_manager slot icons | none | PLANNED |
| M2 | CalculatorView Overhaul | `stat_inputs.py`, `forecast_panel.py`, `calculator_view.py` with R2 features | M1 | PLANNED |
| M3 | Modular Sidebar & Views | `sidebar.py`, `scanner_view.py`, `builds_view.py`, `history_view.py`, `about_view.py`, `app.py` | M1, M2 | PLANNED |
| M4 | Entrypoints & Hotkeys | `hotkeys.py`, `test_ui.py`, `main.py`, `calculator.py`, legacy facade | M2, M3 | PLANNED |
| M5 | Final E2E Pass & Hardening | Phase 1: 100% E2E test pass (T1-T4); Phase 2: Tier 5 adversarial hardening | E2E, M4 | PLANNED |

## Interface Contracts

### 1. `theme.py` Contract
- Exports:
  - `ThemeColors`: `BG_DEEP`, `BG_PANEL`, `BG_CARD`, `BG_INPUT`, `GOLD`, `CYAN`, `TEXT_PRIMARY`, `TEXT_MUTED`, `BORDER`, `SUCCESS`, `WARNING`, `DANGER`.
  - `ELEMENT_COLORS`: Dict[str, str] mapping 'Пиро', 'Гидро', 'Анемо', 'Электро', 'Дендро', 'Крио', 'Гео' to hex.
  - `RANK_COLORS`: Dict[str, str] mapping 'SSS', 'SS', 'S', 'A', 'B', 'C' to hex.
  - `FONTS`: dict with standard tuples for `title`, `header`, `body`, `small`, `mono`.
  - `METRICS`: dict with `corner_radius_card=10`, `corner_radius_btn=6`, `border_width=1`.

### 2. `CalculatorView` ↔ Subcomponents Contract
- `StatInputs`:
  - Callback: `on_artifact_changed(artifact_data: dict)` fired on any stat/slot/level update.
  - Method: `load_parsed_artifact(parsed: ParsedArtifact)` to populate slot, set, level, main stat, and substats from external scanner or history.
  - Method: `clear_inputs()` resets all fields.
  - Method: `get_data() -> dict`: Returns slot, set, level, main_stat, main_val, substats list `[(stat_name, val, rolls, addends)]`.
- `ForecastPanel`:
  - Method: `update_forecast(artifact_data: dict)` recalculates PAV%, CV, +20 forecast, build card, compatibility verdict, alternative carriers.
  - Method: `set_selected_character(character_display_name: str)` updates active character & build.
  - Callback: `on_fit_character(char_name: str)` when user clicks "Примерить" on top alternative carrier.
  - Callback: `on_save_history(artifact_data: dict, evaluation: dict)`.

### 3. `GenshinCalcApp` ↔ Sidebar & Views Contract
- `GenshinCalcApp`:
  - Holds `self.views: Dict[str, ctk.CTkFrame]` with keys: `"calculator"`, `"scanner"`, `"builds"`, `"history"`, `"about"`.
  - Method: `show_view(view_id: str)` switches visible frame and informs sidebar.
  - Method: `transfer_artifact_to_calculator(parsed: ParsedArtifact)` calls `CalculatorView.load_parsed_artifact(parsed)` and switches to `"calculator"` view.
  - Method: `select_character_for_calculator(char_build_name: str)` passes selected character to `ForecastPanel` and switches to `"calculator"` view.

### 4. `hotkeys.py` Contract
- `setup_layout_agnostic_hotkeys(root: ctk.CTk)`:
  - Binds `<Control-KeyPress>` globally.
  - Handles keycodes 65 (Select All), 67 (Copy), 86 (Paste), 88 (Cut) regardless of active input language (RU/EN).

## Code Layout
- `src/genshin_calc/ui/theme.py`: Theme definitions & styles.
- `src/genshin_calc/ui/hotkeys.py`: Hotkey handler.
- `src/genshin_calc/ui/app.py`: Main `GenshinCalcApp` class.
- `src/genshin_calc/ui/components/`:
  - `sidebar.py`: Navigation sidebar.
  - `stat_inputs.py`: Stat input panel.
  - `forecast_panel.py`: Forecast & recommendation panel.
- `src/genshin_calc/ui/views/`:
  - `calculator_view.py`: Split-column calculator view.
  - `scanner_view.py`: Enka / Kamera / GOOD scanner view.
  - `builds_view.py`: 134 build catalog view.
  - `history_view.py`: History list & side-by-side comparison view.
  - `about_view.py`: About & documentation view.
- `test_ui.py`, `main.py`, `calculator.py`: Top-level entrypoints.
- `tests/e2e/`: Automated E2E testing track test cases and runner.
