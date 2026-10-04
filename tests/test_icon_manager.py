"""Tests for icon_manager module."""
import os
import unittest

from icon_manager import IconManager, icon_manager


class TestIconManager(unittest.TestCase):
    def test_singleton(self):
        mgr1 = IconManager()
        mgr2 = IconManager()
        self.assertIs(mgr1, mgr2)
        self.assertIs(mgr1, icon_manager)

    def test_element_color(self):
        self.assertEqual(icon_manager.get_element_color("Пиро"), "#ff5252")
        self.assertEqual(icon_manager.get_element_color("Гидро"), "#00e5ff")
        self.assertEqual(icon_manager.get_element_color("Гео"), "#ffd700")

    def test_find_character_meta(self):
        furina = icon_manager.find_character_meta("Фурина")
        self.assertIsNotNone(furina)
        self.assertEqual(furina["name_ru"], "Фурина")
        self.assertEqual(furina["element"], "Гидро")

        raiden = icon_manager.find_character_meta("Райдэн")
        self.assertIsNotNone(raiden)
        self.assertEqual(raiden["element"], "Электро")

    def test_get_character_avatar_placeholder(self):
        img, border_color = icon_manager.get_character_avatar("Фурина", size=(48, 48))
        self.assertIsNotNone(img)
        self.assertEqual(border_color, "#00e5ff")


if __name__ == "__main__":
    unittest.main()
