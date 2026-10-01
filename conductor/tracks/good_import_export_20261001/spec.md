# Specification: GOOD Format (Genshin Open Object Data) Import & Export

## 1. Overview
This feature introduces support for the Genshin Open Object Data (GOOD) specification (v1/v2), allowing users to seamlessly import and export 5★ artifact builds. Users can import single artifacts directly into the calculator from the clipboard or file, export the currently evaluated artifact to GOOD format, and bulk-export or bulk-import their saved artifact evaluation history.

## 2. Functional Requirements
### 2.1 Format Mapping Layer (`good_adapter.py`)
- **Key Translation:** Provide bidirectional mapping between GOOD standard stat keys and internal application names:
  - Slots: `flower` -> Цветок жизни, `plume` -> Перо смерти, `sands` -> Пески времени, `goblet` -> Кубок пространства, `circlet` -> Корона проницательности.
  - Substats & Main Stats: `hp` -> HP, `hp_` -> HP %, `atk` -> Сила атаки, `atk_` -> Сила атаки %, `def` -> Защита, `def_` -> Защита %, `eleMas` -> Мастерство стихий, `enerRech_` -> Восст. энергии, `critRate_` -> Шанс крит. попадания, `critDMG_` -> Крит. урон, elemental/physical damage bonuses, healing bonus.
  - Set Keys: Retain standard GOOD set keys (e.g. `GladiatorsFinale`, `CrimsonWitchOfFlames`, etc.).
- **Data Serialization:**
  - Convert single artifact state into a valid GOOD JSON artifact object.
  - Convert full history list into a valid GOOD root document:
    ```json
    {
      "format": "GOOD",
      "version": 2,
      "source": "Genshin Artifact Calculator v2",
      "artifacts": [...]
    }
    ```
- **Data Deserialization:**
  - Parse both isolated GOOD artifact objects and complete GOOD collections (`artifacts` array).
  - Convert numeric values cleanly to `Decimal` representation, avoiding floating-point precision loss.

### 2.2 Validation & Diagnostics
- When an imported artifact is loaded:
  - If a stat is mathematically unreachable or violates slot rules, load the inputs into the calculator but flag unreachable stats with inline warnings.
  - Never crash or silently discard data due to partial format deviations.

### 2.3 UI Integration (CustomTkinter)
- **Import/Export Modal Dialog:**
  - Accessible via a dedicated "Импорт / Экспорт (GOOD)" button on the main window.
  - Features:
    1. **Import:** Paste JSON directly from clipboard or load via file dialog. Options: "Загрузить в калькулятор" (active inputs) and "Добавить в историю" (bulk/history).
    2. **Export:** Copy active artifact to clipboard as GOOD JSON, or export history to a `.json` file.
  - Visual toast/notification when JSON is successfully copied to clipboard.

## 3. Non-Functional Requirements
- **Zero Heavy Dependencies:** Use Python standard library `json` and `decimal` modules; no external web packages.
- **Architectural Isolation:** Keep parsing and serialization in pure domain functions separate from CustomTkinter UI widgets.
- **Unit Test Coverage:** >80% coverage for the new mapping and parsing module with complete round-trip regression tests.

## 4. Acceptance Criteria
- [ ] Valid GOOD artifact JSON can be pasted into the import dialog and populates slot, main stat, level, and all substats in the calculator.
- [ ] Calculator accurately performs discrete roll reachability on imported artifacts.
- [ ] Active artifact can be exported to valid GOOD JSON format and copied to clipboard.
- [ ] Bulk import properly parses multi-artifact GOOD JSON payloads and appends them to history.
- [ ] Malformed or impossible artifacts trigger informative non-blocking UI diagnostics without crashing.
- [ ] Full test suite passes (`unittest`) covering bidirectional mapping and round-trip conversion.

## 5. Out of Scope
- Weapons, characters, and materials sections of GOOD format (artifacts only).
- Optical character recognition (OCR) / screen scanning.
