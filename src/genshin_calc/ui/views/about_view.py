"""About View displaying application metadata, credits, sources, and hotkeys."""
from __future__ import annotations

import customtkinter as ctk

from ..theme import (
    ThemeColors,
    FONTS,
    METRICS,
    card_style,
    panel_style,
)


class AboutView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Title Card
        title_card = ctk.CTkFrame(container, **card_style())
        title_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            title_card,
            text="⚔️ GENSHIN ARTIFACT CALCULATOR v2.0",
            font=FONTS["title"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        ).pack(anchor="w", padx=20, pady=(20, 5))

        ctk.CTkLabel(
            title_card,
            text="Модульный калькулятор, оценщик и аналитик артефактов в стилистике Genshin Impact.",
            font=FONTS["body"],
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", padx=20, pady=(0, 20))

        # Sources & Credits Card
        sources_card = ctk.CTkFrame(container, **card_style(alt=True))
        sources_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            sources_card,
            text="📚 Источники данных и математики",
            font=FONTS["header"],
            text_color=ThemeColors.CYAN,
            anchor="w",
        ).pack(anchor="w", padx=20, pady=(15, 8))

        sources_text = (
            "✦ AnimeGameData & Dimbreath: Точные таблицы весов появления сабстатов и шаги дискретных роллов 5★ артефактов.\n"
            "✦ KeqingMains (KQM) & Akasha System: Экспертные коэффициенты полезности статов под персонажей и роли.\n"
            "✦ Enka.Network API: Протокол загрузки витрин персонажей и артефактов по открытому UID.\n"
            "✦ Inventory Kamera: Интеграция с официальным OCR-сканером инвентаря Genshin Impact и GOOD JSON."
        )
        ctk.CTkLabel(
            sources_card,
            text=sources_text,
            font=FONTS["small"],
            text_color=ThemeColors.TEXT_PRIMARY,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # Hotkeys & Controls Card
        hotkeys_card = ctk.CTkFrame(container, **card_style())
        hotkeys_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            hotkeys_card,
            text="⌨️ Сочетания клавиш (работают в RU и EN раскладках)",
            font=FONTS["header"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        ).pack(anchor="w", padx=20, pady=(15, 8))

        hotkeys_text = (
            "• Ctrl+A: Выделить всё содержимое поля ввода\n"
            "• Ctrl+C: Скопировать выделенный текст в буфер обмена\n"
            "• Ctrl+V: Вставить текст или спарсить статы артефакта из буфера\n"
            "• Ctrl+X: Вырезать выделенный фрагмент"
        )
        ctk.CTkLabel(
            hotkeys_card,
            text=hotkeys_text,
            font=FONTS["small"],
            text_color=ThemeColors.TEXT_SUBS,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 15))
