# Implementation Plan: GOOD Format Import & Export

## Phase 1: Format Mapping & Logic Engine (TDD)
- [x] Task: Write Unit Tests for GOOD Format Translation (Red Phase) [573a89e]
    - [ ] Create `test_good_format.py` covering slot and stat bidirectional key mapping
    - [ ] Add unit tests for single-artifact GOOD export serialization
    - [ ] Add unit tests for single and multi-artifact GOOD import deserialization with Decimal precision
    - [ ] Add test cases for invalid, partial, or malformed payloads
- [x] Task: Implement Pure GOOD Format Module `good_adapter.py` (Green Phase) [51c4211]
    - [ ] Define bidirectional mapping dictionaries for slots, main stats, substats, and sets
    - [ ] Implement `to_good_artifact()` and `to_good_collection()`
    - [ ] Implement `from_good_artifact()` and `from_good_collection()`
    - [ ] Verify all tests pass
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [Phase 1 verified: 8/8 tests pass]

## Phase 2: GUI Integration & User Workflows
- [x] Task: Write GUI State Tests for Import/Export Dialog (Red Phase) [4da7ed1]
    - [ ] Add test cases in `test_calculator_state.py` or new `test_good_ui.py` for dialog state transitions
- [ ] Task: Implement GOOD Import/Export Dialog in CustomTkinter (Green Phase)
    - [ ] Add "Импорт / Экспорт (GOOD)" launcher button to `calculator.py`
    - [ ] Implement `GoodTransferDialog` modal with Import and Export tabs
    - [ ] Wire "Загрузить в калькулятор" action to populate active input fields and trigger reachability evaluation
    - [ ] Wire "Добавить в историю" to append valid imported artifacts to `artifact_history.json`
    - [ ] Add copy-to-clipboard functionality with non-blocking feedback
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 3: Integration & Acceptance Testing
- [ ] Task: End-to-End Round-Trip Validation
    - [ ] Perform full round-trip verification: enter artifact -> export GOOD -> re-import -> verify exact reachability
    - [ ] Verify non-blocking diagnostic warnings when importing unreachable roll values
    - [ ] Run complete regression test suite (`test_*.py`)
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
