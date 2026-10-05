import json
import os
import sys
import tempfile
import types
import unittest


class FakeVar:
    def __init__(self, *args, **kwargs):
        self._v = kwargs.get("value", args[0] if args else "")

    def get(self):
        return self._v

    def set(self, value):
        self._v = value


class FakeWidget:
    def __init__(self, *args, **kwargs):
        if kwargs.get("border_color") == "transparent":
            raise ValueError("transparency is not allowed for this attribute")
        self.opts = dict(kwargs)
        self.command = kwargs.get("command")
        self.bindings = {}
        self._text = str(kwargs.get("text", ""))
        self._last_child_ids = {}
        self._w = ".fake"
        self.children = {}

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return lambda *a, **k: None

    def configure(self, **kw):
        self.opts.update(kw)
        if "text" in kw:
            self._text = str(kw["text"])

    def cget(self, key):
        if key == "text":
            return self._text
        return self.opts.get(key, "")

    def bind(self, event, cb, add=None):
        self.bindings[event] = cb

    def fire(self, event):
        self.bindings[event](types.SimpleNamespace())

    def get(self, *args):
        return self._text

    def set(self, value):
        self._text = value

    def insert(self, idx, text):
        self._text = str(text) + self._text

    def delete(self, *args):
        self._text = ""

    def winfo_children(self):
        return []

    def winfo_exists(self):
        return True

    def add(self, *args, **kwargs):
        return FakeWidget()


class FakeApp(FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app_title = ""
        self.clipboard = []

    def title(self, *args):
        if args:
            self._app_title = str(args[0])
        return self._app_title

    def clipboard_clear(self):
        self.clipboard = []

    def clipboard_append(self, text):
        self.clipboard.append(text)

    def clipboard_get(self):
        return "".join(self.clipboard)

    def bind_all(self, sequence, func=None, add=None):
        self.bindings[sequence] = func

    def after(self, ms, fn):
        if callable(fn):
            fn()
        return None


def install_stub():
    ctk = types.ModuleType("customtkinter")
    ctk.set_appearance_mode = lambda *_: None
    ctk.set_default_color_theme = lambda *_: None
    ctk.StringVar = FakeVar
    ctk.IntVar = FakeVar
    ctk.CTk = FakeApp
    for name in (
        "CTkFrame", "CTkLabel", "CTkOptionMenu", "CTkComboBox", "CTkEntry",
        "CTkButton", "CTkTextbox", "CTkToplevel", "CTkScrollableFrame", "CTkTabview",
        "CTkProgressBar", "CTkSegmentedButton", "CTkRadioButton", "CTkImage",
    ):
        setattr(ctk, name, type(name, (FakeWidget,), {}))
    sys.modules["customtkinter"] = ctk


install_stub()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calculator  # noqa: E402

FOUR = ["Крит. урон", "Шанс крит. попадания", "Сила атаки %", "Восст. энергии"]
GOOD = ["7.77", "3.89", "5.83", "6.48"]


class AppStateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        calculator.HISTORY_FILE = os.path.join(self._tmp.name, "hist.json")
        self.app = calculator.ArtifactCalculatorApp()

    def tearDown(self):
        self._tmp.cleanup()

    def fill(self, values, stats=FOUR, level="+0", start="4 сабстата", preset=None):
        a = self.app
        a.level_var.set(level)
        a.initial_stats_var.set(start)
        if preset:
            a.preset_var.set(preset)
        for i, w in enumerate(a.stat_widgets):
            w["entry"].delete(0, "end")
            if i < len(values):
                w["stat_combo"].set(stats[i])
                w["entry"].insert(0, values[i])

    def texts(self):
        return self.app.result_textbox._text

    def assert_no_result(self):
        self.assertIsNone(self.app.last_calculation)
        self.assertIsNone(self.app._calc_snapshot)
        self.assertEqual(self.app.save_btn.opts.get("state"), "disabled")
        self.assertEqual(self.app.share_btn.opts.get("state"), "disabled")

    def test_successful_calculation(self):
        self.fill(GOOD)
        self.app.calculate()
        self.assertIsNotNone(self.app.last_calculation)
        self.assertEqual(self.app.last_calculation["main_stat"], "Мастерство стихий")
        self.assertEqual(self.app.last_calculation["slot"], "Пески времени")
        self.assertEqual(self.app.save_btn.opts["state"], "normal")
        self.assertEqual(self.app.share_btn.opts["state"], "normal")
        self.assertIn("Основной стат: Мастерство стихий", self.texts())

    def test_main_stat_change_invalidates(self):
        self.fill(GOOD)
        self.app.calculate()
        self.app.main_stat_var.set("Восст. энергии")
        # Simulate a missed UI event; snapshot must still reject stale Save/Copy.
        self.app.save_to_history()
        self.app.copy_share_card()
        self.assert_no_result()

    def test_slot_change_invalidates_and_updates_main_pool(self):
        self.fill(GOOD)
        self.app.calculate()
        self.app.slot_var.set("Цветок жизни")
        self.app._on_slot_change("Цветок жизни")
        self.assertEqual(self.app.main_stat_var.get(), "HP")
        self.assertEqual(self.app.main_stat_menu.opts.get("state"), "disabled")
        self.assert_no_result()

    def test_main_stat_equals_substat_rejected(self):
        self.app.main_stat_var.set("Сила атаки %")
        self.fill(["5.83", "7.77", "19.45", "6.48"], stats=["Сила атаки %", "Крит. урон", "Сила атаки", "Восст. энергии"])
        self.app.calculate()
        self.assertIn("основной стат", self.texts())
        self.assert_no_result()

    def test_three_stat_plus0_with_four_fields_blocked(self):
        self.fill(GOOD, start="3 сабстата")
        self.app.calculate()
        self.assertIn("ровно 3 поля", self.texts())
        self.assert_no_result()

    def test_failed_recalculation_cannot_save_or_copy_old_result(self):
        self.fill(GOOD)
        self.app.calculate()
        entry = self.app.stat_widgets[0]["entry"]
        entry.delete()
        entry.insert(0, "7.7")
        entry.fire("<KeyRelease>")
        self.app.calculate()
        self.app.save_to_history()
        self.app.copy_share_card()
        self.assertFalse(os.path.exists(calculator.HISTORY_FILE))
        self.assertEqual(self.app.clipboard, [])
        self.assert_no_result()

    def test_missed_event_snapshot_blocks_stale_save(self):
        self.fill(GOOD)
        self.app.calculate()
        self.app.stat_widgets[0]["entry"].set("6.99")
        self.app.save_to_history()
        self.assertFalse(os.path.exists(calculator.HISTORY_FILE))
        self.assert_no_result()

    def test_duplicate_stats_blocked(self):
        self.fill(GOOD, stats=[FOUR[0], FOUR[0], FOUR[2], FOUR[3]])
        self.app.calculate()
        self.assertIn("повторно", self.texts())
        self.assert_no_result()

    def test_bad_input_blocked(self):
        for bad in ("abc", "-3", "1e2", "NaN", "7.7", "99999"):
            with self.subTest(bad=bad):
                self.fill([bad, "3.89", "5.83", "6.48"])
                self.app.calculate()
                self.assertIn("❌", self.texts())
                self.assert_no_result()

    def test_manual_weights_do_not_crash(self):
        self.fill(GOOD, preset="Свой выбор (Ручной)")
        self.app.calculate()
        self.assertIsNotNone(self.app.last_calculation)

    def test_save_and_copy_after_success(self):
        self.fill(GOOD)
        self.app.calculate()
        self.app.save_to_history()
        self.assertTrue(os.path.exists(calculator.HISTORY_FILE))
        with open(calculator.HISTORY_FILE, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data[0]["slot"], "Пески времени")
        self.assertEqual(data[0]["main_stat"], "Мастерство стихий")
        self.app.copy_share_card()
        self.assertEqual(len(self.app.clipboard), 1)
        self.assertIn("Основной стат: Мастерство стихий", self.app.clipboard[0])

    def test_history_window_handles_new_record(self):
        self.fill(GOOD)
        self.app.calculate()
        self.app.save_to_history()
        self.app.open_history_window()

    def test_readonly_stat_combos(self):
        for w in self.app.stat_widgets:
            self.assertEqual(w["stat_combo"].opts.get("state"), "readonly")


if __name__ == "__main__":
    unittest.main()
