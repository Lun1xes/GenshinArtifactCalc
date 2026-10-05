# E2E Test Infra: Genshin Impact Modular Artifact Calculator UI

## Test Philosophy
- Opaque-box, requirement-driven. Derives from ORIGINAL_REQUEST.md.
- No dependency on private implementation details.
- Headless-compatible: Exercises Tkinter/CustomTkinter widgets safely in Windows CLI environment without requiring an active physical display server.
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + Real-World Workload Testing.

## Feature Inventory Under Test
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| F1 | Genshin Theme & Color Palette | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| F2 | Unified Widget Styling & Metrics | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| F3 | Slot Selector with Emojis & Active Highlight | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F4 | Set Selector Autocomplete & Sorting | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F5 | Main Stat & Level Selectors | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F6 | Substat Discrete Rolls Breakdown & Indicators | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F7 | Clear & Quick Paste Actions | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F8 | Dynamic Round Avatar & Elemental Border | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F9 | Character Build Summary Card | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F10 | Rank, PAV % & Crit Value Metrics | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F11 | +20 Upgrade Monte Carlo Forecast | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F12 | Character Compatibility Card & Verdict | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F13 | Alternative Carriers Matcher & "Примерить" | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F14 | History Persistence & Report Copy | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F15 | Sidebar Navigation (5 Tabs) & Active Highlight | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| F16 | ScannerView: Enka.Network Showcase Integration | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| F17 | ScannerView: Inventory Kamera Folder Monitoring | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| F18 | ScannerView: GOOD JSON Import/Export | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| F19 | BuildsView: 130+ Character Catalog & Element Filter | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| F20 | HistoryView: Filtered Table & Side-by-Side Diff | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| F21 | AboutView: Metadata & Sources & Hotkeys | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| F22 | Entrypoints Compatibility (`test_ui`, `main`, `calculator`) | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ |
| F23 | Windows Layout-Agnostic Hotkeys (VK 65, 67, 86, 88) | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ |

## Test Architecture
- **Location**: `tests/e2e/`
- **Runner**: `python -m unittest discover -s tests/e2e -p "test_*.py"`
- **Pass/Fail Semantics**: All tests must complete with exit code 0.
- **Directory Layout**:
  - `tests/e2e/test_tier1_feature_coverage.py`: Happy path coverage (>=5 tests per feature).
  - `tests/e2e/test_tier2_boundary_corner.py`: Boundary conditions, max/min/empty/error cases.
  - `tests/e2e/test_tier3_pairwise_combinations.py`: Cross-feature interactions and data transfers.
  - `tests/e2e/test_tier4_real_world_scenarios.py`: End-to-end user workflows.
  - `tests/e2e/run_all_e2e.py`: Dedicated test runner producing structured summary and publishing `TEST_READY.md`.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full Manual Calculator Workflow | F1, F3, F4, F5, F6, F8, F9, F10, F11, F12, F14 | High |
| 2 | Enka UID Showcase Import -> 1-Click Calc -> Upgrade Forecast | F16, F3, F5, F6, F11, F12 | High |
| 3 | Kamera GOOD Scan Ingestion -> History Persistence -> Side-by-Side Compare | F17, F18, F14, F20 | High |
| 4 | BuildsView Search & Filter -> "Выбрать для калькулятора" -> Alternative Carrier "Примерить" | F19, F8, F9, F12, F13 | High |
| 5 | Cross-Layout Keyboard Shortcut Editing & Clear/Paste Cycle | F23, F7, F6, F10 | Medium |

## Coverage Thresholds
- Tier 1: ≥5 per feature
- Tier 2: ≥5 per feature (where boundaries exist)
- Tier 3: Pairwise coverage of major feature interactions
- Tier 4: ≥5 realistic application scenarios
