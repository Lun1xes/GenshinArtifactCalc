# Product Guidelines: Genshin Impact 5★ Artifact Calculator (v2)

## 1. Tone and Voice
- **Technical & Rigorous:** Communication should be objective, mathematically precise, and transparent. Avoid exaggerated claims in favor of clear, accurate descriptors ("Discrete Roll Reachability", "PAV Score").
- **Clarity & Honesty:** Explicitly distinguish between confirmed game mechanics (substat roll values, slot stat tables, HoYoverse spawn weights) and project-specific heuristics (e.g., Project Artifact Value / PAV).
- **Concise & Instructive:** Diagnostic error messages should state what is invalid and why (e.g., "Main stat cannot also be a substat", "Value is unreachable by any combination of discrete rolls").

## 2. Visual Identity and Styling
- **Theme:** Dark mode default using CustomTkinter (`Dark` appearance, `blue` theme).
- **Hierarchy:**
  - Primary controls: Dropdown selectors for Slot, Main Stat, and Level.
  - Substat inputs: Clean tabular alignment of stat selector, numeric input, and live roll status indicators.
  - Results Panel: Prominent, high-contrast visual display of calculated PAV, total rolls, breakdown of roll combinations, and upgrade potential.
- **Color Coding:**
  - Green / Cyan: Reachable, optimal, or approved values.
  - Amber / Yellow: Borderline or partial roll state (e.g., unrevealed 4th substat).
  - Red: Error states, unreachable values, or rule violations.

## 3. User Experience Principles
- **Fail Fast & Non-Destructive:** Validate inputs continuously and fail gracefully. Invalid inputs display actionable inline guidance rather than application freezes or crashes.
- **State Integrity:** Prevent impossible state configurations at the UI level (e.g., dynamically filter out the selected Main Stat from the substat dropdowns).
- **Persistent Context:** History and evaluations automatically persist to local storage across restarts, with easy deletion and reset capabilities.
