# Product Definition: Genshin Impact 5★ Artifact Calculator (v2)

## Overview
Genshin Impact 5★ Artifact Calculator (v2) is a specialized desktop utility engineered to calculate, evaluate, and track 5-star Genshin Impact artifacts. Unlike naive calculators that compute simple statistical averages, this application implements exact mathematical discrete roll reachability matching HoYoverse's underlying substat roll tiers (70%, 80%, 90%, 100%).

## Problem Statement
Artifact evaluation in Genshin Impact is frequently misled by rounding errors, floating-point approximations, and impossible substat combinations. Players often waste valuable in-game resources (mora, artifact exp) leveling suboptimal or mathematically impossible artifacts without knowing whether substat totals are genuinely reachable or what their true potential is at level +20.

## Core Value Proposition
- **Mathematical Accuracy:** Discrete roll solver verifying that substat values match valid combinations of tier rolls rather than approximations.
- **Rule Enforcement:** Enforces slot-dependent main stat constraints and mutual exclusivity between main stats and substats.
- **Decision Support:** Provides a customizable Project Artifact Value (PAV) rating heuristic tailored to character archetypes (Main DPS, HP Support, EM Reactor, DEF Tank).
- **Potential Upgrade Modeling:** Evaluates the remaining potential of partially upgraded artifacts (+0 to +16) up to level +20.

## Target Audience
- Genshin Impact theorycrafters and min-maxers seeking exact roll breakdowns.
- Casual and intermediate players who need clear guidance on whether an artifact is worth leveling or discarding.
- Community members and build creators wanting a reproducible, transparent rating system.

## Key Features
1. **Artifact Slot & Stat Selection:**
   - Dedicated slots: Flower of Life, Plume of Death, Sands of Eon, Goblet of Eonothem, Circlet of Logos.
   - Slot-specific main stat filtering (e.g., HP on Flower, ATK on Plume, Elemental/Physical damage on Goblet).
   - Exclusion logic preventing main stat from appearing in substats or future revealed substat pools.

2. **Discrete Roll Reachability Engine:**
   - Exact roll tier mapping using Python `Decimal` arithmetic to avoid floating-point drift.
   - Detection of initial 3-line vs 4-line drop artifacts.
   - Total roll boundary enforcement (minimum and maximum allowable rolls for a given level).

3. **Project Artifact Value (PAV) & Role Presets:**
   - Weighted scoring system with presets for standard character roles (Main DPS, HP Support, EM Reactor, DEF Tank).
   - Custom weight editor allowing manual stat prioritization.
   - Transparent calculation explaining PAV as an engineering heuristic rather than official in-game metric.

4. **Persistence & History Tracking:**
   - Local JSON history persistence (`artifact_history.json`) for saving, reviewing, and deleting evaluated artifacts.

5. **Modern Desktop Interface:**
   - CustomTkinter dark-mode graphical user interface with responsive real-time feedback.

6. **GOOD Format (Genshin Open Object Data) Interoperability:**
   - Direct import/export of 5★ artifacts and complete evaluation histories adhering to the GOOD standard.
   - Bidirectional translation between standard GOOD keys and localized terminology with exact Decimal precision.
