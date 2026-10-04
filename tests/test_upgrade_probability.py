"""Unit tests for upgrade_probability.py module."""
import unittest

from upgrade_probability import calculate_upgrade_forecast


class TestUpgradeProbability(unittest.TestCase):
    def test_plus20_returns_zero_remaining(self):
        res = calculate_upgrade_forecast(
            slot="Цветок жизни",
            main_stat="HP",
            current_substats={"Крит. урон": "21.0", "Шанс крит. попадания": "7.0"},
            level=20,
        )
        self.assertEqual(res.remaining_rolls, 0)
        self.assertEqual(res.current_level, 20)

    def test_plus0_god_piece_high_potential(self):
        # Piece with dual crit at level 0
        res = calculate_upgrade_forecast(
            slot="Перо смерти",
            main_stat="Сила атаки",
            current_substats={
                "Крит. урон": "7.77",
                "Шанс крит. попадания": "3.89",
                "Сила атаки %": "5.83",
                "Восст. энергии": "6.48",
            },
            level=0,
        )
        self.assertEqual(res.remaining_rolls, 5)
        self.assertGreater(res.prob_s_plus, 60.0)
        self.assertIn("Высокий потенциал", res.verdict)
        self.assertGreater(res.expected_cv, 20.0)

    def test_plus0_trash_piece_low_potential(self):
        # Piece with all flat dead stats
        res = calculate_upgrade_forecast(
            slot="Перо смерти",
            main_stat="Сила атаки",
            current_substats={
                "HP": "209",
                "Защита": "16",
                "Защита %": "5.1",
            },
            level=0,
        )
        self.assertEqual(res.remaining_rolls, 5)
        self.assertLess(res.prob_ss_plus, 15.0)
        self.assertIn("Низкий потенциал", res.verdict)


if __name__ == "__main__":
    unittest.main()
