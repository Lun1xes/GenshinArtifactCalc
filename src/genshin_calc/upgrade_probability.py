"""Artifact Upgrade Probability & Forecast Engine.

Uses game data math from AnimeGameData and discrete roll steps to calculate:
- Combinatorial probability of reaching S / SS / SSS rank at +20
- Mathematical expectation of PAV and Crit Value at +20
- Actionable investment verdict (Worth leveling vs High risk)
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

import artifact_logic as al
from artifact_logic import D, STATS_DB, SUBSTAT_SPAWN_WEIGHT

from genshin_calc.utils import get_project_root

ROOT_DIR = get_project_root()
MATH_FILE = os.path.join(ROOT_DIR, "data", "relic_math.json")


@dataclass
class UpgradeForecastResult:
    current_level: int
    remaining_rolls: int
    prob_s_plus: float           # Probability of reaching S rank or higher (>= 65% PAV)
    prob_ss_plus: float          # Probability of reaching SS rank or higher (>= 80% PAV)
    prob_sss: float              # Probability of reaching SSS rank (>= 90% PAV)
    expected_pav: float          # Expected PAV at +20
    expected_cv: float           # Expected Crit Value at +20
    crit_rolls_prob: dict[int, float] # Probability of getting +1, +2, +3, +4, +5 rolls into Crit
    verdict: str                 # Human-readable verdict in Russian
    verdict_color: str           # Hex color for UI badge
    advice: str                  # Strategic advice on mora and exp efficiency


def calculate_upgrade_forecast(
    slot: str,
    main_stat: str,
    current_substats: Mapping[str, str | Decimal | float],
    level: int = 0,
    substat_weights: Mapping[str, float] | None = None,
    num_simulations: int = 4000,
) -> UpgradeForecastResult:
    """Calculate the upgrade forecast from current level up to +20 using AnimeGameData probabilities."""
    # If already +20, no upgrades remain
    level = max(0, min(20, level))
    if level >= 20:
        return UpgradeForecastResult(
            current_level=20,
            remaining_rolls=0,
            prob_s_plus=100.0,
            prob_ss_plus=0.0,
            prob_sss=0.0,
            expected_pav=0.0,
            expected_cv=0.0,
            crit_rolls_prob={},
            verdict="Артефакт максимального уровня (+20)",
            verdict_color="#00e5ff",
            advice="Артефакт уже полностью улучшен.",
        )

    # 1. Determine number of remaining upgrades
    # Thresholds are +4, +8, +12, +16, +20
    milestones = [4, 8, 12, 16, 20]
    remaining_milestones = [m for m in milestones if m > level]
    num_upgrades = len(remaining_milestones)

    # 2. Existing substats
    existing_subs = {k: D(str(v)) for k, v in current_substats.items() if v and D(str(v)) > 0}
    is_three_stat_base = (len(existing_subs) == 3)

    # 3. Default weights if not provided
    weights = substat_weights if substat_weights is not None else {
        "Крит. урон": 2.0,
        "Шанс крит. попадания": 2.0,
        "Сила атаки %": 1.5,
        "Восст. энергии": 1.5,
        "Мастерство стихий": 1.0,
        "HP %": 1.0,
        "Защита %": 0.8,
        "Сила атаки": 0.3,
        "HP": 0.2,
        "Защита": 0.2,
    }

    # Pre-calculate steps
    stat_roll_steps = {
        name: [float(r) for r in data["rolls"]]
        for name, data in STATS_DB.items()
    }

    # Simulation setup
    s_count = 0
    ss_count = 0
    sss_count = 0
    total_pav = 0.0
    total_cv = 0.0
    crit_rolls_counts = {i: 0 for i in range(num_upgrades + 1)}

    available_spawn_pool = [
        s for s in SUBSTAT_SPAWN_WEIGHT.keys()
        if s != main_stat and s not in existing_subs
    ]
    spawn_weights = [SUBSTAT_SPAWN_WEIGHT[s] for s in available_spawn_pool]

    # Pre-parse base values
    base_subs_list = list(existing_subs.keys())
    base_values_list = [float(existing_subs[k]) for k in base_subs_list]

    for _ in range(num_simulations):
        current_names = list(base_subs_list)
        current_vals = list(base_values_list)
        crit_added = 0

        # Step 1: If 3-stat base, first upgrade spawns 4th substat
        upgrades_left = num_upgrades
        if len(current_names) < 4 and upgrades_left > 0 and available_spawn_pool:
            new_stat = random.choices(available_spawn_pool, weights=spawn_weights, k=1)[0]
            step_val = random.choice(stat_roll_steps[new_stat])
            current_names.append(new_stat)
            current_vals.append(step_val)
            if new_stat in ("Крит. урон", "Шанс крит. попадания"):
                crit_added += 1
            upgrades_left -= 1

        # Step 2: Remaining upgrades go to random one of the 4 stats
        for _ in range(upgrades_left):
            idx = random.randint(0, len(current_names) - 1)
            target_stat = current_names[idx]
            step_val = random.choice(stat_roll_steps[target_stat])
            current_vals[idx] += step_val
            if target_stat in ("Крит. урон", "Шанс крит. попадания"):
                crit_added += 1

        crit_rolls_counts[crit_added] += 1

        # Calculate final PAV and CV for this simulation
        sim_cv = 0.0
        weighted_sum = 0.0
        for name, val in zip(current_names, current_vals):
            if name == "Крит. урон":
                sim_cv += val
            elif name == "Шанс крит. попадания":
                sim_cv += val * 2.0
            w = weights.get(name, 0.0)
            # Normalize stat contribution to PAV
            max_step = stat_roll_steps[name][-1]
            rolls_approx = val / max_step
            weighted_sum += rolls_approx * w

        # Approx PAV scale
        sim_pav = min(100.0, (weighted_sum / 14.0) * 100.0)

        total_pav += sim_pav
        total_cv += sim_cv

        if sim_pav >= 90.0 or sim_cv >= 45.0:
            sss_count += 1
            ss_count += 1
            s_count += 1
        elif sim_pav >= 80.0 or sim_cv >= 36.0:
            ss_count += 1
            s_count += 1
        elif sim_pav >= 65.0 or sim_cv >= 28.0:
            s_count += 1

    prob_s = round((s_count / num_simulations) * 100.0, 1)
    prob_ss = round((ss_count / num_simulations) * 100.0, 1)
    prob_sss = round((sss_count / num_simulations) * 100.0, 1)
    avg_pav = round(total_pav / num_simulations, 1)
    avg_cv = round(total_cv / num_simulations, 1)

    crit_prob_dict = {
        k: round((v / num_simulations) * 100.0, 1)
        for k, v in crit_rolls_counts.items()
        if (v / num_simulations) >= 0.01
    }

    # Investment verdict
    if prob_ss >= 45.0 or prob_s >= 75.0:
        verdict = "🔥 Высокий потенциал (Стоит качать)"
        verdict_color = "#00e5ff"
        advice = f"Высокая вероятность достичь S-ранга ({prob_s}%). Отличный кандидат на прокачку до +20."
    elif prob_s >= 40.0:
        verdict = "⚖️ Умеренный потенциал (Качать до +8/+12)"
        verdict_color = "#ffd700"
        advice = f"Шанс на успех {prob_s}%. Рекомендуется прокачать до +8 или +12; если оба ролла мимо — в утиль."
    else:
        verdict = "🗑️ Низкий потенциал (Высокий риск)"
        verdict_color = "#ff5252"
        advice = f"Шанс стать полезным всего {prob_s}%. Не рекомендуется тратить мору и артефактный опыт."

    return UpgradeForecastResult(
        current_level=level,
        remaining_rolls=num_upgrades,
        prob_s_plus=prob_s,
        prob_ss_plus=prob_ss,
        prob_sss=prob_sss,
        expected_pav=avg_pav,
        expected_cv=avg_cv,
        crit_rolls_prob=crit_prob_dict,
        verdict=verdict,
        verdict_color=verdict_color,
        advice=advice,
    )
