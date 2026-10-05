"""Navigation Sidebar for Genshin Impact Artifact Calculator.

Provides clean navigation between Calculator, Scanner/Import,
Character Builds, History & Compare, and About views.
"""
from __future__ import annotations

from typing import Callable, List, Tuple
import customtkinter as ctk

from ..theme import ThemeColors, FONTS, METRICS, button_nav_style


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_nav_click: Callable[[str], None], **kwargs):
        # Set default width and background
        kwargs.setdefault("width", METRICS["sidebar_width"])
        kwargs.setdefault("fg_color", ThemeColors.BG_PANEL)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        
        self.on_nav_click = on_nav_click
        self.buttons: List[Tuple[str, ctk.CTkButton]] = []
        self.active_view: str = "calculator"
        
        self._build_sidebar()

    def _build_sidebar(self):
        # App Title / Logo Area
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=15, pady=(20, 25))

        title_lbl = ctk.CTkLabel(
            logo_frame,
            text="✦ GENSHIN CALC",
            font=FONTS["title"],
            text_color=ThemeColors.GOLD,
            anchor="w",
        )
        title_lbl.pack(fill="x")

        subtitle_lbl = ctk.CTkLabel(
            logo_frame,
            text="Artifact Analyzer v2",
            font=FONTS["caption"],
            text_color=ThemeColors.TEXT_MUTED,
            anchor="w",
        )
        subtitle_lbl.pack(fill="x")

        # Separator line
        sep = ctk.CTkFrame(self, height=1, fg_color=ThemeColors.BORDER)
        sep.pack(fill="x", padx=15, pady=(0, 15))

        # Navigation Items
        nav_items: List[Tuple[str, str, str]] = [
            ("calculator", "⚖️", "Калькулятор"),
            ("scanner", "📥", "Импорт / Скан"),
            ("builds", "👤", "Билды героев"),
            ("history", "📜", "История и Сравнение"),
            ("about", "ℹ️", "О программе"),
        ]

        for view_id, icon, label in nav_items:
            style = button_nav_style(active=(view_id == "calculator"))
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}  {label}",
                height=38,
                command=lambda vid=view_id: self._handle_nav(vid),
                **style,
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.buttons.append((view_id, btn))

    def _handle_nav(self, view_id: str):
        self.active_view = view_id
        for vid, btn in self.buttons:
            is_active = (vid == view_id)
            style = button_nav_style(active=is_active)
            btn.configure(**style)
            
        if self.on_nav_click:
            self.on_nav_click(view_id)

    def set_active(self, view_id: str):
        self._handle_nav(view_id)
