"""Чистая логика калькулятора 5★ артефактов Genshin Impact.

Игровая механика хранится отдельно от GUI. PAV (Project Artifact Value) —
собственная эвристика приложения, а не внутриигровая формула HoYoverse.

Внешние ссылки, использованные как технические справочники для текущей
реализации (проверены/предоставлены в рабочем контексте):
  https://keqingmains.com/misc/artifacts/
  https://genshin-impact.fandom.com/wiki/Artifact/Stats
  https://genshin-impact.fandom.com/wiki/Artifact/Distribution

В этой сессии live-web проверка недоступна, поэтому новые игровые факты не
следует считать заново подтверждёнными здесь; значения ниже основаны на
справочных данных из предоставленного пользователем аудита.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal
from functools import lru_cache
from itertools import combinations_with_replacement, product
from typing import Mapping, Sequence

D = Decimal


def _stat(step: str, *rolls: str) -> dict:
    return {"rolls": tuple(D(r) for r in rolls), "display_step": D(step)}


STATS_DB: dict[str, dict] = {
    "Крит. урон":           _stat("0.1", "5.44", "6.22", "6.99", "7.77"),
    "Шанс крит. попадания": _stat("0.1", "2.72", "3.11", "3.50", "3.89"),
    "Сила атаки %":         _stat("0.1", "4.08", "4.66", "5.25", "5.83"),
    "Защита %":             _stat("0.1", "5.10", "5.83", "6.56", "7.29"),
    "HP %":                 _stat("0.1", "4.08", "4.66", "5.25", "5.83"),
    "Мастерство стихий":    _stat("1", "16.32", "18.65", "20.98", "23.31"),
    "Восст. энергии":       _stat("0.1", "4.53", "5.18", "5.83", "6.48"),
    "Сила атаки":           _stat("1", "13.62", "15.56", "17.51", "19.45"),
    "Защита":               _stat("1", "16.20", "18.52", "20.83", "23.15"),
    "HP":                   _stat("1", "209.13", "239.00", "268.88", "298.75"),
}

# Вес появления НОВОГО сабстата. В исходном проекте эти веса были частью
# community/reference model, а не официальной UI-таблицей HoYoverse.
SUBSTAT_SPAWN_WEIGHT: dict[str, int] = {
    "HP": 6,
    "Сила атаки": 6,
    "Защита": 6,
    "HP %": 4,
    "Сила атаки %": 4,
    "Защита %": 4,
    "Мастерство стихий": 4,
    "Восст. энергии": 4,
    "Шанс крит. попадания": 3,
    "Крит. урон": 3,
}

# Основные статы по типу артефакта. Значения, которые совпадают с
# сабстатами, автоматически исключаются из пула сабстатов.
ARTIFACT_SLOTS: tuple[str, ...] = (
    "Цветок жизни",
    "Перо смерти",
    "Пески времени",
    "Кубок пространства",
    "Корона разума",
)

MAIN_STATS_BY_SLOT: dict[str, tuple[str, ...]] = {
    "Цветок жизни": ("HP",),
    "Перо смерти": ("Сила атаки",),
    "Пески времени": (
        "HP %",
        "Сила атаки %",
        "Защита %",
        "Восст. энергии",
        "Мастерство стихий",
    ),
    "Кубок пространства": (
        "HP %",
        "Сила атаки %",
        "Защита %",
        "Пиро урон %",
        "Гидро урон %",
        "Крио урон %",
        "Электро урон %",
        "Анемо урон %",
        "Гео урон %",
        "Дендро урон %",
        "Бонус элементального урона",
        "Физ. урон %",
        "Мастерство стихий",
    ),
    "Корона разума": (
        "HP %",
        "Сила атаки %",
        "Защита %",
        "Шанс крит. попадания",
        "Крит. урон",
        "Бонус лечения",
        "Мастерство стихий",
    ),
}

LEVELS = (0, 4, 8, 12, 16, 20)


class ArtifactInputError(ValueError):
    """Ввод описывает невозможное или неполное состояние артефакта."""


def min_roll(stat: str) -> Decimal:
    return STATS_DB[stat]["rolls"][0]


def max_roll(stat: str) -> Decimal:
    return STATS_DB[stat]["rolls"][-1]


def avg_roll(stat: str) -> Decimal:
    rolls = STATS_DB[stat]["rolls"]
    return sum(rolls, D(0)) / len(rolls)


@dataclass(frozen=True)
class RollLimits:
    stat_count: int
    total_rolls: int
    min_per_stat: int
    max_per_stat: int


def roll_limits(level: int, is_3_stat: bool) -> RollLimits:
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}, got {level}")
    k = level // 4
    if not is_3_stat:
        return RollLimits(4, 4 + k, 1, 1 + k)
    if k == 0:
        return RollLimits(3, 3, 1, 1)
    return RollLimits(4, 3 + k, 1, k)


def validate_main_stat(slot: str, main_stat: str) -> None:
    slot_key = "Корона разума" if slot == "Корона проницательности" else slot
    if slot_key not in MAIN_STATS_BY_SLOT:
        raise ArtifactInputError(f"Неизвестный тип артефакта: «{slot}».")
    if main_stat not in MAIN_STATS_BY_SLOT[slot_key]:
        allowed = ", ".join(MAIN_STATS_BY_SLOT[slot_key])
        raise ArtifactInputError(
            f"Основной стат «{main_stat}» недопустим для «{slot}». "
            f"Допустимые: {allowed}."
        )


@lru_cache(maxsize=None)
def eligible_substats(slot: str, main_stat: str) -> tuple[str, ...]:
    validate_main_stat(slot, main_stat)
    return tuple(s for s in STATS_DB if s != main_stat)


@lru_cache(maxsize=None)
def _display_candidates(raw: Decimal, step: Decimal) -> frozenset[Decimal]:
    units = raw / step
    floor_u = units.to_integral_value(rounding=ROUND_FLOOR)
    frac = units - floor_u
    if frac > D("0.5"):
        picks = (floor_u + 1,)
    elif frac < D("0.5"):
        picks = (floor_u,)
    else:
        # На математической границе допускаем оба соседних показания,
        # чтобы учитывать разницу представления между внутренним числом
        # и тем, что пользователь видит в клиенте.
        picks = (floor_u, floor_u + 1)
    return frozenset((u * step).quantize(step) for u in picks)


@lru_cache(maxsize=None)
def raw_sums(stat: str, n: int) -> frozenset[Decimal]:
    if n < 1:
        return frozenset()
    rolls = STATS_DB[stat]["rolls"]
    return frozenset(sum(c, D(0)) for c in combinations_with_replacement(rolls, n))


@lru_cache(maxsize=None)
def displayed_values(stat: str, n: int) -> frozenset[Decimal]:
    step = STATS_DB[stat]["display_step"]
    out: set[Decimal] = set()
    for raw in raw_sums(stat, n):
        out.update(_display_candidates(raw, step))
    return frozenset(out)


@lru_cache(maxsize=None)
def accepted_values(stat: str, n: int) -> frozenset[Decimal]:
    # Принимаем число, которое реально можно получить и показать в игре,
    # а также точную табличную сумму датамайна/reference-data.
    return displayed_values(stat, n) | raw_sums(stat, n)


def possible_roll_counts(stat: str, value: Decimal, min_n: int, max_n: int) -> tuple[int, ...]:
    return tuple(
        n for n in range(min_n, max_n + 1)
        if value in accepted_values(stat, n)
    )


_NUM_RE = re.compile(r"^(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$")


def parse_value(raw: str, row: int | None = None) -> Decimal:
    prefix = f"Строка {row}: " if row is not None else ""
    s = raw.strip().replace(",", ".")
    if not s:
        raise ArtifactInputError(f"{prefix}значение пустое.")
    if not _NUM_RE.fullmatch(s):
        raise ArtifactInputError(
            f"{prefix}«{raw.strip()}» — не число. Допустимы цифры и один десятичный разделитель."
        )
    value = D(s)
    if not value.is_finite() or value < 0:
        raise ArtifactInputError(f"{prefix}значение должно быть конечным и неотрицательным.")
    return value


def _fmt(x: Decimal) -> str:
    return f"{x:f}"


def _explain_unreachable(stat: str, value: Decimal, limits: RollLimits) -> str:
    pool = set()
    for n in range(limits.min_per_stat, limits.max_per_stat + 1):
        pool.update(accepted_values(stat, n))
    lowest, highest = min(pool), max(pool)
    if value < lowest:
        return f"слишком мало: минимум — {_fmt(lowest)}."
    if value > highest:
        return f"слишком много: максимум — {_fmt(highest)}."
    shown = set()
    for n in range(limits.min_per_stat, limits.max_per_stat + 1):
        shown.update(displayed_values(stat, n))
    below = max((v for v in shown if v < value), default=None)
    above = min((v for v in shown if v > value), default=None)
    near = ", ".join(_fmt(v) for v in (below, above) if v is not None)
    return f"такое значение не является достижимой суммой роллов; ближайшие отображаемые значения: {near}."


def _validate_entries_shape(limits: RollLimits, entries: Sequence[tuple[int, str, str]], level: int) -> None:
    if len(entries) != limits.stat_count:
        if level == 0 and limits.stat_count == 3:
            raise ArtifactInputError(
                f"У 3-сабстатного артефакта на +0 должно быть ровно 3 поля (введено: {len(entries)})."
            )
        raise ArtifactInputError(
            f"На уровне +{level} должно быть ровно {limits.stat_count} заполненных сабстата "
            f"(введено: {len(entries)})."
        )


def validate_artifact(
    level: int,
    is_3_stat: bool,
    entries: Sequence[tuple[int, str, str]],
    *,
    slot: str,
    main_stat: str,
):
    """Валидирует физически достижимое состояние артефакта."""
    validate_main_stat(slot, main_stat)
    limits = roll_limits(level, is_3_stat)
    _validate_entries_shape(limits, entries, level)

    allowed_substats = set(eligible_substats(slot, main_stat))
    seen: set[str] = set()
    parsed = []
    for row, stat, raw in entries:
        if stat not in STATS_DB:
            raise ArtifactInputError(f"Строка {row}: неизвестная характеристика «{stat}».")
        if stat == main_stat:
            raise ArtifactInputError(
                f"Строка {row}: «{stat}» — основной стат и не может одновременно быть сабстатом."
            )
        if stat not in allowed_substats:
            raise ArtifactInputError(f"Строка {row}: характеристика «{stat}» недоступна с выбранным основным статом.")
        if stat in seen:
            raise ArtifactInputError(f"Строка {row}: характеристика «{stat}» введена повторно.")
        seen.add(stat)
        value = parse_value(raw, row)
        counts = possible_roll_counts(stat, value, limits.min_per_stat, limits.max_per_stat)
        if not counts:
            raise ArtifactInputError(
                f"Строка {row} ({stat}): значение {raw.strip()} невозможно на +{level}: "
                + _explain_unreachable(stat, value, limits)
            )
        parsed.append((row, stat, value, counts))

    combos = [c for c in product(*(p[3] for p in parsed)) if sum(c) == limits.total_rolls]
    if not combos:
        lo = sum(min(p[3]) for p in parsed)
        hi = sum(max(p[3]) for p in parsed)
        if lo > limits.total_rolls:
            why = f"минимум по введённым значениям уже даёт {lo} роллов, а нужно ровно {limits.total_rolls}."
        elif hi < limits.total_rolls:
            why = f"максимум по введённым значениям даёт {hi} роллов, а нужно ровно {limits.total_rolls}."
        else:
            why = f"по отдельности значения возможны, но вместе не дают ровно {limits.total_rolls} роллов."
        raise ArtifactInputError("Невозможная комбинация значений: " + why)
    return limits, parsed, combos


@dataclass(frozen=True)
class ArtifactEvaluation:
    slot: str
    main_stat: str
    level: int
    is_3_stat: bool
    substats: dict[str, Decimal]
    roll_counts: dict[str, tuple[int, ...]]
    total_rolls: int
    remaining_events: int
    upgrades_info: str
    current_score: float
    ideal_max_score: float
    max_possible_score: float
    expected_score: float
    current_pct: float
    potential_pct: float
    expected_pct: float


def _peak(stat: str, weights: Mapping[str, float]) -> float:
    return weights.get(stat, 0.0) * float(max_roll(stat) / avg_roll(stat))


def evaluate_artifact(
    level: int,
    is_3_stat: bool,
    entries: Sequence[tuple[int, str, str]],
    weights: Mapping[str, float],
    *,
    slot: str,
    main_stat: str,
) -> ArtifactEvaluation:
    limits, parsed, combos = validate_artifact(
        level, is_3_stat, entries, slot=slot, main_stat=main_stat
    )

    substats = {stat: value for _, stat, value, _ in parsed}
    roll_counts = {
        stat: tuple(sorted({combo[i] for combo in combos}))
        for i, (_, stat, _, _) in enumerate(parsed)
    }

    # PAV — проектная эвристика.
    current = sum(
        float(value / avg_roll(stat)) * weights.get(stat, 0.0)
        for stat, value in substats.items()
    )

    eligible = eligible_substats(slot, main_stat)
    eligible_peaks = sorted((_peak(stat, weights) for stat in eligible), reverse=True)
    ideal = sum(eligible_peaks[:4]) + 5 * (eligible_peaks[0] if eligible_peaks else 0.0)
    if ideal <= 0:
        ideal = 1.0

    events_left = (20 - level) // 4
    present = list(substats)

    if is_3_stat and level == 0:
        absent = [s for s in eligible if s not in present]
        best_present = max((_peak(s, weights) for s in present), default=0.0)
        reveal_peak = max((_peak(s, weights) for s in absent), default=0.0)
        best_gain = reveal_peak + 4 * max(best_present, reveal_peak)

        spawn_pool = sum(SUBSTAT_SPAWN_WEIGHT.get(s, 0) for s in absent)
        if spawn_pool:
            expected_reveal_weight = sum(
                SUBSTAT_SPAWN_WEIGHT.get(s, 0) * weights.get(s, 0.0)
                for s in absent
            ) / spawn_pool
        else:
            expected_reveal_weight = 0.0

        # Один reveal + четыре последующих равновероятных enhancement rolls.
        expected_gain = expected_reveal_weight + (
            sum(weights.get(s, 0.0) for s in present) + expected_reveal_weight
        )
        upgrades_info = "Осталось: 1 раскрытие 4-го сабстата (+4) + 4 прока"
    else:
        best_present = max((_peak(s, weights) for s in present), default=0.0)
        mean_weight = sum(weights.get(s, 0.0) for s in present) / len(present)
        best_gain = events_left * best_present
        expected_gain = events_left * mean_weight
        upgrades_info = f"Осталось проков до +20: {events_left}"

    max_possible = current + best_gain
    expected = current + expected_gain
    pct = lambda score: min(100.0, max(0.0, score / ideal * 100.0))

    return ArtifactEvaluation(
        slot=slot,
        main_stat=main_stat,
        level=level,
        is_3_stat=is_3_stat,
        substats=substats,
        roll_counts=roll_counts,
        total_rolls=limits.total_rolls,
        remaining_events=events_left,
        upgrades_info=upgrades_info,
        current_score=current,
        ideal_max_score=ideal,
        max_possible_score=max_possible,
        expected_score=expected,
        current_pct=pct(current),
        potential_pct=pct(max_possible),
        expected_pct=pct(expected),
    )


def describe_rolls(counts: tuple[int, ...]) -> str:
    if len(counts) == 1:
        return f"{counts[0]} ролл."
    return f"{counts[0]}–{counts[-1]} ролл."

SLOT_EMOJI = {'Цветок жизни': '🌺', 'Перо смерти': '✒️', 'Пески времени': '⏳', 'Кубок пространства': '🍷', 'Корона разума': '👑'}
