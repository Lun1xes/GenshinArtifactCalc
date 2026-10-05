"""Forecast and analysis panel for artifact ratings, upgrade probabilities,
character compatibility, build recommendations, and alternative carrier suggestions.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple
import customtkinter as ctk

from ...artifact_logic import (
    evaluate_artifact,
    ArtifactInputError,
    get_rank,
    ArtifactEvaluation,
    SLOT_EMOJI,
)
from ...character_builds import (
    CHARACTER_BUILDS,
    get_unique_character_names,
    get_builds_for_character,
    evaluate_artifact_for_build,
    find_top_matching_characters,
    CharacterBuild,
    SET_NAME_TO_KEY,
)
from ...upgrade_probability import calculate_upgrade_forecast, UpgradeForecastResult
from ...icon_manager import icon_manager
from ..theme import (
    ThemeColors,
    FONTS,
    METRICS,
    card_style,
    panel_style,
    button_primary_style,
    button_secondary_style,
    button_accent_cyan_style,
    progress_bar_style,
    get_element_color,
    get_compatibility_color,
)

# Standard history path
DEFAULT_HISTORY_FILE = "artifact_history.json"


class ForecastPanel(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        on_fit_character: Optional[Callable[[str], None]] = None,
        on_save_history: Optional[Callable[[dict, dict], None]] = None,
        **kwargs,
    ):
        kwargs.setdefault("fg_color", ThemeColors.BG_CARD)
        kwargs.setdefault("corner_radius", METRICS["corner_radius_card"])
        super().__init__(master, **kwargs)
        
        self.on_fit_character = on_fit_character
        self.on_save_history = on_save_history
        
        self.artifact_data: Optional[dict] = None
        self.last_eval: Optional[ArtifactEvaluation] = None
        self.last_forecast: Optional[UpgradeForecastResult] = None
        
        # Character & Role Selection
        self.char_var = ctk.StringVar(value="(Выберите персонажа)")
        self.role_var = ctk.StringVar(value="(Выберите билд)")
        self.selected_build: Optional[CharacterBuild] = None
        
        self._build_ui()

    def _build_ui(self):
        # Title
        ctk.CTkLabel(
            self,
            text="ШАГ 4: Оценка и Прогноз (+20)",
            font=FONTS["header"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # --- SECTION: Target Build & Avatar ---
        char_card = ctk.CTkFrame(self, **card_style(alt=True))
        char_card.pack(fill="x", padx=10, pady=5)

        # Avatar and selectors row
        sel_row = ctk.CTkFrame(char_card, fg_color="transparent")
        sel_row.pack(fill="x", padx=8, pady=8)

        # Avatar image label
        self.avatar_lbl = ctk.CTkLabel(sel_row, text="", width=48, height=48)
        self.avatar_lbl.pack(side="left", padx=(0, 10))

        # Dropdowns column
        menus_col = ctk.CTkFrame(sel_row, fg_color="transparent")
        menus_col.pack(side="left", fill="x", expand=True)

        self.char_menu = ctk.CTkOptionMenu(
            menus_col,
            values=["(Выберите персонажа)"] + get_unique_character_names(),
            variable=self.char_var,
            command=self._on_char_change,
            fg_color=ThemeColors.BG_INPUT,
            button_color=ThemeColors.BG_CARD,
            button_hover_color=ThemeColors.BG_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY,
            dropdown_fg_color=ThemeColors.BG_CARD,
            font=FONTS["body_bold"],
        )
        self.char_menu.pack(fill="x", pady=(0, 4))

        self.role_menu = ctk.CTkOptionMenu(
            menus_col,
            values=["(Выберите билд)"],
            variable=self.role_var,
            command=self._on_role_change,
            fg_color=ThemeColors.BG_INPUT,
            button_color=ThemeColors.BG_CARD,
            button_hover_color=ThemeColors.BG_HOVER,
            text_color=ThemeColors.TEXT_MUTED,
            dropdown_fg_color=ThemeColors.BG_CARD,
            font=FONTS["body"],
        )
        self.role_menu.pack(fill="x")

        # Build Details info card
        self.build_info_lbl = ctk.CTkLabel(
            char_card,
            text="Выберите героя для проверки рекомендаций и совместимости.",
            font=FONTS["small"],
            text_color=ThemeColors.TEXT_MUTED,
            wraplength=380,
            justify="left",
            anchor="w",
        )
        self.build_info_lbl.pack(fill="x", padx=10, pady=(0, 8))

        # --- SECTION: Score & Rank Metrics ---
        metrics_card = ctk.CTkFrame(self, **card_style())
        metrics_card.pack(fill="x", padx=10, pady=5)

        rank_row = ctk.CTkFrame(metrics_card, fg_color="transparent")
        rank_row.pack(fill="x", padx=10, pady=8)

        # Large Rank Badge
        self.rank_lbl = ctk.CTkLabel(
            rank_row,
            text="?",
            font=FONTS["display"],
            text_color=ThemeColors.TEXT_MUTED,
            width=70,
        )
        self.rank_lbl.pack(side="left", padx=(5, 15))

        # Metrics text column
        m_col = ctk.CTkFrame(rank_row, fg_color="transparent")
        m_col.pack(side="left", fill="x", expand=True)

        self.score_lbl = ctk.CTkLabel(
            m_col,
            text="Рейтинг: 0.0%",
            font=FONTS["title"],
            text_color=ThemeColors.TEXT_PRIMARY,
            anchor="w",
        )
        self.score_lbl.pack(fill="x")

        self.cv_lbl = ctk.CTkLabel(
            m_col,
            text="Crit Value (CV): 0.0",
            font=FONTS["body_bold"],
            text_color=ThemeColors.PURPLE,
            anchor="w",
        )
        self.cv_lbl.pack(fill="x")

        # --- SECTION: Upgrade Forecast (+20) ---
        forecast_card = ctk.CTkFrame(self, **card_style(alt=True))
        forecast_card.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            forecast_card,
            text="Прогноз докачки до +20 (Математика AnimeGameData):",
            font=FONTS["header"],
            text_color=ThemeColors.CYAN,
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(8, 4))

        self.progress_bar = ctk.CTkProgressBar(forecast_card, **progress_bar_style(ThemeColors.CYAN))
        self.progress_bar.pack(fill="x", padx=10, pady=4)
        self.progress_bar.set(0)

        self.prob_details_lbl = ctk.CTkLabel(
            forecast_card,
            text="Шанс S-тира (>70%): 0.0%\nШанс SS-тира (>80%): 0.0%",
            font=FONTS["small"],
            text_color=ThemeColors.TEXT_MUTED,
            justify="left",
            anchor="w",
        )
        self.prob_details_lbl.pack(fill="x", padx=10, pady=2)

        self.advice_lbl = ctk.CTkLabel(
            forecast_card,
            text="Вердикт: Введите характеристики артефакта",
            font=FONTS["body_bold"],
            text_color=ThemeColors.TEXT_MUTED,
            wraplength=380,
            justify="left",
            anchor="w",
        )
        self.advice_lbl.pack(fill="x", padx=10, pady=(4, 8))

        # --- SECTION: Compatibility & Top Alternative Carriers ---
        self.compat_card = ctk.CTkFrame(self, **card_style())
        self.compat_card.pack(fill="x", padx=10, pady=5)

        self.compat_verdict_lbl = ctk.CTkLabel(
            self.compat_card,
            text="Совместимость с выбранным героем: -",
            font=FONTS["body_bold"],
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
        )
        self.compat_verdict_lbl.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            self.compat_card,
            text="Кому ещё подойдёт этот артефакт (Топ носители):",
            font=FONTS["small_bold"],
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(4, 2))

        self.carriers_container = ctk.CTkFrame(self.compat_card, fg_color="transparent")
        self.carriers_container.pack(fill="x", padx=8, pady=(0, 8))

        # --- SECTION: Action Buttons ---
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(10, 15))

        save_btn = ctk.CTkButton(
            btn_row,
            text="💾 В историю",
            height=34,
            command=self.save_to_history,
            **button_primary_style(),
        )
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        share_btn = ctk.CTkButton(
            btn_row,
            text="📋 Копировать отчёт",
            height=34,
            command=self.copy_share_card,
            **button_accent_cyan_style(),
        )
        share_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Initial Avatar Placeholder
        self._update_avatar_display()

    def _update_avatar_display(self):
        char = self.char_var.get()
        if char == "(Выберите персонажа)" or not char:
            self.avatar_lbl.configure(text="👤", image=None)
            return

        def on_avatar_ready(img, border_color):
            def apply_img():
                if self.winfo_exists() and hasattr(self, "avatar_lbl") and self.avatar_lbl.winfo_exists():
                    try:
                        self.avatar_lbl.configure(image=img, text="")
                    except Exception:
                        pass
            try:
                self.after(0, apply_img)
            except Exception:
                pass

        img, b_col = icon_manager.get_character_avatar(char, size=(48, 48), on_ready_cb=on_avatar_ready)
        if img:
            self.avatar_lbl.configure(image=img, text="")
        else:
            self.avatar_lbl.configure(text="👤", image=None)

    def _on_char_change(self, choice: str):
        if choice == "(Выберите персонажа)":
            self.role_menu.configure(values=["(Выберите билд)"])
            self.role_var.set("(Выберите билд)")
            self.selected_build = None
            self.build_info_lbl.configure(text="Выберите героя для проверки рекомендаций и совместимости.")
        else:
            builds = get_builds_for_character(choice)
            role_names = [b.role for b in builds] if builds else ["(Нет билдов)"]
            self.role_menu.configure(values=role_names)
            self.role_var.set(role_names[0] if role_names else "(Выберите билд)")
            self.selected_build = builds[0] if builds else None
            self._update_build_info_display()

        self._update_avatar_display()
        self._recalculate()

    def _on_role_change(self, choice: str):
        char = self.char_var.get()
        builds = get_builds_for_character(char)
        self.selected_build = next((b for b in builds if b.role == choice), None)
        self._update_build_info_display()
        self._recalculate()

    def _update_build_info_display(self):
        if not self.selected_build:
            self.build_info_lbl.configure(text="")
            return

        b = self.selected_build
        sets_txt = ", ".join(b.best_sets[:2]) if b.best_sets else "Любые"
        weapons_txt = ", ".join(b.top_weapon_names[:3]) if b.top_weapon_names else "Любое"
        
        info = (
            f"✦ Сеты: {sets_txt}\n"
            f"✦ Оружие: {weapons_txt}\n"
            f"✦ Заметка: {b.notes if b.notes else 'Базовый мета-билд'}"
        )
        self.build_info_lbl.configure(text=info)

    def set_selected_character(self, character_display_name: str):
        """Set active character from external view or try-on click."""
        clean_name = character_display_name.split("(")[0].strip()
        names = get_unique_character_names()
        matched = next((n for n in names if clean_name.lower() in n.lower() or n.lower() in clean_name.lower()), None)
        if matched:
            self.char_var.set(matched)
            self._on_char_change(matched)

    def update_forecast(self, artifact_data: dict):
        self.artifact_data = artifact_data
        self._recalculate()

    def _recalculate(self):
        if not self.artifact_data:
            return

        slot = self.artifact_data.get("slot", "Цветок жизни")
        set_name = self.artifact_data.get("set", "(Не выбран)")
        main_stat = self.artifact_data.get("main_stat", "HP")
        level = self.artifact_data.get("level", 20)
        substats = self.artifact_data.get("substats", [])

        if not substats:
            self._reset_ui("Введите сабстаты для оценки")
            return

        # Determine weights
        if self.selected_build:
            weights = dict(self.selected_build.substat_weights)
        else:
            weights = {
                "Крит. урон": 2.0,
                "Шанс крит. попадания": 2.0,
                "Сила атаки %": 1.0,
                "Восст. энергии": 0.5,
            }

        entries = [(i + 1, s, str(v)) for i, (s, v) in enumerate(substats)]
        is_3_stat = len(substats) <= 3 and level <= 4

        try:
            # 1. Artifact Evaluation
            ev = evaluate_artifact(level, is_3_stat, entries, weights, slot=slot, main_stat=main_stat)
            self.last_eval = ev
            rank, color = get_rank(ev.potential_pct)

            self.rank_lbl.configure(text=rank, text_color=color)
            self.score_lbl.configure(text=f"Рейтинг: {ev.potential_pct:.1f}%")

            # 2. Upgrade Forecast
            curr_subs_dict = {s: v for s, v in substats}
            forecast = calculate_upgrade_forecast(
                slot=slot,
                main_stat=main_stat,
                current_substats=curr_subs_dict,
                level=level,
                substat_weights=weights,
            )
            self.last_forecast = forecast

            # Progress Bar & Probabilities
            expected_pct = min(forecast.expected_pav / 100.0, 1.0)
            self.progress_bar.set(expected_pct)

            self.cv_lbl.configure(text=f"Crit Value (CV): {forecast.expected_cv:.1f}")
            self.prob_details_lbl.configure(
                text=(
                    f"Шанс S-тира (≥70%): {forecast.prob_s_plus:.1f}%\n"
                    f"Шанс SS-тира (≥80%): {forecast.prob_ss_plus:.1f}%"
                )
            )
            self.advice_lbl.configure(text=f"Вердикт: {forecast.advice}", text_color=color)

            # 3. Compatibility Evaluation
            if self.selected_build:
                good_key = SET_NAME_TO_KEY.get(set_name, None)
                compat_score = evaluate_artifact_for_build(
                    slot=slot,
                    main_stat=main_stat,
                    substats=curr_subs_dict,
                    build=self.selected_build,
                    set_key=good_key,
                )
                if compat_score >= 85:
                    verdict, v_col = "⭐ Идеально", ThemeColors.GOLD
                elif compat_score >= 70:
                    verdict, v_col = "✅ Отлично", ThemeColors.GREEN
                elif compat_score >= 50:
                    verdict, v_col = "⚠️ Приемлемо", ThemeColors.YELLOW_WARN
                else:
                    verdict, v_col = "❌ Не подходит", ThemeColors.RED
                    
                self.compat_verdict_lbl.configure(
                    text=f"Совместимость с {self.selected_build.name}: {verdict} ({compat_score:.0f}%)",
                    text_color=v_col,
                )
            else:
                self.compat_verdict_lbl.configure(
                    text="Совместимость: Выберите персонажа",
                    text_color=ThemeColors.TEXT_MUTED,
                )

            # 4. Top Alternative Carriers
            self._update_alternative_carriers(slot, main_stat, curr_subs_dict)

        except ArtifactInputError as e:
            self._reset_ui(str(e))
        except Exception as e:
            self._reset_ui(f"Ошибка расчета: {str(e)}")

    def _update_alternative_carriers(self, slot: str, main_stat: str, substats: dict):
        for w in self.carriers_container.winfo_children():
            w.destroy()

        matches = find_top_matching_characters(
            slot=slot,
            main_stat=main_stat,
            substats=substats,
            top_n=3,
        )

        if not matches:
            ctk.CTkLabel(
                self.carriers_container,
                text="Подходящих персонажей не найдено",
                font=FONTS["small"],
                text_color=ThemeColors.TEXT_MUTED,
            ).pack(anchor="w", padx=5, pady=2)
            return

        for build, score in matches:
            row = ctk.CTkFrame(self.carriers_container, fg_color=ThemeColors.BG_CARD_ALT, corner_radius=6)
            row.pack(fill="x", pady=2)

            elem_col = get_element_color(build.element)
            name_lbl = ctk.CTkLabel(
                row,
                text=f" {build.name} ({build.role})",
                font=FONTS["small_bold"],
                text_color=elem_col,
                anchor="w",
            )
            name_lbl.pack(side="left", padx=5, pady=3, fill="x", expand=True)

            score_lbl = ctk.CTkLabel(
                row,
                text=f"{score:.0f}%",
                font=FONTS["small"],
                text_color=ThemeColors.TEXT_MUTED,
            )
            score_lbl.pack(side="left", padx=5)

            fit_btn = ctk.CTkButton(
                row,
                text="Примерить",
                width=75,
                height=22,
                font=FONTS["caption"],
                command=lambda b=build: self._handle_fit_click(b.name),
                **button_accent_cyan_style(),
            )
            fit_btn.pack(side="right", padx=5, pady=3)

    def _handle_fit_click(self, char_name: str):
        self.set_selected_character(char_name)
        if self.on_fit_character:
            self.on_fit_character(char_name)

    def _reset_ui(self, message: str):
        self.rank_lbl.configure(text="?", text_color=ThemeColors.TEXT_MUTED)
        self.score_lbl.configure(text="Рейтинг: 0.0%")
        self.cv_lbl.configure(text="Crit Value: 0.0")
        self.progress_bar.set(0)
        self.prob_details_lbl.configure(text="Шанс S-тира: 0.0%\nШанс SS-тира: 0.0%")
        self.advice_lbl.configure(text=message, text_color=ThemeColors.RED)
        self.compat_verdict_lbl.configure(text="Совместимость: -", text_color=ThemeColors.TEXT_MUTED)
        for w in self.carriers_container.winfo_children():
            w.destroy()

    def save_to_history(self):
        """Persist current artifact into artifact history."""
        if not self.artifact_data or not self.last_eval:
            return

        from ...calculator import HISTORY_FILE
        history_path = HISTORY_FILE if hasattr(self, "history_file") else getattr(self, "history_file", "artifact_history.json")
        try:
            from ... import calculator as legacy_calc
            if hasattr(legacy_calc, "HISTORY_FILE"):
                history_path = legacy_calc.HISTORY_FILE
        except Exception:
            pass

        rank, _ = get_rank(self.last_eval.potential_pct)
        cv = self.last_forecast.expected_cv if self.last_forecast else 0.0

        item = {
            "timestamp": datetime.now().isoformat(),
            "slot": self.artifact_data.get("slot"),
            "set": self.artifact_data.get("set"),
            "main_stat": self.artifact_data.get("main_stat"),
            "level": self.artifact_data.get("level"),
            "substats": self.artifact_data.get("substats", []),
            "potential_pct": round(self.last_eval.potential_pct, 1),
            "current_pct": round(self.last_eval.current_pct, 1),
            "rank": rank,
            "crit_value": round(cv, 1),
            "character": self.selected_build.name if self.selected_build else "",
        }

        history = []
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.insert(0, item)
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        self.advice_lbl.configure(text="✅ Артефакт успешно сохранён в историю!", text_color=ThemeColors.GREEN)
        if self.on_save_history:
            self.on_save_history(self.artifact_data, item)

    def copy_share_card(self):
        """Format markdown share card and copy to clipboard."""
        if not self.artifact_data or not self.last_eval:
            return

        slot = self.artifact_data.get("slot", "")
        set_name = self.artifact_data.get("set", "")
        main_stat = self.artifact_data.get("main_stat", "")
        level = self.artifact_data.get("level", 20)
        substats = self.artifact_data.get("substats", [])
        rank, _ = get_rank(self.last_eval.potential_pct)
        cv = self.last_forecast.expected_cv if self.last_forecast else 0.0

        lines = [
            f"⚔️ **Genshin Artifact Report** ⚔️",
            f"✦ **Слот**: {slot} (+{level})",
            f"✦ **Сет**: {set_name}",
            f"✦ **Основной стат**: {main_stat}",
            "✦ **Сабстаты**:",
        ]
        for s, v in substats:
            lines.append(f"   • {s}: +{v}")

        lines.extend([
            f"✦ **Ранг**: {rank} ({self.last_eval.potential_pct:.1f}%)",
            f"✦ **Crit Value (CV)**: {cv:.1f}",
        ])
        if self.selected_build:
            lines.append(f"✦ **Для персонажа**: {self.selected_build.display_name}")

        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.advice_lbl.configure(text="📋 Отчёт скопирован в буфер обмена!", text_color=ThemeColors.CYAN)
