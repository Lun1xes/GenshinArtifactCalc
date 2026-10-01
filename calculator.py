import json
import os
from datetime import datetime

import customtkinter as ctk

import good_adapter
from artifact_logic import (
    ARTIFACT_SLOTS,
    MAIN_STATS_BY_SLOT,
    STATS_DB,
    ArtifactInputError,
    describe_rolls,
    evaluate_artifact,
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


ROLE_PRESETS = {
    "Свой выбор (Ручной)": None,
    "Main DPS (Криты / Атака)": {
        "Крит. урон": 2.0,
        "Шанс крит. попадания": 2.0,
        "Сила атаки %": 1.0,
        "Восст. энергии": 1.0,
        "Мастерство стихий": 1.0,
        "Сила атаки": 0.5,
        "HP %": 0.0,
        "Защита %": 0.0,
        "HP": 0.0,
        "Защита": 0.0,
    },
    "HP Support (Чжун Ли, Е Лань)": {
        "HP %": 2.0,
        "Восст. энергии": 2.0,
        "HP": 1.0,
        "Крит. урон": 1.0,
        "Шанс крит. попадания": 1.0,
        "Сила атаки %": 0.0,
        "Защита %": 0.0,
        "Мастерство стихий": 0.0,
        "Сила атаки": 0.0,
        "Защита": 0.0,
    },
    "EM Reactor (Кадзуха, Нахида)": {
        "Мастерство стихий": 2.0,
        "Восст. энергии": 2.0,
        "Сила атаки %": 1.0,
        "HP %": 1.0,
        "Крит. урон": 0.5,
        "Шанс крит. попадания": 0.5,
        "Защита %": 0.0,
        "Сила атаки": 0.0,
        "HP": 0.0,
        "Защита": 0.0,
    },
    "DEF Tank (Итто, Альбедо)": {
        "Защита %": 2.0,
        "Крит. урон": 2.0,
        "Шанс крит. попадания": 2.0,
        "Защита": 1.0,
        "Восст. энергии": 1.0,
        "Сила атаки %": 0.0,
        "HP %": 0.0,
        "Мастерство стихий": 0.0,
        "Сила атаки": 0.0,
        "HP": 0.0,
    },
}

HISTORY_FILE = "artifact_history.json"


class ArtifactCalculatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Genshin Impact — Калькулятор и Анализатор Артефактов")
        self.geometry("1020x790")
        self.resizable(False, False)

        self.slot_var = ctk.StringVar(value="Пески времени")
        self.main_stat_var = ctk.StringVar(value="Мастерство стихий")
        self.preset_var = ctk.StringVar(value="Main DPS (Криты / Атака)")
        self.level_var = ctk.StringVar(value="+0")
        self.initial_stats_var = ctk.StringVar(value="4 сабстата")
        self.last_calculation = None
        self._calc_snapshot = None

        self._build_ui()
        self._update_main_stat_options(self.slot_var.get(), invalidate=False)
        self._apply_preset_selection(self.preset_var.get())

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="⚔️ Калькулятор Ценности & Потенциала Артефактов",
            font=("Arial", 22, "bold"),
        ).pack(pady=(15, 10))

        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=5)

        left_panel = ctk.CTkFrame(main_container, width=510)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=5)

        ctk.CTkLabel(
            left_panel, text="1. Тип и основной стат:", font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 2))

        slot_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        slot_frame.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(slot_frame, text="Тип:").pack(side="left", padx=(0, 5))
        self.slot_menu = ctk.CTkOptionMenu(
            slot_frame,
            values=list(ARTIFACT_SLOTS),
            variable=self.slot_var,
            command=self._on_slot_change,
            width=205,
        )
        self.slot_menu.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(slot_frame, text="Основной стат:").pack(side="left", padx=(0, 5))
        self.main_stat_menu = ctk.CTkOptionMenu(
            slot_frame,
            values=list(MAIN_STATS_BY_SLOT[self.slot_var.get()]),
            variable=self.main_stat_var,
            command=self._on_main_stat_change,
            width=215,
        )
        self.main_stat_menu.pack(side="left")

        ctk.CTkLabel(
            left_panel, text="2. Выберите роль персонажа:", font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 2))
        ctk.CTkOptionMenu(
            left_panel,
            values=list(ROLE_PRESETS.keys()),
            variable=self.preset_var,
            command=self._on_preset_change,
            width=470,
        ).pack(padx=15, pady=5)

        ctk.CTkLabel(
            left_panel, text="3. Состояние артефакта:", font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 2))
        state_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        state_frame.pack(fill="x", padx=15, pady=2)
        ctk.CTkLabel(state_frame, text="Уровень:").pack(side="left", padx=(0, 5))
        ctk.CTkOptionMenu(
            state_frame,
            values=["+0", "+4", "+8", "+12", "+16", "+20"],
            variable=self.level_var,
            command=lambda _: self._invalidate_calculation(),
            width=90,
        ).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(state_frame, text="Старт:").pack(side="left", padx=(0, 5))
        ctk.CTkOptionMenu(
            state_frame,
            values=["4 сабстата", "3 сабстата"],
            variable=self.initial_stats_var,
            command=lambda _: self._invalidate_calculation(),
            width=130,
        ).pack(side="left")

        ctk.CTkLabel(
            left_panel,
            text="4. Дополнительные характеристики (сабстаты):",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=15, pady=(12, 5))

        self.stat_widgets = []
        stat_names = list(STATS_DB)
        weight_options = [
            "2.0 (Высший)",
            "1.0 (Средний)",
            "0.5 (Низкий)",
            "0.0 (Бесполезно)",
        ]
        for i in range(4):
            row_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=4)
            combo = ctk.CTkComboBox(
                row_frame,
                values=stat_names,
                width=175,
                state="readonly",
                command=lambda choice, idx=i: self._on_stat_changed(idx, choice),
            )
            combo.set(stat_names[i])
            combo.pack(side="left", padx=(0, 8))
            entry = ctk.CTkEntry(row_frame, placeholder_text="Значение", width=95)
            entry.pack(side="left", padx=(0, 8))
            entry.bind("<KeyRelease>", lambda _e: self._invalidate_calculation())
            weight_combo = ctk.CTkOptionMenu(
                row_frame,
                values=weight_options,
                width=150,
                command=lambda _: self._invalidate_calculation(),
            )
            weight_combo.set("1.0 (Средний)" if i >= 2 else "2.0 (Высший)")
            weight_combo.pack(side="left")
            self.stat_widgets.append(
                {"stat_combo": combo, "entry": entry, "weight_combo": weight_combo}
            )

        ctk.CTkButton(
            left_panel,
            text="⚡ Рассчитать ценность и потенциал",
            font=("Arial", 14, "bold"),
            fg_color="#1f538d",
            hover_color="#14375e",
            height=40,
            command=self.calculate,
        ).pack(fill="x", padx=15, pady=(15, 10))

        right_panel = ctk.CTkFrame(main_container, width=450)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=5)
        ctk.CTkLabel(
            right_panel, text="📊 Результаты анализа", font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.rank_card = ctk.CTkFrame(right_panel, fg_color="#2b2b2b", corner_radius=10)
        self.rank_card.pack(fill="x", padx=15, pady=5)
        self.rank_label = ctk.CTkLabel(
            self.rank_card, text="Ранг: —", font=("Arial", 28, "bold"), text_color="#aaaaaa"
        )
        self.rank_label.pack(pady=10)
        self.current_score_label = ctk.CTkLabel(
            right_panel, text="Текущая ценность (PAV): —", font=("Arial", 14)
        )
        self.current_score_label.pack(anchor="w", padx=15, pady=3)
        self.potential_score_label = ctk.CTkLabel(
            right_panel, text="Потолок на +20 (PAV): —", font=("Arial", 14, "bold")
        )
        self.potential_score_label.pack(anchor="w", padx=15, pady=3)
        self.expected_score_label = ctk.CTkLabel(
            right_panel, text="Ожидаемо на +20 (PAV): —", font=("Arial", 13)
        )
        self.expected_score_label.pack(anchor="w", padx=15, pady=3)
        self.upgrades_info_label = ctk.CTkLabel(
            right_panel, text="Осталось проков: —", font=("Arial", 12), text_color="#aaaaaa"
        )
        self.upgrades_info_label.pack(anchor="w", padx=15, pady=2)
        self.result_textbox = ctk.CTkTextbox(right_panel, height=250, font=("Consolas", 12))
        self.result_textbox.pack(fill="both", expand=True, padx=15, pady=10)
        self.result_textbox.insert("1.0", "Введите характеристики артефакта и нажмите «Рассчитать».")

        action_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        action_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.save_btn = ctk.CTkButton(
            action_frame, text="💾 Сохранить", width=120, command=self.save_to_history, state="disabled"
        )
        self.save_btn.pack(side="left", padx=(0, 5))
        self.share_btn = ctk.CTkButton(
            action_frame,
            text="📋 Скопировать отчет",
            width=155,
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self.copy_share_card,
            state="disabled",
        )
        self.share_btn.pack(side="left", padx=(0, 5))
        self.good_btn = ctk.CTkButton(
            action_frame,
            text="📤 GOOD",
            width=90,
            fg_color="#00695c",
            hover_color="#004d40",
            command=self.open_good_transfer_dialog,
        )
        self.good_btn.pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            action_frame,
            text="📜 История",
            width=100,
            fg_color="#4a148c",
            hover_color="#311b92",
            command=self.open_history_window,
        ).pack(side="right")

    def _update_main_stat_options(self, slot, invalidate=True):
        options = list(MAIN_STATS_BY_SLOT[slot])
        current = self.main_stat_var.get()
        if current not in options:
            self.main_stat_var.set(options[0])
        self.main_stat_menu.configure(values=options)
        if len(options) == 1:
            self.main_stat_var.set(options[0])
            self.main_stat_menu.configure(state="disabled")
        else:
            self.main_stat_menu.configure(state="normal")
        if invalidate:
            self._invalidate_calculation()

    def _on_slot_change(self, choice):
        self._update_main_stat_options(choice, invalidate=True)
        # Пресетные веса остаются, но расчёт должен заново проверить допустимость статов.
        self._apply_preset_selection(self.preset_var.get(), invalidate=False)

    def _on_main_stat_change(self, _choice):
        self._invalidate_calculation()

    def _invalidate_calculation(self):
        self.last_calculation = None
        self._calc_snapshot = None
        self.save_btn.configure(text="💾 Сохранить", state="disabled")
        self.share_btn.configure(text="📋 Скопировать отчет", state="disabled")
        self.rank_label.configure(text="Ранг: —", text_color="#aaaaaa")
        self.current_score_label.configure(text="Текущая ценность (PAV): —")
        self.potential_score_label.configure(text="Потолок на +20 (PAV): —")
        self.expected_score_label.configure(text="Ожидаемо на +20 (PAV): —")
        self.upgrades_info_label.configure(text="Осталось проков: —")
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", "Введите характеристики артефакта и нажмите «Рассчитать».")

    def _input_snapshot(self):
        return (
            self.slot_var.get(),
            self.main_stat_var.get(),
            self.level_var.get(),
            self.initial_stats_var.get(),
            self.preset_var.get(),
            tuple(
                (w["stat_combo"].get(), w["entry"].get(), w["weight_combo"].get())
                for w in self.stat_widgets
            ),
        )

    def _result_is_current(self):
        if self.last_calculation is None:
            return False
        if self._calc_snapshot != self._input_snapshot():
            self._invalidate_calculation()
            return False
        return True

    def _show_message(self, text):
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", text)

    def _on_preset_change(self, choice):
        self._invalidate_calculation()
        self._apply_preset_selection(choice, invalidate=False)

    def _apply_preset_selection(self, choice, invalidate=False):
        preset_data = ROLE_PRESETS.get(choice)
        if preset_data is None:
            for w in self.stat_widgets:
                w["weight_combo"].configure(state="normal")
            return
        main_stat = self.main_stat_var.get()
        eligible = [s for s in STATS_DB if s != main_stat]
        ranked = sorted(
            (s for s in preset_data if s in eligible),
            key=lambda s: preset_data[s],
            reverse=True,
        )
        # Заполняем четыре строки уникальными и допустимыми сабстатами.
        ranked += [s for s in eligible if s not in ranked]
        for i, widget in enumerate(self.stat_widgets):
            stat_name = ranked[i]
            widget["stat_combo"].set(stat_name)
            self._update_widget_weight(widget, stat_name, preset_data)
        if invalidate:
            self._invalidate_calculation()

    def _on_stat_changed(self, idx, choice):
        self._invalidate_calculation()
        preset_data = ROLE_PRESETS.get(self.preset_var.get())
        if preset_data is not None:
            self._update_widget_weight(self.stat_widgets[idx], choice, preset_data)

    def _update_widget_weight(self, widget, stat_name, preset_data):
        weight_val = preset_data.get(stat_name, 0.0)
        if weight_val == 2.0:
            text = "2.0 (Высший)"
        elif weight_val == 1.0:
            text = "1.0 (Средний)"
        elif weight_val == 0.5:
            text = "0.5 (Низкий)"
        else:
            text = "0.0 (Бесполезно)"
        widget["weight_combo"].set(text)
        widget["weight_combo"].configure(state="disabled")

    def _collect_weights(self, role_name):
        preset = ROLE_PRESETS.get(role_name)
        if preset is not None:
            return dict(preset)
        weights = {s: 0.0 for s in STATS_DB}
        for w in self.stat_widgets:
            stat = w["stat_combo"].get()
            if stat in weights:
                weights[stat] = float(w["weight_combo"].get().split()[0])
        return weights

    def calculate(self):
        self._invalidate_calculation()
        level = int(self.level_var.get().replace("+", ""))
        is_3_stat = self.initial_stats_var.get() == "3 сабстата"
        slot = self.slot_var.get()
        main_stat = self.main_stat_var.get()
        role_name = self.preset_var.get()
        entries = []
        for i, widget in enumerate(self.stat_widgets):
            raw = widget["entry"].get().strip()
            if raw:
                entries.append((i + 1, widget["stat_combo"].get(), raw))

        try:
            ev = evaluate_artifact(
                level,
                is_3_stat,
                entries,
                self._collect_weights(role_name),
                slot=slot,
                main_stat=main_stat,
            )
        except ArtifactInputError as exc:
            self._show_message(f"❌ {exc}")
            return

        rank, color = self._get_rank(ev.potential_pct)
        self.rank_label.configure(text=f"Ранг: {rank}", text_color=color)
        self.current_score_label.configure(
            text=f"Текущая ценность (PAV): {ev.current_score:.1f} балл. ({ev.current_pct:.1f}%)"
        )
        self.potential_score_label.configure(
            text=f"Потолок на +20 (PAV, лучший случай): {ev.max_possible_score:.1f} балл. ({ev.potential_pct:.1f}%)"
        )
        self.expected_score_label.configure(
            text=f"Ожидаемо на +20 (PAV): {ev.expected_score:.1f} балл. ({ev.expected_pct:.1f}%)"
        )
        self.upgrades_info_label.configure(text=ev.upgrades_info)

        report_lines = [
            f"=== РАСЧЕТ АРТЕФАКТА ({self.level_var.get()}) ===",
            f"Тип: {slot}",
            f"Основной стат: {main_stat}",
            f"Роль: {role_name}",
            "[Игровая механика: дискретные роллы 5★ | PAV: собственная проектная эвристика]\n",
            f"Роллов всего: ровно {ev.total_rolls}",
        ]
        for stat, value in ev.substats.items():
            report_lines.append(f"• {stat}: {value:f} ({describe_rolls(ev.roll_counts[stat])})")
        report_lines.extend([
            "\n=== ПОТЕНЦИАЛ (PAV) ===",
            ev.upgrades_info,
            f"Текущий уровень качества: {ev.current_pct:.1f}%",
            f"Потолок на +20: {ev.potential_pct:.1f}% [{rank}]",
            f"Ожидаемо на +20: {ev.expected_pct:.1f}%",
        ])
        self._show_message("\n".join(report_lines))

        self.last_calculation = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "slot": slot,
            "main_stat": main_stat,
            "role": role_name,
            "level": self.level_var.get(),
            "rank": rank,
            "current_pct": round(ev.current_pct, 1),
            "potential_pct": round(ev.potential_pct, 1),
            "expected_pct": round(ev.expected_pct, 1),
            "substats": {k: float(v) for k, v in ev.substats.items()},
        }
        self._calc_snapshot = self._input_snapshot()
        self.save_btn.configure(text="💾 Сохранить", state="normal")
        self.share_btn.configure(state="normal")

    def _get_rank(self, pct):
        if pct >= 90.0:
            return "SSS", "#E040FB"
        if pct >= 80.0:
            return "SS", "#4488FF"
        if pct >= 70.0:
            return "S", "#44CC44"
        if pct >= 50.0:
            return "A", "#FFD700"
        if pct >= 30.0:
            return "B", "#FF8C00"
        return "C", "#FF4444"

    def _load_history(self) -> list:
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                return loaded if isinstance(loaded, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def save_to_history(self):
        if not self._result_is_current():
            return
        history = self._load_history()
        history.insert(0, self.last_calculation)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
        self.save_btn.configure(text="✅ Сохранено", state="disabled")

    def copy_share_card(self):
        if not self._result_is_current():
            return
        c = self.last_calculation
        stats_text = "\n".join(f"  • {k}: {v}" for k, v in c["substats"].items())
        card_text = (
            "⚔️ **Genshin Impact — Карточка Артефакта** ⚔️\n"
            f"🧩 Тип: {c['slot']}\n"
            f"🎯 Основной стат: {c['main_stat']}\n"
            f"🎯 Роль: {c['role']}\n"
            f"🔹 Уровень: {c['level']} | 🏆 Ранг потенциала: **{c['rank']}**\n"
            f"📊 Текущая ценность (PAV): {c['current_pct']}%\n"
            f"🚀 Потолок на +20: **{c['potential_pct']}%**\n"
            f"📈 Ожидаемо на +20: {c['expected_pct']}%\n"
            f"📜 Характеристики:\n{stats_text}\n"
            "───────────────\n"
            "Сгенерировано в Artifact Calculator"
        )
        self.clipboard_clear()
        self.clipboard_append(card_text)
        self.share_btn.configure(text="✅ Скопировано!")
        self.after(2000, lambda: self.share_btn.configure(text="📋 Скопировать отчет"))

    def load_artifact_from_good(self, parsed: good_adapter.ParsedArtifact):
        self.slot_var.set(parsed.slot)
        self._update_main_stat_options(parsed.slot, invalidate=False)
        self.main_stat_var.set(parsed.main_stat)

        lvl = parsed.level
        level_str = f"+{lvl}" if not str(lvl).startswith("+") else str(lvl)
        if level_str in ["+0", "+4", "+8", "+12", "+16", "+20"]:
            self.level_var.set(level_str)
        else:
            self.level_var.set("+0")

        if len(parsed.substats) <= 3 and parsed.level <= 4:
            self.initial_stats_var.set("3 сабстата")
        else:
            self.initial_stats_var.set("4 сабстата")

        for i, w in enumerate(self.stat_widgets):
            w["entry"].delete(0, "end")
            if i < len(parsed.substats):
                stat_name, val = parsed.substats[i]
                w["stat_combo"].set(stat_name)
                w["entry"].insert(0, str(val))
            else:
                w["entry"].insert(0, "")

        self._invalidate_calculation()
        self.calculate_artifact()

    def export_current_artifact_to_good(self) -> dict:
        level_raw = self.level_var.get().replace("+", "").strip()
        level = int(level_raw) if level_raw.isdigit() else 0
        substats = []
        for w in self.stat_widgets:
            val_str = w["entry"].get().strip().replace("%", "").replace(",", ".")
            if val_str:
                try:
                    val_dec = good_adapter.D(val_str)
                    substats.append({"stat": w["stat_combo"].get(), "value": val_dec})
                except Exception:
                    pass
        raw_art = {
            "slot": self.slot_var.get(),
            "main_stat": self.main_stat_var.get(),
            "level": level,
            "rarity": 5,
            "substats": substats,
        }
        return good_adapter.to_good_artifact(raw_art)

    def bulk_import_to_history(self, artifacts):
        history = self._load_history()
        for parsed in artifacts:
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "slot": parsed.slot,
                "main_stat": parsed.main_stat,
                "role": self.preset_var.get(),
                "level": f"+{parsed.level}",
                "rank": "GOOD",
                "current_pct": 0.0,
                "potential_pct": 0.0,
                "expected_pct": 0.0,
                "substats": {s: float(v) for s, v in parsed.substats},
                "set_key": parsed.set_key,
            }
            history.insert(0, entry)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

    def open_good_transfer_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("📤 GOOD Импорт / Экспорт")
        dialog.geometry("640x540")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Genshin Open Object Data (GOOD)", font=("Arial", 16, "bold")).pack(pady=(12, 5))

        info_lbl = ctk.CTkLabel(
            dialog,
            text="Вставьте GOOD JSON для импорта или выберите экспорт:",
            font=("Arial", 11),
            text_color="#aaaaaa",
        )
        info_lbl.pack(pady=(0, 5))

        textbox = ctk.CTkTextbox(dialog, width=600, height=330, font=("Consolas", 11))
        textbox.pack(padx=15, pady=5, fill="both", expand=True)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=10)

        def do_import():
            content = textbox.get("1.0", "end").strip()
            if not content:
                info_lbl.configure(text="❌ Поле ввода пусто!", text_color="#ff5252")
                return
            try:
                parsed_list = good_adapter.from_good_json(content)
                if not parsed_list:
                    info_lbl.configure(text="❌ Артефакты не найдены в JSON", text_color="#ff5252")
                    return
                self.load_artifact_from_good(parsed_list[0])
                if len(parsed_list) > 1:
                    self.bulk_import_to_history(parsed_list)
                    info_lbl.configure(
                        text=f"✅ Загружен 1 артефакт, {len(parsed_list)} сохранено в историю!",
                        text_color="#69f0ae",
                    )
                else:
                    info_lbl.configure(text="✅ Артефакт успешно загружен в калькулятор!", text_color="#69f0ae")
            except Exception as e:
                info_lbl.configure(text=f"❌ Ошибка импорта: {e}", text_color="#ff5252")

        def do_export_active():
            try:
                good_obj = self.export_current_artifact_to_good()
                json_str = json.dumps(good_obj, indent=2, ensure_ascii=False)
                textbox.delete("1.0", "end")
                textbox.insert("1.0", json_str)
                self.clipboard_clear()
                self.clipboard_append(json_str)
                info_lbl.configure(text="✅ Текущий артефакт экспортирован и скопирован в буфер!", text_color="#69f0ae")
            except Exception as e:
                info_lbl.configure(text=f"❌ Ошибка экспорта: {e}", text_color="#ff5252")

        def do_export_history():
            try:
                history = self._load_history()
                if not history:
                    info_lbl.configure(text="⚠️ История пуста!", text_color="#ffd700")
                    return
                good_list = []
                for item in history:
                    subs = [{"stat": k, "value": v} for k, v in item.get("substats", {}).items()]
                    raw_art = {
                        "slot": item.get("slot", "Перо смерти"),
                        "main_stat": item.get("main_stat", "Сила атаки"),
                        "level": int(str(item.get("level", "0")).replace("+", "") or 0),
                        "rarity": 5,
                        "substats": subs,
                        "set_key": item.get("set_key", ""),
                    }
                    try:
                        good_list.append(good_adapter.to_good_artifact(raw_art))
                    except Exception:
                        pass
                json_str = good_adapter.to_good_json(good_list)
                textbox.delete("1.0", "end")
                textbox.insert("1.0", json_str)
                self.clipboard_clear()
                self.clipboard_append(json_str)
                info_lbl.configure(text=f"✅ {len(good_list)} артефактов из истории скопированы в буфер!", text_color="#69f0ae")
            except Exception as e:
                info_lbl.configure(text=f"❌ Ошибка экспорта истории: {e}", text_color="#ff5252")

        ctk.CTkButton(btn_frame, text="📥 Импортировать", command=do_import, width=130, fg_color="#1565c0").pack(
            side="left", padx=(0, 5)
        )
        ctk.CTkButton(btn_frame, text="📋 Экспорт текущего", command=do_export_active, width=150, fg_color="#2e7d32").pack(
            side="left", padx=(0, 5)
        )
        ctk.CTkButton(btn_frame, text="📜 Экспорт истории", command=do_export_history, width=140, fg_color="#4a148c").pack(
            side="left", padx=(0, 5)
        )
        ctk.CTkButton(btn_frame, text="Закрыть", command=dialog.destroy, width=90, fg_color="#424242").pack(side="right")

    def open_history_window(self):
        history_win = ctk.CTkToplevel(self)
        history_win.title("📜 История артефактов")
        history_win.geometry("650x520")
        history_win.grab_set()
        ctk.CTkLabel(history_win, text="Сохраненные артефакты", font=("Arial", 16, "bold")).pack(pady=10)
        scroll_frame = ctk.CTkScrollableFrame(history_win, width=600, height=380)
        scroll_frame.pack(padx=15, pady=5, fill="both", expand=True)

        if not os.path.exists(HISTORY_FILE):
            ctk.CTkLabel(scroll_frame, text="История пуста.").pack(pady=20)
            return
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (OSError, json.JSONDecodeError):
            history = []
        if not history:
            ctk.CTkLabel(scroll_frame, text="История пуста.").pack(pady=20)
            return

        for item in history:
            card = ctk.CTkFrame(scroll_frame)
            card.pack(fill="x", pady=4, padx=5)
            slot = item.get("slot", "не указан")
            main_stat = item.get("main_stat", "не указан")
            title_str = f"[{item.get('rank', '?')}] {slot} / {main_stat} — {item.get('potential_pct', '?')}%"
            ctk.CTkLabel(card, text=title_str, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(5, 2))
            stats_str = ", ".join(f"{k}: {v}" for k, v in item.get("substats", {}).items())
            ctk.CTkLabel(card, text=stats_str, font=("Arial", 10), text_color="#aaaaaa").pack(anchor="w", padx=10, pady=(0, 5))

        def clear_history():
            try:
                if os.path.exists(HISTORY_FILE):
                    os.remove(HISTORY_FILE)
            finally:
                history_win.destroy()

        ctk.CTkButton(
            history_win,
            text="🗑️ Очистить историю",
            fg_color="#c62828",
            hover_color="#8e0000",
            command=clear_history,
        ).pack(pady=10)


if __name__ == "__main__":
    app = ArtifactCalculatorApp()
    app.mainloop()
