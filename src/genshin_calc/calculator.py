"""Genshin Impact — Калькулятор и Анализатор Артефактов v2.

Полностью переписанный GUI в стиле Genshin Impact.
Цветовая схема: тёмный фон (#1a1a2e / #16213e), золотые (#ffd700)
и бирюзовые (#00e5ff) акценты.
"""

import json
import os
import threading
import tkinter as tk
from datetime import datetime
from typing import Any, Optional, List, Dict, Union, Tuple, Callable

import customtkinter as ctk

from . import character_builds as cb
from . import enka_adapter
from . import good_adapter
from . import kamera_adapter
from .icon_manager import icon_manager
from .upgrade_probability import calculate_upgrade_forecast, UpgradeForecastResult
from .artifact_logic import (
    ARTIFACT_SLOTS,
    MAIN_STATS_BY_SLOT,
    STATS_DB,
    ArtifactInputError,
    describe_rolls,
    evaluate_artifact,
)

# ─── Тема ────────────────────────────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
try:
    if hasattr(ctk, "deactivate_automatic_dpi_awareness"):
        ctk.deactivate_automatic_dpi_awareness()
except Exception:
    pass

# ─── Цвета Genshin ───────────────────────────────────────────────────
class C:
    """Цветовая палитра приложения в стиле Genshin Impact."""
    BG_DEEP     = "#0f0f1e"
    BG_DARK     = "#1a1a2e"
    BG_PANEL    = "#16213e"
    BG_CARD     = "#1e2a45"
    BG_CARD_ALT = "#1b2540"
    BG_INPUT    = "#0e1a30"
    BG_HOVER    = "#243555"
    BORDER      = "#243555"
    GOLD        = "#ffd700"
    GOLD_DIM    = "#c9a900"
    CYAN        = "#00e5ff"
    CYAN_DIM    = "#00acc1"
    GREEN       = "#69f0ae"
    GREEN_BTN   = "#2e7d32"
    GREEN_HOVER = "#1b5e20"
    RED         = "#ff5252"
    RED_BTN     = "#c62828"
    RED_HOVER   = "#8e0000"
    RED_ERR     = "#d32f2f"
    ORANGE      = "#ff8c00"
    ORANGE_WARM = "#ffb74d"
    PURPLE      = "#e040fb"
    PURPLE_BTN  = "#4a148c"
    PURPLE_HOVER= "#311b92"
    BLUE_LIGHT  = "#64b5f6"
    BLUE_LINK   = "#81d4fa"
    BLUE_BTN    = "#1565c0"
    BLUE_SS     = "#4488ff"
    TEAL_BTN    = "#00695c"
    TEAL_HOVER  = "#004d40"
    KAMERA_BTN  = "#bf360c"
    KAMERA_HOVER= "#d84315"
    GRAY        = "#424242"
    GRAY_HOVER  = "#616161"
    GRAY_SLATE  = "#37474f"
    GRAY_SLATE_H= "#455a64"
    TEXT_PRIMARY = "#e0e0e0"
    TEXT_MUTED   = "#90a4ae"
    TEXT_DIM     = "#aaaaaa"
    TEXT_SUBS    = "#b0bec5"
    YELLOW_WARN  = "#ffd54f"
    TRANSPARENT  = "transparent"


def _is_real_tk(widget) -> bool:
    return isinstance(widget, (tk.Widget, tk.Tk, tk.Toplevel))


class _FastFrame:
    """Легковесный Frame: tk.Frame в реальном GUI (0 холстов) или CTkFrame под тестовым стабом."""
    def __new__(cls, master=None, *args, **kwargs):
        if not _is_real_tk(master):
            if "bg" in kwargs and "fg_color" not in kwargs:
                kwargs["fg_color"] = kwargs.pop("bg")
            kwargs.pop("highlightthickness", None)
            kwargs.pop("highlightbackground", None)
            kwargs.pop("bd", None)
            return ctk.CTkFrame(master, *args, **kwargs)
        fg_col = kwargs.pop("fg_color", None)
        if fg_col and "bg" not in kwargs:
            kwargs["bg"] = fg_col
        kwargs.pop("corner_radius", None)
        kwargs.pop("border_width", None)
        kwargs.pop("border_color", None)
        return tk.Frame(master, *args, **kwargs)


class _FastLabel:
    """Легковесный Label: tk.Label в реальном GUI (0 холстов) или CTkLabel под тестовым стабом."""
    def __new__(cls, master=None, *args, **kwargs):
        if not _is_real_tk(master):
            return ctk.CTkLabel(master, *args, **kwargs)
        if "text_color" in kwargs:
            kwargs["fg"] = kwargs.pop("text_color")
        return _RealFastLabel(master, *args, **kwargs)


class _RealFastLabel(tk.Label):
    def configure(self, **kwargs):
        if "text_color" in kwargs:
            kwargs["fg"] = kwargs.pop("text_color")
        return super().configure(**kwargs)
    config = configure


class _FastButton:
    """Легковесный Button: tk.Button в реальном GUI (0 холстов) или CTkButton под тестовым стабом."""
    def __new__(cls, master=None, *args, **kwargs):
        if not _is_real_tk(master):
            return ctk.CTkButton(master, *args, **kwargs)
        return _RealFastButton(master, *args, **kwargs)


class _RealFastButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        fg_col = kwargs.pop("fg_color", None)
        hov_col = kwargs.pop("hover_color", None)
        txt_col = kwargs.pop("text_color", None)
        kwargs.pop("corner_radius", None)
        kwargs.pop("border_width", None)
        kwargs.pop("border_color", None)
        if fg_col and "bg" not in kwargs:
            kwargs["bg"] = fg_col
        if txt_col and "fg" not in kwargs:
            kwargs["fg"] = txt_col
        kwargs.setdefault("relief", "flat")
        kwargs.setdefault("bd", 0)
        kwargs.setdefault("cursor", "hand2")
        kwargs.setdefault("activebackground", hov_col or kwargs.get("bg"))
        kwargs.setdefault("activeforeground", kwargs.get("fg", C.TEXT_PRIMARY))
        super().__init__(master, **kwargs)
        self._bg_normal = kwargs.get("bg")
        self._bg_hover = hov_col
        if self._bg_hover:
            self.bind("<Enter>", self._on_enter, add=True)
            self.bind("<Leave>", self._on_leave, add=True)

    def _on_enter(self, _e):
        if str(self.cget("state")) != "disabled" and self._bg_hover:
            super().configure(bg=self._bg_hover)

    def _on_leave(self, _e):
        if self._bg_normal:
            super().configure(bg=self._bg_normal)

    def configure(self, **kwargs):
        if "fg_color" in kwargs:
            self._bg_normal = kwargs.pop("fg_color")
            kwargs["bg"] = self._bg_normal
        if "hover_color" in kwargs:
            self._bg_hover = kwargs.pop("hover_color")
            kwargs["activebackground"] = self._bg_hover
        if "text_color" in kwargs:
            kwargs["fg"] = kwargs.pop("text_color")
            kwargs["activeforeground"] = kwargs["fg"]
        kwargs.pop("corner_radius", None)
        kwargs.pop("border_width", None)
        kwargs.pop("border_color", None)
        return super().configure(**kwargs)
    config = configure


# ─── Ранги ────────────────────────────────────────────────────────────
RANK_THRESHOLDS = [
    (90.0, "SSS", C.PURPLE),
    (80.0, "SS",  C.BLUE_SS),
    (70.0, "S",   C.GREEN),
    (50.0, "A",   C.GOLD),
    (30.0, "B",   C.ORANGE),
    (0.0,  "C",   C.RED),
]

def get_rank(pct: float) -> tuple[str, str]:
    for threshold, name, color in RANK_THRESHOLDS:
        if pct >= threshold:
            return name, color
    return "C", C.RED

RANK_COLORS = {name: color for _, name, color in RANK_THRESHOLDS}

# ─── Пресеты ─────────────────────────────────────────────────────────
ROLE_PRESETS = {
    "Свой выбор (Ручной)": None,
    "Main DPS (Криты / Атака)": {
        "Крит. урон": 2.0, "Шанс крит. попадания": 2.0,
        "Сила атаки %": 1.0, "Восст. энергии": 1.0, "Мастерство стихий": 1.0,
        "Сила атаки": 0.5, "HP %": 0.0, "Защита %": 0.0, "HP": 0.0, "Защита": 0.0,
    },
    "HP Support (Чжун Ли, Е Лань)": {
        "HP %": 2.0, "Восст. энергии": 2.0, "HP": 1.0,
        "Крит. урон": 1.0, "Шанс крит. попадания": 1.0,
        "Сила атаки %": 0.0, "Защита %": 0.0, "Мастерство стихий": 0.0,
        "Сила атаки": 0.0, "Защита": 0.0,
    },
    "EM Reactor (Кадзуха, Нахида)": {
        "Мастерство стихий": 2.0, "Восст. энергии": 2.0,
        "Сила атаки %": 1.0, "HP %": 1.0,
        "Крит. урон": 0.5, "Шанс крит. попадания": 0.5,
        "Защита %": 0.0, "Сила атаки": 0.0, "HP": 0.0, "Защита": 0.0,
    },
    "DEF Tank (Итто, Альбедо)": {
        "Защита %": 2.0, "Крит. урон": 2.0, "Шанс крит. попадания": 2.0,
        "Защита": 1.0, "Восст. энергии": 1.0,
        "Сила атаки %": 0.0, "HP %": 0.0, "Мастерство стихий": 0.0,
        "Сила атаки": 0.0, "HP": 0.0,
    },
}

HISTORY_FILE = "artifact_history.json"

SLOT_EMOJI = {
    "Цветок жизни": "🌺",
    "Перо смерти": "✒️",
    "Пески времени": "⏳",
    "Кубок пространства": "🍷",
    "Корона разума": "👑",
}

WEIGHT_OPTIONS = [
    ("2.0", "Высший",     C.GOLD),
    ("1.0", "Средний",    C.CYAN),
    ("0.5", "Низкий",     C.ORANGE_WARM),
    ("0.0", "Бесполезно", C.TEXT_MUTED),
]


# ═══════════════════════════════════════════════════════════════════════
#  ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ
# ═══════════════════════════════════════════════════════════════════════
class ArtifactCalculatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Genshin Impact — Калькулятор и Анализатор Артефактов")
        try:
            sw = self.winfo_screenwidth() or 1920
            sh = self.winfo_screenheight() or 1080
            x = max(0, (sw - 1200) // 2)
            y = max(0, (sh - 820) // 2)
            self.geometry(f"1200x820+{x}+{y}")
            self.minsize(1050, 700)
        except Exception:
            self.geometry("1200x820")
            self.minsize(1050, 700)
        self.resizable(False, False)
        self.configure(fg_color=C.BG_DEEP)
        self._block_update_dimensions_event = True

        # Состояние
        self.slot_var = ctk.StringVar(value="Пески времени")
        self.main_stat_var = ctk.StringVar(value="Мастерство стихий")
        self.set_var = ctk.StringVar(value="(Без сета / Любой)")
        self.char_name_var = ctk.StringVar(value="(Выбрать героя...)")
        self.role_name_var = ctk.StringVar(value="(Роль / Билд)")
        self.character_var = ctk.StringVar(value="(Выбрать персонажа...)")
        self.preset_var = ctk.StringVar(value="Main DPS (Криты / Атака)")
        self.level_var = ctk.StringVar(value="+0")
        self.initial_stats_var = ctk.StringVar(value="4 сабстата")
        self.last_calculation = None
        self._calc_snapshot = None

        # Состояние All-in-One GUI навигации
        self._current_view = "calc"
        self._nav_buttons = {}

        # Состояние вкладки Сравнение
        self._compare_slot_filter = ctk.StringVar(value="Все слоты")
        self._compare_source_a = ctk.StringVar(value="current")
        self._compare_artifact_a = None
        self._compare_artifact_b = None
        self._compare_slot_buttons = {}

        # Состояние вкладки История
        self._hist_search_var = ctk.StringVar(value="")
        self._hist_slot_filter = ctk.StringVar(value="Все слоты")
        self._hist_loc_filter = ctk.StringVar(value="Все артефакты")
        self._hist_rank_filter = ctk.StringVar(value="Все ранги")

        # Состояние Kamera
        self._kamera_state: dict[str, Any] = {
            "all_artifacts": [],
            "filtered_artifacts": [],
            "current_file": None,
            "metadata": {},
            "current_page": 0,
            "page_size": 10,
            "watcher": None,
        }

        # Ctrl+V/C/A/X для кириллической раскладки
        try:
            self.bind_all("<Control-KeyPress>", self._handle_control_keys)
        except Exception:
            pass

        self._build_ui()
        self._update_main_stat_options(self.slot_var.get(), invalidate=False)
        self._apply_preset_selection(self.preset_var.get())

    # ──────────────────────────────────────────────────────────────────
    #  ГЛАВНЫЙ UI
    # ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ─── 1. Верхняя шапка с навигацией по вкладкам ───
        self._build_header_and_navbar()

        # ─── 2. Контейнер экранов (вкладок) ───
        self.view_container = ctk.CTkFrame(self, fg_color=C.TRANSPARENT)
        self.view_container.pack(fill="both", expand=True, padx=12, pady=(2, 4))

        # Флаги ленивой загрузки экранов для максимальной производительности
        self._history_built = False
        self._compare_built = False
        self._hub_built = False

        # ─── Экран 1: Калькулятор (загружается сразу) ───
        self.view_calc = ctk.CTkFrame(self.view_container, fg_color=C.TRANSPARENT)
        self.view_calc.grid_columnconfigure(0, weight=0, minsize=460)
        self.view_calc.grid_columnconfigure(1, weight=1)
        self.view_calc.grid_rowconfigure(0, weight=1)
        self._build_left_panel(self.view_calc)
        self._build_right_panel(self.view_calc)

        # ─── Экран 2: История (ленивая загрузка) ───
        self.view_history = ctk.CTkFrame(self.view_container, fg_color=C.TRANSPARENT)

        # ─── Экран 3: Сравнение (ленивая загрузка) ───
        self.view_compare = ctk.CTkFrame(self.view_container, fg_color=C.TRANSPARENT)

        # ─── Экран 4: Импорт / Data Hub (ленивая загрузка) ───
        self.view_hub = ctk.CTkFrame(self.view_container, fg_color=C.TRANSPARENT)

        # Ссылки для обратной совместимости
        self._good_dialog = self.view_hub
        self._history_win = self.view_history
        self._compare_win = None

        # Показать начальный экран
        self.show_view("calc")

    def _build_header_and_navbar(self):
        header = ctk.CTkFrame(self, fg_color=C.BG_PANEL, corner_radius=0, height=54)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_box = ctk.CTkFrame(header, fg_color=C.TRANSPARENT)
        title_box.pack(side="left", padx=16, pady=8)
        ctk.CTkLabel(
            title_box,
            text="⚔️  Genshin Artifact Calculator",
            font=("Segoe UI", 16, "bold"),
            text_color=C.GOLD,
        ).pack(side="left")
        ctk.CTkLabel(
            title_box,
            text=" v2.0",
            font=("Segoe UI", 11),
            text_color=C.TEXT_MUTED,
        ).pack(side="left", padx=(4, 0))

        nav_box = ctk.CTkFrame(header, fg_color=C.TRANSPARENT)
        nav_box.pack(side="right", padx=16, pady=8)

        nav_items = [
            ("calc", "⚔️  Калькулятор"),
            ("history", "📜  История"),
            ("compare", "⚖️  Сравнение"),
            ("hub", "⚡  Импорт / Hub"),
        ]

        self._nav_buttons = {}
        for key, title in nav_items:
            btn = ctk.CTkButton(
                nav_box,
                text=title,
                font=("Segoe UI", 12, "bold"),
                width=140,
                height=34,
                corner_radius=8,
                fg_color=C.BG_CARD,
                hover_color=C.BG_HOVER,
                text_color=C.TEXT_MUTED,
                command=lambda k=key: self.show_view(k),
            )
            btn.pack(side="left", padx=4)
            self._nav_buttons[key] = btn

    def _ensure_history_built(self):
        if not self._history_built:
            self._build_history_view(self.view_history)
            self._history_built = True

    def _ensure_compare_built(self):
        if not self._compare_built:
            self._build_compare_view(self.view_compare)
            self._compare_built = True

    def _ensure_hub_built(self):
        if not self._hub_built:
            self._build_hub_view(self.view_hub)
            self._hub_built = True

    def show_view(self, view_name: str):
        self._current_view = view_name
        self.view_calc.pack_forget()
        self.view_history.pack_forget()
        self.view_compare.pack_forget()
        self.view_hub.pack_forget()

        for name, btn in self._nav_buttons.items():
            if name == view_name:
                btn.configure(fg_color=C.CYAN_DIM, text_color=C.BG_DEEP)
            else:
                btn.configure(fg_color=C.BG_CARD, text_color=C.TEXT_MUTED)

        if view_name == "calc":
            self.view_calc.pack(fill="both", expand=True)
        elif view_name == "history":
            self._ensure_history_built()
            self.view_history.pack(fill="both", expand=True)
            self._refresh_history_view()
        elif view_name == "compare":
            self._ensure_compare_built()
            self.view_compare.pack(fill="both", expand=True)
            self._refresh_compare_view()
        elif view_name == "hub":
            self._ensure_hub_built()
            self.view_hub.pack(fill="both", expand=True)

    # ──────────────────────────────────────────────────────────────────
    #  ЛЕВАЯ ПАНЕЛЬ — ВВОД ДАННЫХ
    # ──────────────────────────────────────────────────────────────────
    def _build_left_panel(self, parent):
        left = ctk.CTkScrollableFrame(parent, fg_color=C.BG_DARK, corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

        # ─── 1. Сегментные кнопки слотов ───
        self._section_label(left, "⬡  Тип артефакта")
        slot_frame = ctk.CTkFrame(left, fg_color=C.TRANSPARENT)
        slot_frame.pack(fill="x", padx=14, pady=(2, 4))

        self._slot_buttons = {}
        for slot_name in ARTIFACT_SLOTS:
            emoji = SLOT_EMOJI[slot_name]
            short = slot_name.split()[0]
            btn = ctk.CTkButton(
                slot_frame,
                text=f"{emoji}\n{short}",
                font=("Segoe UI", 11),
                width=80, height=52,
                corner_radius=10,
                fg_color=C.BG_CARD,
                hover_color=C.BG_HOVER,
                text_color=C.TEXT_MUTED,
                command=lambda s=slot_name: self._select_slot(s),
            )
            btn.pack(side="left", expand=True, fill="x", padx=2)
            self._slot_buttons[slot_name] = btn

        self._highlight_slot(self.slot_var.get())

        # ─── 2. Основной стат ───
        stat_row = ctk.CTkFrame(left, fg_color=C.TRANSPARENT)
        stat_row.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(stat_row, text="Основной стат:", font=("Segoe UI", 12),
                     text_color=C.TEXT_PRIMARY).pack(side="left", padx=(0, 8))
        self.main_stat_menu = ctk.CTkOptionMenu(
            stat_row,
            values=list(MAIN_STATS_BY_SLOT[self.slot_var.get()]),
            variable=self.main_stat_var,
            command=self._on_main_stat_change,
            width=240,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER,
            button_hover_color=C.CYAN_DIM,
        )
        self.main_stat_menu.pack(side="left", fill="x", expand=True)

        # ─── Сет артефакта ───
        set_row = ctk.CTkFrame(left, fg_color=C.TRANSPARENT)
        set_row.pack(fill="x", padx=14, pady=(4, 4))
        ctk.CTkLabel(set_row, text="Сет артефакта:", font=("Segoe UI", 12),
                     text_color=C.TEXT_PRIMARY).pack(side="left", padx=(0, 8))
        self.set_menu = ctk.CTkOptionMenu(
            set_row,
            values=["(Без сета / Любой)"] + sorted(cb.SET_NAME_TO_KEY.keys()),
            variable=self.set_var,
            command=self._on_set_change,
            width=240,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER,
            button_hover_color=C.CYAN_DIM,
        )
        self.set_menu.pack(side="left", fill="x", expand=True)

        # ─── 3. Роль и выбор персонажа ───
        self._section_label(left, "🎭  Роль / Персонаж")

        char_card = ctk.CTkFrame(left, fg_color=C.BG_CARD_ALT, corner_radius=10)
        char_card.pack(fill="x", padx=14, pady=(0, 4))

        # Аватар активного персонажа (с круглой рамкой стихии)
        self.char_avatar_lbl = ctk.CTkLabel(
            char_card, text="👤", font=("Segoe UI", 20),
            width=50, height=50, fg_color=C.BG_CARD, corner_radius=25,
        )
        self.char_avatar_lbl.pack(side="left", padx=(8, 10), pady=6)

        # Двухуровневый выбор: Герой -> Билд
        char_inputs = ctk.CTkFrame(char_card, fg_color=C.TRANSPARENT)
        char_inputs.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)

        row_char = ctk.CTkFrame(char_inputs, fg_color=C.TRANSPARENT)
        row_char.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(row_char, text="Герой:", font=("Segoe UI", 11, "bold"),
                     text_color=C.GOLD, width=48, anchor="w").pack(side="left")
        self.char_name_menu = ctk.CTkOptionMenu(
            row_char,
            values=["(Выбрать героя...)"] + cb.get_unique_character_names(),
            variable=self.char_name_var,
            command=self._on_char_name_change,
            width=180,
            height=26,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER,
            button_hover_color=C.CYAN_DIM,
        )
        self.char_name_menu.pack(side="left", fill="x", expand=True)

        row_role = ctk.CTkFrame(char_inputs, fg_color=C.TRANSPARENT)
        row_role.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(row_role, text="Билд:", font=("Segoe UI", 11, "bold"),
                     text_color=C.GOLD, width=48, anchor="w").pack(side="left")
        self.role_name_menu = ctk.CTkOptionMenu(
            row_role,
            values=["(Сначала выберите героя)"],
            variable=self.role_name_var,
            command=self._on_role_name_change,
            width=180,
            height=26,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER,
            button_hover_color=C.CYAN_DIM,
        )
        self.role_name_menu.pack(side="left", fill="x", expand=True)

        # Сохраняем ссылку для обратной совместимости
        self.character_menu = self.char_name_menu

        # Карточка подробностей билда (сеты, главные статы, топ оружия, советы)
        self.char_info_card = ctk.CTkFrame(left, fg_color=C.BG_CARD, corner_radius=8)
        self.char_info_card.pack(fill="x", padx=14, pady=(2, 4))

        self.char_tip_lbl = ctk.CTkLabel(
            self.char_info_card,
            text="💡 Выберите персонажа для просмотра рекомендаций сетов, главных статов и оружия.",
            font=("Segoe UI", 10),
            text_color=C.CYAN, wraplength=420, justify="left",
        )
        self.char_tip_lbl.pack(fill="x", padx=8, pady=6, anchor="w")

        preset_frame = ctk.CTkFrame(left, fg_color=C.TRANSPARENT)
        preset_frame.pack(fill="x", padx=14, pady=(2, 4))

        self._preset_buttons = {}
        preset_configs = [
            ("Свой выбор (Ручной)", "✏️ Ручной",  C.GRAY, C.GRAY_HOVER),
            ("Main DPS (Криты / Атака)", "⚔️ DPS", C.KAMERA_BTN, C.KAMERA_HOVER),
            ("HP Support (Чжун Ли, Е Лань)", "❤️ HP", C.TEAL_BTN, C.TEAL_HOVER),
            ("EM Reactor (Кадзуха, Нахида)", "🌀 EM", C.PURPLE_BTN, C.PURPLE_HOVER),
            ("DEF Tank (Итто, Альбедо)", "🛡️ DEF", C.BLUE_BTN, "#0d47a1"),
        ]
        for key, label, color, hover in preset_configs:
            btn = ctk.CTkButton(
                preset_frame, text=label, font=("Segoe UI", 11, "bold"),
                width=80, height=34, corner_radius=8,
                fg_color=color, hover_color=hover,
                command=lambda k=key: self._on_preset_click(k),
            )
            btn.pack(side="left", expand=True, fill="x", padx=2)
            self._preset_buttons[key] = btn
        self._highlight_preset(self.preset_var.get())

        # ─── 4. Состояние артефакта ───
        self._section_label(left, "📊  Состояние артефакта")
        state_frame = ctk.CTkFrame(left, fg_color=C.TRANSPARENT)
        state_frame.pack(fill="x", padx=14, pady=(2, 4))

        ctk.CTkLabel(state_frame, text="Уровень:", font=("Segoe UI", 12),
                     text_color=C.TEXT_PRIMARY).pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(
            state_frame,
            values=["+0", "+4", "+8", "+12", "+16", "+20"],
            variable=self.level_var,
            command=lambda _: self._invalidate_calculation(),
            width=90,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER,
            button_hover_color=C.CYAN_DIM,
        ).pack(side="left", padx=(0, 20))

        ctk.CTkLabel(state_frame, text="Старт:", font=("Segoe UI", 12),
                     text_color=C.TEXT_PRIMARY).pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(
            state_frame,
            values=["4 сабстата", "3 сабстата"],
            variable=self.initial_stats_var,
            command=lambda _: self._invalidate_calculation(),
            width=135,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER,
            button_hover_color=C.CYAN_DIM,
        ).pack(side="left")

        # ─── 5. Сабстаты (мини-карточки) ───
        self._section_label(left, "🎲  Сабстаты")
        self.stat_widgets = []
        stat_names = list(STATS_DB)

        for i in range(4):
            card = ctk.CTkFrame(left, fg_color=C.BG_CARD, corner_radius=8)
            card.pack(fill="x", padx=14, pady=3)

            # Ряд: [ComboBox стата] [Entry значения] [OptionMenu веса]
            row = ctk.CTkFrame(card, fg_color=C.TRANSPARENT)
            row.pack(fill="x", padx=8, pady=6)

            combo = ctk.CTkComboBox(
                row, values=stat_names, width=170, state="readonly",
                fg_color=C.BG_INPUT, border_color=C.BG_HOVER,
                button_color=C.BG_HOVER, button_hover_color=C.CYAN_DIM,
                dropdown_fg_color=C.BG_PANEL,
                command=lambda choice, idx=i: self._on_stat_changed(idx, choice),
            )
            combo.set(stat_names[i])
            combo.pack(side="left", padx=(0, 6))

            entry = ctk.CTkEntry(
                row, placeholder_text="Значение", width=90,
                fg_color=C.BG_INPUT, border_color=C.BG_HOVER,
                text_color=C.TEXT_PRIMARY,
            )
            entry.pack(side="left", padx=(0, 6))
            entry.bind("<KeyRelease>", lambda _e: self._invalidate_calculation())

            weight_combo = ctk.CTkOptionMenu(
                row,
                values=[f"{v} ({lbl})" for v, lbl, _ in WEIGHT_OPTIONS],
                width=150,
                fg_color=C.BG_INPUT, button_color=C.BG_HOVER,
                button_hover_color=C.CYAN_DIM,
                command=lambda _: self._invalidate_calculation(),
            )
            weight_combo.set("1.0 (Средний)" if i >= 2 else "2.0 (Высший)")
            weight_combo.pack(side="left", fill="x", expand=True)

            self.stat_widgets.append(
                {"stat_combo": combo, "entry": entry, "weight_combo": weight_combo}
            )
            self._attach_context_menu(entry)

        # ─── Кнопки расчёта и сохранения ───
        btn_frame = ctk.CTkFrame(left, fg_color=C.TRANSPARENT)
        btn_frame.pack(fill="x", padx=14, pady=(6, 10))
        
        self.calc_btn = ctk.CTkButton(
            btn_frame,
            text="⚡  Рассчитать",
            font=("Segoe UI", 14, "bold"),
            fg_color=C.CYAN_DIM, hover_color=C.CYAN,
            text_color=C.BG_DEEP,
            height=42, corner_radius=8,
            command=self.calculate,
        )
        self.calc_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        self.save_btn = ctk.CTkButton(
            btn_frame, text="💾  Сохранить",
            font=("Segoe UI", 14, "bold"),
            fg_color=C.TEAL_BTN, hover_color=C.TEAL_HOVER,
            height=42, corner_radius=8,
            command=self.save_to_history, state="disabled",
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

    # ──────────────────────────────────────────────────────────────────
    #  ПРАВАЯ ПАНЕЛЬ — РЕЗУЛЬТАТЫ
    # ──────────────────────────────────────────────────────────────────
    def _build_right_panel(self, parent):
        right = ctk.CTkScrollableFrame(parent, fg_color=C.BG_DARK, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

        # ─── Карточка ранга ───
        self.rank_card = ctk.CTkFrame(right, fg_color=C.BG_PANEL, corner_radius=14, height=100)
        self.rank_card.pack(fill="x", padx=14, pady=(2, 4))
        self.rank_card.pack_propagate(False)

        rank_inner = ctk.CTkFrame(self.rank_card, fg_color=C.TRANSPARENT)
        rank_inner.pack(expand=True)

        # Иконка слота/сета артефакта
        self.art_icon_lbl = ctk.CTkLabel(
            rank_inner, text="⏳", font=("Segoe UI", 24),
            width=50, height=50, fg_color=C.BG_CARD, corner_radius=10,
        )
        self.art_icon_lbl.pack(side="left", padx=(0, 12))

        self.rank_label = ctk.CTkLabel(
            rank_inner, text="—", font=("Segoe UI", 40, "bold"),
            text_color=C.TEXT_DIM,
        )
        self.rank_label.pack(side="left", padx=(0, 14))

        rank_text_col = ctk.CTkFrame(rank_inner, fg_color=C.TRANSPARENT)
        rank_text_col.pack(side="left")
        self.rank_title_lbl = ctk.CTkLabel(
            rank_text_col, text="Ранг артефакта",
            font=("Segoe UI", 13, "bold"), text_color=C.TEXT_MUTED,
        )
        self.rank_title_lbl.pack(anchor="w")
        self.rank_subtitle_lbl = ctk.CTkLabel(
            rank_text_col, text="Введите данные и нажмите «Рассчитать»",
            font=("Segoe UI", 11), text_color=C.TEXT_DIM,
        )
        self.rank_subtitle_lbl.pack(anchor="w")

        # ─── Прогресс-бар PAV ───
        pav_frame = ctk.CTkFrame(right, fg_color=C.TRANSPARENT)
        pav_frame.pack(fill="x", padx=14, pady=(4, 2))

        self.pav_current_lbl = ctk.CTkLabel(
            pav_frame, text="Текущий PAV: —",
            font=("Segoe UI", 12), text_color=C.TEXT_PRIMARY,
        )
        self.pav_current_lbl.pack(anchor="w")

        self.pav_progress = ctk.CTkProgressBar(
            pav_frame, width=400, height=16, corner_radius=8,
            fg_color=C.BG_CARD, progress_color=C.CYAN,
        )
        self.pav_progress.pack(fill="x", pady=(4, 2))
        self.pav_progress.set(0)

        pav_row2 = ctk.CTkFrame(pav_frame, fg_color=C.TRANSPARENT)
        pav_row2.pack(fill="x")
        self.pav_potential_lbl = ctk.CTkLabel(
            pav_row2, text="Потолок: —", font=("Segoe UI", 12, "bold"),
            text_color=C.GOLD,
        )
        self.pav_potential_lbl.pack(side="left")
        self.pav_expected_lbl = ctk.CTkLabel(
            pav_row2, text="Ожидаемо: —", font=("Segoe UI", 11),
            text_color=C.TEXT_MUTED,
        )
        self.pav_expected_lbl.pack(side="right")

        self.upgrades_lbl = ctk.CTkLabel(
            right, text="Осталось проков: —",
            font=("Segoe UI", 11), text_color=C.TEXT_DIM,
        )
        self.upgrades_lbl.pack(anchor="w", padx=14, pady=(2, 4))

        # ─── Визуализация роллов (Progress-бары) ───
        self._section_label(right, "📈  Распределение роллов")
        self.rolls_frame = ctk.CTkFrame(right, fg_color=C.TRANSPARENT)
        self.rolls_frame.pack(fill="x", padx=14, pady=(0, 4))

        self.roll_bars = {}  # будет заполнено при расчёте

        # ─── Прогноз улучшений (AnimeGameData Math) ───
        self._section_label(right, "🔮  Прогноз улучшений до +20 (AnimeGameData)")
        self.forecast_card = ctk.CTkFrame(right, fg_color=C.BG_CARD, corner_radius=8)
        self.forecast_card.pack(fill="x", padx=14, pady=(0, 4))

        self.forecast_verdict_lbl = ctk.CTkLabel(
            self.forecast_card,
            text="💎 Оценка потенциала артефакта",
            font=("Segoe UI", 11, "bold"),
            text_color=C.CYAN,
        )
        self.forecast_verdict_lbl.pack(anchor="w", padx=10, pady=(6, 2))

        self.forecast_stats_lbl = ctk.CTkLabel(
            self.forecast_card,
            text="Шансы: S+ (—) | SS+ (—) | SSS (—)  |  Ожидаемо: PAV — | CV —",
            font=("Segoe UI", 10),
            text_color=C.TEXT_PRIMARY,
            justify="left",
            anchor="w",
        )
        self.forecast_stats_lbl.pack(fill="x", padx=10, pady=(0, 2))

        self.forecast_advice_lbl = ctk.CTkLabel(
            self.forecast_card,
            text="Введите характеристики артефакта и нажмите «Рассчитать».",
            font=("Segoe UI", 10),
            text_color=C.TEXT_MUTED,
            wraplength=430,
            justify="left",
            anchor="w",
        )
        self.forecast_advice_lbl.pack(fill="x", padx=10, pady=(2, 4))

        # ─── Совместимость с персонажами ───
        self._section_label(right, "🎯  Совместимость с персонажами")
        self.compat_frame = ctk.CTkFrame(right, fg_color=C.BG_CARD, corner_radius=8)
        self.compat_frame.pack(fill="x", padx=14, pady=(0, 4))
        self.compat_lbl = ctk.CTkLabel(
            self.compat_frame,
            text="Выберите сет артефакта или персонажа для оценки совместимости.",
            font=("Segoe UI", 11), text_color=C.TEXT_MUTED,
            wraplength=430, justify="left",
        )
        self.compat_lbl.pack(padx=10, pady=8, anchor="w")

        # ─── Текстовый отчёт ───
        self.result_textbox = ctk.CTkTextbox(
            right, height=90, font=("Consolas", 11),
            fg_color=C.BG_CARD, text_color=C.TEXT_PRIMARY,
            corner_radius=8,
        )
        self.result_textbox.pack(fill="both", expand=True, padx=14, pady=(2, 4))
        self.result_textbox.insert(
            "1.0", "Введите характеристики артефакта и нажмите «Рассчитать»."
        )

        # ─── Кнопки действий (верхний ряд) ───
        act1 = ctk.CTkFrame(right, fg_color=C.TRANSPARENT)
        act1.pack(fill="x", padx=14, pady=(0, 4))



        self.share_btn = ctk.CTkButton(
            act1, text="📋  Скопировать отчёт", width=160,
            fg_color=C.GREEN_BTN, hover_color=C.GREEN_HOVER,
            command=self.copy_share_card, state="disabled",
        )
        self.share_btn.pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            act1, text="📜  История", width=110,
            fg_color=C.PURPLE_BTN, hover_color=C.PURPLE_HOVER,
            command=self.open_history_window,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            act1, text="⚖️  Сравнить", width=100,
            fg_color=C.GRAY_SLATE, hover_color=C.GRAY_SLATE_H,
            command=self.open_compare_window,
        ).pack(side="right")

        # ─── Кнопки действий (нижний ряд) ───
        act2 = ctk.CTkFrame(right, fg_color=C.TRANSPARENT)
        act2.pack(fill="x", padx=14, pady=(2, 4))

        self.good_btn = ctk.CTkButton(
            act2, text="🌐  Enka / GOOD JSON", width=190,
            fg_color=C.TEAL_BTN, hover_color=C.TEAL_HOVER,
            command=self.open_good_transfer_dialog,
        )
        self.good_btn.pack(side="left", padx=(0, 4), fill="x", expand=True)

        self.kamera_btn = ctk.CTkButton(
            act2, text="📷  Сканер рюкзака (Kamera)", width=210,
            fg_color=C.KAMERA_BTN, hover_color=C.KAMERA_HOVER,
            command=self.open_kamera_dialog,
        )
        self.kamera_btn.pack(side="left", fill="x", expand=True)

    # ──────────────────────────────────────────────────────────────────
    #  UI HELPERS
    # ──────────────────────────────────────────────────────────────────
    def _section_label(self, parent, text: str):
        """Заголовок секции с отступами."""
        ctk.CTkLabel(
            parent, text=text, font=("Segoe UI", 13, "bold"),
            text_color=C.GOLD_DIM,
        ).pack(anchor="w", padx=14, pady=(10, 4))

    def _select_slot(self, slot_name: str):
        """Обработчик нажатия на кнопку слота."""
        self.slot_var.set(slot_name)
        self._highlight_slot(slot_name)
        self._update_main_stat_options(slot_name, invalidate=True)
        self._apply_preset_selection(self.preset_var.get(), invalidate=False)
        self._update_artifact_icon(slot_name, cb.SET_NAME_TO_KEY.get(self.set_var.get(), ""))

    def _on_slot_change(self, choice: str):
        """Совместимый callback для смены слота."""
        self._select_slot(choice)

    def _highlight_slot(self, active_slot: str):
        """Подсветить активную кнопку слота."""
        for name, btn in self._slot_buttons.items():
            if name == active_slot:
                btn.configure(fg_color=C.CYAN_DIM, text_color=C.BG_DEEP)
            else:
                btn.configure(fg_color=C.BG_CARD, text_color=C.TEXT_MUTED)

    def _on_set_change(self, _choice):
        """Обработчик смены сета артефакта."""
        self._invalidate_calculation()
        self._update_artifact_icon(self.slot_var.get(), cb.SET_NAME_TO_KEY.get(self.set_var.get(), ""))

    def _update_avatar(self, char_name: str):
        """Update avatar image and elemental border asynchronously."""
        if not hasattr(self, "char_avatar_lbl"):
            return
        if not char_name or char_name.startswith("("):
            self.char_avatar_lbl.configure(image=None, text="👤")
            return

        def _on_ready(img, _border_color):
            try:
                if img and hasattr(self, "char_avatar_lbl") and self.char_avatar_lbl.winfo_exists():
                    self.char_avatar_lbl.configure(image=img, text="")
            except Exception:
                pass

        try:
            img, _ = icon_manager.get_character_avatar(char_name, size=(48, 48), on_ready_cb=_on_ready)
            if img:
                self.char_avatar_lbl.configure(image=img, text="")
            else:
                self.char_avatar_lbl.configure(image=None, text="👤")
        except Exception:
            self.char_avatar_lbl.configure(image=None, text="👤")

    def _update_artifact_icon(self, slot: str, set_key: str = ""):
        """Update slot/set preview icon in rank card asynchronously."""
        if not hasattr(self, "art_icon_lbl"):
            return

        def _on_ready(img):
            try:
                if img and hasattr(self, "art_icon_lbl") and self.art_icon_lbl.winfo_exists():
                    self.art_icon_lbl.configure(image=img, text="")
            except Exception:
                pass

        try:
            img = icon_manager.get_artifact_slot_icon(slot, set_key=set_key, size=(48, 48), on_ready_cb=_on_ready)
            if img:
                self.art_icon_lbl.configure(image=img, text="")
            else:
                emoji = SLOT_EMOJI.get(slot, "⬡")
                self.art_icon_lbl.configure(image=None, text=emoji)
        except Exception:
            emoji = SLOT_EMOJI.get(slot, "⬡")
            self.art_icon_lbl.configure(image=None, text=emoji)

    def _on_char_name_change(self, choice: str):
        """Level 1 character selection callback."""
        self._invalidate_calculation()
        self.char_name_var.set(choice)
        if not choice or choice.startswith("("):
            self.char_name_var.set("(Выбрать героя...)")
            self.role_name_var.set("(Роль / Билд)")
            self.character_var.set("(Выбрать персонажа...)")
            self.role_name_menu.configure(values=["(Сначала выберите героя)"])
            self._update_avatar("")
            self.char_tip_lbl.configure(
                text="💡 Выберите персонажа для просмотра рекомендаций сетов, главных статов и оружия."
            )
            return

        self._update_avatar(choice)
        builds = cb.get_builds_for_character(choice)
        if not builds:
            single = cb.find_build_for_character(choice)
            if single:
                builds = [single]

        if builds:
            role_options = [b.build_name for b in builds]
            self.role_name_menu.configure(values=role_options)
            chosen_build = builds[0]
            self.role_name_var.set(chosen_build.build_name)
            self.character_var.set(chosen_build.display_name)
            self._apply_character_build(chosen_build)
        else:
            self.role_name_menu.configure(values=["(Стандартный)"])
            self.role_name_var.set("(Стандартный)")
            self.character_var.set(choice)

    def _on_role_name_change(self, choice: str):
        """Level 2 build/role selection callback."""
        self._invalidate_calculation()
        self.role_name_var.set(choice)
        char_name = self.char_name_var.get()
        builds = cb.get_builds_for_character(char_name)
        matched_build = next((b for b in builds if b.build_name == choice), None)
        if matched_build:
            self.character_var.set(matched_build.display_name)
            self._apply_character_build(matched_build)

    def _on_character_change(self, choice: str):
        """Backwards-compatible callback when full display name is passed."""
        self._invalidate_calculation()
        build = cb.get_build_by_display_name(choice)
        if not build:
            build = cb.find_build_for_character(choice)
        if not build:
            self.char_name_var.set("(Выбрать героя...)")
            self.role_name_var.set("(Роль / Билд)")
            self.character_var.set("(Выбрать персонажа...)")
            self._update_avatar("")
            self.char_tip_lbl.configure(
                text="💡 Выберите персонажа для просмотра рекомендаций сетов, главных статов и оружия."
            )
            return

        self.char_name_var.set(build.name)
        self._update_avatar(build.name)
        builds = cb.get_builds_for_character(build.name)
        if builds:
            self.role_name_menu.configure(values=[b.build_name for b in builds])
        self.role_name_var.set(build.build_name)
        self.character_var.set(build.display_name)
        self._apply_character_build(build)

    def _apply_character_build(self, build: cb.CharacterBuild):
        self._highlight_preset(None)
        self.preset_var.set(f"Персонаж: {build.name}")

        rec_sands = " / ".join(build.main_stats.get("Пески времени", ["—"]))
        rec_goblet = " / ".join(build.main_stats.get("Кубок пространства", ["—"]))
        rec_circlet = " / ".join(build.main_stats.get("Корона разума", ["—"]))
        sets_str = ", ".join(build.best_sets[:2])

        weapon_list = build.top_weapon_names[:3]
        weapons_str = ", ".join(weapon_list) if weapon_list else "—"

        tip_lines = [
            f"💡 {build.name} ({build.role})  |  🎭 Сеты: {sets_str}",
            f"  ⏳ {rec_sands}  |  🍷 {rec_goblet}  |  👑 {rec_circlet}",
            f"  🗡️ Оружие: {weapons_str}",
        ]
        if build.notes:
            tip_lines.append(f"  ℹ️ {build.notes}")

        self.char_tip_lbl.configure(text="\n".join(tip_lines))
        self._apply_character_weights(build)

    def _apply_character_weights(self, build: cb.CharacterBuild):
        weights = build.substat_weights
        main_stat = self.main_stat_var.get()
        eligible = [s for s in STATS_DB if s != main_stat]
        ranked = sorted(
            (s for s in weights if s in eligible),
            key=lambda s: weights[s], reverse=True,
        )
        ranked += [s for s in eligible if s not in ranked]
        has_values = any(w["entry"].get().strip() for w in self.stat_widgets)
        for i, widget in enumerate(self.stat_widgets):
            if not has_values:
                stat_name = ranked[i]
                widget["stat_combo"].set(stat_name)
            else:
                stat_name = widget["stat_combo"].get()
            self._update_widget_weight(widget, stat_name, weights)

    def _on_preset_click(self, key: str):
        """Обработчик нажатия на кнопку общего пресета."""
        self.preset_var.set(key)
        self.character_var.set("(Выбрать персонажа...)")
        if hasattr(self, "char_name_var"):
            self.char_name_var.set("(Выбрать героя...)")
        if hasattr(self, "role_name_var"):
            self.role_name_var.set("(Роль / Билд)")
            self.role_name_menu.configure(values=["(Сначала выберите героя)"])
        self._update_avatar("")
        self.char_tip_lbl.configure(
            text="💡 Выберите персонажа для просмотра рекомендаций сетов, главных статов и оружия."
        )
        self._highlight_preset(key)
        self._invalidate_calculation()
        self._apply_preset_selection(key, invalidate=False)

    def _highlight_preset(self, active_key: str):
        """Визуально выделить активный пресет (рамкой)."""
        for key, btn in self._preset_buttons.items():
            if key == active_key:
                btn.configure(border_width=2, border_color=C.GOLD)
            else:
                btn.configure(border_width=0)

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

    def _on_main_stat_change(self, _choice):
        self._invalidate_calculation()

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
            key=lambda s: preset_data[s], reverse=True,
        )
        ranked += [s for s in eligible if s not in ranked]
        for i, widget in enumerate(self.stat_widgets):
            stat_name = ranked[i]
            widget["stat_combo"].set(stat_name)
            self._update_widget_weight(widget, stat_name, preset_data)
        if invalidate:
            self._invalidate_calculation()

    def _on_stat_changed(self, idx, choice):
        self._invalidate_calculation()
        build = cb.get_build_by_display_name(self.character_var.get())
        if build is not None:
            self._update_widget_weight(self.stat_widgets[idx], choice, build.substat_weights)
            return
        preset_data = ROLE_PRESETS.get(self.preset_var.get())
        if preset_data is not None:
            self._update_widget_weight(self.stat_widgets[idx], choice, preset_data)

    def _update_widget_weight(self, widget, stat_name, preset_data):
        weight_val = preset_data.get(stat_name, 0.0)
        for v, lbl, _ in WEIGHT_OPTIONS:
            if float(v) == weight_val:
                widget["weight_combo"].set(f"{v} ({lbl})")
                break
        else:
            widget["weight_combo"].set("0.0 (Бесполезно)")
        widget["weight_combo"].configure(state="disabled")

    def _collect_weights(self, role_name):
        build = cb.get_build_by_display_name(self.character_var.get())
        if build is not None:
            return dict(build.substat_weights)
        preset = ROLE_PRESETS.get(role_name)
        if preset is not None:
            return dict(preset)
        weights = {s: 0.0 for s in STATS_DB}
        for w in self.stat_widgets:
            stat = w["stat_combo"].get()
            if stat in weights:
                try:
                    weights[stat] = float(w["weight_combo"].get().split()[0])
                except (ValueError, IndexError):
                    weights[stat] = 0.0
        return weights

    # ──────────────────────────────────────────────────────────────────
    #  СОСТОЯНИЕ РАСЧЁТА
    # ──────────────────────────────────────────────────────────────────
    def _invalidate_calculation(self):
        self.last_calculation = None
        self._calc_snapshot = None
        self.save_btn.configure(text="💾  Сохранить", state="disabled")
        self.share_btn.configure(text="📋  Скопировать отчёт", state="disabled")
        self.rank_label.configure(text="—", text_color=C.TEXT_DIM)
        self.rank_subtitle_lbl.configure(text="Введите данные и нажмите «Рассчитать»")
        self.pav_current_lbl.configure(text="Текущий PAV: —")
        self.pav_potential_lbl.configure(text="Потолок: —")
        self.pav_expected_lbl.configure(text="Ожидаемо: —")
        self.upgrades_lbl.configure(text="Осталось проков: —")
        self.pav_progress.set(0)
        self.pav_progress.configure(progress_color=C.CYAN)
        self._clear_roll_bars()
        self._clear_recommendations()
        if hasattr(self, "forecast_verdict_lbl"):
            is_max = self.level_var.get() == "+20"
            if is_max:
                self.forecast_verdict_lbl.configure(
                    text="🏁 Максимальный уровень (+20)", text_color=C.CYAN
                )
                self.forecast_stats_lbl.configure(
                    text="Шансы: —  |  Ожидаемо: PAV — | CV —"
                )
                self.forecast_advice_lbl.configure(
                    text="Артефакт полностью улучшен. Все 5 роллов распределены."
                )
            else:
                self.forecast_verdict_lbl.configure(
                    text="💎 Оценка потенциала артефакта", text_color=C.CYAN
                )
                self.forecast_stats_lbl.configure(
                    text="Шансы: S+ (—) | SS+ (—) | SSS (—)  |  Ожидаемо: PAV — | CV —"
                )
                self.forecast_advice_lbl.configure(
                    text="Введите характеристики артефакта и нажмите «Рассчитать»."
                )
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", "Введите характеристики артефакта и нажмите «Рассчитать».")

    def _input_snapshot(self):
        return (
            self.slot_var.get(), self.main_stat_var.get(),
            self.set_var.get(), self.character_var.get(),
            self.level_var.get(), self.initial_stats_var.get(),
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

    # ──────────────────────────────────────────────────────────────────
    #  ВИЗУАЛИЗАЦИЯ РОЛЛОВ
    # ──────────────────────────────────────────────────────────────────
    def _clear_roll_bars(self):
        for child in self.rolls_frame.winfo_children():
            child.destroy()
        self.roll_bars = {}

    def _render_roll_bars(self, ev):
        """Отрисовать прогресс-бары для каждого сабстата."""
        self._clear_roll_bars()
        if not ev.substats:
            return

        weights = self._collect_weights(self.preset_var.get())
        max_rolls = max(len(ev.roll_counts.get(s, [])) for s in ev.substats) if ev.substats else 1

        for stat, value in ev.substats.items():
            rolls = ev.roll_counts.get(stat, [])
            n_rolls = len(rolls)
            weight = weights.get(stat, 0.0)

            row = ctk.CTkFrame(self.rolls_frame, fg_color=C.TRANSPARENT, height=24)
            row.pack(fill="x", pady=1)

            # Цвет по весу
            if weight >= 2.0:
                bar_color = C.GOLD
            elif weight >= 1.0:
                bar_color = C.CYAN
            elif weight >= 0.5:
                bar_color = C.ORANGE_WARM
            else:
                bar_color = C.TEXT_MUTED

            ctk.CTkLabel(
                row, text=f"{stat}", font=("Segoe UI", 10),
                text_color=bar_color, width=140, anchor="w",
            ).pack(side="left")

            bar = ctk.CTkProgressBar(
                row, width=120, height=10, corner_radius=5,
                fg_color=C.BG_CARD, progress_color=bar_color,
            )
            bar.pack(side="left", padx=(4, 6))
            bar.set(n_rolls / max(max_rolls, 1))
            self.roll_bars[stat] = bar

            roll_text = describe_rolls(rolls) if rolls else "—"
            ctk.CTkLabel(
                row, text=f"{value:f}  ({roll_text})",
                font=("Consolas", 10), text_color=C.TEXT_SUBS,
            ).pack(side="left")

    # ──────────────────────────────────────────────────────────────────
    #  РАСЧЁТ
    # ──────────────────────────────────────────────────────────────────
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
                level, is_3_stat, entries,
                self._collect_weights(role_name),
                slot=slot, main_stat=main_stat,
            )
        except ArtifactInputError as exc:
            self._show_message(f"❌ {exc}")
            return

        rank, color = get_rank(ev.potential_pct)

        # Обновить карточку ранга
        self.rank_label.configure(text=rank, text_color=color)
        self.rank_subtitle_lbl.configure(
            text=f"Потенциал: {ev.potential_pct:.1f}%  |  {slot}  |  {role_name}",
        )

        # Обновить прогресс-бар
        pav_val = min(ev.potential_pct / 100.0, 1.0)
        self.pav_progress.set(pav_val)
        self.pav_progress.configure(progress_color=color)

        self.pav_current_lbl.configure(
            text=f"Текущий PAV: {ev.current_score:.1f} бал. ({ev.current_pct:.1f}%)",
        )
        self.pav_potential_lbl.configure(
            text=f"Потолок +20: {ev.max_possible_score:.1f} бал. ({ev.potential_pct:.1f}%)",
        )
        self.pav_expected_lbl.configure(
            text=f"Ожидаемо +20: {ev.expected_score:.1f} бал. ({ev.expected_pct:.1f}%)",
        )
        self.upgrades_lbl.configure(text=ev.upgrades_info)

        # Отрисовать бары роллов
        self._render_roll_bars(ev)

        # Совместимость и рекомендации персонажей
        substats_dict = {s: str(v) for s, v in ev.substats.items()}
        self._render_recommendations(slot, main_stat, substats_dict)

        # Прогноз улучшений через AnimeGameData Math
        forecast = None
        try:
            forecast = calculate_upgrade_forecast(
                slot=slot,
                main_stat=main_stat,
                current_substats=ev.substats,
                level=level,
                substat_weights=self._collect_weights(role_name),
            )
            self._render_upgrade_forecast(forecast)
        except Exception as e:
            print("FORECAST ERROR:", str(e))
            import traceback
            traceback.print_exc()

        # Текстовый отчёт
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
        if forecast and forecast.current_level < 20:
            report_lines.extend([
                "\n=== ПРОГНОЗ УЛУЧШЕНИЙ ДО +20 (AnimeGameData Math) ===",
                f"Вердикт: {forecast.verdict}",
                f"Шанс S+ (≥65% PAV): {forecast.prob_s_plus:.1f}%",
                f"Шанс SS+ (≥80% PAV): {forecast.prob_ss_plus:.1f}%",
                f"Шанс SSS (≥90% PAV): {forecast.prob_sss:.1f}%",
                f"Ожидаемый PAV на +20: {forecast.expected_pav:.1f}%",
                f"Ожидаемый Crit Value: {forecast.expected_cv:.1f}",
                f"Совет: {forecast.advice}",
            ])
        self._show_message("\n".join(report_lines))

        # Сохранить результат
        self.last_calculation = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "slot": slot,
            "main_stat": main_stat,
            "role": role_name,
            "set_key": cb.SET_NAME_TO_KEY.get(self.set_var.get(), ""),
            "character": self.character_var.get(),
            "level": self.level_var.get(),
            "rank": rank,
            "current_pct": round(ev.current_pct, 1),
            "potential_pct": round(ev.potential_pct, 1),
            "expected_pct": round(ev.expected_pct, 1),
            "substats": {k: float(v) for k, v in ev.substats.items()},
            "forecast": {
                "verdict": forecast.verdict if forecast else "",
                "prob_s_plus": round(forecast.prob_s_plus, 1) if forecast else 0.0,
                "prob_ss_plus": round(forecast.prob_ss_plus, 1) if forecast else 0.0,
                "expected_cv": round(forecast.expected_cv, 1) if forecast else 0.0,
            } if forecast else None,
        }
        self._calc_snapshot = self._input_snapshot()
        self.save_btn.configure(text="💾  Сохранить", state="normal")
        self.share_btn.configure(state="normal")

    def _render_upgrade_forecast(self, forecast: UpgradeForecastResult):
        if not hasattr(self, "forecast_verdict_lbl") or not forecast:
            return
        if forecast.current_level >= 20:
            self.forecast_verdict_lbl.configure(
                text="🏁 Максимальный уровень (+20)", text_color=C.CYAN
            )
            self.forecast_stats_lbl.configure(
                text="Шансы: —  |  Ожидаемо: PAV — | CV —"
            )
            self.forecast_advice_lbl.configure(
                text="Артефакт полностью улучшен. Все 5 роллов распределены."
            )
            return

        self.forecast_verdict_lbl.configure(
            text=forecast.verdict, text_color=forecast.verdict_color
        )
        stats_text = (
            f"🎯 Шанс S+ (≥65%): {forecast.prob_s_plus:.1f}%  |  "
            f"🌟 SS+ (≥80%): {forecast.prob_ss_plus:.1f}%  |  "
            f"👑 SSS: {forecast.prob_sss:.1f}%\n"
            f"📊 Ожид. PAV на +20: {forecast.expected_pav:.1f}%  |  "
            f"⚔️ Ожид. CV: {forecast.expected_cv:.1f}"
        )
        self.forecast_stats_lbl.configure(text=stats_text)
        self.forecast_advice_lbl.configure(text=f"💡 {forecast.advice}")

    def _clear_recommendations(self):
        for child in self.compat_frame.winfo_children():
            child.destroy()
        self.compat_lbl = ctk.CTkLabel(
            self.compat_frame,
            text="Выберите сет артефакта или персонажа для оценки совместимости.",
            font=("Segoe UI", 11), text_color=C.TEXT_MUTED,
            wraplength=430, justify="left",
        )
        self.compat_lbl.pack(padx=10, pady=8, anchor="w")

    def _apply_character_and_calculate(self, build: cb.CharacterBuild):
        self.character_var.set(build.display_name)
        self._on_character_change(build.display_name)
        self.calculate()

    def _render_recommendations(self, slot: str, main_stat: str, substats: dict):
        for child in self.compat_frame.winfo_children():
            child.destroy()

        chosen_char_name = self.character_var.get()
        chosen_build = cb.get_build_by_display_name(chosen_char_name)

        set_name = self.set_var.get()
        set_key = cb.SET_NAME_TO_KEY.get(set_name, "")

        # 1. Если выбран конкретный персонаж: выводим статус совместимости
        if chosen_build:
            res = cb.evaluate_artifact_for_build(
                chosen_build, slot, main_stat, substats, set_name_or_key=set_key
            )
            banner = ctk.CTkFrame(self.compat_frame, fg_color=C.BG_PANEL, corner_radius=6)
            banner.pack(fill="x", padx=6, pady=4)

            verdict_color = C.GREEN if res.main_stat_matches else C.RED
            icon = "⭐" if res.is_ideal else ("✅" if res.main_stat_matches else "⚠️")
            ctk.CTkLabel(
                banner,
                text=f"{icon} {res.verdict} для {chosen_build.display_name} ({res.score:.0f}%)",
                font=("Segoe UI", 11, "bold"), text_color=verdict_color, anchor="w",
            ).pack(fill="x", padx=8, pady=(4, 1))

            ctk.CTkLabel(
                banner,
                text=res.explanation,
                font=("Segoe UI", 10), text_color=C.TEXT_PRIMARY if res.main_stat_matches else C.YELLOW_WARN,
                wraplength=430, justify="left", anchor="w",
            ).pack(fill="x", padx=8, pady=(0, 4))

        # 2. Рекомендации по сету и лучшим носителям
        rec_builds = cb.find_top_characters_for_artifact(
            slot=slot, main_stat=main_stat, substats=substats,
            set_name_or_key=set_key, limit=3
        )

        header_str = "🏆 Рекомендуемые персонажи"
        if set_name and set_name != "(Без сета / Любой)":
            header_str += f" (Сет: {set_name})"

        ctk.CTkLabel(
            self.compat_frame, text=header_str, font=("Segoe UI", 10, "bold"),
            text_color=C.GOLD, anchor="w",
        ).pack(fill="x", padx=6, pady=(4, 2))

        for rec in rec_builds:
            if chosen_build and rec.build.display_name == chosen_build.display_name:
                continue

            row = ctk.CTkFrame(self.compat_frame, fg_color=C.BG_CARD_ALT, corner_radius=6)
            row.pack(fill="x", padx=6, pady=2)

            btn = ctk.CTkButton(
                row, text="Примерить", width=80, height=24,
                font=("Segoe UI", 10, "bold"),
                fg_color=C.CYAN_DIM, hover_color=C.CYAN, text_color=C.BG_DEEP,
                command=lambda b=rec.build: self._apply_character_and_calculate(b),
            )
            btn.pack(side="right", padx=6, pady=4)

            score_color = C.GREEN if rec.score >= 70 else (C.GOLD if rec.score >= 50 else C.TEXT_MUTED)
            info_txt = f"{rec.build.display_name} — {rec.verdict} ({rec.score:.0f}%)"
            ctk.CTkLabel(
                row, text=info_txt, font=("Segoe UI", 10, "bold"),
                text_color=score_color, anchor="w",
            ).pack(fill="x", padx=8, pady=(4, 1))

            sub_note = rec.explanation if len(rec.explanation) < 70 else rec.explanation[:67] + "..."
            ctk.CTkLabel(
                row, text=sub_note, font=("Segoe UI", 9),
                text_color=C.TEXT_SUBS, anchor="w",
            ).pack(fill="x", padx=8, pady=(0, 4))

    calculate_artifact = calculate

    # ──────────────────────────────────────────────────────────────────
    #  ИСТОРИЯ
    # ──────────────────────────────────────────────────────────────────
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
        set_str = self.set_var.get()
        set_line = f"🔮 Сет: {set_str}\n" if set_str and set_str != "(Без сета / Любой)" else ""
        char_str = self.character_var.get()
        char_line = f"👤 Персонаж: {char_str}\n" if char_str and char_str != "(Выбрать персонажа...)" else ""
        forecast_line = ""
        fc = c.get("forecast")
        if fc and fc.get("verdict"):
            forecast_line = f"🔮 Прогноз (+20): {fc['verdict']} (S+: {fc['prob_s_plus']}%, CV: {fc['expected_cv']})\n"
        card_text = (
            "⚔️ **Genshin Impact — Карточка Артефакта** ⚔️\n"
            f"🧩 Тип: {c['slot']}\n"
            f"{set_line}"
            f"🎯 Основной стат: {c['main_stat']}\n"
            f"{char_line}"
            f"🎯 Роль: {c['role']}\n"
            f"🔹 Уровень: {c['level']} | 🏆 Ранг потенциала: **{c['rank']}**\n"
            f"📊 Текущая ценность (PAV): {c['current_pct']}%\n"
            f"🚀 Потолок на +20: **{c['potential_pct']}%**\n"
            f"📈 Ожидаемо на +20: {c['expected_pct']}%\n"
            f"{forecast_line}"
            f"📜 Характеристики:\n{stats_text}\n"
            "───────────────\n"
            "Сгенерировано в Artifact Calculator"
        )
        self.clipboard_clear()
        self.clipboard_append(card_text)
        self.share_btn.configure(text="✅ Скопировано!")
        self.after(2000, lambda: self.share_btn.configure(text="📋  Скопировать отчёт"))

    # ──────────────────────────────────────────────────────────────────
    #  ИМПОРТ/ЭКСПОРТ
    # ──────────────────────────────────────────────────────────────────
    def load_artifact_from_good(self, parsed: good_adapter.ParsedArtifact):
        slot = "Корона разума" if parsed.slot == "Корона проницательности" else parsed.slot
        self.slot_var.set(slot)
        self._highlight_slot(slot)
        self._update_main_stat_options(slot, invalidate=False)
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

        # 1. Установка сета артефакта
        if parsed.set_key:
            set_ru = cb.get_set_name_ru(parsed.set_key)
            if set_ru:
                self.set_var.set(set_ru)
            else:
                self.set_var.set("(Без сета / Любой)")
        else:
            self.set_var.set("(Без сета / Любой)")
        self._on_set_change(self.set_var.get())

        # 2. Привязка к персонажу из location
        if parsed.location:
            matched_build = cb.find_build_for_character(parsed.location)
            if matched_build:
                self.character_var.set(matched_build.display_name)
                self._on_character_change(matched_build.display_name)
            else:
                self.character_var.set("(Выбрать персонажа...)")
                self._on_character_change("(Выбрать персонажа...)")
        else:
            self.character_var.set("(Выбрать персонажа...)")
            self._on_character_change("(Выбрать персонажа...)")

        self._invalidate_calculation()
        self.calculate()
        if self.last_calculation is None and parsed.level > 4:
            self.initial_stats_var.set("3 сабстата")
            self.calculate()
            if self.last_calculation is None:
                self.initial_stats_var.set("4 сабстата")

        # Переключить экран на калькулятор для моментального просмотра результата
        self.show_view("calc")

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

        set_key = cb.get_set_key_from_name(self.set_var.get()) or "GladiatorsFinale"
        chosen_build = cb.get_build_by_display_name(self.character_var.get())
        location = ""
        if chosen_build:
            for k, v in cb.CHARACTER_KEY_MAP.items():
                if v == chosen_build.name:
                    location = k
                    break

        raw_art = {
            "slot": self.slot_var.get(),
            "main_stat": self.main_stat_var.get(),
            "level": level,
            "rarity": 5,
            "substats": substats,
            "set_key": set_key,
            "location": location,
        }
        return good_adapter.to_good_artifact(raw_art)

    def bulk_import_to_history(self, artifacts):
        history = self._load_history()
        role_name = self.preset_var.get()
        default_weights = self._collect_weights(role_name)
        for parsed in artifacts:
            slot_name = "Корона разума" if parsed.slot == "Корона проницательности" else parsed.slot
            location = parsed.location if parsed.location else "Инвентарь"

            char_build = cb.find_build_for_character(location) if location != "Инвентарь" else None
            weights = char_build.substat_weights if char_build else default_weights
            art_role = f"Персонаж: {char_build.name}" if char_build else role_name

            rank_str = "—"
            curr_pct = 0.0
            pot_pct = 0.0
            exp_pct = 0.0
            try:
                lvl = parsed.level
                if lvl in (0, 4, 8, 12, 16, 20) and parsed.substats:
                    is_3_stat = len(parsed.substats) <= 3 and lvl <= 4
                    entries_list = [(i + 1, s, str(v)) for i, (s, v) in enumerate(parsed.substats)]
                    ev = evaluate_artifact(lvl, is_3_stat, entries_list, weights, slot=slot_name, main_stat=parsed.main_stat)
                    rank_str, _ = get_rank(ev.potential_pct)
                    curr_pct = round(ev.current_pct, 1)
                    pot_pct = round(ev.potential_pct, 1)
                    exp_pct = round(ev.expected_pct, 1)
            except Exception:
                pass

            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "slot": slot_name,
                "main_stat": parsed.main_stat,
                "role": art_role,
                "level": f"+{parsed.level}",
                "rank": rank_str,
                "current_pct": curr_pct,
                "potential_pct": pot_pct,
                "expected_pct": exp_pct,
                "substats": {s: float(v) for s, v in parsed.substats},
                "set_key": parsed.set_key,
                "location": location,
            }
            history.insert(0, entry)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

    # ──────────────────────────────────────────────────────────────────
    #  CLIPBOARD / CONTEXT MENU (Ctrl+V/C/A/X для кириллицы)
    # ──────────────────────────────────────────────────────────────────
    def _handle_control_keys(self, event):
        widget = getattr(event, "widget", None)
        if widget is None:
            return
        keysym = getattr(event, "keysym", "").lower()
        keycode = getattr(event, "keycode", 0)

        if keycode == 86 and keysym != "v":  # Ctrl+V
            try:
                text = None
                try:
                    text = widget.clipboard_get()
                except Exception:
                    pass
                if not text:
                    try:
                        text = self.clipboard_get()
                    except Exception:
                        pass
                if not text:
                    return
                if hasattr(widget, "delete"):
                    try:
                        widget.delete("sel.first", "sel.last")
                    except Exception:
                        pass
                if hasattr(widget, "insert"):
                    widget.insert("insert", text)
                    return "break"
            except Exception:
                pass
        elif keycode == 65 and keysym != "a":  # Ctrl+A
            if hasattr(widget, "select_range"):
                widget.select_range(0, "end")
                if hasattr(widget, "icursor"):
                    widget.icursor("end")
                return "break"
            elif hasattr(widget, "tag_add"):
                widget.tag_add("sel", "1.0", "end")
                return "break"
        elif keycode == 67 and keysym != "c":  # Ctrl+C
            try:
                selected = None
                if hasattr(widget, "selection_get"):
                    try:
                        selected = widget.selection_get()
                    except Exception:
                        pass
                if selected:
                    self.clipboard_clear()
                    self.clipboard_append(selected)
                    return "break"
            except Exception:
                pass
        elif keycode == 88 and keysym != "x":  # Ctrl+X
            try:
                selected = None
                if hasattr(widget, "selection_get"):
                    try:
                        selected = widget.selection_get()
                    except Exception:
                        pass
                if selected:
                    self.clipboard_clear()
                    self.clipboard_append(selected)
                    if hasattr(widget, "delete"):
                        try:
                            widget.delete("sel.first", "sel.last")
                        except Exception:
                            pass
                    return "break"
            except Exception:
                pass

    def _attach_context_menu(self, widget):
        try:
            target = getattr(widget, "_entry", getattr(widget, "_textbox", widget))
            menu = tk.Menu(target, tearoff=0)

            def do_paste():
                try:
                    text = self.clipboard_get()
                    if hasattr(target, "delete"):
                        try:
                            target.delete("sel.first", "sel.last")
                        except Exception:
                            pass
                    if hasattr(target, "insert"):
                        target.insert("insert", text)
                except Exception:
                    pass

            def do_copy():
                try:
                    if hasattr(target, "selection_get"):
                        text = target.selection_get()
                        self.clipboard_clear()
                        self.clipboard_append(text)
                except Exception:
                    pass

            def do_cut():
                try:
                    if hasattr(target, "selection_get"):
                        text = target.selection_get()
                        self.clipboard_clear()
                        self.clipboard_append(text)
                        if hasattr(target, "delete"):
                            target.delete("sel.first", "sel.last")
                except Exception:
                    pass

            def do_select_all():
                if hasattr(target, "select_range"):
                    target.select_range(0, "end")
                    if hasattr(target, "icursor"):
                        target.icursor("end")
                elif hasattr(target, "tag_add"):
                    target.tag_add("sel", "1.0", "end")

            menu.add_command(label="Вставить (Ctrl+V)", command=do_paste)
            menu.add_command(label="Копировать (Ctrl+C)", command=do_copy)
            menu.add_command(label="Вырезать (Ctrl+X)", command=do_cut)
            menu.add_separator()
            menu.add_command(label="Выделить всё (Ctrl+A)", command=do_select_all)

            def show_menu(event):
                try:
                    menu.tk_popup(event.x_root, event.y_root)
                finally:
                    menu.grab_release()

            target.bind("<Button-3>", show_menu)
            if widget is not target and hasattr(widget, "bind"):
                widget.bind("<Button-3>", show_menu)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════
    #  ВКЛАДКА: GOOD / ENKA / KAMERA (Data Hub)
    # ══════════════════════════════════════════════════════════════════
    def _build_hub_view(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color=C.BG_PANEL, corner_radius=10, height=44)
        hdr.pack(fill="x", padx=4, pady=(6, 4))
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="⚡ Genshin Data Hub",
            font=("Segoe UI", 14, "bold"), text_color=C.GOLD,
        ).pack(side="left", padx=16)

        subnav_box = ctk.CTkFrame(hdr, fg_color=C.TRANSPARENT)
        subnav_box.pack(side="right", padx=10, pady=4)

        self._hub_subnav_buttons = {}
        sub_items = [
            ("kamera", "📷 Сканер рюкзака"),
            ("enka", "🌐 Enka.Network"),
            ("good", "📄 GOOD JSON"),
        ]

        for s_key, s_title in sub_items:
            btn = ctk.CTkButton(
                subnav_box,
                text=s_title,
                font=("Segoe UI", 11, "bold"),
                width=140,
                height=28,
                corner_radius=6,
                fg_color=C.CYAN_DIM if s_key == "kamera" else C.BG_CARD,
                hover_color=C.BG_HOVER,
                text_color=C.BG_DEEP if s_key == "kamera" else C.TEXT_MUTED,
                command=lambda k=s_key: self.show_hub_subtab(k),
            )
            btn.pack(side="left", padx=3)
            self._hub_subnav_buttons[s_key] = btn

        self._hub_container = ctk.CTkFrame(parent, fg_color=C.BG_DARK, corner_radius=10)
        self._hub_container.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self.tab_kamera = _FastFrame(self._hub_container, fg_color=C.BG_DARK)
        self.tab_enka = _FastFrame(self._hub_container, fg_color=C.BG_DARK)
        self.tab_good = _FastFrame(self._hub_container, fg_color=C.BG_DARK)

        self._hub_kamera_built = False
        self._hub_enka_built = False
        self._hub_good_built = False
        self._current_hub_subtab = "kamera"

        # Proxy for backwards compatibility with test stubs and legacy callers
        class _SubNavProxy:
            def __init__(proxy_self):
                pass
            def set(proxy_self, tab_name):
                self.show_hub_subtab(tab_name)
            def get(proxy_self):
                return self._current_hub_subtab
        self._good_tabview = _SubNavProxy()

        # Показать начальную подвкладку (Сканер рюкзака)
        self.show_hub_subtab("kamera")

    def show_hub_subtab(self, subtab_name: str):
        name_map = {
            "kamera": "kamera",
            "📷 Сканер рюкзака": "kamera",
            "enka": "enka",
            "🌐 Enka.Network": "enka",
            "good": "good",
            "📄 GOOD JSON": "good",
        }
        key = name_map.get(subtab_name, subtab_name)
        if key not in ("kamera", "enka", "good"):
            key = "kamera"

        self._current_hub_subtab = key

        if hasattr(self, "_hub_subnav_buttons"):
            for k, btn in self._hub_subnav_buttons.items():
                if k == key:
                    btn.configure(fg_color=C.CYAN_DIM, text_color=C.BG_DEEP)
                else:
                    btn.configure(fg_color=C.BG_CARD, text_color=C.TEXT_MUTED)

        if hasattr(self, "tab_kamera"):
            self.tab_kamera.pack_forget()
        if hasattr(self, "tab_enka"):
            self.tab_enka.pack_forget()
        if hasattr(self, "tab_good"):
            self.tab_good.pack_forget()

        if key == "kamera":
            if not self._hub_kamera_built:
                self._build_kamera_tab(self.tab_kamera, self._kamera_state, self, lambda: None)
                self._hub_kamera_built = True
            self.tab_kamera.pack(fill="both", expand=True, padx=4, pady=4)
        elif key == "enka":
            if not self._hub_enka_built:
                self._build_enka_tab(self.tab_enka, self, lambda: None)
                self._hub_enka_built = True
            self.tab_enka.pack(fill="both", expand=True, padx=4, pady=4)
        elif key == "good":
            if not self._hub_good_built:
                self._build_good_tab(self.tab_good, self, lambda: None)
                self._hub_good_built = True
            self.tab_good.pack(fill="both", expand=True, padx=4, pady=4)

    def open_kamera_dialog(self):
        return self.open_good_transfer_dialog(initial_tab="📷 Сканер рюкзака")

    def open_good_transfer_dialog(self, initial_tab=None):
        self._ensure_hub_built()
        self.show_view("hub")
        if initial_tab:
            self.show_hub_subtab(initial_tab)
        return self.view_hub

    # ─── Kamera Tab ───────────────────────────────────────────────────
    def _build_kamera_tab(self, tab, kamera_state, dialog, on_close):
        kamera_top = _FastFrame(tab, bg=C.BG_DARK)
        kamera_top.pack(fill="x", padx=10, pady=(6, 4))

        status_badge = _FastLabel(
            kamera_top, text="🔍 Проверка Inventory Kamera...",
            font=("Segoe UI", 11, "bold"), text_color=C.BLUE_LINK, bg=C.BG_DARK,
        )
        status_badge.pack(side="left", padx=(0, 10))

        btn_launch = ctk.CTkButton(
            kamera_top, text="🚀 Запустить", width=130,
            fg_color=C.KAMERA_BTN, hover_color=C.KAMERA_HOVER,
        )
        btn_launch.pack(side="left", padx=(0, 6))

        btn_install = ctk.CTkButton(
            kamera_top, text="⬇️ Установить", width=130,
            fg_color=C.GRAY_SLATE, hover_color=C.GRAY_SLATE_H,
        )

        btn_load_latest = ctk.CTkButton(
            kamera_top, text="📥 Последний скан", width=150,
            fg_color=C.TEAL_BTN, hover_color=C.TEAL_HOVER,
        )
        btn_load_latest.pack(side="left", padx=(0, 6))

        btn_browse = ctk.CTkButton(
            kamera_top, text="📁 Файл...", width=90,
            fg_color=C.GRAY, hover_color=C.GRAY_HOVER,
        )
        btn_browse.pack(side="left")

        info_lbl = _FastLabel(
            tab,
            text="⚠️ Перед сканированием: 1) Раскладка Windows → ENG. "
                 "2) В игре откройте меню Паймон (ESC). 3) В Kamera нажмите «Scan».",
            font=("Segoe UI", 10, "bold"), text_color=C.YELLOW_WARN, bg=C.BG_DARK,
            wraplength=760, justify="left",
        )
        info_lbl.pack(fill="x", padx=12, pady=(2, 4))

        # Фильтры
        fbar = _FastFrame(tab, bg=C.BG_DARK)
        fbar.pack(fill="x", padx=10, pady=(2, 4))

        _FastLabel(fbar, text="Слот:", text_color=C.TEXT_PRIMARY, bg=C.BG_DARK).pack(side="left", padx=(0, 4))
        slot_menu = ctk.CTkOptionMenu(
            fbar, values=["Все слоты", "Цветок жизни", "Перо смерти", "Пески времени", "Кубок пространства", "Корона проницательности"],
            width=135, fg_color=C.BG_CARD, button_color=C.BG_HOVER, button_hover_color=C.CYAN_DIM,
        )
        slot_menu.pack(side="left", padx=(0, 8))

        _FastLabel(fbar, text="Уровень:", text_color=C.TEXT_PRIMARY, bg=C.BG_DARK).pack(side="left", padx=(0, 4))
        lvl_menu = ctk.CTkOptionMenu(
            fbar, values=["Все уровни", "+20 только", "+16..+20", "+0..+15"],
            width=105, fg_color=C.BG_CARD, button_color=C.BG_HOVER, button_hover_color=C.CYAN_DIM,
        )
        lvl_menu.pack(side="left", padx=(0, 8))

        _FastLabel(fbar, text="Герой:", text_color=C.TEXT_PRIMARY, bg=C.BG_DARK).pack(side="left", padx=(0, 4))
        loc_menu = ctk.CTkOptionMenu(
            fbar, values=["Все", "Надетые", "В инвентаре"],
            width=100, fg_color=C.BG_CARD, button_color=C.BG_HOVER, button_hover_color=C.CYAN_DIM,
        )
        loc_menu.pack(side="left", padx=(0, 8))

        search_entry = ctk.CTkEntry(
            fbar, placeholder_text="🔍 Поиск...", width=130,
            fg_color=C.BG_INPUT, border_color=C.BG_HOVER,
        )
        search_entry.pack(side="left", padx=(0, 6))
        self._attach_context_menu(search_entry)

        # Пагинация
        page_bar = _FastFrame(tab, bg=C.BG_DARK)
        page_bar.pack(fill="x", padx=10, pady=(2, 4))

        count_lbl = _FastLabel(
            page_bar, text="Скан не загружен. Нажмите «Последний скан» или выберите файл.",
            font=("Segoe UI", 11, "bold"), text_color=C.YELLOW_WARN, bg=C.BG_DARK,
        )
        count_lbl.pack(side="left", padx=(0, 10))

        btn_next = ctk.CTkButton(page_bar, text="Вперед (10) ▶", width=105, fg_color=C.GRAY_SLATE, hover_color=C.GRAY_SLATE_H, state="disabled")
        btn_next.pack(side="right", padx=(4, 0))
        btn_prev = ctk.CTkButton(page_bar, text="◀ Назад (10)", width=105, fg_color=C.GRAY_SLATE, hover_color=C.GRAY_SLATE_H, state="disabled")
        btn_prev.pack(side="right", padx=(4, 0))
        page_lbl = _FastLabel(page_bar, text="", font=("Segoe UI", 11), bg=C.BG_DARK)
        page_lbl.pack(side="right", padx=6)

        # Список артефактов
        scroll = ctk.CTkScrollableFrame(tab, width=740, height=250, fg_color=C.BG_CARD, corner_radius=8)
        scroll.pack(fill="both", expand=True, padx=10, pady=4)

        # Нижняя панель
        bot = _FastFrame(tab, bg=C.BG_DARK)
        bot.pack(fill="x", padx=10, pady=(6, 4))

        btn_save_hist = ctk.CTkButton(
            bot, text="💾 Сохранить в Историю", width=200,
            fg_color=C.CYAN_DIM, hover_color=C.CYAN, text_color=C.BG_DEEP, state="disabled",
        )
        btn_save_hist.pack(side="left", padx=(0, 8))

        btn_copy_good = ctk.CTkButton(
            bot, text="📋 Скопировать GOOD", width=170,
            fg_color=C.PURPLE_BTN, hover_color=C.PURPLE_HOVER, state="disabled",
        )
        btn_copy_good.pack(side="left", padx=(0, 8))

        ctk.CTkButton(bot, text="Закрыть", command=on_close, width=90,
                      fg_color=C.GRAY, hover_color=C.GRAY_HOVER).pack(side="right")

        # ─── Логика ───
        def on_load_artifact(art):
            self.load_artifact_from_good(art)
            count_lbl.configure(
                text=f"✅ {art.slot} (+{art.level}) перенесен в калькулятор!",
                text_color=C.GREEN,
            )

        def render_page():
            for child in scroll.winfo_children():
                child.destroy()
            items = kamera_state["filtered_artifacts"]
            total = len(items)
            page = kamera_state["current_page"]
            ps = kamera_state["page_size"]
            total_pages = max(1, (total + ps - 1) // ps)
            if page >= total_pages:
                page = max(0, total_pages - 1)
                kamera_state["current_page"] = page
            btn_prev.configure(state="normal" if page > 0 else "disabled")
            btn_next.configure(state="normal" if page < total_pages - 1 else "disabled")
            if total == 0:
                page_lbl.configure(text="")
                msg = ("Нажмите «Запустить» или «Последний скан»."
                       if not kamera_state["all_artifacts"]
                       else "Нет артефактов, соответствующих фильтрам.")
                _FastLabel(scroll, text=msg, text_color=C.TEXT_DIM, bg=C.BG_CARD).pack(pady=40)
                return
            page_lbl.configure(text=f"Стр. {page + 1}/{total_pages}")
            count_lbl.configure(
                text=f"Показано: {min(ps, total - page * ps)} (Всего: {total})",
                text_color=C.BLUE_LIGHT,
            )
            start = page * ps
            end = min(start + ps, total)
            for art in items[start:end]:
                self._render_artifact_card(scroll, art, on_load_artifact)

        def on_prev():
            if kamera_state["current_page"] > 0:
                kamera_state["current_page"] -= 1
                render_page()

        def on_next():
            total = len(kamera_state["filtered_artifacts"])
            tp = max(1, (total + kamera_state["page_size"] - 1) // kamera_state["page_size"])
            if kamera_state["current_page"] < tp - 1:
                kamera_state["current_page"] += 1
                render_page()

        btn_prev.configure(command=on_prev)
        btn_next.configure(command=on_next)

        def apply_filters(*_args):
            slot_ch = slot_menu.get()
            lvl_ch = lvl_menu.get()
            loc_ch = loc_menu.get()
            query = search_entry.get().strip().lower()
            filtered = []
            for art in kamera_state["all_artifacts"]:
                if slot_ch != "Все слоты" and art.slot != slot_ch:
                    continue
                if lvl_ch == "+20 только" and art.level != 20:
                    continue
                elif lvl_ch == "+16..+20" and art.level < 16:
                    continue
                elif lvl_ch == "+0..+15" and art.level > 15:
                    continue
                if loc_ch == "Надетые" and not art.location:
                    continue
                elif loc_ch == "В инвентаре" and art.location:
                    continue
                if query:
                    match = (
                        query in art.set_key.lower()
                        or query in art.slot.lower()
                        or query in art.main_stat.lower()
                        or query in art.location.lower()
                        or any(query in s.lower() for s, _ in art.substats)
                    )
                    if not match:
                        continue
                filtered.append(art)
            filtered.sort(key=lambda a: (a.level, a.rarity), reverse=True)
            kamera_state["filtered_artifacts"] = filtered
            kamera_state["current_page"] = 0
            render_page()

        slot_menu.configure(command=apply_filters)
        lvl_menu.configure(command=apply_filters)
        loc_menu.configure(command=apply_filters)

        search_timer = [None]
        def on_search_key(e=None):
            if search_timer[0] is not None:
                try:
                    tab.after_cancel(search_timer[0])
                except Exception:
                    pass
            search_timer[0] = tab.after(180, apply_filters)

        search_entry.bind("<KeyRelease>", on_search_key)
        search_entry.bind("<Return>", lambda e: apply_filters())

        def load_scan_file(filepath, is_auto=False):
            try:
                artifacts, meta = kamera_adapter.load_kamera_good_file(filepath)
                if not artifacts:
                    info_lbl.configure(text=f"⚠️ В файле нет артефактов.", text_color=C.YELLOW_WARN)
                    return
                kamera_state["all_artifacts"] = artifacts
                kamera_state["metadata"] = meta
                kamera_state["current_file"] = filepath
                btn_save_hist.configure(state="normal")
                btn_copy_good.configure(state="normal")
                src = meta.get("source", "Kamera")
                msg = f"✅ {'Авто' if is_auto else ''}Загружено: {os.path.basename(filepath)} ({len(artifacts)} арт.) [{src}]"
                info_lbl.configure(text=msg, text_color=C.GREEN)
                apply_filters()
            except Exception as e:
                info_lbl.configure(text=f"❌ Ошибка: {e}", text_color=C.RED)

        def on_launch():
            try:
                kamera_adapter.launch_kamera()
                info_lbl.configure(
                    text="⏳ Kamera запускается! Нажмите «Да» в UAC, затем «Scan» в окне Kamera.",
                    text_color=C.YELLOW_WARN,
                )
                if kamera_state["watcher"] is None:
                    out_dirs = kamera_adapter.get_kamera_output_dirs()
                    watcher = kamera_adapter.KameraFolderWatcher(
                        folders=out_dirs,
                        callback=lambda p: dialog.after(0, lambda: load_scan_file(p, is_auto=True)),
                        poll_interval=1.0,
                    )
                    watcher.start()
                    kamera_state["watcher"] = watcher
            except PermissionError as e:
                info_lbl.configure(text=f"⚠️ {e}", text_color=C.ORANGE_WARM)
            except Exception as e:
                info_lbl.configure(text=f"❌ Ошибка: {e}", text_color=C.RED)

        btn_launch.configure(command=on_launch)

        def on_install():
            btn_install.configure(state="disabled", text="⏳ Загрузка...")
            info_lbl.configure(text="⏳ Скачивание Inventory Kamera (24 МБ)...", text_color=C.YELLOW_WARN)

            def worker():
                try:
                    kamera_adapter.download_and_extract_kamera("kamera")
                    dialog.after(0, install_done)
                except Exception as err:
                    dialog.after(0, lambda: install_err(str(err)))

            def install_done():
                btn_install.pack_forget()
                check_status()
                info_lbl.configure(text="✅ Inventory Kamera установлен!", text_color=C.GREEN)

            def install_err(err):
                btn_install.configure(state="normal", text="⬇️ Установить")
                info_lbl.configure(text=f"❌ Ошибка установки: {err}", text_color=C.RED)

            threading.Thread(target=worker, daemon=True).start()

        btn_install.configure(command=on_install)

        def check_status():
            exe = kamera_adapter.find_kamera_executable()
            if exe:
                parent = os.path.basename(os.path.dirname(str(exe)))
                status_badge.configure(text=f"🟢 Kamera готова ({parent})", text_color=C.GREEN)
                btn_launch.configure(state="normal")
                btn_install.pack_forget()
            else:
                status_badge.configure(text="⚠️ Сканер не найден", text_color=C.ORANGE_WARM)
                btn_launch.configure(state="disabled")
                btn_install.pack(side="left", padx=(0, 6))

        check_status()

        def on_load_latest():
            latest = kamera_adapter.find_latest_kamera_export()
            if latest:
                load_scan_file(str(latest))
            else:
                info_lbl.configure(text="ℹ️ Файлы скана не найдены. Запустите Kamera.", text_color=C.YELLOW_WARN)

        btn_load_latest.configure(command=on_load_latest)

        def on_browse():
            try:
                from tkinter import filedialog
                fp = filedialog.askopenfilename(
                    title="Выберите GOOD JSON файл",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                )
                if fp:
                    load_scan_file(fp)
            except Exception as e:
                info_lbl.configure(text=f"❌ {e}", text_color=C.RED)

        btn_browse.configure(command=on_browse)

        def on_save_all():
            arts = kamera_state["all_artifacts"]
            if not arts:
                return
            self.bulk_import_to_history(arts)
            info_lbl.configure(text=f"✅ {len(arts)} артефактов сохранены в историю!", text_color=C.GREEN)

        btn_save_hist.configure(command=on_save_all)

        def on_copy():
            cur = kamera_state.get("current_file")
            if cur and os.path.exists(cur):
                with open(cur, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = good_adapter.to_good_json(kamera_state["all_artifacts"])
            self.clipboard_clear()
            self.clipboard_append(content)
            info_lbl.configure(text="✅ GOOD JSON скопирован!", text_color=C.GREEN)

        btn_copy_good.configure(command=on_copy)

        # Автозагрузка
        init_latest = kamera_adapter.find_latest_kamera_export()
        if init_latest:
            load_scan_file(str(init_latest))

    # ─── Enka Tab ─────────────────────────────────────────────────────
    def _build_enka_tab(self, tab, dialog, on_close):
        _FastLabel(
            tab,
            text="ℹ️ Enka загружает открытую витрину профиля (до 8-12 героев). "
                 "Для всего рюкзака используйте Inventory Kamera.",
            font=("Segoe UI", 10), text_color=C.BLUE_LINK, bg=C.BG_DARK,
            wraplength=720, justify="left",
        ).pack(fill="x", padx=12, pady=(4, 2))

        top = _FastFrame(tab, bg=C.BG_DARK)
        top.pack(fill="x", padx=10, pady=(4, 4))

        _FastLabel(top, text="UID:", font=("Segoe UI", 12, "bold"),
                   text_color=C.TEXT_PRIMARY, bg=C.BG_DARK).pack(side="left", padx=(0, 6))
        uid_entry = ctk.CTkEntry(top, placeholder_text="618285856", width=150,
                                 fg_color=C.BG_INPUT, border_color=C.BG_HOVER)
        uid_entry.pack(side="left", padx=(0, 6))

        def on_paste_uid():
            try:
                clip = self.clipboard_get().strip()
                if clip:
                    uid_entry.delete(0, "end")
                    uid_entry.insert(0, clip)
            except Exception:
                pass

        ctk.CTkButton(top, text="📋", width=36, fg_color=C.GRAY_SLATE,
                      hover_color=C.GRAY_SLATE_H, command=on_paste_uid).pack(side="left", padx=(0, 8))
        self._attach_context_menu(uid_entry)

        btn_fetch = ctk.CTkButton(top, text="🔍 Загрузить витрину", width=160,
                                  fg_color=C.BLUE_BTN, hover_color="#0d47a1")
        btn_fetch.pack(side="left", padx=(0, 8))

        status_lbl = _FastLabel(top, text="Введите 9-значный UID",
                                font=("Segoe UI", 11), text_color=C.TEXT_DIM, bg=C.BG_DARK)
        status_lbl.pack(side="left", padx=5)

        char_bar = _FastFrame(tab, bg=C.BG_DARK)
        char_bar.pack(fill="x", padx=10, pady=4)

        profile_lbl = _FastLabel(char_bar, text="", font=("Segoe UI", 12, "bold"),
                                 text_color=C.BLUE_LIGHT, bg=C.BG_DARK)
        profile_lbl.pack(side="left", padx=(0, 15))

        _FastLabel(char_bar, text="Персонаж:", text_color=C.TEXT_PRIMARY, bg=C.BG_DARK).pack(side="left", padx=(0, 5))
        char_menu = ctk.CTkOptionMenu(
            char_bar, values=["(нет данных)"], width=250,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER, button_hover_color=C.CYAN_DIM,
        )
        char_menu.pack(side="left", padx=(0, 10))

        scroll = ctk.CTkScrollableFrame(tab, width=700, height=290, fg_color=C.BG_CARD, corner_radius=8)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        _FastLabel(scroll, text="Загрузите витрину по UID.", text_color=C.TEXT_DIM, bg=C.BG_CARD).pack(pady=40)

        btn_frame = _FastFrame(tab, bg=C.BG_DARK)
        btn_frame.pack(fill="x", padx=10, pady=8)

        btn_export_good = ctk.CTkButton(
            btn_frame, text="📋 Экспорт в GOOD", width=180,
            fg_color=C.PURPLE_BTN, hover_color=C.PURPLE_HOVER, state="disabled",
        )
        btn_export_good.pack(side="left", padx=(0, 8))

        btn_save_hist = ctk.CTkButton(
            btn_frame, text="💾 Сохранить в историю", width=180,
            fg_color=C.CYAN_DIM, hover_color=C.CYAN, text_color=C.BG_DEEP, state="disabled",
        )
        btn_save_hist.pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_frame, text="Закрыть", command=on_close, width=90,
                      fg_color=C.GRAY, hover_color=C.GRAY_HOVER).pack(side="right")

        enka_state: dict[str, Any] = {"profile": None, "characters": []}

        def on_load_art(art):
            self.load_artifact_from_good(art)
            status_lbl.configure(text=f"✅ {art.slot} перенесен!", text_color=C.GREEN)

        def render_char(idx, show_all=False):
            for child in scroll.winfo_children():
                child.destroy()
            chars = enka_state["characters"]
            if not chars:
                return
            if show_all:
                items = [(c.name, art) for c in chars for art in c.artifacts]
                if not items:
                    _FastLabel(scroll, text="Нет 5★ артефактов.", text_color=C.TEXT_DIM, bg=C.BG_CARD).pack(pady=30)
                    return
            else:
                if idx >= len(chars):
                    return
                ch = chars[idx]
                items = [(ch.name, art) for art in ch.artifacts]
                if not items:
                    _FastLabel(scroll, text=f"У {ch.name} нет артефактов.", text_color=C.TEXT_DIM, bg=C.BG_CARD).pack(pady=30)
                    return
            for name, art in items:
                self._render_artifact_card(scroll, art, on_load_art, char_name=name if show_all else None)

        def on_char_select(choice):
            if choice.startswith("🌟"):
                render_char(0, show_all=True)
                return
            for idx, c in enumerate(enka_state["characters"]):
                if choice.startswith(c.name):
                    render_char(idx, show_all=False)
                    break

        def on_fetch_success(profile):
            btn_fetch.configure(state="normal")
            enka_state["profile"] = profile
            enka_state["characters"] = profile.characters
            profile_lbl.configure(text=f"👤 {profile.nickname} (Ур. {profile.level})")
            total = sum(len(c.artifacts) for c in profile.characters)
            if not profile.characters:
                status_lbl.configure(text="⚠️ Нет персонажей в витрине.", text_color=C.GOLD)
                return
            all_opt = f"🌟 Все ({total} арт.)"
            names = [all_opt] + [f"{c.name} ({len(c.artifacts)} арт.)" for c in profile.characters]
            char_menu.configure(values=names, command=on_char_select)
            char_menu.set(all_opt)
            render_char(0, show_all=True)
            btn_export_good.configure(state="normal")
            btn_save_hist.configure(state="normal")
            status_lbl.configure(text=f"✅ {len(profile.characters)} персонажей ({total} арт.)!", text_color=C.GREEN)

        def on_fetch_error(err):
            btn_fetch.configure(state="normal")
            status_lbl.configure(text=f"❌ {err}", text_color=C.RED)

        def start_fetch():
            uid = uid_entry.get().strip()
            if not uid:
                status_lbl.configure(text="❌ Введите UID!", text_color=C.RED)
                return
            status_lbl.configure(text="⏳ Подключение...", text_color=C.GOLD)
            btn_fetch.configure(state="disabled")

            def worker():
                try:
                    profile = enka_adapter.fetch_enka_profile(uid, use_cache=True)
                    dialog.after(0, lambda: on_fetch_success(profile))
                except enka_adapter.EnkaPrivateShowcaseError as e:
                    dialog.after(0, lambda: on_fetch_error(str(e)))
                except enka_adapter.EnkaRateLimitError as e:
                    dialog.after(0, lambda: on_fetch_error(str(e)))
                except enka_adapter.EnkaUserNotFoundError as e:
                    dialog.after(0, lambda: on_fetch_error(str(e)))
                except Exception as e:
                    dialog.after(0, lambda: on_fetch_error(f"Ошибка: {e}"))

            threading.Thread(target=worker, daemon=True).start()

        btn_fetch.configure(command=start_fetch)

        def do_export_good():
            prof = enka_state["profile"]
            if not prof:
                return
            try:
                j = enka_adapter.enka_profile_to_good_json(prof)
                self.clipboard_clear()
                self.clipboard_append(j)
                total = sum(len(c.artifacts) for c in prof.characters)
                status_lbl.configure(text=f"✅ {total} арт. → GOOD JSON!", text_color=C.GREEN)
            except Exception as e:
                status_lbl.configure(text=f"❌ {e}", text_color=C.RED)

        btn_export_good.configure(command=do_export_good)

        def do_save_hist():
            prof = enka_state["profile"]
            if not prof:
                return
            all_arts = [art for c in prof.characters for art in c.artifacts]
            if not all_arts:
                status_lbl.configure(text="⚠️ Нет артефактов.", text_color=C.GOLD)
                return
            self.bulk_import_to_history(all_arts)
            status_lbl.configure(text=f"✅ {len(all_arts)} арт. → история!", text_color=C.GREEN)

        btn_save_hist.configure(command=do_save_hist)

    # ─── GOOD Tab ─────────────────────────────────────────────────────
    def _build_good_tab(self, tab, dialog, on_close):
        info_lbl = _FastLabel(
            tab, text="Вставьте GOOD JSON для импорта или экспортируйте данные:",
            font=("Segoe UI", 11), text_color=C.TEXT_DIM, bg=C.BG_DARK,
        )
        info_lbl.pack(pady=(6, 4))

        textbox = ctk.CTkTextbox(
            tab, width=700, height=330, font=("Consolas", 11),
            fg_color=C.BG_CARD, text_color=C.TEXT_PRIMARY, corner_radius=8,
        )
        textbox.pack(padx=10, pady=5, fill="both", expand=True)
        self._attach_context_menu(textbox)

        bf = _FastFrame(tab, bg=C.BG_DARK)
        bf.pack(fill="x", padx=10, pady=8)

        def do_import():
            content = textbox.get("1.0", "end").strip()
            if not content:
                info_lbl.configure(text="❌ Поле пусто!", text_color=C.RED)
                return
            try:
                parsed = good_adapter.from_good_json(content)
                if not parsed:
                    info_lbl.configure(text="❌ Артефакты не найдены", text_color=C.RED)
                    return
                self.load_artifact_from_good(parsed[0])
                if len(parsed) > 1:
                    self.bulk_import_to_history(parsed)
                    info_lbl.configure(text=f"✅ 1 арт. → калькулятор, {len(parsed)} → история!", text_color=C.GREEN)
                else:
                    info_lbl.configure(text="✅ Загружено!", text_color=C.GREEN)
            except Exception as e:
                info_lbl.configure(text=f"❌ {e}", text_color=C.RED)

        def do_export_active():
            try:
                good_obj = self.export_current_artifact_to_good()
                j = json.dumps(good_obj, indent=2, ensure_ascii=False)
                textbox.delete("1.0", "end")
                textbox.insert("1.0", j)
                self.clipboard_clear()
                self.clipboard_append(j)
                info_lbl.configure(text="✅ Экспортировано и скопировано!", text_color=C.GREEN)
            except Exception as e:
                info_lbl.configure(text=f"❌ {e}", text_color=C.RED)

        def do_export_history():
            try:
                history = self._load_history()
                if not history:
                    info_lbl.configure(text="⚠️ История пуста!", text_color=C.GOLD)
                    return
                good_list = []
                for item in history:
                    subs = [{"stat": k, "value": v} for k, v in item.get("substats", {}).items()]
                    raw = {
                        "slot": item.get("slot", "Перо смерти"),
                        "main_stat": item.get("main_stat", "Сила атаки"),
                        "level": int(str(item.get("level", "0")).replace("+", "") or 0),
                        "rarity": 5,
                        "substats": subs,
                        "set_key": item.get("set_key", ""),
                    }
                    try:
                        good_list.append(good_adapter.to_good_artifact(raw))
                    except Exception:
                        pass
                j = good_adapter.to_good_json(good_list)
                textbox.delete("1.0", "end")
                textbox.insert("1.0", j)
                self.clipboard_clear()
                self.clipboard_append(j)
                info_lbl.configure(text=f"✅ {len(good_list)} арт. → буфер!", text_color=C.GREEN)
            except Exception as e:
                info_lbl.configure(text=f"❌ {e}", text_color=C.RED)

        def do_load_file():
            try:
                from tkinter import filedialog
                fp = filedialog.askopenfilename(
                    title="Выберите GOOD JSON",
                    filetypes=[("JSON", "*.json"), ("All", "*.*")],
                )
                if not fp:
                    return
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                textbox.delete("1.0", "end")
                textbox.insert("1.0", content)
                do_import()
            except Exception as e:
                info_lbl.configure(text=f"❌ {e}", text_color=C.RED)

        ctk.CTkButton(bf, text="📁 Загрузить .json", command=do_load_file, width=150,
                      fg_color=C.TEAL_BTN, hover_color=C.TEAL_HOVER).pack(side="left", padx=(0, 4))
        ctk.CTkButton(bf, text="📥 Импорт текста", command=do_import, width=130,
                      fg_color=C.BLUE_BTN, hover_color="#0d47a1").pack(side="left", padx=(0, 4))
        ctk.CTkButton(bf, text="📋 Экспорт текущего", command=do_export_active, width=140,
                      fg_color=C.GREEN_BTN, hover_color=C.GREEN_HOVER).pack(side="left", padx=(0, 4))
        ctk.CTkButton(bf, text="📜 Экспорт истории", command=do_export_history, width=130,
                      fg_color=C.PURPLE_BTN, hover_color=C.PURPLE_HOVER).pack(side="left", padx=(0, 4))
        ctk.CTkButton(bf, text="Закрыть", command=on_close, width=80,
                      fg_color=C.GRAY, hover_color=C.GRAY_HOVER).pack(side="right")

    # ──────────────────────────────────────────────────────────────────
    #  ОБЩИЙ РЕНДЕР КАРТОЧКИ АРТЕФАКТА
    # ──────────────────────────────────────────────────────────────────
    def _render_artifact_card(self, parent, art, on_click_cb, char_name=None):
        """Отрисовать карточку артефакта в стиле Genshin (ультралёгкая структура без лишних холстов)."""
        card = _FastFrame(parent, bg=C.BG_CARD_ALT, highlightthickness=1, highlightbackground=C.BORDER, bd=0)
        card.pack(fill="x", padx=4, pady=3)

        btn = _FastButton(
            card, text="📥 В калькулятор",
            font=("Segoe UI", 10, "bold"),
            fg_color=C.GREEN_BTN, hover_color=C.GREEN_HOVER, text_color=C.BG_DEEP,
            padx=10, pady=4,
            command=lambda: on_click_cb(art),
        )
        btn.pack(side="right", padx=10, pady=8)

        emoji = SLOT_EMOJI.get(art.slot, "📦")
        loc_str = f"👤 {char_name or art.location}" if (char_name or art.location) else "🎒 Инвентарь"
        set_str = f"  ({art.set_key})" if art.set_key else ""
        header_text = f"{emoji} {art.slot} +{art.level}{set_str}   {loc_str}   🎯 {art.main_stat}"

        header_lbl = _FastLabel(
            card, text=header_text, font=("Segoe UI", 11, "bold"),
            bg=C.BG_CARD_ALT, text_color=C.GREEN, anchor="w",
        )
        header_lbl.pack(fill="x", padx=10, pady=(6, 2))

        subs = "  |  ".join(f"{s}: {v}" for s, v in art.substats)
        subs_lbl = _FastLabel(
            card, text=subs, font=("Consolas", 10),
            bg=C.BG_CARD_ALT, text_color=C.TEXT_SUBS, anchor="w",
        )
        subs_lbl.pack(fill="x", padx=10, pady=(2, 4))

    # ══════════════════════════════════════════════════════════════════
    #  ВКЛАДКА: ИСТОРИЯ И ИНВЕНТАРЬ
    # ══════════════════════════════════════════════════════════════════
    def _build_history_view(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color=C.BG_DARK, corner_radius=10)
        top_bar.pack(fill="x", padx=4, pady=(2, 4))

        ctk.CTkLabel(
            top_bar, text="📜 История и Инвентарь",
            font=("Segoe UI", 14, "bold"), text_color=C.GOLD,
        ).pack(side="left", padx=12, pady=10)

        ctk.CTkOptionMenu(
            top_bar,
            values=["Все слоты"] + list(ARTIFACT_SLOTS),
            variable=self._hist_slot_filter,
            command=lambda _: self._refresh_history_view(),
            width=140,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER, button_hover_color=C.CYAN_DIM,
        ).pack(side="left", padx=4)

        ctk.CTkOptionMenu(
            top_bar,
            values=["Все артефакты", "🎒 В инвентаре", "👤 На персонажах"],
            variable=self._hist_loc_filter,
            command=lambda _: self._refresh_history_view(),
            width=150,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER, button_hover_color=C.CYAN_DIM,
        ).pack(side="left", padx=4)

        ctk.CTkOptionMenu(
            top_bar,
            values=["Все ранги", "SSS", "SS", "S", "A", "B", "C"],
            variable=self._hist_rank_filter,
            command=lambda _: self._refresh_history_view(),
            width=110,
            fg_color=C.BG_CARD, button_color=C.BG_HOVER, button_hover_color=C.CYAN_DIM,
        ).pack(side="left", padx=4)

        search_entry = ctk.CTkEntry(
            top_bar, placeholder_text="🔍 Поиск по сету / статам / герою...",
            textvariable=self._hist_search_var, width=180,
            fg_color=C.BG_CARD, border_color=C.BG_HOVER,
        )
        search_entry.pack(side="left", padx=6)

        hist_timer = [None]
        def on_hist_search_key(e=None):
            if hist_timer[0] is not None:
                try:
                    parent.after_cancel(hist_timer[0])
                except Exception:
                    pass
            hist_timer[0] = parent.after(180, self._refresh_history_view)

        search_entry.bind("<KeyRelease>", on_hist_search_key)
        search_entry.bind("<Return>", lambda _: self._refresh_history_view())

        self._hist_count_lbl = ctk.CTkLabel(
            top_bar, text="", font=("Segoe UI", 11), text_color=C.TEXT_DIM,
        )
        self._hist_count_lbl.pack(side="left", padx=8)

        ctk.CTkButton(
            top_bar, text="🗑️ Очистить всё", width=120, height=30,
            fg_color=C.GRAY, hover_color=C.RED_ERR,
            command=self._clear_all_history,
        ).pack(side="right", padx=10)

        self._hist_scroll = ctk.CTkScrollableFrame(
            parent, fg_color=C.BG_DARK, corner_radius=10,
        )
        self._hist_scroll.pack(fill="both", expand=True, padx=4, pady=4)

    def _refresh_history_view(self):
        if not hasattr(self, "_hist_scroll"):
            return
        for child in self._hist_scroll.winfo_children():
            child.destroy()

        history = self._load_history()
        if not history:
            ctk.CTkLabel(
                self._hist_scroll,
                text="История пуста. Сохраняйте артефакты из калькулятора или импортируйте через Enka / Kamera / GOOD.",
                font=("Segoe UI", 12), text_color=C.TEXT_DIM,
            ).pack(pady=40)
            if hasattr(self, "_hist_count_lbl"):
                self._hist_count_lbl.configure(text="Всего: 0")
            return

        sel_slot = self._hist_slot_filter.get()
        sel_loc = self._hist_loc_filter.get()
        sel_rank = self._hist_rank_filter.get()
        query = self._hist_search_var.get().strip().lower()

        filtered = []
        for it in history:
            slot = it.get("slot", "")
            if sel_slot != "Все слоты" and slot != sel_slot:
                continue
            loc = it.get("location", "Инвентарь")
            if sel_loc == "🎒 В инвентаре" and loc != "Инвентарь":
                continue
            if sel_loc == "👤 На персонажах" and loc == "Инвентарь":
                continue
            rank = it.get("rank", "—")
            if sel_rank != "Все ранги" and rank != sel_rank:
                continue
            if query:
                set_name = cb.get_set_name_ru(it.get("set_key", ""))
                search_blob = f"{slot} {loc} {it.get('set_key','')} {set_name} {it.get('main_stat','')} {it.get('role','')} {list(it.get('substats',{}).keys())}".lower()
                if query not in search_blob:
                    continue
            filtered.append(it)

        if hasattr(self, "_hist_count_lbl"):
            self._hist_count_lbl.configure(text=f"Показано: {min(len(filtered), 25)} из {len(filtered)} (Всего: {len(history)})")

        if not filtered:
            ctk.CTkLabel(
                self._hist_scroll, text="Нет артефактов, соответствующих фильтрам.",
                font=("Segoe UI", 12), text_color=C.TEXT_DIM,
            ).pack(pady=40)
            return

        for item in filtered[:25]:
            card = _FastFrame(self._hist_scroll, bg=C.BG_CARD_ALT, highlightthickness=1, highlightbackground=C.BORDER, bd=0)
            card.pack(fill="x", pady=3, padx=4)

            btn_box = _FastFrame(card, bg=C.BG_CARD_ALT)
            btn_box.pack(side="right", padx=8, pady=6)

            _FastButton(
                btn_box, text="📥 В калькулятор", padx=8, pady=3,
                font=("Segoe UI", 10, "bold"),
                fg_color=C.TEAL_BTN, hover_color=C.TEAL_HOVER, text_color=C.TEXT_PRIMARY,
                command=lambda it=item: self._load_history_item_to_calc(it),
            ).pack(side="left", padx=2)

            _FastButton(
                btn_box, text="⚖️ В сравнение", padx=8, pady=3,
                font=("Segoe UI", 10, "bold"),
                fg_color=C.GRAY_SLATE, hover_color=C.GRAY_SLATE_H, text_color=C.TEXT_PRIMARY,
                command=lambda it=item: self.compare_with_history_item(it),
            ).pack(side="left", padx=2)

            _FastButton(
                btn_box, text="📋", padx=6, pady=3,
                font=("Segoe UI", 10),
                fg_color=C.GREEN_BTN, hover_color=C.GREEN_HOVER, text_color=C.BG_DEEP,
                command=lambda it=item: self._copy_history_item_card(it),
            ).pack(side="left", padx=2)

            _FastButton(
                btn_box, text="🗑️", padx=6, pady=3,
                font=("Segoe UI", 10),
                fg_color=C.GRAY, hover_color=C.RED_ERR, text_color=C.TEXT_PRIMARY,
                command=lambda it=item: self._delete_history_item(it),
            ).pack(side="left", padx=2)

            info_box = _FastFrame(card, bg=C.BG_CARD_ALT)
            info_box.pack(side="left", fill="both", expand=True, padx=8, pady=4)

            rank = item.get("rank", "—")
            rank_color = RANK_COLORS.get(rank, C.TEXT_PRIMARY)
            slot_name = item.get("slot", "")
            emoji = SLOT_EMOJI.get(slot_name, "📦")
            lvl = item.get("level", "+0")
            set_key = item.get("set_key", "")
            set_ru = cb.get_set_name_ru(set_key) or set_key
            loc = item.get("location", "Инвентарь")
            loc_str = f"👤 {loc}" if loc != "Инвентарь" else "🎒 Инвентарь"
            pot = item.get("potential_pct", 0.0)
            curr = item.get("current_pct", 0.0)

            title_txt = f"[{rank}]  {emoji} {slot_name} {lvl}"
            if set_ru:
                title_txt += f"  •  {set_ru}"
            title_txt += f"   ({loc_str})   🎯 {item.get('main_stat', '—')}   |   PAV: {curr:.1f}% (потолок {pot:.1f}%)"

            _FastLabel(
                info_box, text=title_txt, font=("Segoe UI", 11, "bold"),
                bg=C.BG_CARD_ALT, text_color=rank_color, anchor="w",
            ).pack(fill="x")

            stats_strs = [f"{k}: {v}" for k, v in item.get("substats", {}).items()]
            _FastLabel(
                info_box, text="   •  " + "   •  ".join(stats_strs),
                font=("Consolas", 10), bg=C.BG_CARD_ALT, text_color=C.TEXT_SUBS, anchor="w",
            ).pack(fill="x", pady=(2, 0))

    def _load_history_item_to_calc(self, item: dict):
        subs = []
        for s, v in item.get("substats", {}).items():
            try:
                subs.append((s, good_adapter.D(str(v))))
            except Exception:
                pass
        lvl_raw = str(item.get("level", "0")).replace("+", "").strip()
        lvl = int(lvl_raw) if lvl_raw.isdigit() else 0
        parsed = good_adapter.ParsedArtifact(
            slot=item.get("slot", "Перо смерти"),
            main_stat=item.get("main_stat", "Сила атаки"),
            level=lvl, rarity=5, substats=subs,
            set_key=item.get("set_key", ""),
            location=item.get("location", ""),
        )
        self.load_artifact_from_good(parsed)

    def _copy_history_item_card(self, c: dict):
        stats_text = "\n".join(f"  • {k}: {v}" for k, v in c.get("substats", {}).items())
        set_ru = cb.get_set_name_ru(c.get("set_key", ""))
        set_line = f"🔮 Сет: {set_ru}\n" if set_ru else ""
        card_text = (
            "⚔️ **Genshin Impact — Карточка Артефакта** ⚔️\n"
            f"🧩 Тип: {c.get('slot', '—')}\n"
            f"{set_line}"
            f"🎯 Основной стат: {c.get('main_stat', '—')}\n"
            f"🎯 Роль: {c.get('role', '—')}\n"
            f"🔹 Уровень: {c.get('level', '+0')} | 🏆 Ранг: **{c.get('rank', '—')}**\n"
            f"📊 Текущая ценность (PAV): {c.get('current_pct', 0)}%\n"
            f"🚀 Потолок на +20: **{c.get('potential_pct', 0)}%**\n"
            f"📜 Характеристики:\n{stats_text}\n"
            "───────────────\n"
            "Сгенерировано в Artifact Calculator"
        )
        self.clipboard_clear()
        self.clipboard_append(card_text)

    def _delete_history_item(self, target_item: dict):
        history = self._load_history()
        updated = [h for h in history if h != target_item]
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(updated, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
        self._refresh_history_view()

    def _clear_all_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
        except Exception:
            pass
        self._refresh_history_view()

    def open_history_window(self):
        self.show_view("history")
        return self.view_history

    # ══════════════════════════════════════════════════════════════════
    #  ВКЛАДКА: СРАВНЕНИЕ АРТЕФАКТОВ (Side-by-Side без наэкранных меню)
    # ══════════════════════════════════════════════════════════════════
    def _build_compare_view(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color=C.BG_DARK, corner_radius=10)
        top_bar.pack(fill="x", padx=4, pady=(2, 4))

        ctk.CTkLabel(
            top_bar, text="⚖️ Сравнение артефактов",
            font=("Segoe UI", 14, "bold"), text_color=C.GOLD,
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkLabel(
            top_bar, text="Слот:", font=("Segoe UI", 11), text_color=C.TEXT_MUTED,
        ).pack(side="left", padx=(8, 4))

        slots_buttons = [
            ("Все слоты", "Все"),
            ("Цветок жизни", "🌺 Цветок"),
            ("Перо смерти", "✒️ Перо"),
            ("Пески времени", "⏳ Пески"),
            ("Кубок пространства", "🍷 Кубок"),
            ("Корона разума", "👑 Корона"),
        ]

        self._compare_slot_buttons = {}
        for s_key, s_label in slots_buttons:
            btn = ctk.CTkButton(
                top_bar, text=s_label, width=95, height=28,
                font=("Segoe UI", 11, "bold"),
                fg_color=C.CYAN_DIM if s_key == "Все слоты" else C.BG_CARD,
                text_color=C.BG_DEEP if s_key == "Все слоты" else C.TEXT_MUTED,
                hover_color=C.BG_HOVER,
                command=lambda k=s_key: self._on_compare_slot_filter_change(k),
            )
            btn.pack(side="left", padx=3)
            self._compare_slot_buttons[s_key] = btn

        sel_box = ctk.CTkFrame(parent, fg_color=C.TRANSPARENT)
        sel_box.pack(fill="x", padx=4, pady=(2, 4))
        sel_box.grid_columnconfigure(0, weight=1)
        sel_box.grid_columnconfigure(1, weight=1)

        # Колонка А
        self._col_a_frame = ctk.CTkFrame(sel_box, fg_color=C.BG_DARK, corner_radius=10)
        self._col_a_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        a_hdr = ctk.CTkFrame(self._col_a_frame, fg_color=C.TRANSPARENT)
        a_hdr.pack(fill="x", padx=10, pady=(6, 4))
        ctk.CTkLabel(
            a_hdr, text="Артефакт А", font=("Segoe UI", 13, "bold"), text_color=C.CYAN,
        ).pack(side="left")

        self._btn_a_curr = ctk.CTkButton(
            a_hdr, text="⚡ Текущий", width=85, height=24, font=("Segoe UI", 10, "bold"),
            fg_color=C.CYAN_DIM, text_color=C.BG_DEEP, hover_color=C.CYAN,
            command=lambda: self._set_compare_source_a("current"),
        )
        self._btn_a_curr.pack(side="right", padx=(2, 0))

        self._btn_a_hist = ctk.CTkButton(
            a_hdr, text="📜 Из истории", width=95, height=24, font=("Segoe UI", 10),
            fg_color=C.BG_CARD, text_color=C.TEXT_MUTED, hover_color=C.BG_HOVER,
            command=lambda: self._set_compare_source_a("history"),
        )
        self._btn_a_hist.pack(side="right", padx=(0, 2))

        self._compare_a_container = ctk.CTkFrame(self._col_a_frame, fg_color=C.TRANSPARENT)
        self._compare_a_container.pack(fill="both", expand=True, padx=8, pady=(2, 4))

        # Колонка B
        self._col_b_frame = ctk.CTkFrame(sel_box, fg_color=C.BG_DARK, corner_radius=10)
        self._col_b_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        b_hdr = ctk.CTkFrame(self._col_b_frame, fg_color=C.TRANSPARENT)
        b_hdr.pack(fill="x", padx=10, pady=(6, 4))
        ctk.CTkLabel(
            b_hdr, text="Артефакт B (Из истории)", font=("Segoe UI", 13, "bold"), text_color=C.GOLD,
        ).pack(side="left")

        self._compare_b_container = ctk.CTkFrame(self._col_b_frame, fg_color=C.TRANSPARENT)
        self._compare_b_container.pack(fill="both", expand=True, padx=8, pady=(2, 4))

        # Карточки сравнения
        self._compare_cards_frame = ctk.CTkFrame(parent, fg_color=C.BG_DARK, corner_radius=10)
        self._compare_cards_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))

    def _on_compare_slot_filter_change(self, slot_key: str):
        self._ensure_compare_built()
        self._compare_slot_filter.set(slot_key)
        for s_key, btn in self._compare_slot_buttons.items():
            if s_key == slot_key:
                btn.configure(fg_color=C.CYAN_DIM, text_color=C.BG_DEEP)
            else:
                btn.configure(fg_color=C.BG_CARD, text_color=C.TEXT_MUTED)
        self._refresh_compare_view()

    def _set_compare_source_a(self, source: str):
        self._ensure_compare_built()
        self._compare_source_a.set(source)
        if source == "current":
            self._btn_a_curr.configure(fg_color=C.CYAN_DIM, text_color=C.BG_DEEP, font=("Segoe UI", 10, "bold"))
            self._btn_a_hist.configure(fg_color=C.BG_CARD, text_color=C.TEXT_MUTED, font=("Segoe UI", 10))
            self._compare_artifact_a = self._get_current_artifact_for_compare()
        else:
            self._btn_a_hist.configure(fg_color=C.CYAN_DIM, text_color=C.BG_DEEP, font=("Segoe UI", 10, "bold"))
            self._btn_a_curr.configure(fg_color=C.BG_CARD, text_color=C.TEXT_MUTED, font=("Segoe UI", 10))
        self._refresh_compare_view()

    def _get_current_artifact_for_compare(self) -> Optional[dict]:
        if not self._result_is_current() or not self.last_calculation:
            return None
        c = self.last_calculation
        return {
            "slot": c["slot"],
            "main_stat": c["main_stat"],
            "level": c["level"],
            "rank": c["rank"],
            "current_pct": c["current_pct"],
            "potential_pct": c["potential_pct"],
            "expected_pct": c["expected_pct"],
            "substats": dict(c["substats"]),
            "set_key": c.get("set_key", ""),
            "location": "Текущий в калькуляторе",
            "role": c.get("role", ""),
            "is_current": True,
        }

    def _refresh_compare_view(self):
        if not hasattr(self, "_compare_a_container"):
            return

        for child in self._compare_a_container.winfo_children():
            child.destroy()
        for child in self._compare_b_container.winfo_children():
            child.destroy()

        history = self._load_history()
        slot_filter = self._compare_slot_filter.get()
        filtered_history = [
            h for h in history
            if slot_filter == "Все слоты" or h.get("slot") == slot_filter
        ]

        # ─── Рендер колонки А ───
        if self._compare_source_a.get() == "current":
            curr = self._get_current_artifact_for_compare()
            self._compare_artifact_a = curr
            if curr:
                rank_col = RANK_COLORS.get(curr["rank"], C.TEXT_PRIMARY)
                set_ru = cb.get_set_name_ru(curr.get("set_key", "")) or curr.get("set_key", "")
                box = ctk.CTkFrame(self._compare_a_container, fg_color=C.BG_CARD_ALT, corner_radius=6, height=135)
                box.pack(fill="x", padx=2, pady=2)
                box.pack_propagate(False)

                ctk.CTkLabel(
                    box, text=f"⚡ [{curr['rank']}] {SLOT_EMOJI.get(curr['slot'],'📦')} {curr['slot']} {curr['level']} — {set_ru or 'Без сета'}",
                    font=("Segoe UI", 11, "bold"), text_color=rank_col, anchor="w",
                ).pack(fill="x", padx=10, pady=(8, 2))
                ctk.CTkLabel(
                    box, text=f"🎯 {curr['main_stat']}  |  PAV: {curr['current_pct']:.1f}% (потолок {curr['potential_pct']:.1f}%)",
                    font=("Segoe UI", 10), text_color=C.CYAN, anchor="w",
                ).pack(fill="x", padx=10, pady=1)

                subs_txt = " • ".join(f"{s}: {v}" for s, v in curr["substats"].items())
                ctk.CTkLabel(
                    box, text=subs_txt, font=("Consolas", 9), text_color=C.TEXT_SUBS, anchor="w", wraplength=480,
                ).pack(fill="x", padx=10, pady=(2, 4))
            else:
                ctk.CTkLabel(
                    self._compare_a_container,
                    text="Калькулятор пуст. Рассчитайте артефакт или выберите «Из истории».",
                    font=("Segoe UI", 11), text_color=C.TEXT_DIM,
                ).pack(pady=35)
        else:
            if not filtered_history:
                ctk.CTkLabel(
                    self._compare_a_container, text="Нет артефактов в истории по данному слоту.",
                    font=("Segoe UI", 11), text_color=C.TEXT_DIM,
                ).pack(pady=35)
            else:
                scroll_a = ctk.CTkScrollableFrame(self._compare_a_container, height=135, fg_color=C.BG_CARD)
                scroll_a.pack(fill="both", expand=True, padx=2, pady=2)
                if not self._compare_artifact_a and filtered_history:
                    self._compare_artifact_a = filtered_history[0]

                for item in filtered_history[:25]:
                    is_sel = (self._compare_artifact_a == item)
                    row_btn = _FastButton(
                        scroll_a,
                        text=f"[{item.get('rank','—')}] {SLOT_EMOJI.get(item.get('slot',''),'📦')} {item.get('slot','')} {item.get('level','+0')} | {cb.get_set_name_ru(item.get('set_key','')) or '—'} | 🎯 {item.get('main_stat','—')} — {item.get('potential_pct',0):.0f}%",
                        anchor="w",
                        font=("Segoe UI", 10, "bold" if is_sel else "normal"),
                        fg_color=C.BG_HOVER if is_sel else C.BG_CARD_ALT,
                        text_color=C.CYAN if is_sel else C.TEXT_PRIMARY,
                        padx=6, pady=4,
                        command=lambda it=item: self._select_compare_item_a(it),
                    )
                    row_btn.pack(fill="x", padx=2, pady=2)

        # ─── Рендер колонки B ───
        if not filtered_history:
            ctk.CTkLabel(
                self._compare_b_container, text="Нет артефактов в истории по данному слоту.",
                font=("Segoe UI", 11), text_color=C.TEXT_DIM,
            ).pack(pady=35)
        else:
            scroll_b = ctk.CTkScrollableFrame(self._compare_b_container, height=135, fg_color=C.BG_CARD)
            scroll_b.pack(fill="both", expand=True, padx=2, pady=2)

            if not self._compare_artifact_b and filtered_history:
                if len(filtered_history) > 1 and filtered_history[0] == self._compare_artifact_a:
                    self._compare_artifact_b = filtered_history[1]
                else:
                    self._compare_artifact_b = filtered_history[min(1, len(filtered_history) - 1)]

            for item in filtered_history[:25]:
                is_sel = (self._compare_artifact_b == item)
                row_btn = _FastButton(
                    scroll_b,
                    text=f"[{item.get('rank','—')}] {SLOT_EMOJI.get(item.get('slot',''),'📦')} {item.get('slot','')} {item.get('level','+0')} | {cb.get_set_name_ru(item.get('set_key','')) or '—'} | 🎯 {item.get('main_stat','—')} — {item.get('potential_pct',0):.0f}%",
                    anchor="w",
                    font=("Segoe UI", 10, "bold" if is_sel else "normal"),
                    fg_color=C.BG_HOVER if is_sel else C.BG_CARD_ALT,
                    text_color=C.GOLD if is_sel else C.TEXT_PRIMARY,
                    padx=6, pady=4,
                    command=lambda it=item: self._select_compare_item_b(it),
                )
                row_btn.pack(fill="x", padx=2, pady=2)

        self._update_comparison_display()

    def _select_compare_item_a(self, item: dict):
        self._compare_artifact_a = item
        self._refresh_compare_view()

    def _select_compare_item_b(self, item: dict):
        self._compare_artifact_b = item
        self._refresh_compare_view()

    def compare_with_history_item(self, item: dict):
        slot = item.get("slot", "Все слоты")
        self._on_compare_slot_filter_change(slot)
        if self._result_is_current() and self.last_calculation:
            self._set_compare_source_a("current")
            self._compare_artifact_b = item
        else:
            self._set_compare_source_a("history")
            self._compare_artifact_a = item
            self._compare_artifact_b = None
        self.show_view("compare")

    def _update_comparison_display(self):
        if not hasattr(self, "_compare_cards_frame"):
            return

        for child in self._compare_cards_frame.winfo_children():
            child.destroy()

        art_a = self._compare_artifact_a
        art_b = self._compare_artifact_b

        if not art_a or not art_b:
            ctk.CTkLabel(
                self._compare_cards_frame,
                text="ℹ️ Выберите артефакты в колонках А и B выше для детального сравнения.",
                font=("Segoe UI", 13), text_color=C.TEXT_DIM,
            ).pack(pady=60)
            return

        # Карточки A и B side-by-side
        cards_row = ctk.CTkFrame(self._compare_cards_frame, fg_color=C.TRANSPARENT)
        cards_row.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        cards_row.grid_columnconfigure(0, weight=1)
        cards_row.grid_columnconfigure(1, weight=1)

        def render_side_card(parent, item, other_item, col, accent, label_title):
            card = ctk.CTkFrame(parent, fg_color=C.BG_CARD_ALT, corner_radius=10, border_width=1, border_color=accent)
            card.grid(row=0, column=col, sticky="nsew", padx=6, pady=2)

            rank = item.get("rank", "—")
            rank_color = RANK_COLORS.get(rank, C.TEXT_PRIMARY)
            slot = item.get("slot", "—")
            emoji = SLOT_EMOJI.get(slot, "📦")
            lvl = item.get("level", "+0")
            set_ru = cb.get_set_name_ru(item.get("set_key", "")) or item.get("set_key", "Без сета")

            hdr = ctk.CTkFrame(card, fg_color=C.TRANSPARENT)
            hdr.pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(
                hdr, text=f"{label_title}: {rank}", font=("Segoe UI", 20, "bold"), text_color=rank_color,
            ).pack(side="left")
            ctk.CTkLabel(
                hdr, text=f"{emoji} {slot} {lvl}", font=("Segoe UI", 12, "bold"), text_color=C.TEXT_PRIMARY,
            ).pack(side="right")

            ctk.CTkLabel(
                card, text=f"🔮 Сет: {set_ru} | 🎯 {item.get('main_stat', '—')}",
                font=("Segoe UI", 11), text_color=C.GOLD, anchor="w",
            ).pack(fill="x", padx=12, pady=(0, 4))

            # PAV шкалы
            pav_box = ctk.CTkFrame(card, fg_color=C.BG_DARK, corner_radius=6)
            pav_box.pack(fill="x", padx=12, pady=4)

            curr_a = item.get("current_pct", 0.0)
            pot_a = item.get("potential_pct", 0.0)
            curr_b = other_item.get("current_pct", 0.0)
            pot_b = other_item.get("potential_pct", 0.0)

            # Текущий PAV
            p1 = ctk.CTkFrame(pav_box, fg_color=C.TRANSPARENT)
            p1.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(p1, text="Текущий PAV:", font=("Segoe UI", 10), text_color=C.TEXT_MUTED, width=80, anchor="w").pack(side="left")
            b1 = ctk.CTkProgressBar(p1, width=120, height=8, corner_radius=4, fg_color=C.BG_DEEP, progress_color=accent)
            b1.pack(side="left", padx=4)
            b1.set(min(curr_a / 100.0, 1.0))
            diff_curr = curr_a - curr_b
            diff_curr_txt = f" ({'+' if diff_curr > 0 else ''}{diff_curr:.1f}%)" if diff_curr != 0 else ""
            curr_col = C.GREEN if diff_curr > 0 else (C.TEXT_MUTED if diff_curr == 0 else C.YELLOW_WARN)
            ctk.CTkLabel(p1, text=f"{curr_a:.1f}%{diff_curr_txt}", font=("Segoe UI", 10, "bold"), text_color=curr_col).pack(side="left", padx=4)

            # Потолок PAV
            p2 = ctk.CTkFrame(pav_box, fg_color=C.TRANSPARENT)
            p2.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(p2, text="Потолок (+20):", font=("Segoe UI", 10), text_color=C.TEXT_MUTED, width=80, anchor="w").pack(side="left")
            b2 = ctk.CTkProgressBar(p2, width=120, height=8, corner_radius=4, fg_color=C.BG_DEEP, progress_color=accent)
            b2.pack(side="left", padx=4)
            b2.set(min(pot_a / 100.0, 1.0))
            diff_pot = pot_a - pot_b
            diff_pot_txt = f" ({'+' if diff_pot > 0 else ''}{diff_pot:.1f}%)" if diff_pot != 0 else ""
            pot_col = C.GREEN if diff_pot > 0 else (C.TEXT_MUTED if diff_pot == 0 else C.YELLOW_WARN)
            ctk.CTkLabel(p2, text=f"{pot_a:.1f}%{diff_pot_txt}", font=("Segoe UI", 10, "bold"), text_color=pot_col).pack(side="left", padx=4)

            # Сабстаты
            subs_frame = ctk.CTkFrame(card, fg_color=C.TRANSPARENT)
            subs_frame.pack(fill="both", expand=True, padx=12, pady=(2, 4))

            all_stats = list(dict.fromkeys(list(item.get("substats", {}).keys()) + list(other_item.get("substats", {}).keys())))
            for stat in all_stats:
                val = item.get("substats", {}).get(stat)
                other_val = other_item.get("substats", {}).get(stat)

                s_row = ctk.CTkFrame(subs_frame, fg_color=C.TRANSPARENT)
                s_row.pack(fill="x", pady=1)

                if val is not None:
                    if other_val is not None:
                        diff = val - other_val
                        if diff > 0.05:
                            tag_txt = f"▲ +{diff:.1f}"
                            tag_col = C.GREEN
                        elif diff < -0.05:
                            tag_txt = f"▼ -{abs(diff):.1f}"
                            tag_col = C.TEXT_MUTED
                        else:
                            tag_txt = "="
                            tag_col = C.TEXT_MUTED
                    else:
                        tag_txt = "★ только здесь"
                        tag_col = accent

                    ctk.CTkLabel(s_row, text=f"• {stat}:", font=("Segoe UI", 10), text_color=C.TEXT_PRIMARY, width=140, anchor="w").pack(side="left")
                    ctk.CTkLabel(s_row, text=f"{val:.1f}" if isinstance(val, float) else str(val), font=("Segoe UI", 10, "bold"), text_color=C.TEXT_PRIMARY).pack(side="left", padx=4)
                    ctk.CTkLabel(s_row, text=tag_txt, font=("Segoe UI", 9, "bold"), text_color=tag_col).pack(side="left", padx=6)
                else:
                    ctk.CTkLabel(s_row, text=f"• {stat}: —", font=("Segoe UI", 10), text_color=C.TEXT_DIM, width=140, anchor="w").pack(side="left")

        render_side_card(cards_row, art_a, art_b, 0, C.CYAN, "Артефакт А")
        render_side_card(cards_row, art_b, art_a, 1, C.GOLD, "Артефакт B")

        # Итоговый вердикт
        verdict_box = ctk.CTkFrame(self._compare_cards_frame, fg_color=C.BG_PANEL, corner_radius=8)
        verdict_box.pack(fill="x", padx=14, pady=(2, 4))

        pot_diff = art_a.get("potential_pct", 0) - art_b.get("potential_pct", 0)
        if abs(pot_diff) < 0.5:
            win_msg = "⚖️ Артефакты практически равны по общему потенциалу!"
            win_col = C.CYAN
        elif pot_diff > 0:
            win_msg = f"🏆 Артефакт А превосходит Артефакт B по потенциалу на +{pot_diff:.1f}% ({art_a.get('potential_pct',0):.1f}% vs {art_b.get('potential_pct',0):.1f}%)"
            win_col = C.CYAN
        else:
            win_msg = f"🏆 Артефакт B превосходит Артефакт А по потенциалу на +{abs(pot_diff):.1f}% ({art_b.get('potential_pct',0):.1f}% vs {art_a.get('potential_pct',0):.1f}%)"
            win_col = C.GOLD

        ctk.CTkLabel(
            verdict_box, text=win_msg, font=("Segoe UI", 12, "bold"), text_color=win_col,
        ).pack(side="left", padx=12, pady=8)

        act_box = ctk.CTkFrame(verdict_box, fg_color=C.TRANSPARENT)
        act_box.pack(side="right", padx=8, pady=4)

        ctk.CTkButton(
            act_box, text="📥 Загрузить А", width=110, height=26, font=("Segoe UI", 10, "bold"),
            fg_color=C.TEAL_BTN, hover_color=C.TEAL_HOVER,
            command=lambda: self._load_history_item_to_calc(art_a),
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            act_box, text="📥 Загрузить B", width=110, height=26, font=("Segoe UI", 10, "bold"),
            fg_color=C.GREEN_BTN, hover_color=C.GREEN_HOVER,
            command=lambda: self._load_history_item_to_calc(art_b),
        ).pack(side="left", padx=3)

    def open_compare_window(self):
        history = self._load_history()
        has_curr = self._result_is_current() and (self.last_calculation is not None)
        if len(history) < 2 and not (has_curr and len(history) >= 1):
            self._show_message("⚠️ Для сравнения нужно минимум 2 артефакта в истории.\n"
                               "Рассчитайте и сохраните несколько артефактов.")
            self._compare_win = None
            return None
        self._compare_win = self.view_compare
        self.show_view("compare")
        return self.view_compare


# ═══════════════════════════════════════════════════════════════════════
#  ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = ArtifactCalculatorApp()
    app.mainloop()
