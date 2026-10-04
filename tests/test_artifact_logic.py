import itertools
import random
import unittest
from decimal import ROUND_HALF_UP, Decimal as D

import artifact_logic as L
from artifact_logic import (
    ARTIFACT_SLOTS,
    MAIN_STATS_BY_SLOT,
    STATS_DB,
    ArtifactInputError,
    avg_roll,
    eligible_substats,
    evaluate_artifact,
    parse_value,
    possible_roll_counts,
    roll_limits,
    validate_artifact,
)

LEVELS = (0, 4, 8, 12, 16, 20)
W1 = {s: 1.0 for s in STATS_DB}
FOUR = ["Крит. урон", "Шанс крит. попадания", "Сила атаки %", "Восст. энергии"]


def game_display(stat, raw):
    step = STATS_DB[stat]["display_step"]
    return ((raw / step).quantize(D(1), rounding=ROUND_HALF_UP) * step).quantize(step)


def all_vectors_by_events(is_3_stat):
    states = {(1, 1, 1) if is_3_stat else (1, 1, 1, 1)}
    out = {0: states}
    for event in range(1, 6):
        nxt = set()
        for st in states:
            if is_3_stat and event == 1:
                nxt.add(st + (1,))
            else:
                for i in range(len(st)):
                    v = list(st)
                    v[i] += 1
                    nxt.add(tuple(v))
        states = nxt
        out[event] = states
    return out


def entries_from(stats, values):
    return [(i + 1, s, str(v)) for i, (s, v) in enumerate(zip(stats, values))]


def value_for(stat, count, rng):
    return sum((STATS_DB[stat]["rolls"][rng.randrange(4)] for _ in range(count)), D(0))


class DataTests(unittest.TestCase):
    def test_slots_and_main_stats_exist(self):
        self.assertEqual(set(ARTIFACT_SLOTS), set(MAIN_STATS_BY_SLOT))
        for slot in ARTIFACT_SLOTS:
            self.assertGreaterEqual(len(MAIN_STATS_BY_SLOT[slot]), 1)

    def test_main_stat_pools(self):
        self.assertEqual(MAIN_STATS_BY_SLOT["Цветок жизни"], ("HP",))
        self.assertEqual(MAIN_STATS_BY_SLOT["Перо смерти"], ("Сила атаки",))
        self.assertIn("Восст. энергии", MAIN_STATS_BY_SLOT["Пески времени"])
        self.assertIn("Крит. урон", MAIN_STATS_BY_SLOT["Корона разума"])
        self.assertIn("Крио урон %", MAIN_STATS_BY_SLOT["Кубок пространства"])
        self.assertIn("Пиро урон %", MAIN_STATS_BY_SLOT["Кубок пространства"])

    def test_every_substat_has_four_increasing_rolls(self):
        for name, data in STATS_DB.items():
            self.assertEqual(len(data["rolls"]), 4, name)
            self.assertEqual(list(data["rolls"]), sorted(set(data["rolls"])), name)

    def test_known_roll_values(self):
        self.assertEqual(tuple(map(D, ("5.44", "6.22", "6.99", "7.77"))), STATS_DB["Крит. урон"]["rolls"])
        self.assertEqual(tuple(map(D, ("13.62", "15.56", "17.51", "19.45"))), STATS_DB["Сила атаки"]["rolls"])

    def test_average_is_exact_mean(self):
        for stat in STATS_DB:
            expected = sum(STATS_DB[stat]["rolls"], D(0)) / 4
            self.assertEqual(avg_roll(stat), expected, stat)

    def test_flat_atk_average_and_min(self):
        self.assertEqual(avg_roll("Сила атаки"), D("16.535"))
        self.assertEqual(STATS_DB["Сила атаки"]["rolls"][0], D("13.62"))

    def test_max_over_avg_varies_by_stat(self):
        ratios = [STATS_DB[s]["rolls"][-1] / avg_roll(s) for s in STATS_DB]
        self.assertGreater(max(ratios) - min(ratios), D("0.0001"))


class MainStatTests(unittest.TestCase):
    def test_main_stat_excluded_from_substat_pool(self):
        self.assertNotIn("HP", eligible_substats("Цветок жизни", "HP"))
        self.assertNotIn("Крит. урон", eligible_substats("Корона разума", "Крит. урон"))
        self.assertNotIn("Восст. энергии", eligible_substats("Пески времени", "Восст. энергии"))

    def test_all_other_substats_remain_eligible(self):
        eligible = set(eligible_substats("Корона разума", "Крит. урон"))
        self.assertEqual(eligible, set(STATS_DB) - {"Крит. урон"})

    def test_invalid_main_stat_for_slot(self):
        with self.assertRaises(ArtifactInputError):
            validate_artifact(0, False, entries_from(FOUR, ["7.77", "3.89", "5.83", "6.48"]),
                              slot="Цветок жизни", main_stat="Крит. урон")

    def test_main_stat_cannot_be_substat(self):
        stats = ["HP", "Крит. урон", "Сила атаки %", "Восст. энергии"]
        with self.assertRaises(ArtifactInputError) as cm:
            evaluate_artifact(0, False, entries_from(stats, ["298.75", "7.77", "5.83", "6.48"]), W1,
                              slot="Цветок жизни", main_stat="HP")
        self.assertIn("основной стат", str(cm.exception))

    def test_main_stat_excluded_from_three_stat_reveal(self):
        weights = {s: 0.0 for s in STATS_DB}
        weights["HP"] = 100.0
        # HP is main stat for Flower, so it must not become the revealed 4th stat.
        stats = ["Защита", "HP %", "Восст. энергии"]
        vals = [str(STATS_DB[s]["rolls"][0]) for s in stats]
        ev = evaluate_artifact(0, True, entries_from(stats, vals), weights,
                                slot="Цветок жизни", main_stat="HP")
        other_best = max(weights[s] for s in STATS_DB if s not in stats and s != "HP")
        reveal_expected = other_best
        actual_gain = ev.max_possible_score - ev.current_score
        self.assertLess(actual_gain, 5 * 100.0)
        self.assertGreaterEqual(reveal_expected, 0.0)


class RollLimitsTests(unittest.TestCase):
    def test_total_rolls(self):
        self.assertEqual([roll_limits(l, False).total_rolls for l in LEVELS], [4, 5, 6, 7, 8, 9])
        self.assertEqual([roll_limits(l, True).total_rolls for l in LEVELS], [3, 4, 5, 6, 7, 8])

    def test_max_per_stat(self):
        self.assertEqual([roll_limits(l, False).max_per_stat for l in LEVELS], [1, 2, 3, 4, 5, 6])
        self.assertEqual([roll_limits(l, True).max_per_stat for l in LEVELS], [1, 1, 2, 3, 4, 5])

    def test_stat_count(self):
        self.assertEqual(roll_limits(0, True).stat_count, 3)
        self.assertEqual([roll_limits(l, True).stat_count for l in LEVELS[1:]], [4, 4, 4, 4, 4])
        self.assertEqual([roll_limits(l, False).stat_count for l in LEVELS], [4] * 6)

    def test_limits_match_exhaustive_history(self):
        for is_3 in (False, True):
            histories = all_vectors_by_events(is_3)
            for k, real in histories.items():
                level = 4 * k
                lim = roll_limits(level, is_3)
                modelled = {
                    v for v in itertools.product(range(lim.min_per_stat, lim.max_per_stat + 1), repeat=lim.stat_count)
                    if sum(v) == lim.total_rolls
                }
                self.assertEqual(real, modelled, (is_3, level))

    def test_bad_level(self):
        with self.assertRaises(ValueError):
            roll_limits(2, False)


class DiscreteRollTests(unittest.TestCase):
    def test_round_based_false_positive_is_rejected(self):
        self.assertEqual(round(13.0 / 6.605), 2)
        self.assertEqual(possible_roll_counts("Крит. урон", D("13.0"), 1, 6), ())

    def test_flat_and_percent_display(self):
        self.assertEqual(possible_roll_counts("Крит. урон", D("7.8"), 1, 1), (1,))
        self.assertEqual(possible_roll_counts("Крит. урон", D("7.77"), 1, 1), (1,))
        self.assertEqual(possible_roll_counts("Сила атаки", D("14"), 1, 1), (1,))
        self.assertEqual(possible_roll_counts("Мастерство стихий", D("21"), 1, 1), (1,))

    def test_impossible_between_values_rejected(self):
        for value in ("7.7", "7.75", "7.85", "13.0"):
            self.assertEqual(possible_roll_counts("Крит. урон", D(value), 1, 3), (), value)

    def test_comma_and_bad_numeric_input(self):
        self.assertEqual(parse_value("7,8"), D("7.8"))
        for bad in ("", "-1", "NaN", "inf", "1e2", "1_0", "1.2.3", "1.234,5"):
            with self.subTest(bad=bad):
                with self.assertRaises(ArtifactInputError):
                    parse_value(bad)

    def test_real_histories_are_accepted(self):
        rng = random.Random(1234)
        names = list(STATS_DB)
        for _ in range(500):
            is_3 = rng.random() < 0.5
            k = rng.randrange(6)
            level = k * 4
            vecs = sorted(all_vectors_by_events(is_3)[k])
            vec = rng.choice(vecs)
            stats = rng.sample(names, len(vec))
            values = [value_for(s, n, rng) for s, n in zip(stats, vec)]
            # Use a non-conflicting main stat so sampled substats remain valid.
            slot = "Песок времени" if False else "Пески времени"
            main_candidates = [m for m in MAIN_STATS_BY_SLOT[slot] if m not in stats]
            if not main_candidates:
                continue
            main = main_candidates[0]
            for vals in (values, [game_display(s, v) for s, v in zip(stats, values)]):
                ev = evaluate_artifact(level, is_3, entries_from(stats, vals), W1, slot=slot, main_stat=main)
                self.assertEqual(ev.total_rolls, roll_limits(level, is_3).total_rolls)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.slot = "Пески времени"
        self.main = "HP %"

    def test_three_stat_plus0_requires_three(self):
        stats = FOUR[:2]
        with self.assertRaises(ArtifactInputError):
            evaluate_artifact(0, True, entries_from(stats, ["7.77", "3.89"]), W1, slot=self.slot, main_stat=self.main)

    def test_three_stat_plus0_four_fields_rejected(self):
        with self.assertRaises(ArtifactInputError) as cm:
            evaluate_artifact(0, True, entries_from(FOUR, ["7.77", "3.89", "5.83", "6.48"]), W1,
                              slot=self.slot, main_stat=self.main)
        self.assertIn("ровно 3", str(cm.exception))

    def test_four_stat_plus0_requires_four(self):
        with self.assertRaises(ArtifactInputError):
            evaluate_artifact(0, False, entries_from(FOUR[:3], ["7.77", "3.89", "5.83"]), W1,
                              slot=self.slot, main_stat=self.main)

    def test_plus4_requires_four_visible_stats(self):
        with self.assertRaises(ArtifactInputError):
            evaluate_artifact(4, True, entries_from(FOUR[:3], ["7.77", "3.89", "5.83"]), W1,
                              slot=self.slot, main_stat=self.main)

    def test_duplicate_substat_rejected(self):
        stats = [FOUR[0], FOUR[0], FOUR[2], FOUR[3]]
        with self.assertRaises(ArtifactInputError):
            evaluate_artifact(0, False, entries_from(stats, ["7.77", "7.77", "5.83", "6.48"]), W1,
                              slot=self.slot, main_stat=self.main)

    def test_total_rolls_exact(self):
        # +8, 4-stat => exactly 6 total rolls.
        ok = ["12.44", "3.89", "5.83", "6.48"]  # 2 + 1 + 1 + 1 = 5 -> should fail because +8 needs 6
        with self.assertRaises(ArtifactInputError):
            evaluate_artifact(8, False, entries_from(FOUR, ok), W1, slot=self.slot, main_stat=self.main)

    def test_three_stat_plus20_total_is_eight(self):
        stats = FOUR
        # 5+1+1+1 = 8, valid at +20 for a 3-stat artifact.
        vals = ["38.85", "3.89", "5.83", "6.48"]
        ev = evaluate_artifact(20, True, entries_from(stats, vals), W1, slot=self.slot, main_stat=self.main)
        self.assertEqual(ev.total_rolls, 8)

    def test_three_stat_plus4_per_stat_limit(self):
        vals = ["12.44", "3.89", "5.83", "6.48"]
        with self.assertRaises(ArtifactInputError):
            evaluate_artifact(4, True, entries_from(FOUR, vals), W1, slot=self.slot, main_stat=self.main)
        evaluate_artifact(4, False, entries_from(FOUR, vals), W1, slot=self.slot, main_stat=self.main)


class ScoringTests(unittest.TestCase):
    def peak(self, stat, weight):
        return weight * float(STATS_DB[stat]["rolls"][-1] / avg_roll(stat))

    def test_four_stat_potential_uses_present_stats(self):
        weights = {s: 0.0 for s in STATS_DB}
        weights["Крит. урон"] = 10.0
        weights["HP"] = 0.5
        stats = ["HP", "Защита", "HP %", "Защита %"]
        vals = [str(STATS_DB[s]["rolls"][0]) for s in stats]
        ev = evaluate_artifact(0, False, entries_from(stats, vals), weights, slot="Перо смерти", main_stat="Сила атаки")
        self.assertAlmostEqual(ev.max_possible_score - ev.current_score, 5 * self.peak("HP", 0.5), places=9)

    def test_main_stat_is_excluded_from_ideal(self):
        weights = {s: 1.0 for s in STATS_DB}
        stats = ["Крит. урон", "Шанс крит. попадания", "Сила атаки %", "Восст. энергии"]
        vals = [str(STATS_DB[s]["rolls"][0]) for s in stats]
        a = evaluate_artifact(0, False, entries_from(stats, vals), weights, slot="Цветок жизни", main_stat="HP")
        b = evaluate_artifact(0, False, entries_from(stats, vals), weights, slot="Перо смерти", main_stat="Сила атаки")
        # Both main stats are outside the chosen four substats here, so ideal remains the same.
        self.assertAlmostEqual(a.ideal_max_score, b.ideal_max_score, places=9)

    def test_three_stat_reveal_excludes_main(self):
        weights = {s: 0.0 for s in STATS_DB}
        weights["HP"] = 100.0
        weights["Крит. урон"] = 1.0
        stats = ["Защита", "HP %", "Восст. энергии"]
        vals = [str(STATS_DB[s]["rolls"][0]) for s in stats]
        ev = evaluate_artifact(0, True, entries_from(stats, vals), weights, slot="Цветок жизни", main_stat="HP")
        self.assertLess(ev.max_possible_score - ev.current_score, self.peak("HP", 100.0) * 5)

    def test_expected_is_not_above_best_case(self):
        rng = random.Random(7)
        for _ in range(300):
            is_3 = rng.random() < 0.5
            k = rng.randrange(6)
            level = 4 * k
            vec = rng.choice(sorted(all_vectors_by_events(is_3)[k]))
            stats = rng.sample(list(STATS_DB), len(vec))
            main = next(m for m in MAIN_STATS_BY_SLOT["Пески времени"] if m not in stats)
            weights = {s: rng.choice([0.0, 0.5, 1.0, 2.0]) for s in STATS_DB}
            vals = [str(value_for(s, n, rng)) for s, n in zip(stats, vec)]
            ev = evaluate_artifact(level, is_3, entries_from(stats, vals), weights, slot="Пески времени", main_stat=main)
            self.assertLessEqual(ev.expected_score, ev.max_possible_score + 1e-9)
            self.assertLessEqual(ev.current_score, ev.expected_score + 1e-9)


if __name__ == "__main__":
    unittest.main()
